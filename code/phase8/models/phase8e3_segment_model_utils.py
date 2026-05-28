"""
Phase 8E-3 partial-fabrication segment model utilities.

Experimental-only utilities. Timestamp-aligned labels required.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.feature_selection import SelectKBest, VarianceThreshold, f_classif
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

SCHEMA_VERSION = "phase8e3_v1"
TASK_NAME = "partial_fabrication_segment_model"
ALLOWED_FEATURE_SETS = ("localization", "acoustic", "ssl", "combined")

FORBIDDEN_FEATURE_COLUMNS = {
    "timestamp_segment_label",
    "training_label_available",
    "max_fabricated_overlap_sec",
    "max_fabricated_overlap_ratio",
    "total_fabricated_overlap_sec",
    "overlaps_true_fabricated_region",
    "candidate_type",
    "allowed_use",
    "candidate_reason",
    "file_id",
    "segment_id",
    "audio_path",
    "start_sec",
    "end_sec",
    "known_origin_label",
    "known_manipulation_labels",
    "suspicious_segment_flag",
    "final_forensic_status",
    "fake_score",
    "real_score",
    "evidence_origin_score",
    "origin_score",
    "y_true",
    "y_pred_experimental",
    "y_proba_experimental",
    "fold",
    "segment_label_source",
    "has_true_timestamp_labels",
}

FORBIDDEN_FEATURE_SUBSTRINGS = (
    "fabricated_baseline",
    "outside_baseline",
    "inside_outside_margin",
    "inside_outside_separation",
    "max_fabricated_overlap",
    "total_fabricated_overlap",
    "overlaps_true_fabricated_region",
)

SAFE_LOCALIZATION_FEATURES = [
    "within_file_acoustic_deviation_score",
    "within_file_ssl_deviation_score",
    "combined_within_file_deviation_score",
    "neighbor_acoustic_transition_score",
    "neighbor_ssl_transition_score",
    "combined_neighbor_transition_score",
    "acoustic_distance_from_file_median",
    "ssl_distance_from_file_median",
    "acoustic_deviation_percentile_within_file",
    "ssl_deviation_percentile_within_file",
]


def is_forbidden_label_derived_feature(col_name: str) -> bool:
    c = str(col_name).strip().lower()
    if not c:
        return True
    if c in FORBIDDEN_FEATURE_COLUMNS:
        return True
    return any(tok in c for tok in FORBIDDEN_FEATURE_SUBSTRINGS)


def split_forbidden_features(features: list[str]) -> tuple[list[str], list[str]]:
    forbidden = [c for c in features if is_forbidden_label_derived_feature(c)]
    allowed = [c for c in features if c not in forbidden]
    return allowed, forbidden


def _collect_feature_candidates(df: pd.DataFrame, feature_set: str) -> list[str]:
    acoustic = [
        c
        for c in df.columns
        if (
            c.startswith("rms_")
            or c.startswith("spectral_")
            or c.startswith("mfcc_")
            or c.endswith("_band_energy_ratio")
            or c.startswith("zero_crossing_rate_")
            or c
            in {
                "noise_floor_proxy",
                "snr_proxy",
                "dynamic_range_proxy",
                "bandwidth_occupied_95",
                "peak_amplitude",
                "zero_crossing_rate_mean",
                "clipping_ratio",
                "silence_ratio",
                "very_high_band_energy_ratio",
            }
        )
    ]
    ssl = [c for c in df.columns if c.startswith("ssl_emb_")]
    localization = [c for c in SAFE_LOCALIZATION_FEATURES if c in df.columns]
    if feature_set == "localization":
        return localization
    if feature_set == "acoustic":
        return acoustic
    if feature_set == "ssl":
        return ssl
    return sorted(set(localization + acoustic + ssl))


@dataclass(frozen=True)
class SplitChoice:
    splitter: Any
    split_method: str
    used_folds: int


def now_utc_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def load_csv_required(path: str | Path) -> pd.DataFrame:
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Required CSV missing: {p}")
    return pd.read_csv(p, dtype=str, keep_default_na=False)


def parse_binary_target(labels: pd.Series) -> np.ndarray:
    vals = labels.astype(str).str.strip()
    bad = vals[~vals.isin({"0", "1"})]
    if len(bad):
        raise ValueError(f"Target contains non-binary values: {sorted(set(bad))[:5]}")
    return vals.astype(int).to_numpy()


def pick_feature_columns(df: pd.DataFrame, feature_set: str) -> list[str]:
    if feature_set not in ALLOWED_FEATURE_SETS:
        raise ValueError(f"Unsupported feature_set={feature_set}")
    cols_raw = _collect_feature_candidates(df, feature_set)

    cols, _forbidden = split_forbidden_features(cols_raw)
    if not cols:
        raise ValueError(f"No usable features for feature_set={feature_set}")
    return cols


def clean_feature_matrix(
    df: pd.DataFrame, features: list[str]
) -> tuple[pd.DataFrame, list[str], list[str], list[str]]:
    raw = df[features].copy()
    x = raw.mask(raw.eq(""))
    num_cols = []
    non_numeric = []
    for c in x.columns:
        vals = pd.to_numeric(x[c], errors="coerce")
        if vals.notna().sum() == 0 and raw[c].astype(str).str.strip().ne("").any():
            non_numeric.append(c)
        else:
            x[c] = vals
            num_cols.append(c)
    x = x[num_cols]
    all_missing = [c for c in x.columns if x[c].notna().sum() == 0]
    usable = [c for c in x.columns if c not in all_missing]
    x = x[usable]
    return x, usable, all_missing, non_numeric


def choose_splitter(y: np.ndarray, groups: np.ndarray, cv_folds: int, random_seed: int) -> SplitChoice:
    class_counts = pd.Series(y).value_counts()
    max_by_class = int(class_counts.min()) if len(class_counts) else 0
    folds = min(cv_folds, max_by_class)
    if folds < 3:
        folds = min(3, max_by_class)
    if folds < 3:
        raise ValueError(f"Insufficient class support for CV: {class_counts.to_dict()}")

    if len(set(groups.astype(str))) >= folds:
        try:
            from sklearn.model_selection import StratifiedGroupKFold

            return SplitChoice(
                splitter=StratifiedGroupKFold(n_splits=folds, shuffle=True, random_state=random_seed),
                split_method="StratifiedGroupKFold",
                used_folds=folds,
            )
        except Exception:
            return SplitChoice(
                splitter=GroupKFold(n_splits=folds),
                split_method="GroupKFold",
                used_folds=folds,
            )
    return SplitChoice(
        splitter=StratifiedKFold(n_splits=folds, shuffle=True, random_state=random_seed),
        split_method="StratifiedKFold",
        used_folds=folds,
    )


def build_pipeline(max_selected_features: int, random_seed: int) -> Pipeline:
    return Pipeline(
        [
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


def run_cv(
    df: pd.DataFrame,
    feature_set: str,
    cv_folds: int,
    random_seed: int,
    max_selected_features: int,
    model_type: str,
) -> dict[str, pd.DataFrame | str | int | list[str]]:
    candidate_features = _collect_feature_candidates(df, feature_set)
    raw_feature_count = len(candidate_features)
    feats, forbidden_cols = split_forbidden_features(candidate_features)
    if not feats:
        raise ValueError(f"No usable features for feature_set={feature_set}")
    x, feats, all_missing_cols, non_numeric_cols = clean_feature_matrix(df, feats)
    if len(feats) == 0:
        raise ValueError(f"No usable features for feature_set={feature_set} after cleaning.")
    leakage_status = "failed" if len(split_forbidden_features(feats)[1]) > 0 else "passed"
    y = parse_binary_target(df["target_partial_fabricated"])
    groups = df["split_group_id"].astype(str).to_numpy()
    split_choice = choose_splitter(y, groups, cv_folds, random_seed)
    splitter = split_choice.splitter

    rows_metrics = []
    rows_oof = []
    rows_conf = []
    rows_manifest = []

    if split_choice.split_method == "StratifiedGroupKFold":
        split_iter = splitter.split(x, y, groups)
    elif split_choice.split_method == "GroupKFold":
        split_iter = splitter.split(x, y, groups)
    else:
        split_iter = splitter.split(x, y)

    for fold_i, (tr, te) in enumerate(split_iter, start=1):
        model = clone(build_pipeline(min(max_selected_features, len(feats)), random_seed))
        model.fit(x.iloc[tr], y[tr])
        pred = model.predict(x.iloc[te]).astype(int)
        proba = model.predict_proba(x.iloc[te])[:, 1]
        tn, fp, fn, tp = confusion_matrix(y[te], pred, labels=[0, 1]).ravel()
        rows_conf.append(
            {
                "task_name": TASK_NAME,
                "feature_set": feature_set,
                "fold": fold_i,
                "tn": int(tn),
                "fp": int(fp),
                "fn": int(fn),
                "tp": int(tp),
                "split_method": split_choice.split_method,
                "model_type": model_type,
            }
        )
        rows_metrics.append(
            {
                "task_name": TASK_NAME,
                "feature_set": feature_set,
                "fold": fold_i,
                "accuracy": float(accuracy_score(y[te], pred)),
                "balanced_accuracy": float(balanced_accuracy_score(y[te], pred)),
                "precision": float(precision_score(y[te], pred, zero_division=0)),
                "recall": float(recall_score(y[te], pred, zero_division=0)),
                "f1": float(f1_score(y[te], pred, zero_division=0)),
                "roc_auc": float(roc_auc_score(y[te], proba)) if len(np.unique(y[te])) > 1 else np.nan,
                "average_precision": float(average_precision_score(y[te], proba)) if len(np.unique(y[te])) > 1 else np.nan,
                "brier_score": float(brier_score_loss(y[te], proba)),
                "split_method": split_choice.split_method,
                "used_folds": split_choice.used_folds,
                "model_type": model_type,
            }
        )
        for j, idx in enumerate(te):
            rows_oof.append(
                {
                    "task_name": TASK_NAME,
                    "feature_set": feature_set,
                    "file_id": df.iloc[idx]["file_id"],
                    "segment_id": df.iloc[idx]["segment_id"],
                    "start_sec": df.iloc[idx].get("start_sec", ""),
                    "end_sec": df.iloc[idx].get("end_sec", ""),
                    "y_true": int(y[te][j]),
                    "y_pred_experimental": int(pred[j]),
                    "y_proba_experimental": float(proba[j]),
                    "fold": fold_i,
                    "split_method": split_choice.split_method,
                    "model_type": model_type,
                }
            )
        rows_manifest.append(
            {
                "task_name": TASK_NAME,
                "feature_set": feature_set,
                "fold": fold_i,
                "split_method": split_choice.split_method,
                "train_rows": len(tr),
                "test_rows": len(te),
                "model_type": model_type,
                "feature_count": len(feats),
                "raw_feature_count": raw_feature_count,
                "usable_feature_count": len(feats),
                "excluded_all_missing_count": len(all_missing_cols),
                "excluded_non_numeric_count": len(non_numeric_cols),
                "excluded_forbidden_label_derived_count": len(forbidden_cols),
                "excluded_all_missing_features": ";".join(all_missing_cols[:200]),
                "excluded_non_numeric_features": ";".join(non_numeric_cols[:200]),
                "excluded_forbidden_label_derived_features": ";".join(forbidden_cols[:200]),
                "feature_leakage_check_status": leakage_status,
                "features_preview": ";".join(feats[:100]),
            }
        )

    metrics_df = pd.DataFrame(rows_metrics)
    conf_df = pd.DataFrame(rows_conf)
    oof_df = pd.DataFrame(rows_oof)
    manifest_df = pd.DataFrame(rows_manifest)
    agg = (
        metrics_df.drop(columns=["fold"])
        .groupby(["task_name", "feature_set", "split_method", "used_folds", "model_type"], as_index=False)
        .mean(numeric_only=True)
    )
    # partial-specific metrics from OOF
    fabricated_total = int((oof_df["y_true"] == 1).sum())
    fabricated_detected = int(((oof_df["y_true"] == 1) & (oof_df["y_pred_experimental"] == 1)).sum())
    outside_total = int((oof_df["y_true"] == 0).sum())
    outside_false = int(((oof_df["y_true"] == 0) & (oof_df["y_pred_experimental"] == 1)).sum())
    agg["fabricated_segment_total"] = fabricated_total
    agg["fabricated_segment_detected_count"] = fabricated_detected
    agg["fabricated_segment_detected_rate"] = fabricated_detected / fabricated_total if fabricated_total else np.nan
    agg["outside_segment_total"] = outside_total
    agg["outside_false_fabricated_count"] = outside_false
    agg["outside_false_fabricated_rate"] = outside_false / outside_total if outside_total else np.nan
    agg["metric_scope"] = "cross_validated_experimental_mean"
    return {
        "metrics_mean": agg,
        "metrics_fold": metrics_df,
        "oof": oof_df,
        "confusion": conf_df,
        "manifest": manifest_df,
        "split_method": split_choice.split_method,
        "raw_feature_count": raw_feature_count,
        "usable_feature_count": len(feats),
        "excluded_all_missing_count": len(all_missing_cols),
        "excluded_non_numeric_count": len(non_numeric_cols),
        "excluded_forbidden_label_derived_count": len(forbidden_cols),
        "excluded_all_missing_features": all_missing_cols,
        "excluded_non_numeric_features": non_numeric_cols,
        "excluded_forbidden_label_derived_features": forbidden_cols,
        "feature_leakage_check_status": leakage_status,
    }


def threshold_grid(oof_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (feature_set,), g in oof_df.groupby(["feature_set"], dropna=False):
        y_true = pd.to_numeric(g["y_true"], errors="coerce").astype(int).to_numpy()
        y_prob = pd.to_numeric(g["y_proba_experimental"], errors="coerce").to_numpy(dtype=float)
        for th in np.arange(0.10, 0.901, 0.05):
            y_pred = (y_prob >= th).astype(int)
            tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
            fpr = fp / (fp + tn) if (fp + tn) else np.nan
            fnr = fn / (fn + tp) if (fn + tp) else np.nan
            rows.append(
                {
                    "task_name": TASK_NAME,
                    "feature_set": feature_set,
                    "threshold": round(float(th), 2),
                    "tn": int(tn),
                    "fp": int(fp),
                    "fn": int(fn),
                    "tp": int(tp),
                    "accuracy": float(accuracy_score(y_true, y_pred)),
                    "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
                    "precision": float(precision_score(y_true, y_pred, zero_division=0)),
                    "recall": float(recall_score(y_true, y_pred, zero_division=0)),
                    "f1": float(f1_score(y_true, y_pred, zero_division=0)),
                    "false_positive_rate": fpr,
                    "false_negative_rate": fnr,
                    "outside_false_fabricated_rate": fpr,
                    "fabricated_detected_rate": float(recall_score(y_true, y_pred, zero_division=0)),
                }
            )
    return pd.DataFrame(rows)


def file_level_localization_summary(oof_df: pd.DataFrame, top_k: int = 5) -> pd.DataFrame:
    rows = []
    oof_df = oof_df.copy()
    oof_df["y_true"] = pd.to_numeric(oof_df["y_true"], errors="coerce").astype(int)
    oof_df["y_proba_experimental"] = pd.to_numeric(oof_df["y_proba_experimental"], errors="coerce")
    for (feature_set, file_id), g in oof_df.groupby(["feature_set", "file_id"], dropna=False):
        g = g.sort_values("y_proba_experimental", ascending=False).reset_index(drop=True)
        top = g.head(top_k)
        rows.append(
            {
                "task_name": TASK_NAME,
                "feature_set": feature_set,
                "file_id": file_id,
                "total_segments": len(g),
                "true_fabricated_segments": int((g["y_true"] == 1).sum()),
                "true_outside_segments": int((g["y_true"] == 0).sum()),
                "predicted_top_k_segments": ";".join(top["segment_id"].astype(str).tolist()),
                "top_k_hit_any_fabricated_region": "true" if (top["y_true"] == 1).any() else "false",
                "top_k_hit_rate": float((top["y_true"] == 1).mean()) if len(top) else np.nan,
                "max_probability_in_true_fabricated_region": float(g[g["y_true"] == 1]["y_proba_experimental"].max()) if (g["y_true"] == 1).any() else np.nan,
                "max_probability_outside_region": float(g[g["y_true"] == 0]["y_proba_experimental"].max()) if (g["y_true"] == 0).any() else np.nan,
                "mean_probability_fabricated_region": float(g[g["y_true"] == 1]["y_proba_experimental"].mean()) if (g["y_true"] == 1).any() else np.nan,
                "mean_probability_outside_region": float(g[g["y_true"] == 0]["y_proba_experimental"].mean()) if (g["y_true"] == 0).any() else np.nan,
                "localization_review_note": "experimental timestamp-aligned localization summary; not proof of fabrication",
            }
        )
    return pd.DataFrame(rows)
