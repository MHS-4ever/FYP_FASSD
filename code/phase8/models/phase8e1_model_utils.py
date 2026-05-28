"""
Phase 8E-1 lightweight file-level model utilities.

Experimental-only helpers for origin/replay/mixer evidence modeling.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.exceptions import NotFittedError
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GroupKFold, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import VarianceThreshold

SCHEMA_VERSION = "phase8e1_v1"
ALLOWED_TASKS = ("origin_file_model", "replay_file_model", "mixer_file_model")
ALLOWED_FEATURE_SETS = ("acoustic", "ssl", "combined")

FORBIDDEN_COLUMNS = {
    "fake_score",
    "real_score",
    "ai_score",
    "predicted_label",
    "prediction",
    "final_forensic_status",
    "suspicious_segment_flag",
    "evidence_origin_score",
    "origin_score",
    "evidence_replay_score",
    "evidence_mixer_channel_score",
}

IDENTITY_EXCLUDE_PREFIXES = ("target_", "eligible_")
IDENTITY_EXCLUDE_EXACT = {
    "schema_version",
    "file_id",
    "audio_path",
    "source_dataset",
    "split",
    "known_origin_label",
    "known_manipulation_labels",
    "source_group_id",
    "leakage_group_id",
    "extraction_status",
    "warning_message",
    "feature_source",
    "embedding_model_name",
    "embedding_layer",
    "pooling",
    "target_sample_rate",
    "embedding_dim",
    "model_type",
    "segment_id",
    "start_sec",
    "end_sec",
    "segment_duration_sec",
}


@dataclass(frozen=True)
class TaskConfig:
    task_name: str
    target_col: str
    positive_label_name: str
    negative_label_name: str
    dataset_arg_name: str


TASK_CONFIGS: dict[str, TaskConfig] = {
    "origin_file_model": TaskConfig(
        task_name="origin_file_model",
        target_col="target_is_ai_synthetic",
        positive_label_name="clean_ai_synthetic",
        negative_label_name="clean_human",
        dataset_arg_name="origin_dataset",
    ),
    "replay_file_model": TaskConfig(
        task_name="replay_file_model",
        target_col="target_is_replay",
        positive_label_name="replay_positive",
        negative_label_name="clean_negative",
        dataset_arg_name="replay_dataset",
    ),
    "mixer_file_model": TaskConfig(
        task_name="mixer_file_model",
        target_col="target_is_mixer_channel",
        positive_label_name="mixer_positive",
        negative_label_name="clean_negative",
        dataset_arg_name="mixer_dataset",
    ),
}


def load_csv_required(path: str | Path) -> pd.DataFrame:
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Required CSV missing: {p}")
    return pd.read_csv(p, dtype=str, keep_default_na=False)


def parse_binary_target(series: pd.Series, target_name: str) -> np.ndarray:
    vals = series.astype(str).str.strip()
    allowed = {"0", "1"}
    bad = vals[~vals.isin(allowed)]
    if len(bad):
        raise ValueError(f"Target column '{target_name}' has non-binary values: {sorted(set(bad))[:5]}")
    return vals.astype(int).to_numpy()


def _is_acoustic_col(col: str) -> bool:
    return (
        col.startswith("rms_")
        or col.startswith("spectral_")
        or col.startswith("mfcc_")
        or col.endswith("_band_energy_ratio")
        or col in {"noise_floor_proxy", "snr_proxy", "dynamic_range_proxy", "high_freq_rolloff_ratio", "bandwidth_occupied_95", "zero_crossing_rate_mean", "zero_crossing_rate_std", "peak_amplitude", "mean_amplitude", "std_amplitude", "dc_offset", "clipping_ratio", "silence_ratio", "active_audio_ratio"}
    )


def get_feature_columns(df: pd.DataFrame, feature_set: str) -> list[str]:
    if feature_set not in ALLOWED_FEATURE_SETS:
        raise ValueError(f"Unsupported feature_set={feature_set}")
    cols: list[str] = []
    for c in df.columns:
        if c in FORBIDDEN_COLUMNS:
            continue
        if c in IDENTITY_EXCLUDE_EXACT or any(c.startswith(p) for p in IDENTITY_EXCLUDE_PREFIXES):
            continue
        if feature_set == "acoustic" and _is_acoustic_col(c):
            cols.append(c)
        elif feature_set == "ssl" and c.startswith("ssl_emb_"):
            cols.append(c)
        elif feature_set == "combined" and (_is_acoustic_col(c) or c.startswith("ssl_emb_")):
            cols.append(c)
    if not cols:
        raise ValueError(f"No features selected for feature_set={feature_set}")
    return cols


def build_pipeline(max_selected_features: int, random_seed: int) -> Pipeline:
    if max_selected_features <= 0:
        raise ValueError("max_selected_features must be > 0")
    return Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("variance", VarianceThreshold()),
            ("scaler", StandardScaler()),
            ("select", SelectKBest(score_func=f_classif, k=max_selected_features)),
            (
                "clf",
                LogisticRegression(
                    penalty="l2",
                    class_weight="balanced",
                    max_iter=2000,
                    solver="liblinear",
                    random_state=random_seed,
                ),
            ),
        ]
    )


def _safe_predict_proba(model: Pipeline, x_test: pd.DataFrame) -> np.ndarray:
    try:
        return model.predict_proba(x_test)[:, 1]
    except (AttributeError, NotFittedError):
        return np.full(shape=(len(x_test),), fill_value=np.nan, dtype=float)


def choose_splitter(
    y: np.ndarray,
    groups: np.ndarray | None,
    cv_folds: int,
    random_seed: int,
) -> tuple[Any, str, int]:
    n = len(y)
    if n < 6:
        raise ValueError("Dataset too small for CV; need at least 6 rows.")
    class_counts = pd.Series(y).value_counts()
    max_folds_by_class = int(class_counts.min()) if len(class_counts) else 0
    folds = min(cv_folds, max_folds_by_class)
    if folds < 3:
        folds = min(3, max_folds_by_class)
    if folds < 3:
        raise ValueError(f"Insufficient class support for CV. class_counts={class_counts.to_dict()}")

    if groups is not None and len(groups) == n:
        group_count = len(set(str(g) for g in groups))
        if group_count >= folds:
            try:
                from sklearn.model_selection import StratifiedGroupKFold

                return StratifiedGroupKFold(n_splits=folds, shuffle=True, random_state=random_seed), "StratifiedGroupKFold", folds
            except Exception:
                return GroupKFold(n_splits=folds), "GroupKFold", folds
    return StratifiedKFold(n_splits=folds, shuffle=True, random_state=random_seed), "StratifiedKFold", folds


def run_cv_for_task(
    df: pd.DataFrame,
    task: TaskConfig,
    feature_set: str,
    max_selected_features: int,
    cv_folds: int,
    random_seed: int,
    model_type: str,
) -> dict[str, Any]:
    features = get_feature_columns(df, feature_set)
    x = df[features].copy()
    # Avoid pandas replace downcasting warning by masking blank strings.
    x = x.mask(x.eq(""))
    x = x.apply(pd.to_numeric, errors="coerce")
    nonempty_features = [c for c in x.columns if x[c].notna().any()]
    if not nonempty_features:
        raise ValueError(f"No usable (non-all-missing) features for task={task.task_name}, feature_set={feature_set}")
    dropped_all_missing = sorted(set(features) - set(nonempty_features))
    x = x[nonempty_features]
    features = nonempty_features
    y = parse_binary_target(df[task.target_col], task.target_col)
    groups = df["source_group_id"].to_numpy() if "source_group_id" in df.columns else None
    splitter, split_method, used_folds = choose_splitter(y, groups, cv_folds, random_seed)

    fold_rows: list[dict[str, Any]] = []
    oof_rows: list[dict[str, Any]] = []
    cm_rows: list[dict[str, Any]] = []
    feats_rows: list[dict[str, Any]] = []
    manifests: list[dict[str, Any]] = []

    if split_method in {"StratifiedGroupKFold", "StratifiedKFold"}:
        split_iter = splitter.split(x, y, groups if split_method == "StratifiedGroupKFold" else None)
    else:
        split_iter = splitter.split(x, y, groups)

    for fold_idx, (train_idx, test_idx) in enumerate(split_iter, start=1):
        x_train = x.iloc[train_idx]
        x_test = x.iloc[test_idx]
        y_train = y[train_idx]
        y_test = y[test_idx]

        safe_k = min(max_selected_features, len(features))
        model = build_pipeline(max_selected_features=safe_k, random_seed=random_seed)
        model = clone(model)
        model.fit(x_train, y_train)
        y_pred = model.predict(x_test)
        y_proba = _safe_predict_proba(model, x_test)

        tn, fp, fn, tp = confusion_matrix(y_test, y_pred, labels=[0, 1]).ravel()
        cm_rows.append(
            {
                "task_name": task.task_name,
                "feature_set": feature_set,
                "fold": fold_idx,
                "tn": int(tn),
                "fp": int(fp),
                "fn": int(fn),
                "tp": int(tp),
                "split_method": split_method,
                "model_type": model_type,
            }
        )

        metric_row = {
            "task_name": task.task_name,
            "feature_set": feature_set,
            "fold": fold_idx,
            "accuracy": float(accuracy_score(y_test, y_pred)),
            "balanced_accuracy": float(balanced_accuracy_score(y_test, y_pred)),
            "precision": float(precision_score(y_test, y_pred, zero_division=0)),
            "recall": float(recall_score(y_test, y_pred, zero_division=0)),
            "f1": float(f1_score(y_test, y_pred, zero_division=0)),
            "roc_auc": float(roc_auc_score(y_test, y_proba)) if len(np.unique(y_test)) > 1 and np.isfinite(y_proba).all() else np.nan,
            "average_precision": float(average_precision_score(y_test, y_proba)) if len(np.unique(y_test)) > 1 and np.isfinite(y_proba).all() else np.nan,
            "brier_score": float(brier_score_loss(y_test, y_proba)) if np.isfinite(y_proba).all() else np.nan,
            "split_method": split_method,
            "used_folds": used_folds,
            "model_type": model_type,
        }
        fold_rows.append(metric_row)

        selector = model.named_steps["select"]
        mask = selector.get_support() if hasattr(selector, "get_support") else np.array([True] * len(features))
        selected = [features[i] for i, m in enumerate(mask) if bool(m)]
        feats_rows.append(
            {
                "task_name": task.task_name,
                "feature_set": feature_set,
                "fold": fold_idx,
                "input_feature_count": len(features),
                "selected_feature_count": len(selected),
                "selected_features_preview": ";".join(selected[:50]),
            }
        )

        for local_i, global_i in enumerate(test_idx):
            oof_rows.append(
                {
                    "task_name": task.task_name,
                    "feature_set": feature_set,
                    "file_id": str(df.iloc[global_i].get("file_id", "")),
                    "source_group_id": str(df.iloc[global_i].get("source_group_id", "")),
                    "y_true": int(y_test[local_i]),
                    "y_pred_experimental": int(y_pred[local_i]),
                    "y_proba_experimental": float(y_proba[local_i]) if np.isfinite(y_proba[local_i]) else "",
                    "fold": fold_idx,
                    "split_method": split_method,
                    "model_type": model_type,
                }
            )

        manifests.append(
            {
                "task_name": task.task_name,
                "feature_set": feature_set,
                "fold": fold_idx,
                "split_method": split_method,
                "train_rows": len(train_idx),
                "test_rows": len(test_idx),
                "model_type": model_type,
            }
        )

    metrics_df = pd.DataFrame(fold_rows)
    metrics_mean = (
        metrics_df.drop(columns=["fold"])
        .groupby(["task_name", "feature_set", "split_method", "used_folds", "model_type"], as_index=False)
        .mean(numeric_only=True)
    )
    metrics_mean["metric_scope"] = "cross_validated_experimental_mean"

    oof_df = pd.DataFrame(oof_rows)
    cm_df = pd.DataFrame(cm_rows)
    feat_df = pd.DataFrame(feats_rows)
    manifest_df = pd.DataFrame(manifests)

    # Task-specific protection/error rates from OOF rows.
    if task.task_name == "origin_file_model":
        clean_human_total = int((oof_df["y_true"] == 0).sum())
        clean_human_false_ai_count = int(((oof_df["y_true"] == 0) & (oof_df["y_pred_experimental"] == 1)).sum())
        clean_ai_total = int((oof_df["y_true"] == 1).sum())
        clean_ai_detected_count = int(((oof_df["y_true"] == 1) & (oof_df["y_pred_experimental"] == 1)).sum())
        metrics_mean["clean_human_total"] = clean_human_total
        metrics_mean["clean_human_false_ai_count"] = clean_human_false_ai_count
        metrics_mean["clean_human_false_ai_rate"] = (
            clean_human_false_ai_count / clean_human_total if clean_human_total else np.nan
        )
        metrics_mean["clean_ai_total"] = clean_ai_total
        metrics_mean["clean_ai_detected_count"] = clean_ai_detected_count
        metrics_mean["clean_ai_detected_rate"] = clean_ai_detected_count / clean_ai_total if clean_ai_total else np.nan
    else:
        clean_negative_total = int((oof_df["y_true"] == 0).sum())
        clean_false_positive_count = int(((oof_df["y_true"] == 0) & (oof_df["y_pred_experimental"] == 1)).sum())
        manipulation_positive_total = int((oof_df["y_true"] == 1).sum())
        manipulation_detected_count = int(((oof_df["y_true"] == 1) & (oof_df["y_pred_experimental"] == 1)).sum())
        metrics_mean["clean_negative_total"] = clean_negative_total
        metrics_mean["clean_false_positive_count"] = clean_false_positive_count
        metrics_mean["clean_false_positive_rate"] = (
            clean_false_positive_count / clean_negative_total if clean_negative_total else np.nan
        )
        metrics_mean["manipulation_positive_total"] = manipulation_positive_total
        metrics_mean["manipulation_detected_count"] = manipulation_detected_count
        metrics_mean["manipulation_detected_rate"] = (
            manipulation_detected_count / manipulation_positive_total if manipulation_positive_total else np.nan
        )

    return {
        "metrics_mean": metrics_mean,
        "metrics_by_fold": metrics_df,
        "oof": oof_df,
        "confusion": cm_df,
        "feature_selection": feat_df,
        "manifest": manifest_df,
        "split_method": split_method,
        "used_folds": used_folds,
        "feature_count": len(features),
        "dropped_all_missing_features": ";".join(dropped_all_missing[:200]),
    }


def write_model_card_section(
    task_name: str,
    feature_set: str,
    dataset_path: str,
    split_method: str,
    used_folds: int,
) -> str:
    return "\n".join(
        [
            f"## {task_name} ({feature_set})",
            "",
            "- Purpose: file-level experimental evidence model.",
            "- Allowed use: research-oriented evidence analysis for the task axis only.",
            "- Not allowed use: final forensic decision, legal certainty claim, active production deployment.",
            f"- Training data: `{dataset_path}`",
            f"- Evaluation: cross-validation via `{split_method}` with {used_folds} folds.",
            "- Limitations: small dataset, group leakage constraints, task-specific scope only.",
            "- Safety note: outputs are experimental and not final forensic proof.",
            "",
        ]
    )


def write_json(path: str | Path, payload: dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def now_utc_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def sanitize_float(v: Any) -> Any:
    try:
        f = float(v)
    except Exception:
        return v
    if not math.isfinite(f):
        return ""
    return f
