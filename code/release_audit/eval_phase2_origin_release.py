"""Phase 2 origin-only evaluation for the promoted release origin model.

This script keeps testing_audios evaluation-only. It uses cached Phase 8 SSL
features for the leakage-safe Phase 7 split and fresh release-path SSL
embeddings for testing_audios.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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
OUT = ROOT / "reports" / "release_audit" / "phase2_origin_release_2026-06-13"
LEAKAGE_MANIFEST = (
    ROOT
    / "reports"
    / "release_audit"
    / "leakage_safe_eval_2026-06-13"
    / "leakage_safe_file_manifest.csv"
)
PHASE8_MASTER = (
    ROOT
    / "reports"
    / "phase8"
    / "models"
    / "phase8e0"
    / "phase8e0_file_level_master_dataset.csv"
)
TESTING_MANIFEST = (
    ROOT
    / "reports"
    / "phase7"
    / "phase7_forensic_tests"
    / "forensic_test_manifest_backup_before_T4_3_timestamp.csv"
)

if str(RELEASE) not in sys.path:
    sys.path.insert(0, str(RELEASE))

from src.audio_io import load_audio  # noqa: E402
from src.feature_extraction import align_features_to_metadata  # noqa: E402
from src.model_loader import (  # noqa: E402
    clear_active_model_cache,
    get_model_input_feature_names,
    get_threshold,
    load_all_active_models,
)
from src.ssl_embeddings import extract_file_ssl_embedding, load_ssl_extractor  # noqa: E402


def resolve_audio(path_str: str) -> Path | None:
    p = Path(path_str)
    if p.is_file():
        return p.resolve()
    q = (ROOT / p).resolve()
    return q if q.is_file() else None


def predict_origin(model: Any, metadata: dict[str, Any], features: dict[str, Any]) -> tuple[float, float, int]:
    names = get_model_input_feature_names(model, metadata)
    x = align_features_to_metadata(features, names)
    prob = float(model.predict_proba(x)[0, 1])
    threshold = float(get_threshold(metadata))
    return prob, threshold, int(prob >= threshold)


def metric_row(scope: str, df: pd.DataFrame, target: str, pred: str, prob: str) -> dict[str, Any]:
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
        "n": int(len(sub)),
        "threshold": float(sub[prob.replace("probability", "threshold")].iloc[0])
        if prob.replace("probability", "threshold") in sub.columns
        else float("nan"),
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


def normalized_path(path: Any) -> str:
    return str(path).replace("\\", "/").lower()


def eval_phase7(model: Any, metadata: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    master = pd.read_csv(PHASE8_MASTER)
    manifest = pd.read_csv(LEAKAGE_MANIFEST)
    master["_join_audio_path"] = master["audio_path"].map(normalized_path)
    manifest["_join_audio_path"] = manifest["audio_path"].map(normalized_path)
    df = manifest.merge(
        master,
        on="_join_audio_path",
        how="left",
        suffixes=("", "_phase8"),
    )
    ssl_cols = [f"ssl_emb_{i:03d}" for i in range(768)]
    rows: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        out = {
            "sample_id": row.get("sample_id"),
            "audio_path": row.get("audio_path"),
            "audit_condition": row.get("audit_condition"),
            "leakage_safe_split": row.get("leakage_safe_split"),
            "ground_truth_origin": row.get("ground_truth_origin"),
            "manipulation_type": row.get("manipulation_type"),
            "audit_origin_expected_ai": row.get("audit_origin_expected_ai"),
            "origin_training_scope": row.get("audit_condition")
            in {
                "ai_clean_direct",
                "ai_mixer_processed",
                "ai_replayed",
                "human_clean",
                "human_mixer_processed",
                "human_replayed",
            },
            "eval_status": "ok",
        }
        if any(c not in row.index or pd.isna(row[c]) for c in ssl_cols):
            out["eval_status"] = "missing_cached_ssl_features"
        else:
            feats = {c: row[c] for c in ssl_cols}
            p, th, pred = predict_origin(model, metadata, feats)
            out["origin_probability"] = p
            out["origin_threshold"] = th
            out["origin_pred"] = pred
        rows.append(out)
    pred = pd.DataFrame(rows)

    metrics: list[dict[str, Any]] = []
    ok = pred[pred["eval_status"].eq("ok")].copy()
    ok["target"] = pd.to_numeric(ok["audit_origin_expected_ai"], errors="coerce")
    for split in ["train", "dev", "test", "all"]:
        scope_df = ok if split == "all" else ok[ok["leakage_safe_split"].eq(split)]
        metrics.append(metric_row(f"phase7_{split}_all_conditions", scope_df, "target", "origin_pred", "origin_probability"))
        train_scope = scope_df[scope_df["origin_training_scope"].eq(True)]
        metrics.append(
            metric_row(
                f"phase7_{split}_origin_training_scope",
                train_scope,
                "target",
                "origin_pred",
                "origin_probability",
            )
        )

    condition_rows: list[dict[str, Any]] = []
    for cond, group in ok.groupby("audit_condition", dropna=False):
        condition_rows.append(
            {
                "audit_condition": cond,
                "n": len(group),
                "target_ai": int(pd.to_numeric(group["target"], errors="coerce").max()),
                "mean_probability": float(group["origin_probability"].mean()),
                "detected_rate": float(group["origin_pred"].mean()),
                "threshold": float(group["origin_threshold"].iloc[0]),
            }
        )
    return pred, pd.DataFrame(metrics), pd.DataFrame(condition_rows)


def eval_testing_audios(model: Any, metadata: dict[str, Any], device: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    manifest = pd.read_csv(TESTING_MANIFEST, dtype=str, keep_default_na=False)
    ssl_model, processor, dev = load_ssl_extractor(device=device)
    rows: list[dict[str, Any]] = []
    for idx, row in manifest.iterrows():
        out = row.to_dict()
        audio = resolve_audio(row["audio_path"])
        out["resolved_audio_path"] = str(audio) if audio else ""
        out["eval_status"] = "ok"
        if audio is None:
            out["eval_status"] = "missing_audio"
            rows.append(out)
            continue
        try:
            print(f"[testing_audios] {idx + 1}/{len(manifest)} {row['test_id']}", flush=True)
            y, sr = load_audio(str(audio), target_sample_rate=16000)
            feats = extract_file_ssl_embedding(y, sr, ssl_model, processor, dev)
            p, th, pred = predict_origin(model, metadata, feats)
            out["origin_probability"] = p
            out["origin_threshold"] = th
            out["origin_pred"] = pred
        except Exception as exc:
            out["eval_status"] = f"error: {exc}"
        rows.append(out)
    pred = pd.DataFrame(rows)
    ok = pred[pred["eval_status"].eq("ok")].copy()
    ok["target"] = ok["ground_truth_origin"].map({"human": 0, "ai": 1})
    binary = ok[ok["ground_truth_origin"].isin(["human", "ai"])].copy()
    metrics = pd.DataFrame(
        [
            metric_row(
                "testing_audios_binary_human_ai",
                binary,
                "target",
                "origin_pred",
                "origin_probability",
            )
        ]
    )
    errors = binary[binary["target"].astype(int) != binary["origin_pred"].astype(int)].copy()
    return pred, metrics, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", choices=["cpu", "auto"], default="cpu")
    args = parser.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    clear_active_model_cache()
    models = load_all_active_models()
    model = models["origin"]["model"]
    metadata = models["origin"]["metadata"]

    phase7_pred, phase7_metrics, phase7_conditions = eval_phase7(model, metadata)
    testing_pred, testing_metrics, testing_errors = eval_testing_audios(model, metadata, args.device)

    phase7_pred.to_csv(OUT / "phase2_origin_phase7_predictions.csv", index=False)
    phase7_metrics.to_csv(OUT / "phase2_origin_phase7_metrics.csv", index=False)
    phase7_conditions.to_csv(OUT / "phase2_origin_phase7_condition_summary.csv", index=False)
    testing_pred.to_csv(OUT / "phase2_origin_testing_audios_predictions.csv", index=False)
    testing_metrics.to_csv(OUT / "phase2_origin_testing_audios_metrics.csv", index=False)
    testing_errors.to_csv(OUT / "phase2_origin_testing_audios_errors.csv", index=False)

    binary_metric = testing_metrics.iloc[0].to_dict()
    stop_rule_pass = (
        float(binary_metric.get("recall", 0.0)) >= 0.90
        and int(binary_metric.get("fp", 999)) <= 2
    )

    model_sha = metadata.get("phase2_origin_promotion", {}).get("installed_artifact_sha256", "")
    report = [
        "# Phase 2 Origin Release Evaluation",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "Promoted release origin model evaluated with leakage-safe Phase 7 cached SSL features and fresh testing_audios SSL embeddings.",
        "",
        f"- Release artifact SHA-256: `{model_sha}`",
        f"- Threshold candidate: `{metadata.get('threshold_candidate')}`",
        f"- Threshold source: {metadata.get('threshold_source')}",
        f"- Testing device: `{args.device}`",
        "",
        "## Phase 7 Leakage-Safe Metrics",
        "",
        phase7_metrics.round(4).to_string(index=False),
        "",
        "## Phase 7 Condition Summary",
        "",
        phase7_conditions.round(4).to_string(index=False),
        "",
        "## testing_audios Origin Metrics",
        "",
        testing_metrics.round(4).to_string(index=False),
        "",
        "## testing_audios Remaining Origin Failures",
        "",
        testing_errors[
            [
                "test_id",
                "ground_truth_origin",
                "manipulation_type",
                "language",
                "origin_probability",
                "origin_threshold",
                "origin_pred",
                "expected_forensic_result",
            ]
        ].round(4).to_string(index=False)
        if len(testing_errors)
        else "(none)",
        "",
        "## Stop Rule",
        "",
        f"- AI recall >= 0.90: `{float(binary_metric.get('recall', 0.0)) >= 0.90}`",
        f"- No new clean false positives vs current experimental model (<=2 known FPs): `{int(binary_metric.get('fp', 999)) <= 2}`",
        f"- Phase 2 stop rule pass: `{stop_rule_pass}`",
        "",
        "## Output Files",
        "",
        f"- `{OUT / 'phase2_origin_phase7_predictions.csv'}`",
        f"- `{OUT / 'phase2_origin_phase7_metrics.csv'}`",
        f"- `{OUT / 'phase2_origin_phase7_condition_summary.csv'}`",
        f"- `{OUT / 'phase2_origin_testing_audios_predictions.csv'}`",
        f"- `{OUT / 'phase2_origin_testing_audios_metrics.csv'}`",
        f"- `{OUT / 'phase2_origin_testing_audios_errors.csv'}`",
    ]
    (OUT / "phase2_origin_release_report.md").write_text("\n".join(report), encoding="utf-8")
    print(f"Wrote Phase 2 origin release evaluation to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
