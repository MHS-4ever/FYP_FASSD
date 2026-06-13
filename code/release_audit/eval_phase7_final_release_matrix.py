"""Phase 7 final release matrix over all testing_audios (current packaged release)."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, precision_score, recall_score

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / "release"
OUT = ROOT / "reports" / "release_audit" / "phase7_final_release_2026-06-13"
MANIFEST = (
    ROOT
    / "reports"
    / "phase7"
    / "phase7_forensic_tests"
    / "forensic_test_manifest_backup_before_T4_3_timestamp.csv"
)

if str(RELEASE) not in sys.path:
    sys.path.insert(0, str(RELEASE))

from src.app_report_formatting import build_evidence_axis_cards, enrich_phase9c_response  # noqa: E402
from src.inference_pipeline import analyze_audio_file  # noqa: E402


def resolve_audio(path_str: str) -> Path | None:
    p = Path(path_str)
    if p.is_file():
        return p.resolve()
    q = (ROOT / p).resolve()
    return q if q.is_file() else None


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def axis_pred(evidence: dict[str, Any]) -> int | None:
    if not evidence.get("prediction_success"):
        return None
    label = str(evidence.get("evidence_label") or evidence.get("label") or "").lower()
    strength = str(evidence.get("evidence_strength") or "").lower()
    if "elevated" in label or strength in {"moderate", "high"}:
        return 1
    return 0


def origin_pred(enriched: dict[str, Any]) -> int | None:
    voice = enriched.get("voice_origin_result") or {}
    if voice.get("ssl_origin_detected") is True:
        return 1
    label = str(voice.get("origin_label") or "")
    if label in {"likely_human"}:
        return 0
    if label in {"likely_ai_generated", "likely_ai_generated_with_processing"}:
        return 1
    return None


def metric_row(axis: str, df: pd.DataFrame, target: str, pred: str) -> dict[str, Any]:
    sub = df.dropna(subset=[target, pred]).copy()
    if sub.empty:
        return {"axis": axis, "n": 0}
    y = sub[target].astype(int).to_numpy()
    yp = sub[pred].astype(int).to_numpy()
    tn, fp, fn, tp = confusion_matrix(y, yp, labels=[0, 1]).ravel()
    return {
        "axis": axis,
        "n": int(len(sub)),
        "tp": int(tp),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "accuracy": float(accuracy_score(y, yp)),
        "balanced_accuracy": float(balanced_accuracy_score(y, yp)) if len(set(y)) > 1 else float("nan"),
        "precision": float(precision_score(y, yp, zero_division=0)),
        "recall": float(recall_score(y, yp, zero_division=0)),
        "specificity": float(tn / max(tn + fp, 1)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", default="cpu", choices=["auto", "cpu", "cuda"])
    parser.add_argument("--cpu-ids", nargs="*", default=["T4.1", "T4.3", "T5_FAB_001"])
    parser.add_argument("--skip-existing", action="store_true")
    args = parser.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    raw_dir = OUT / "raw_pipeline_json"
    raw_dir.mkdir(exist_ok=True)

    manifest = pd.read_csv(MANIFEST, dtype=str, keep_default_na=False)
    rows: list[dict[str, Any]] = []

    for _, row in manifest.iterrows():
        test_id = row["test_id"]
        out = row.to_dict()
        audio = resolve_audio(row["audio_path"])
        out["resolved_audio_path"] = str(audio) if audio else ""
        if audio is None:
            out["analysis_status"] = "missing_audio"
            rows.append(out)
            continue

        raw_path = raw_dir / f"{test_id}.json"
        if args.skip_existing and raw_path.is_file():
            result = json.loads(raw_path.read_text(encoding="utf-8"))
        else:
            device = "cpu" if test_id in set(args.cpu_ids) else args.device
            result = analyze_audio_file(
                str(audio),
                case_id=f"FINAL-{test_id}",
                output_dir=None,
                device=device,
                return_debug=True,
            )
            raw_path.write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")

        enriched = enrich_phase9c_response(result, file_name=Path(row["audio_path"]).name)
        cards = build_evidence_axis_cards(enriched)
        origin = result.get("origin_evidence") or {}
        replay = result.get("replay_evidence") or {}
        mixer = result.get("mixer_channel_evidence") or {}
        partial = result.get("partial_fabrication_evidence") or {}
        pf = enriched.get("partial_fabrication") or {}

        out["analysis_status"] = result.get("status", "ok")
        out["origin_probability"] = origin.get("probability")
        out["replay_probability"] = replay.get("probability")
        out["mixer_probability"] = mixer.get("probability")
        out["partial_max_segment_probability"] = partial.get("max_segment_probability")
        out["partial_high_segment_fraction"] = partial.get("high_segment_fraction")
        out["partial_gate"] = partial.get("partial_localization_gate")
        out["partial_fusion_eligible"] = partial.get("partial_fusion_eligible")
        out["partial_ui_state"] = pf.get("ui_state")
        out["origin_pred"] = origin_pred(enriched)
        out["replay_pred"] = axis_pred(replay)
        out["mixer_pred"] = axis_pred(mixer)
        out["partial_pred"] = 1 if partial.get("partial_fusion_eligible") is True else 0
        out["origin_target_ai"] = 1 if row.get("ground_truth_origin") == "ai" else (0 if row.get("ground_truth_origin") == "human" else "")
        out["replay_target"] = 1 if row.get("manipulation_type") in {"human_replay", "ai_replay"} else 0
        out["mixer_target"] = 1 if row.get("manipulation_type") == "mixer_processed" else 0
        out["partial_target"] = 1 if str(row.get("partial_fabrication_detected")).lower() == "true" else 0
        out["card_statuses"] = "; ".join(f"{c.get('axis_name')}={c.get('status')}" for c in cards)
        rows.append(out)
        print(f"[phase7-final] {test_id}: {out['analysis_status']}")

    pred = pd.DataFrame(rows)
    pred.to_csv(OUT / "phase7_final_testing_audios_predictions.csv", index=False)

    metrics = pd.DataFrame(
        [
            metric_row("origin", pred[pred["origin_target_ai"].astype(str).isin(["0", "1"])], "origin_target_ai", "origin_pred"),
            metric_row("replay", pred, "replay_target", "replay_pred"),
            metric_row("mixer", pred, "mixer_target", "mixer_pred"),
            metric_row("partial", pred, "partial_target", "partial_pred"),
        ]
    )
    metrics.to_csv(OUT / "phase7_final_testing_audios_metrics.csv", index=False)

    failure_rows = []
    for axis, target, pred_col in [
        ("origin", "origin_target_ai", "origin_pred"),
        ("replay", "replay_target", "replay_pred"),
        ("mixer", "mixer_target", "mixer_pred"),
        ("partial", "partial_target", "partial_pred"),
    ]:
        valid = pred[pred[target].astype(str).isin(["0", "1"]) & pred[pred_col].notna()].copy()
        bad = valid[valid[target].astype(int) != valid[pred_col].astype(int)].copy()
        for _, r in bad.iterrows():
            failure_rows.append(
                {
                    "axis": axis,
                    "test_id": r.get("test_id"),
                    "audio_path": r.get("audio_path"),
                    "manipulation_type": r.get("manipulation_type"),
                    "ground_truth_origin": r.get("ground_truth_origin"),
                    "target": r.get(target),
                    "prediction": r.get(pred_col),
                    "origin_probability": r.get("origin_probability"),
                    "replay_probability": r.get("replay_probability"),
                    "mixer_probability": r.get("mixer_probability"),
                    "partial_max_segment_probability": r.get("partial_max_segment_probability"),
                    "partial_gate": r.get("partial_gate"),
                    "notes": r.get("notes"),
                }
            )
    failures = pd.DataFrame(failure_rows)
    failures.to_csv(OUT / "phase7_final_testing_audios_failures.csv", index=False)

    report = [
        "# Phase 7 Final Release Matrix — testing_audios",
        "",
        f"Generated: {utc_now()}",
        "",
        "Current packaged release models + Phase 6 evidence band formatting.",
        "",
        "## Axis metrics",
        "",
        metrics.round(4).to_string(index=False),
        "",
        "## Failure table",
        "",
        failures.to_string(index=False) if len(failures) else "No failures in valid rows.",
    ]
    (OUT / "phase7_final_testing_audios_matrix.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
