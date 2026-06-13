"""Phase 1 baseline snapshot: full release pipeline on all testing_audios."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
    roc_auc_score,
)

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / "release"
OUT = ROOT / "reports" / "release_audit" / "phase1_baseline_2026-06-13"
MANIFEST = (
    ROOT
    / "reports"
    / "phase7"
    / "phase7_forensic_tests"
    / "forensic_test_manifest_backup_before_T4_3_timestamp.csv"
)

if str(RELEASE) not in sys.path:
    sys.path.insert(0, str(RELEASE))

from src.app_report_formatting import enrich_phase9c_response  # noqa: E402
from src.audio_io import SUPPORTED_EXTENSIONS, validate_audio_path  # noqa: E402
from src.inference_pipeline import analyze_audio_file  # noqa: E402


def resolve_audio(path_str: str) -> Path | None:
    p = Path(path_str)
    if p.is_file():
        return p.resolve()
    q = (ROOT / p).resolve()
    return q if q.is_file() else None


def origin_detected(enriched: dict) -> int | None:
    voice = enriched.get("voice_origin_result") or {}
    if voice.get("ssl_origin_detected") is True:
        return 1
    label = str(voice.get("origin_label") or "")
    if label in ("likely_human",):
        return 0
    if label in ("likely_ai_generated", "likely_ai_generated_with_processing"):
        return 1
    return None


def axis_detected(evidence: dict) -> int | None:
    if not evidence.get("prediction_success"):
        return None
    label = str(evidence.get("evidence_label") or evidence.get("label") or "").lower()
    strength = str(evidence.get("evidence_strength") or "").lower()
    if "elevated" in label or strength in {"moderate", "high"}:
        return 1
    if strength in {"low", "borderline", "not_evaluated"} or "low" in label:
        return 0
    return 0


def partial_ui_state(enriched: dict) -> str:
    pf = enriched.get("partial_fabrication") or {}
    return str(pf.get("ui_state") or "")


def metric_row(scope: str, df: pd.DataFrame, target: str, pred: str, prob: str) -> dict:
    sub = df.dropna(subset=[target, pred]).copy()
    if sub.empty:
        return {"scope": scope, "n": 0}
    y = sub[target].astype(int).to_numpy()
    yp = sub[pred].astype(int).to_numpy()
    prb = pd.to_numeric(sub[prob], errors="coerce").to_numpy(dtype=float)
    tn, fp, fn, tp = confusion_matrix(y, yp, labels=[0, 1]).ravel()
    precision, recall, f1, _ = precision_recall_fscore_support(
        y, yp, average="binary", zero_division=0
    )
    roc = pr = float("nan")
    if len(set(y)) > 1 and pd.notna(prb).all():
        roc = float(roc_auc_score(y, prb))
        pr = float(average_precision_score(y, prb))
    return {
        "scope": scope,
        "n": len(sub),
        "tp": int(tp),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "accuracy": float(accuracy_score(y, yp)),
        "balanced_accuracy": float(balanced_accuracy_score(y, yp)),
        "precision": float(precision),
        "recall": float(recall),
        "specificity": float(tn / max(tn + fp, 1)),
        "f1": float(f1),
        "roc_auc": roc,
        "pr_auc": pr,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cpu-ids",
        nargs="*",
        default=["T4.1", "T4.3"],
        help="Force CPU inference for long files.",
    )
    parser.add_argument(
        "--device",
        choices=["auto", "cpu"],
        default="cpu",
        help="Inference device. Use cpu for stable 6 GB GPU baseline snapshots.",
    )
    parser.add_argument("--skip-existing", action="store_true")
    args = parser.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    raw_dir = OUT / "raw_pipeline_json"
    raw_dir.mkdir(exist_ok=True)

    manifest = pd.read_csv(MANIFEST, dtype=str, keep_default_na=False)
    rows: list[dict] = []

    for idx, row in manifest.iterrows():
        test_id = row["test_id"]
        out = row.to_dict()
        audio = resolve_audio(row["audio_path"])
        out["resolved_audio_path"] = str(audio) if audio else ""
        out["supported_extension"] = (
            audio.suffix.lower() in SUPPORTED_EXTENSIONS if audio else False
        )
        raw_path = raw_dir / f"{test_id}.json"

        if audio is None:
            out["eval_status"] = "missing_audio"
            rows.append(out)
            continue

        ok, msg = validate_audio_path(str(audio))
        if not ok:
            out["eval_status"] = msg
            rows.append(out)
            continue

        if args.skip_existing and raw_path.is_file():
            phase9c = json.loads(raw_path.read_text(encoding="utf-8"))
            out["eval_status"] = "ok_cached"
        else:
            device = "cpu" if args.device == "cpu" or test_id in set(args.cpu_ids) else "auto"
            phase9c = None
            for attempt_device in ([device] if device == "cpu" else [device, "cpu"]):
                try:
                    print(
                        f"[{idx + 1}/{len(manifest)}] {test_id} device={attempt_device}",
                        flush=True,
                    )
                    phase9c = analyze_audio_file(
                        str(audio),
                        case_id=f"PHASE1-{test_id}",
                        output_dir=None,
                        device=attempt_device,
                        return_debug=True,
                    )
                    out["eval_status"] = "ok"
                    break
                except Exception as exc:
                    err = str(exc)
                    if attempt_device == "auto" and "out of memory" in err.lower():
                        print(f"  retrying {test_id} on cpu after CUDA OOM", flush=True)
                        continue
                    out["eval_status"] = f"error: {exc}"
                    phase9c = None
                    break
            if phase9c is None:
                rows.append(out)
                continue
            raw_path.write_text(json.dumps(phase9c, indent=2, default=str), encoding="utf-8")

        enriched = enrich_phase9c_response(phase9c, file_name=audio.name, return_top_segments=True)
        voice = enriched.get("voice_origin_result") or {}
        pf = enriched.get("partial_fabrication") or {}
        origin = enriched.get("origin_evidence") or {}
        replay = enriched.get("replay_evidence") or {}
        mixer = enriched.get("mixer_channel_evidence") or {}

        out.update(
            {
                "origin_probability": origin.get("probability"),
                "origin_threshold": origin.get("threshold_candidate"),
                "origin_pred": origin_detected(enriched),
                "origin_label": voice.get("origin_label"),
                "origin_display": voice.get("display_text"),
                "origin_score_text": voice.get("confidence_text"),
                "evidence_sources": ",".join(voice.get("evidence_sources") or []),
                "evidence_source": voice.get("evidence_source"),
                "replay_probability": replay.get("probability"),
                "replay_pred": axis_detected(replay),
                "mixer_probability": mixer.get("probability"),
                "mixer_pred": axis_detected(mixer),
                "partial_ui_state": partial_ui_state(enriched),
                "partial_show_segments_table": pf.get("show_segments_table"),
                "partial_segments_listed": len(pf.get("top_segments") or []),
                "partial_block_reason": (enriched.get("partial_fabrication_evidence") or {}).get(
                    "partial_fusion_block_reason"
                ),
                "fusion_status": enriched.get("fusion_status"),
                "forensic_risk_level": enriched.get("forensic_risk_level"),
            }
        )
        rows.append(out)

    pred = pd.DataFrame(rows)
    pred.to_csv(OUT / "phase1_baseline_predictions.csv", index=False)

    ok_df = pred[pred["eval_status"].isin(["ok", "ok_cached"])].copy()
    ok_df["origin_target"] = ok_df["ground_truth_origin"].map({"human": 0, "ai": 1, "mixed": None})
    ok_df["replay_target"] = ok_df["manipulation_type"].isin(["human_replay", "ai_replay"]).astype(int)
    ok_df["mixer_target"] = ok_df["manipulation_type"].isin(
        ["mixer_processed", "whatsapp_compressed"]
    ).astype(int)

    binary = ok_df[ok_df["ground_truth_origin"].isin(["human", "ai"])].copy()
    metrics = [
        metric_row("origin_binary_human_ai", binary, "origin_target", "origin_pred", "origin_probability"),
        metric_row("replay_axis_supported", ok_df, "replay_target", "replay_pred", "replay_probability"),
        metric_row("mixer_axis_supported", ok_df, "mixer_target", "mixer_pred", "mixer_probability"),
    ]
    metrics_df = pd.DataFrame(metrics)
    metrics_df.to_csv(OUT / "phase1_baseline_metrics.csv", index=False)

    ui_checks = ok_df[
        [
            "test_id",
            "partial_ui_state",
            "partial_show_segments_table",
            "partial_segments_listed",
            "partial_block_reason",
            "evidence_sources",
        ]
    ].copy()
    ui_checks.to_csv(OUT / "phase1_baseline_ui_checks.csv", index=False)

    contradictions = ok_df[
        (ok_df["partial_ui_state"].eq("not_detected"))
        & (ok_df["partial_segments_listed"].fillna(0).astype(int) > 0)
    ]
    contradictions.to_csv(OUT / "phase1_baseline_partial_ui_contradictions.csv", index=False)

    report = [
        "# Phase 1 Baseline Snapshot (Current Release Models)",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "Full release pipeline on frozen `testing_audios` manifest.",
        "UI integrity fixes from Phase 1 are applied via `enrich_phase9c_response`.",
        "",
        f"Rows: {len(pred)} | ok: {len(ok_df)} | failed: {len(pred) - len(ok_df)}",
        f"Supported extensions: {sorted(SUPPORTED_EXTENSIONS)}",
        "",
        "## Metrics",
        "",
        metrics_df.round(4).to_string(index=False),
        "",
        "## Partial UI consistency",
        "",
        f"Contradictions (not_detected + segments listed): {len(contradictions)}",
        "",
        ui_checks.to_string(index=False),
        "",
        "## Output files",
        "",
        f"- `{OUT / 'phase1_baseline_predictions.csv'}`",
        f"- `{OUT / 'phase1_baseline_metrics.csv'}`",
        f"- `{OUT / 'phase1_baseline_ui_checks.csv'}`",
        f"- `{OUT / 'phase1_baseline_partial_ui_contradictions.csv'}`",
        f"- `{raw_dir}`",
    ]
    (OUT / "phase1_baseline_report.md").write_text("\n".join(report), encoding="utf-8")
    print(f"Wrote Phase 1 baseline snapshot to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
