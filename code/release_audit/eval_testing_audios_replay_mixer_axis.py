"""Fast replay + mixer/channel axis evaluation on testing_audios (no WavLM / partial)."""

from __future__ import annotations

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
OUT = ROOT / "reports" / "release_audit" / "testing_audios_replay_mixer_eval_2026-06-13"
MANIFEST = (
    ROOT
    / "reports"
    / "phase7"
    / "phase7_forensic_tests"
    / "forensic_test_manifest_backup_before_T4_3_timestamp.csv"
)
AUDIO_SUPPORTED = {".wav", ".flac", ".mp3", ".ogg", ".m4a", ".aac"}

if str(RELEASE) not in sys.path:
    sys.path.insert(0, str(RELEASE))

from src.audio_io import load_audio  # noqa: E402
from src.feature_extraction import align_features_to_metadata, extract_file_acoustic_features  # noqa: E402
from src.model_loader import get_model_input_feature_names, get_threshold, load_all_active_models  # noqa: E402


def resolve_audio(path_str: str) -> Path | None:
    p = Path(path_str)
    if p.is_file():
        return p.resolve()
    q = (ROOT / p).resolve()
    return q if q.is_file() else None


def predict_axis(model, meta, features: dict) -> tuple[float, float, int]:
    names = get_model_input_feature_names(model, meta)
    x = align_features_to_metadata(features, names)
    prob = float(model.predict_proba(x)[0, 1])
    th = float(get_threshold(meta))
    return prob, th, int(prob >= th)


def metric_row(axis: str, scope: str, df: pd.DataFrame, target: str, pred: str, prob: str) -> dict:
    y = df[target].astype(int).to_numpy()
    yp = df[pred].astype(int).to_numpy()
    prb = pd.to_numeric(df[prob], errors="coerce").to_numpy(dtype=float)
    tn, fp, fn, tp = confusion_matrix(y, yp, labels=[0, 1]).ravel()
    precision, recall, f1, _ = precision_recall_fscore_support(y, yp, average="binary", zero_division=0)
    roc = pr = float("nan")
    if len(set(y)) > 1 and pd.notna(prb).all():
        roc = float(roc_auc_score(y, prb))
        pr = float(average_precision_score(y, prb))
    return {
        "axis": axis,
        "scope": scope,
        "n": len(df),
        "tp": int(tp),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "accuracy": float(accuracy_score(y, yp)),
        "balanced_accuracy": float(balanced_accuracy_score(y, yp)) if len(set(y)) > 1 else float("nan"),
        "precision": float(precision),
        "recall": float(recall),
        "specificity": float(tn / max(tn + fp, 1)),
        "fpr": float(fp / max(tn + fp, 1)),
        "fnr": float(fn / max(tp + fn, 1)),
        "f1": float(f1),
        "roc_auc": roc,
        "pr_auc": pr,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = pd.read_csv(MANIFEST, dtype=str, keep_default_na=False)
    models = load_all_active_models()

    rows: list[dict] = []
    for _, row in manifest.iterrows():
        out = row.to_dict()
        audio = resolve_audio(row["audio_path"])
        out["resolved_audio_path"] = str(audio) if audio else ""
        out["eval_status"] = "ok"

        if audio is None:
            out["eval_status"] = "missing_audio"
        elif audio.suffix.lower() not in AUDIO_SUPPORTED:
            out["eval_status"] = "unsupported_audio_extension_for_release_audio_io"
        else:
            try:
                y, sr = load_audio(str(audio), target_sample_rate=16000)
                feats = extract_file_acoustic_features(y, sr)
                for key, prefix in [("replay", "replay"), ("mixer", "mixer")]:
                    p, th, pred = predict_axis(models[key]["model"], models[key]["metadata"], feats)
                    out[f"{prefix}_probability"] = p
                    out[f"{prefix}_threshold"] = th
                    out[f"{prefix}_pred"] = pred
            except Exception as exc:
                out["eval_status"] = f"error: {exc}"
        rows.append(out)

    pred = pd.DataFrame(rows)
    pred["replay_target"] = pred["manipulation_type"].isin(["human_replay", "ai_replay"]).astype(int)
    pred["mixer_target"] = pred["manipulation_type"].isin(["mixer_processed", "whatsapp_compressed"]).astype(int)
    for col in ["replay_probability", "replay_threshold", "replay_pred", "mixer_probability", "mixer_threshold", "mixer_pred"]:
        if col in pred.columns:
            pred[col] = pd.to_numeric(pred[col], errors="coerce")

    pred.to_csv(OUT / "testing_audios_replay_mixer_predictions.csv", index=False)

    axis_df = pred[pred["eval_status"].eq("ok") & pred["ground_truth_origin"].isin(["human", "ai"])].copy()
    metrics = [
        metric_row("replay", "supported_human_ai_nonmixed", axis_df, "replay_target", "replay_pred", "replay_probability"),
        metric_row("mixer", "supported_human_ai_nonmixed", axis_df, "mixer_target", "mixer_pred", "mixer_probability"),
    ]
    metrics_df = pd.DataFrame(metrics)
    metrics_df.to_csv(OUT / "testing_audios_replay_mixer_metrics.csv", index=False)

    errors: list[dict] = []
    for axis, target, pred_col, prob_col in [
        ("replay", "replay_target", "replay_pred", "replay_probability"),
        ("mixer", "mixer_target", "mixer_pred", "mixer_probability"),
    ]:
        bad = axis_df[axis_df[target].astype(int) != axis_df[pred_col].astype(int)]
        for _, r in bad.iterrows():
            errors.append(
                {
                    "axis": axis,
                    "test_id": r["test_id"],
                    "ground_truth_origin": r["ground_truth_origin"],
                    "manipulation_type": r["manipulation_type"],
                    "language": r["language"],
                    "target": int(r[target]),
                    "prediction": int(r[pred_col]),
                    "probability": r[prob_col],
                    "expected_forensic_result": r.get("expected_forensic_result"),
                }
            )
    errors_df = pd.DataFrame(errors)
    errors_df.to_csv(OUT / "testing_audios_replay_mixer_errors.csv", index=False)

    unsupported = pred[pred["eval_status"].str.contains("unsupported", na=False)][
        ["test_id", "audio_path", "manipulation_type", "eval_status"]
    ]
    unsupported.to_csv(OUT / "testing_audios_replay_mixer_unsupported_audio.csv", index=False)

    report = [
        "# Testing Audios Replay + Mixer Axis Evaluation",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "Fast file-level acoustic evaluation only. No WavLM, no partial segmentation.",
        "",
        f"Rows: {len(pred)} | ok: {int((pred['eval_status'] == 'ok').sum())} | unsupported/missing: {len(pred) - int((pred['eval_status'] == 'ok').sum())}",
        "",
        "## Metrics",
        "",
        metrics_df.round(4).to_string(index=False),
        "",
        "## Errors",
        "",
        errors_df.round(4).to_string(index=False) if len(errors_df) else "(none)",
        "",
        "## Output files",
        "",
        f"- `{OUT / 'testing_audios_replay_mixer_predictions.csv'}`",
        f"- `{OUT / 'testing_audios_replay_mixer_metrics.csv'}`",
        f"- `{OUT / 'testing_audios_replay_mixer_errors.csv'}`",
        f"- `{OUT / 'testing_audios_replay_mixer_unsupported_audio.csv'}`",
    ]
    (OUT / "testing_audios_replay_mixer_eval_report.md").write_text("\n".join(report), encoding="utf-8")
    print(f"Wrote replay/mixer evaluation to {OUT}")


if __name__ == "__main__":
    main()
