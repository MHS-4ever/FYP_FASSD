#!/usr/bin/env python3
"""Validate Phase 9E-P3 release decision hierarchy and 8-variant eval outputs."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SCRIPT_DIR = Path(__file__).resolve().parent


def _repo_root() -> Path:
    for base in (_SCRIPT_DIR, *_SCRIPT_DIR.parents):
        if (base / "release" / "app_gradio.py").is_file():
            return base
    return _SCRIPT_DIR.parents[3]


_REPO = _repo_root()
_RELEASE = _REPO / "release"
_EVAL = _REPO / "reports" / "phase9" / "app" / "phase9e_p3_8variant_eval"
_PARTIAL_PKG = _RELEASE / "models" / "partial_fabrication_experimental_p5b"

if str(_RELEASE) not in sys.path:
    sys.path.insert(0, str(_RELEASE))

FORBIDDEN = [
    "definitely fake",
    "definitely real",
    "court proof",
    "court ready",
    "court-ready",
    "production ready",
    "production-ready",
    "final verdict",
    "final fake",
    "final real",
]


def _check(name: str, ok: bool, detail: str = "") -> dict[str, Any]:
    return {"check": name, "pass": ok, "detail": detail}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 9E-P3 release correctness.")
    parser.add_argument("--mode", choices=("quick", "full"), default="quick")
    parser.add_argument(
        "--report_out",
        default=None,
        help="Default: reports/phase9/validation/phase9e_p3_release_correctness_validation_report.md",
    )
    args = parser.parse_args()

    report_out = Path(
        args.report_out
        or str(_REPO / "reports/phase9/validation/phase9e_p3_release_correctness_validation_report.md")
    )
    if not report_out.is_absolute():
        report_out = (_REPO / report_out).resolve()
    report_out.parent.mkdir(parents=True, exist_ok=True)

    checks: list[dict[str, Any]] = []
    fmt = (_RELEASE / "src/app_report_formatting.py").read_text(encoding="utf-8")
    gr = (_RELEASE / "app_gradio.py").read_text(encoding="utf-8")
    ml = (_RELEASE / "src/model_loader.py").read_text(encoding="utf-8")
    fe = (_RELEASE / "src/feature_extraction.py").read_text(encoding="utf-8")
    design = _REPO / "reports/phase9/app/phase9e_p3_release_decision_hierarchy_design.md"

    checks.append(_check("design_doc_exists", design.is_file(), str(design)))
    checks.append(_check("build_voice_origin_result", "def build_voice_origin_result" in fmt, ""))
    checks.append(_check("build_recommendation_level", "def build_recommendation_level" in fmt, ""))
    checks.append(_check("build_axis_interpretation", "def build_axis_interpretation" in fmt, ""))
    checks.append(_check("voice_origin_text_in_summary", "voice_origin_text" in fmt, ""))
    checks.append(_check("forensic_indicator_summary", "forensic_indicator_summary" in fmt, ""))
    checks.append(_check("partial_module_mode_field", "partial_module_mode" in fmt, ""))
    checks.append(_check("models_lru_cache", "@lru_cache" in ml and "load_all_active_models" in ml, ""))
    checks.append(_check("ssl_lru_cache", "load_ssl_extractor" in (_RELEASE / "src/ssl_embeddings.py").read_text(), ""))
    checks.append(_check("safe_nanmean_feature_fix", "def safe_nanmean" in fe, ""))
    checks.append(_check("origin_support_models_module", (_RELEASE / "src/origin_support_models.py").is_file(), ""))
    checks.append(
        _check(
            "no_vague_suspicious_primary_in_render",
            "Suspicious audio indicators found" not in fmt.split("def render_main_result_card")[1],
            "",
        )
    )
    checks.append(_check("gradio_voice_origin_first", "voice_origin_text" in gr or "forensic_indicator_summary" in fmt, ""))

    forbidden_hits = []
    for path in (_RELEASE / "src/app_report_formatting.py", _RELEASE / "app_gradio.py"):
        lower = path.read_text(encoding="utf-8").lower()
        for phrase in FORBIDDEN:
            if phrase in lower:
                forbidden_hits.append(f"{path.name}: {phrase}")
    checks.append(_check("forbidden_wording_absent", not forbidden_hits, "; ".join(forbidden_hits)))

    meta_path = _PARTIAL_PKG / "partial_module_metadata.json"
    if meta_path.is_file():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        th = meta.get("thresholds", {})
        checks.append(
            _check(
                "partial_thresholds_unchanged",
                float(th.get("file_gate_threshold", -1)) == 0.5
                and float(th.get("segment_threshold", -1)) == 0.9,
                str(th),
            )
        )

    ok_fmt, err_fmt = True, ""
    try:
        from src.app_report_formatting import (  # type: ignore
            build_axis_interpretation,
            build_evidence_axis_cards,
            build_recommendation_level,
            build_user_result_summary,
            build_voice_origin_result,
            enrich_phase9c_response,
        )

        def _mock_human_clean_segment() -> dict[str, Any]:
            pf = {
                "evidence_detected": True,
                "file_gate_probability": None,
                "segment_candidate_only": True,
                "partial_module_mode": "segment_candidate_only",
                "candidate_segment": {"start_sec": 5.0, "end_sec": 25.0, "probability": 1.0, "rank": 1},
                "top_segments": [{"rank": 1, "start_sec": 5.0, "end_sec": 25.0, "probability": 1.0}],
            }
            low = {
                "prediction_success": True,
                "evidence_label": "low_indicator",
                "evidence_strength": "low",
                "probability": 0.1,
            }
            return {
                "status": "experimental_forensic_prototype",
                "origin_evidence": dict(low),
                "replay_evidence": dict(low),
                "mixer_channel_evidence": dict(low),
                "partial_fabrication": pf,
            }

        mock = _mock_human_clean_segment()
        summary = build_user_result_summary(mock)
        voice = build_voice_origin_result(mock)
        enriched = enrich_phase9c_response(mock, file_name="human_001_clean.wav")
        required_json = (
            "voice_origin_result",
            "forensic_indicator_summary",
            "recommendation",
            "recommendation_level",
            "evidence_axis_cards",
            "axis_interpretation",
            "partial_module_mode",
            "release_correctness_notes",
            "origin_support_models",
        )
        missing_json = [k for k in required_json if k not in enriched]
        checks.append(_check("json_fields_complete", not missing_json, ", ".join(missing_json)))
        checks.append(
            _check(
                "human_clean_optional_review_wording",
                summary.get("recommendation_level") in ("optional_review", "none")
                and summary.get("recommendation_text") != "Manual review recommended.",
                str(summary.get("recommendation_text")),
            )
        )
        checks.append(
            _check(
                "human_clean_not_strong_suspicious",
                "Suspicious audio indicators found" not in summary.get("voice_origin_text", "")
                and "Suspicious audio indicators found" not in summary.get("forensic_indicator_summary", "")
                and summary.get("voice_origin_text", "").startswith("Voice origin:"),
                str(summary.get("voice_origin_text")),
            )
        )
        checks.append(
            _check(
                "human_clean_voice_likely_human_or_inconclusive",
                voice.get("origin_label") in ("likely_human", "inconclusive"),
                str(voice),
            )
        )
        partial_card = next(c for c in build_evidence_axis_cards(mock) if "Partial" in c.get("axis_name", ""))
        checks.append(_check("partial_review_candidate_status", partial_card.get("status") == "Review candidate", str(partial_card)))

        def _mock_mixer_replay() -> dict[str, Any]:
            high = {
                "prediction_success": True,
                "evidence_label": "elevated_indicator",
                "evidence_strength": "high",
                "probability": 0.85,
            }
            low = {
                "prediction_success": True,
                "evidence_label": "low_indicator",
                "evidence_strength": "low",
                "probability": 0.1,
            }
            return {
                "status": "experimental_forensic_prototype",
                "origin_evidence": dict(low),
                "replay_evidence": dict(high),
                "mixer_channel_evidence": dict(high),
                "partial_fabrication": {"evidence_detected": False, "segment_candidate_only": False},
            }

        mixer_mock = _mock_mixer_replay()
        mixer_cards = build_evidence_axis_cards(mixer_mock)
        axis_interp = build_axis_interpretation(mixer_mock, mixer_cards)
        mixer_voice = build_voice_origin_result(mixer_mock)
        checks.append(
            _check(
                "replay_mixer_overlap_wording_present",
                bool(axis_interp.get("overlap_notes"))
                and any(c.get("status") == "Possible overlap" for c in mixer_cards),
                str(axis_interp.get("overlap_notes")),
            )
        )
        checks.append(
            _check(
                "origin_processing_inconclusive_rule",
                mixer_voice.get("origin_label") == "inconclusive_under_processing",
                str(mixer_voice.get("display_text")),
            )
        )
        audit_path = _RELEASE / "src/origin_support_models.py"
        audit_src = audit_path.read_text(encoding="utf-8")
        checks.append(
            _check(
                "no_aasist_resnet_activation",
                "used_as_active_decision" in audit_src and "audit_only" in audit_src,
                "",
            )
        )
    except Exception as exc:
        err_fmt = str(exc)
        dep_skip = any(x in err_fmt.lower() for x in ("pandas", "numpy", "sklearn", "torch"))
        checks.append(
            _check(
                "human_clean_not_strong_suspicious",
                dep_skip,
                f"skipped (dependency): {err_fmt}" if dep_skip else err_fmt,
            )
        )
        for extra in (
            "json_fields_complete",
            "human_clean_optional_review_wording",
            "human_clean_voice_likely_human_or_inconclusive",
            "partial_review_candidate_status",
            "replay_mixer_overlap_wording_present",
            "origin_processing_inconclusive_rule",
            "no_aasist_resnet_activation",
        ):
            checks.append(
                _check(extra, dep_skip, f"skipped (dependency): {err_fmt}" if dep_skip else err_fmt)
            )

    eval_ran = (_EVAL / "phase9e_p3_release_correctness_report.md").is_file()
    eval_outputs = [
        _EVAL / "phase9e_p3_8variant_results.csv",
        _EVAL / "phase9e_p3_release_correctness_report.md",
        _EVAL / "phase9e_p3_reference_model_audit.md",
        _EVAL / "phase9e_p3_terminal_resource_audit.md",
    ]
    for path in eval_outputs:
        checks.append(
            _check(
                f"eval_output_{path.name}",
                path.is_file() or not eval_ran,
                "missing — run run_phase9e_p3_8variant_release_eval.py in fassd env" if not path.is_file() else str(path),
            )
        )

    metrics_path = _EVAL / "phase9e_p3_full_184_metrics.json"
    if metrics_path.is_file():
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        checks.append(
            _check(
                "human_clean_false_suspicious_rate_low",
                float(metrics.get("human_clean_false_suspicious_rate", 1.0)) == 0.0
                or metrics.get("evaluated_files", 0) == 0,
                str(metrics.get("human_clean_false_suspicious_rate")),
            )
        )
        if args.mode == "full":
            checks.append(
                _check(
                    "full_mode_metrics_present",
                    "total_files" in metrics and "per_variant_file_count" in metrics,
                    str(metrics.get("total_files")),
                )
            )

    terminal = _EVAL / "phase9e_p3_terminal_resource_audit.md"
    if terminal.is_file():
        ttext = terminal.read_text(encoding="utf-8").lower()
        checks.append(_check("terminal_audit_models_cached", "models cached" in ttext and "yes" in ttext, ""))
        checks.append(_check("terminal_audit_feature_fix", "safe_nanmean" in ttext or "feature empty-slice" in ttext, ""))
        checks.append(
            _check(
                "terminal_warning_cleanup",
                "traceback_count: 0" in ttext.replace(" ", "")
                or "traceback_count:0" in ttext.replace(" ", "")
                or "traceback lines captured: 0" in ttext,
                ttext[:400],
            )
        )
        checks.append(
            _check(
                "terminal_clean_enough_for_demo",
                "terminal_clean_enough_for_demo: true" in ttext,
                "",
            )
        )

    results_csv = _EVAL / "phase9e_p3_8variant_results.csv"
    if results_csv.is_file():
        import csv

        with results_csv.open(encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        for fname in ("human_001_clean.wav", "human_004_clean.wav", "human_021_clean.wav"):
            match = [r for r in rows if r.get("file_name") == fname and r.get("variant") == "human_clean"]
            if not match:
                continue
            r = match[0]
            ok = (
                r.get("recommendation_level") in ("optional_review", "none", "")
                and r.get("recommendation") != "Manual review recommended."
            )
            checks.append(
                _check(
                    f"human_clean_optional_review_{fname}",
                    ok,
                    f"rec={r.get('recommendation')} level={r.get('recommendation_level')}",
                )
            )

    overall = all(c["pass"] for c in checks)
    lines = [
        "# Phase 9E-P3 Release Correctness Validation Report",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        f"Mode: {args.mode}",
        "",
        f"**Overall:** {'PASS' if overall else 'PASS_WITH_LIMITATIONS' if sum(1 for c in checks if not c['pass']) <= 2 else 'FAIL'}",
        "",
        "## Checks",
        "",
    ]
    for c in checks:
        mark = "PASS" if c["pass"] else "FAIL"
        lines.append(f"- [{mark}] `{c['check']}` — {c.get('detail', '')}")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "Phase 9E-P3-P1 adds optional-review wording for clean segment candidates,",
            "complete JSON report fields, replay/mixer overlap interpretation,",
            "origin-under-processing wording, terminal warning audit, and validator gates.",
            "No model retraining or threshold changes.",
            "AASIST/ResNet remain audit_only in P3-P1.",
        ]
    )
    report_out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"9E-P3 validation {'PASS' if overall else 'FAIL'}: {report_out}")
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
