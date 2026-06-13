"""Phase 6 — verify Gradio/API/PDF/JSON use the same evidence band formatting."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / "release"
if str(RELEASE) not in sys.path:
    sys.path.insert(0, str(RELEASE))

from src.app_report_formatting import (  # noqa: E402
    EVIDENCE_STRENGTH_LABEL,
    build_api_analyze_response,
    build_evidence_axis_cards,
    enrich_phase9c_response,
    gradio_suspicious_segments_table,
)
from src.evidence_calibration import evidence_band  # noqa: E402
from src.pdf_report_generator import _segments_for_report  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--live-audio", default="", help="Optional short audio for end-to-end check")
    p.add_argument("--out-dir", default=str(ROOT / "reports" / "release_audit" / "phase6_calibration_2026-06-13"))
    return p.parse_args()


def mock_phase9c() -> dict:
    return {
        "status": "experimental_forensic_prototype",
        "case_id": "PHASE6-MOCK",
        "origin_evidence": {
            "prediction_success": True,
            "probability": 0.97,
            "threshold_candidate": 0.92,
            "label": "elevated_indicator",
            "evidence_label": "elevated_indicator",
            "evidence_strength": "pending_fusion",
        },
        "replay_evidence": {
            "prediction_success": True,
            "probability": 0.12,
            "threshold_candidate": 0.65,
            "label": "low_indicator",
            "evidence_label": "low_indicator",
        },
        "mixer_channel_evidence": {
            "prediction_success": False,
            "probability": None,
            "threshold_candidate": 0.75,
        },
        "partial_fabrication_evidence": {
            "prediction_success": True,
            "max_segment_probability": 0.88,
            "threshold_candidate": 0.95,
            "partial_localization_gate": "localized_pattern_supported",
            "partial_fusion_eligible": True,
            "partial_evidence_strength_for_fusion": "high",
            "high_segment_fraction": 0.1,
            "topk_minus_rest_probability": 0.35,
            "evidence_label": "localized_pattern_supported",
        },
        "segment_candidates": [
            {
                "start_sec": 10.0,
                "end_sec": 14.0,
                "partial_probability": 0.88,
                "candidate_rank": 1,
                "above_threshold": False,
            }
        ],
        "limitations": ["experimental_forensic_prototype"],
    }


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    phase9c = mock_phase9c()
    enriched = enrich_phase9c_response(phase9c, file_name="mock.wav")
    api = build_api_analyze_response(file_name="mock.wav", phase9c_result=phase9c)
    cards = build_evidence_axis_cards(enriched)
    table = gradio_suspicious_segments_table(enriched)
    pdf_rows = _segments_for_report(enriched)

    checks: list[dict] = []

    origin_card = next(c for c in cards if "origin" in c["axis_name"].lower())
    checks.append(
        {
            "check": "origin_card_uses_band_not_raw",
            "pass": EVIDENCE_STRENGTH_LABEL in origin_card.get("score_text", "")
            and "0.970" not in origin_card.get("score_text", ""),
            "detail": origin_card.get("score_text"),
        }
    )

    mixer_card = next(c for c in cards if "channel" in c["axis_name"].lower() or "mixer" in c["axis_name"].lower())
    checks.append(
        {
            "check": "mixer_unavailable_is_inconclusive",
            "pass": mixer_card.get("status") == "Inconclusive",
            "detail": mixer_card.get("score_text"),
        }
    )

    def _norm_rows(rows: list[list]) -> list[list[str]]:
        return [[str(c) for c in row] for row in rows]

    checks.append(
        {
            "check": "gradio_table_matches_pdf_segment_rows",
            "pass": _norm_rows(table) == _norm_rows(pdf_rows),
            "detail": f"gradio={table!r} pdf={pdf_rows!r}",
        }
    )

    checks.append(
        {
            "check": "api_and_enriched_same_forensic_summary",
            "pass": api.get("forensic_indicator_summary") == enriched.get("forensic_indicator_summary"),
            "detail": "forensic_indicator_summary",
        }
    )

    if table:
        seg_band = evidence_band("partial_segment", 0.88, prediction_success=True)
        table_band = table[0][2]
        checks.append(
            {
                "check": "segment_table_uses_band",
                "pass": seg_band in table_band,
                "detail": table_band,
            }
        )
    else:
        checks.append(
            {
                "check": "segment_table_uses_band",
                "pass": True,
                "detail": "skipped_no_visible_segment_table",
            }
        )

    if args.live_audio:
        from src.inference_pipeline import analyze_audio_file

        live = analyze_audio_file(args.live_audio, case_id="PHASE6-LIVE", return_debug=False)
        live_enriched = enrich_phase9c_response(live, file_name=Path(args.live_audio).name)
        live_api = build_api_analyze_response(
            file_name=Path(args.live_audio).name, phase9c_result=live
        )
        checks.append(
            {
                "check": "live_api_enriched_cards_match_count",
                "pass": len(live_api.get("evidence_axis_cards") or [])
                == len(build_evidence_axis_cards(live_enriched)),
                "detail": args.live_audio,
            }
        )

    df_checks = __import__("pandas").DataFrame(checks)
    df_checks.to_csv(out_dir / "phase6_consistency_checks.csv", index=False)
    passed = bool(df_checks["pass"].all())
    report = [
        "# Phase 6 consistency checks",
        "",
        f"Overall: **{'PASS' if passed else 'FAIL'}**",
        "",
        df_checks.to_string(index=False),
    ]
    (out_dir / "phase6_consistency_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    (out_dir / "phase6_mock_enriched.json").write_text(json.dumps(enriched, indent=2, default=str), encoding="utf-8")
    print("\n".join(report))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
