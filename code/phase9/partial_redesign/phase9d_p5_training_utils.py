"""Training/evaluation helpers for Phase 9D-P5B partial redesign (experimental only)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

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

TASK_FILE_GATE = "partial_file_candidate_model"
TASK_SEGMENT_LOCALIZER = "partial_segment_localizer_v2"

FILE_GATE_FEATURE_SETS = ("acoustic", "ssl", "combined")
SEGMENT_FEATURE_SETS = ("acoustic", "ssl", "localization", "combined")

PARTIAL_FILE_CATEGORIES = frozenset({"ai_fabricated", "human_fabricated"})
REPLAY_CATEGORIES = frozenset({"ai_replay", "human_replay", "ai_repeat", "human_repeat"})
MIXER_CATEGORIES = frozenset({"ai_mixer", "human_mixer"})
DIRECT_CATEGORIES = frozenset({"ai_direct", "human_direct", "human_clean"})

SAFE_LOCALIZATION_FEATURES = [
    "acoustic_distance_from_file_median",
    "ssl_distance_from_file_median",
    "within_file_acoustic_deviation_score",
    "within_file_ssl_deviation_score",
    "combined_within_file_deviation_score",
    "neighbor_acoustic_transition_score",
    "neighbor_ssl_transition_score",
    "combined_neighbor_transition_score",
    "acoustic_deviation_percentile_within_file",
    "ssl_deviation_percentile_within_file",
]

FILE_GATE_FORBIDDEN_EXACT = frozenset(
    {
        "target_is_partial_fabrication_file",
        "file_category",
        "known_origin_label",
        "known_manipulation_labels",
        "audio_path",
        "file_id",
        "partial_file_label_source",
        "allowed_use",
        "split_group_id",
        "leakage_group_id",
        "model_feature_columns_json",
        "fabricated_start_sec",
        "fabricated_end_sec",
        "timestamp_overlap_sec",
        "timestamp_overlap_ratio_segment",
        "timestamp_region_label",
        "fake_score",
        "real_score",
    }
)

SEGMENT_FORBIDDEN_EXACT = frozenset(
    {
        "target_is_fabricated_segment",
        "timestamp_overlap_sec",
        "timestamp_overlap_ratio_segment",
        "timestamp_region_label",
        "fabricated_start_sec",
        "fabricated_end_sec",
        "fabrication_direction",
        "segment_source_type",
        "file_category",
        "audio_path",
        "file_id",
        "segment_id",
        "allowed_use",
        "split_group_id",
        "leakage_group_id",
        "model_feature_columns_json",
        "fake_score",
        "real_score",
    }
)

FORBIDDEN_SUBSTRINGS = (
    "fabricated_baseline",
    "outside_baseline",
    "inside_outside_margin",
    "inside_outside_separation",
    "fusion_",
    "_fusion",
    "partial_fusion",
    "partial_probability",
    "origin_probability",
    "replay_probability",
    "mixer_probability",
)

ACOUSTIC_PREFIXES = ("rms_", "spectral_", "mfcc_")
ACOUSTIC_EXACT = {
    "peak_amplitude",
    "mean_amplitude",
    "std_amplitude",
    "dc_offset",
    "zero_crossing_rate_mean",
    "zero_crossing_rate_std",
    "clipping_ratio",
    "silence_ratio",
    "active_audio_ratio",
    "noise_floor_proxy",
    "snr_proxy",
    "dynamic_range_proxy",
    "spectral_entropy_mean",
    "spectral_entropy_std",
    "high_freq_rolloff_ratio",
    "bandwidth_occupied_95",
    "low_band_energy_ratio",
    "mid_band_energy_ratio",
    "high_band_energy_ratio",
    "very_high_band_energy_ratio",
}


@dataclass(frozen=True)
class SplitChoice:
    splitter: Any
    split_method: str
    used_folds: int
    group_column: str


def repo_root_from_here(here: Path) -> Path:
    return here.resolve().parents[3]


def now_utc_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def progress(msg: str, *, enabled: bool = True) -> None:
    if enabled:
        print(msg, flush=True)


def load_json_columns(path: Path) -> list[str]:
    if not path.is_file():
        raise FileNotFoundError(f"Feature column JSON missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Feature column JSON must be a list: {path}")
    return [str(c) for c in data]


def load_dataset_csv(path: Path) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(f"Required dataset missing: {path}")
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def is_forbidden_feature(name: str, task: str) -> bool:
    c = str(name).strip()
    cl = c.lower()
    exact = FILE_GATE_FORBIDDEN_EXACT if task == TASK_FILE_GATE else SEGMENT_FORBIDDEN_EXACT
    if c in exact:
        return True
    if "timestamp" in cl and cl not in {"spectral_centroid_mean"}:
        if any(tok in cl for tok in ("overlap", "fabricated", "insert_", "stamp")):
            return True
    return any(tok in cl for tok in FORBIDDEN_SUBSTRINGS)


def split_acoustic_ssl(names: Iterable[str]) -> tuple[list[str], list[str]]:
    acoustic: list[str] = []
    ssl: list[str] = []
    for c in names:
        if str(c).startswith("ssl_emb_"):
            ssl.append(c)
        elif c in ACOUSTIC_EXACT or any(str(c).startswith(p) for p in ACOUSTIC_PREFIXES):
            acoustic.append(c)
    return sorted(acoustic), sorted(ssl)


def select_features_for_set(
    all_columns: list[str],
    feature_set: str,
    task: str,
) -> list[str]:
    allowed = [c for c in all_columns if not is_forbidden_feature(c, task)]
    acoustic, ssl = split_acoustic_ssl(allowed)
    localization = [c for c in SAFE_LOCALIZATION_FEATURES if c in allowed]

    if task == TASK_FILE_GATE:
        if feature_set == "acoustic":
            return acoustic
        if feature_set == "ssl":
            return ssl
        if feature_set == "combined":
            return sorted(set(acoustic + ssl))
        raise ValueError(f"Unknown file feature_set={feature_set}")

    if feature_set == "acoustic":
        return acoustic
    if feature_set == "ssl":
        return ssl
    if feature_set == "localization":
        return localization
    if feature_set == "combined":
        return sorted(set(acoustic + ssl + localization))
    raise ValueError(f"Unknown segment feature_set={feature_set}")


def clean_feature_matrix(
    df: pd.DataFrame,
    features: list[str],
) -> tuple[pd.DataFrame, list[str], list[str], list[str]]:
    raw = df[features].copy().mask(df[features].eq(""))
    non_numeric: list[str] = []
    numeric_cols: list[str] = []
    for c in raw.columns:
        vals = pd.to_numeric(raw[c], errors="coerce")
        if vals.notna().sum() == 0 and raw[c].astype(str).str.strip().ne("").any():
            non_numeric.append(c)
        else:
            raw[c] = vals
            numeric_cols.append(c)
    x = raw[numeric_cols]
    all_missing = [c for c in x.columns if x[c].notna().sum() == 0]
    usable = [c for c in x.columns if c not in all_missing]
    return x[usable], usable, all_missing, non_numeric


def parse_binary_target(series: pd.Series, name: str) -> np.ndarray:
    vals = series.astype(str).str.strip()
    bad = vals[~vals.isin({"0", "1"})]
    if len(bad):
        raise ValueError(f"{name} contains non-binary values: {sorted(set(bad))[:5]}")
    return vals.astype(int).to_numpy()


def resolve_group_column(df: pd.DataFrame, prefer: tuple[str, ...]) -> str:
    for col in prefer:
        if col in df.columns and df[col].astype(str).str.strip().ne("").any():
            return col
    raise ValueError(f"No usable group column among {prefer}")


def choose_group_splitter(
    y: np.ndarray,
    groups: np.ndarray,
    cv_folds: int,
    random_seed: int,
    *,
    require_groups: bool = True,
) -> SplitChoice:
    n = len(y)
    if n < 6:
        raise ValueError("Dataset too small for CV; need at least 6 rows.")

    unique_groups = len(set(str(g) for g in groups))
    if require_groups and unique_groups < 2:
        raise ValueError("Group-aware CV required but fewer than 2 unique groups.")

    class_counts = pd.Series(y).value_counts()
    max_by_class = int(class_counts.min()) if len(class_counts) else 0
    folds = min(cv_folds, max_by_class)
    if folds < 2:
        folds = min(2, max_by_class)
    if folds < 2:
        raise ValueError(f"Insufficient class support for CV: {class_counts.to_dict()}")

    if unique_groups >= folds:
        try:
            from sklearn.model_selection import StratifiedGroupKFold

            return SplitChoice(
                splitter=StratifiedGroupKFold(n_splits=folds, shuffle=True, random_state=random_seed),
                split_method="StratifiedGroupKFold",
                used_folds=folds,
                group_column="",
            )
        except Exception:
            return SplitChoice(
                splitter=GroupKFold(n_splits=folds),
                split_method="GroupKFold",
                used_folds=folds,
                group_column="",
            )

    if require_groups:
        raise ValueError(
            f"Group-aware CV infeasible: unique_groups={unique_groups}, required_folds={folds}. "
            "Refusing to split segments/files across folds without groups."
        )
    return SplitChoice(
        splitter=StratifiedKFold(n_splits=folds, shuffle=True, random_state=random_seed),
        split_method="StratifiedKFold",
        used_folds=folds,
        group_column="",
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
                    max_iter=3000,
                    solver="liblinear",
                    random_state=random_seed,
                ),
            ),
        ]
    )


def safe_predict_proba(model: Pipeline, x: pd.DataFrame) -> np.ndarray:
    proba = model.predict_proba(x)
    if proba.shape[1] == 1:
        return np.zeros(len(x), dtype=float)
    return proba[:, 1]


def audit_features(
    task_name: str,
    feature_set: str,
    raw_features: list[str],
    usable_features: list[str],
    dropped_all_missing: list[str],
    dropped_non_numeric: list[str],
    forbidden_hits: list[str],
) -> dict[str, Any]:
    leakage = "passed" if not forbidden_hits else "failed"
    return {
        "task_name": task_name,
        "feature_set": feature_set,
        "raw_feature_count": len(raw_features),
        "usable_feature_count": len(usable_features),
        "dropped_all_missing_count": len(dropped_all_missing),
        "dropped_non_numeric_count": len(dropped_non_numeric),
        "dropped_forbidden_count": len(forbidden_hits),
        "forbidden_feature_hits": ";".join(forbidden_hits[:100]) if forbidden_hits else "",
        "leakage_check_status": leakage,
    }


def parse_forbidden_feature_hits(value: Any) -> list[str]:
    """Parse audit forbidden_feature_hits; empty/NaN means no forbidden features."""
    if value is None:
        return []
    if isinstance(value, float) and np.isnan(value):
        return []
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "[]", "<na>", "nat"}:
        return []
    parts = [p.strip() for p in text.split(";") if p.strip()]
    return [p for p in parts if p.lower() not in {"nan", "none"}]


def compute_broad_activation_summary(
    segment_oof: pd.DataFrame,
    *,
    feature_set: str = "combined",
    segment_threshold: float = 0.50,
    broad_activation_fraction: float = 0.40,
    top_k: int = 5,
) -> dict[str, Any]:
    """Unique partial-file broad activation stats for one selected model configuration."""
    df = segment_oof[segment_oof["feature_set"].astype(str) == feature_set].copy()
    if df.empty:
        return {
            "selected_feature_set": feature_set,
            "selected_segment_threshold": segment_threshold,
            "partial_file_count": 0,
            "broad_activation_count_selected": 0,
            "localized_pattern_supported_count_selected": 0,
            "top1_hit_count_selected": 0,
            "top3_hit_count_selected": 0,
            "top5_hit_count_selected": 0,
        }

    df["y_true"] = pd.to_numeric(df["y_true"], errors="coerce").astype(int)
    df["y_proba_experimental"] = pd.to_numeric(df["y_proba_experimental"], errors="coerce")

    partial_file_ids: set[str] = set()
    broad_count = 0
    localized_count = 0
    top1_count = 0
    top3_count = 0
    top5_count = 0

    for file_id, g in df.groupby("file_id", sort=False):
        file_cat = str(g["file_category"].iloc[0]) if "file_category" in g.columns else ""
        if file_cat not in PARTIAL_FILE_CATEGORIES:
            continue
        partial_file_ids.add(str(file_id))
        g = g.sort_values(["y_proba_experimental", "start_sec"], ascending=[False, True])
        high_frac = float((g["y_proba_experimental"] >= segment_threshold).mean())
        top1_hit = bool((g.head(1)["y_true"] == 1).any())
        top3_hit = bool((g.head(3)["y_true"] == 1).any())
        top5_hit = bool((g.head(top_k)["y_true"] == 1).any())
        broad = high_frac >= broad_activation_fraction
        localized = top5_hit and not broad

        if broad:
            broad_count += 1
        if localized:
            localized_count += 1
        if top1_hit:
            top1_count += 1
        if top3_hit:
            top3_count += 1
        if top5_hit:
            top5_count += 1

    n = len(partial_file_ids)
    return {
        "selected_feature_set": feature_set,
        "selected_segment_threshold": segment_threshold,
        "partial_file_count": n,
        "broad_activation_count_selected": broad_count,
        "localized_pattern_supported_count_selected": localized_count,
        "top1_hit_count_selected": top1_count,
        "top3_hit_count_selected": top3_count,
        "top5_hit_count_selected": top5_count,
        "p4_broad_activation_reference": "46/46 (Phase 9D-P4)",
        "p5b_broad_activation_selected": f"{broad_count}/{n}" if n else "0/0",
    }


def _segment_localized_evidence(
    seg_df: pd.DataFrame,
    *,
    segment_threshold: float,
    broad_limit: float,
    contrast_threshold: float,
    top_k: int = 5,
) -> dict[str, Any]:
    g = seg_df.sort_values(["y_proba_experimental", "start_sec"], ascending=[False, True]).copy()
    probs = pd.to_numeric(g["y_proba_experimental"], errors="coerce").fillna(0.0).to_numpy(dtype=float)
    if len(probs) == 0:
        return {
            "localized_evidence": False,
            "high_segment_fraction": np.nan,
            "topk_minus_rest_probability": np.nan,
            "top1_hit": False,
            "top3_hit": False,
            "top5_hit": False,
            "broad_activation": False,
        }

    high_frac = float((probs >= segment_threshold).mean())
    has_high = bool((probs >= segment_threshold).any())
    topk_probs = probs[:top_k]
    rest_probs = probs[top_k:] if len(probs) > top_k else np.array([], dtype=float)
    if len(rest_probs):
        topk_minus_rest = float(topk_probs.mean() - rest_probs.mean())
    else:
        topk_minus_rest = float(topk_probs.mean()) if len(topk_probs) else 0.0

    localized = bool(has_high and high_frac <= broad_limit and topk_minus_rest >= contrast_threshold)
    y_true = pd.to_numeric(g["y_true"], errors="coerce").astype(int).to_numpy()
    is_partial = str(g["file_category"].iloc[0]) in PARTIAL_FILE_CATEGORIES if "file_category" in g.columns else False

    return {
        "localized_evidence": localized,
        "high_segment_fraction": high_frac,
        "topk_minus_rest_probability": topk_minus_rest,
        "top1_hit": bool((y_true[:1] == 1).any()) if is_partial and len(y_true) >= 1 else False,
        "top3_hit": bool((y_true[: min(3, len(y_true))] == 1).any()) if is_partial else False,
        "top5_hit": bool((y_true[: min(top_k, len(y_true))] == 1).any()) if is_partial else False,
        "broad_activation": bool(high_frac > broad_limit),
    }


CASCADE_GATE_THRESHOLDS = [0.30, 0.40, 0.50, 0.60, 0.70, 0.80]
CASCADE_SEGMENT_THRESHOLDS = [0.50, 0.60, 0.70, 0.80, 0.85, 0.90]
CASCADE_CONTRAST_THRESHOLDS = [0.15, 0.25, 0.35]
CASCADE_BROAD_LIMITS = [0.25, 0.35, 0.45]

# Shared acceptance rules for cascade recommendation, training report, and validation.
CASCADE_ACCEPTANCE_CONFIG: dict[str, float | None] = {
    "max_direct_false_partial_rate": 0.20,
    "max_replay_false_partial_rate": 0.05,
    "max_mixer_false_partial_rate": 0.05,
    "max_broad_activation_rate_when_positive": 0.10,
    "min_file_gate_threshold": 0.50,
    "max_non_partial_false_alarm_rate": None,
    "min_partial_file_recall": None,
}

CASCADE_CONSTRAINTS = CASCADE_ACCEPTANCE_CONFIG

MANUAL_REVIEW_ONLY_MESSAGE = (
    "No release-ready threshold pair found; use as manual-review support only."
)

MANUAL_REVIEW_NEXT_STEP = (
    "Do not package into release yet. Use P5B outputs as experimental manual-review support only. "
    "Next step is stricter cascade tuning or dataset/feature improvement."
)


def is_valid_recommendation_value(value: Any) -> bool:
    """True only when recommended_threshold_pair contains an actual recommendation."""
    if value is None:
        return False
    if isinstance(value, float) and np.isnan(value):
        return False
    text = str(value).strip()
    return bool(text) and text.lower() not in {"nan", "none", "[]", "<na>", "nat"}


def get_recommended_cascade_rows(cascade_df: pd.DataFrame) -> pd.DataFrame:
    if cascade_df.empty or "recommended_threshold_pair" not in cascade_df.columns:
        return cascade_df.iloc[0:0]
    mask = cascade_df["recommended_threshold_pair"].map(is_valid_recommendation_value)
    return cascade_df[mask].copy()


def _row_metric(row: pd.Series, col: str, default: float = float("nan")) -> float:
    try:
        val = float(row.get(col, default))
    except (TypeError, ValueError):
        return default
    return val if np.isfinite(val) else default


def evaluate_cascade_acceptance(
    row: pd.Series,
    config: dict[str, float | None] | None = None,
) -> tuple[bool, list[str]]:
    """Return (passed, human-readable failed conditions) using shared acceptance config."""
    cfg = config or CASCADE_ACCEPTANCE_CONFIG
    failures: list[str] = []

    direct = _row_metric(row, "direct_false_partial_rate", default=1.0)
    replay = _row_metric(row, "replay_false_partial_rate", default=1.0)
    mixer = _row_metric(row, "mixer_false_partial_rate", default=1.0)
    broad = _row_metric(row, "broad_activation_rate_when_positive", default=1.0)
    gate = _row_metric(row, "file_gate_threshold", default=0.0)
    non_partial = _row_metric(row, "non_partial_false_alarm_rate", default=float("nan"))
    recall = _row_metric(row, "partial_file_recall", default=float("nan"))

    max_direct = cfg.get("max_direct_false_partial_rate")
    if max_direct is not None and direct > float(max_direct):
        failures.append(f"direct_false_partial_rate {direct:.4f} > {float(max_direct):.4f}")

    max_replay = cfg.get("max_replay_false_partial_rate")
    if max_replay is not None and replay > float(max_replay):
        failures.append(f"replay_false_partial_rate {replay:.4f} > {float(max_replay):.4f}")

    max_mixer = cfg.get("max_mixer_false_partial_rate")
    if max_mixer is not None and mixer > float(max_mixer):
        failures.append(f"mixer_false_partial_rate {mixer:.4f} > {float(max_mixer):.4f}")

    max_broad = cfg.get("max_broad_activation_rate_when_positive")
    if max_broad is not None and broad > float(max_broad):
        failures.append(
            f"broad_activation_rate_when_positive {broad:.4f} > {float(max_broad):.4f}"
        )

    min_gate = cfg.get("min_file_gate_threshold")
    if min_gate is not None and gate < float(min_gate):
        failures.append(f"file_gate_threshold {gate:.4f} < {float(min_gate):.4f}")

    max_non_partial = cfg.get("max_non_partial_false_alarm_rate")
    if max_non_partial is not None and np.isfinite(non_partial) and non_partial > float(max_non_partial):
        failures.append(f"non_partial_false_alarm_rate {non_partial:.4f} > {float(max_non_partial):.4f}")

    min_recall = cfg.get("min_partial_file_recall")
    if min_recall is not None and np.isfinite(recall) and recall < float(min_recall):
        failures.append(f"partial_file_recall {recall:.4f} < {float(min_recall):.4f}")

    return len(failures) == 0, failures


def format_acceptance_config_table(config: dict[str, float | None] | None = None) -> str:
    cfg = config or CASCADE_ACCEPTANCE_CONFIG
    lines = [
        "| Rule | Threshold |",
        "|------|----------:|",
    ]
    labels = {
        "max_direct_false_partial_rate": "direct_false_partial_rate <=",
        "max_replay_false_partial_rate": "replay_false_partial_rate <=",
        "max_mixer_false_partial_rate": "mixer_false_partial_rate <=",
        "max_broad_activation_rate_when_positive": "broad_activation_rate_when_positive <=",
        "min_file_gate_threshold": "file_gate_threshold >=",
        "max_non_partial_false_alarm_rate": "non_partial_false_alarm_rate <=",
        "min_partial_file_recall": "partial_file_recall >=",
    }
    for key, label in labels.items():
        val = cfg.get(key)
        display = "not enforced" if val is None else f"{float(val):.4f}"
        lines.append(f"| {label} | {display} |")
    return "\n".join(lines)


def _format_cascade_row_brief(row: pd.Series) -> str:
    return (
        f"file_gate={_row_metric(row, 'file_gate_threshold'):.2f}, "
        f"segment={_row_metric(row, 'segment_threshold'):.2f}, "
        f"contrast={_row_metric(row, 'contrast_threshold'):.2f}, "
        f"broad_limit={_row_metric(row, 'broad_limit'):.2f}"
    )


def compute_cascade_acceptance_diagnostics(
    cascade_df: pd.DataFrame,
    config: dict[str, float | None] | None = None,
) -> dict[str, Any]:
    """Diagnostics shared by training report and validation."""
    cfg = config or CASCADE_ACCEPTANCE_CONFIG
    diag: dict[str, Any] = {
        "acceptance_config": dict(cfg),
        "has_release_ready_pair": False,
        "recommended_row": None,
        "best_accepted_row": None,
        "best_accepted_passed": False,
        "best_accepted_failed_conditions": [],
        "manual_review_only": True,
        "min_direct_false_partial_rate": np.nan,
        "min_non_partial_false_alarm_rate": np.nan,
        "best_recall_replay_mixer_broad_safe_row": None,
        "best_recall_replay_mixer_broad_safe": np.nan,
    }
    if cascade_df.empty:
        return diag

    direct = pd.to_numeric(cascade_df.get("direct_false_partial_rate"), errors="coerce")
    non_partial = pd.to_numeric(cascade_df.get("non_partial_false_alarm_rate"), errors="coerce")
    if direct.notna().any():
        diag["min_direct_false_partial_rate"] = float(direct.min())
    if non_partial.notna().any():
        diag["min_non_partial_false_alarm_rate"] = float(non_partial.min())

    replay_safe = pd.to_numeric(cascade_df.get("replay_false_partial_rate"), errors="coerce") <= float(
        cfg.get("max_replay_false_partial_rate") or 1.0
    )
    mixer_safe = pd.to_numeric(cascade_df.get("mixer_false_partial_rate"), errors="coerce") <= float(
        cfg.get("max_mixer_false_partial_rate") or 1.0
    )
    broad_safe = pd.to_numeric(cascade_df.get("broad_activation_rate_when_positive"), errors="coerce") <= float(
        cfg.get("max_broad_activation_rate_when_positive") or 1.0
    )
    rmb_safe = cascade_df[replay_safe & mixer_safe & broad_safe].copy()
    if not rmb_safe.empty:
        recall = pd.to_numeric(rmb_safe["partial_file_recall"], errors="coerce")
        best_idx = recall.idxmax()
        best_row = rmb_safe.loc[best_idx]
        diag["best_recall_replay_mixer_broad_safe_row"] = best_row
        diag["best_recall_replay_mixer_broad_safe"] = float(recall.loc[best_idx])

    passing_mask = cascade_df.apply(lambda r: evaluate_cascade_acceptance(r, cfg)[0], axis=1)
    passing = cascade_df[passing_mask].copy()
    if not passing.empty:
        if "candidate_score" in passing.columns:
            best_accepted = passing.sort_values("candidate_score", ascending=False).iloc[0]
        else:
            best_accepted = passing.iloc[0]
        diag["best_accepted_row"] = best_accepted
        passed, failures = evaluate_cascade_acceptance(best_accepted, cfg)
        diag["best_accepted_passed"] = passed
        diag["best_accepted_failed_conditions"] = failures

    recommended = get_recommended_cascade_rows(cascade_df)
    if not recommended.empty:
        rec_row = recommended.iloc[0]
        diag["recommended_row"] = rec_row
        passed, failures = evaluate_cascade_acceptance(rec_row, cfg)
        diag["has_release_ready_pair"] = passed
        diag["manual_review_only"] = not passed
        if not passed:
            diag["best_accepted_failed_conditions"] = failures
    else:
        diag["has_release_ready_pair"] = not passing.empty
        diag["manual_review_only"] = passing.empty

    return diag


def format_cascade_acceptance_diagnostics(diagnostics: dict[str, Any]) -> str:
    cfg = diagnostics.get("acceptance_config", CASCADE_ACCEPTANCE_CONFIG)
    lines = [
        "## Cascade acceptance diagnostics",
        "",
        "### Chosen acceptance thresholds",
        "",
        format_acceptance_config_table(cfg),
        "",
        "| Diagnostic | Value |",
        "|------------|------:|",
    ]

    release_ready = "yes" if diagnostics.get("has_release_ready_pair") else "no"
    lines.append(f"| Release-ready pair found | {release_ready} |")

    min_direct = diagnostics.get("min_direct_false_partial_rate", np.nan)
    min_non_partial = diagnostics.get("min_non_partial_false_alarm_rate", np.nan)
    lines.append(
        f"| Minimum observed direct_false_partial_rate (grid) | "
        f"{min_direct:.4f} |" if np.isfinite(min_direct) else "| Minimum observed direct_false_partial_rate (grid) | n/a |"
    )

    if np.isfinite(min_non_partial):
        lines.append(f"| Minimum observed non_partial_false_alarm_rate (grid) | {min_non_partial:.4f} |")
    else:
        lines.append("| Minimum observed non_partial_false_alarm_rate (grid) | n/a |")

    best_rmb = diagnostics.get("best_recall_replay_mixer_broad_safe", np.nan)
    best_rmb_row = diagnostics.get("best_recall_replay_mixer_broad_safe_row")
    if best_rmb_row is not None and np.isfinite(best_rmb):
        lines.append(
            f"| Best recall with replay/mixer/broad safety | {best_rmb:.4f} "
            f"({_format_cascade_row_brief(best_rmb_row)}) |"
        )
    else:
        lines.append("| Best recall with replay/mixer/broad safety | n/a |")

    best_row = diagnostics.get("best_accepted_row")
    if best_row is not None:
        lines.append(f"| Best candidate under acceptance rules | {_format_cascade_row_brief(best_row)} |")
        lines.append(
            f"| Best candidate passed acceptance | "
            f"{'yes' if diagnostics.get('best_accepted_passed') else 'no'} |"
        )
        failures = diagnostics.get("best_accepted_failed_conditions") or []
        fail_text = "; ".join(failures) if failures else "none"
        lines.append(f"| Failed conditions (best/recommended) | {fail_text} |")
    else:
        lines.append("| Best candidate under acceptance rules | none |")
        lines.append("| Best candidate passed acceptance | no |")
        lines.append("| Failed conditions (best/recommended) | no grid row evaluated |")

    rec_row = diagnostics.get("recommended_row")
    if rec_row is not None:
        lines.append(f"| CSV recommended pair | {_format_cascade_row_brief(rec_row)} |")

    return "\n".join(lines)


def assess_cascade_release_ready(
    cascade_df: pd.DataFrame,
    config: dict[str, float | None] | None = None,
) -> tuple[bool, str]:
    """Shared PASS/FAIL assessment for cascade release-ready recommendation."""
    cfg = config or CASCADE_ACCEPTANCE_CONFIG
    diagnostics = compute_cascade_acceptance_diagnostics(cascade_df, cfg)
    recommended = get_recommended_cascade_rows(cascade_df)

    if not recommended.empty:
        row = recommended.iloc[0]
        passed, failures = evaluate_cascade_acceptance(row, cfg)
        if passed:
            return True, f"recommended pair passes shared acceptance rules: {row['recommended_threshold_pair']}"
        return False, f"recommended pair in CSV violates acceptance rules: {'; '.join(failures)}"

    passing = cascade_df[cascade_df.apply(lambda r: evaluate_cascade_acceptance(r, cfg)[0], axis=1)] if not cascade_df.empty else cascade_df
    if not passing.empty:
        return False, (
            "feasible pair exists in cascade grid but recommended_threshold_pair is blank — "
            "re-run --reuse_existing_predictions to regenerate cascade CSV/report"
        )

    failures = diagnostics.get("best_accepted_failed_conditions") or []
    if failures:
        return False, f"no pair satisfied acceptance rules; example failure: {'; '.join(failures)}"

    max_direct = cfg.get("max_direct_false_partial_rate")
    min_direct = diagnostics.get("min_direct_false_partial_rate", np.nan)
    if np.isfinite(min_direct) and max_direct is not None and min_direct > float(max_direct):
        return False, (
            f"no pair satisfied direct_false_partial_rate <= {float(max_direct):.4f} "
            f"(minimum observed {min_direct:.4f})"
        )

    return False, MANUAL_REVIEW_ONLY_MESSAGE


def check_training_report_cascade_alignment(
    report_text: str,
    cascade_df: pd.DataFrame,
    config: dict[str, float | None] | None = None,
) -> tuple[bool, str]:
    """Ensure training report wording matches cascade CSV recommendation state."""
    cfg = config or CASCADE_ACCEPTANCE_CONFIG
    recommended = get_recommended_cascade_rows(cascade_df)
    csv_has_passing = False
    if not recommended.empty:
        csv_has_passing, _ = evaluate_cascade_acceptance(recommended.iloc[0], cfg)

    report_claims_release = "Release-ready pair:" in report_text
    report_claims_legacy_release = (
        "Recommended pair:" in report_text
        and MANUAL_REVIEW_ONLY_MESSAGE not in report_text
        and MANUAL_REVIEW_NEXT_STEP not in report_text
    )
    report_claims_manual = (
        MANUAL_REVIEW_ONLY_MESSAGE in report_text or MANUAL_REVIEW_NEXT_STEP in report_text
    )

    if (report_claims_release or report_claims_legacy_release) and not csv_has_passing:
        if not recommended.empty:
            _, failures = evaluate_cascade_acceptance(recommended.iloc[0], cfg)
            return False, f"training report claims release-ready pair but CSV recommendation fails: {'; '.join(failures)}"
        return False, "training report claims release-ready pair but cascade CSV has no valid recommendation"

    if csv_has_passing and report_claims_manual and not report_claims_release:
        return False, "cascade CSV has passing recommendation but training report says manual-review only"

    if csv_has_passing:
        return True, "training report and cascade CSV both indicate a passing release-ready pair"
    if report_claims_manual:
        return True, "training report and cascade CSV both indicate manual-review only"
    return True, "cascade recommendation state documented"


def _cascade_candidate_score(row: pd.Series) -> float:
    return float(
        0.35 * float(row.get("partial_file_recall", 0) or 0)
        + 0.30 * float(row.get("top5_hit_rate_when_positive", 0) or 0)
        - 0.20 * float(row.get("non_partial_false_alarm_rate", 0) or 0)
        - 0.15 * float(row.get("direct_false_partial_rate", 0) or 0)
    )


def _cascade_meets_constraints(row: pd.Series) -> bool:
    passed, _ = evaluate_cascade_acceptance(row, CASCADE_ACCEPTANCE_CONFIG)
    return passed


def _apply_cascade_recommendations(cascade_df: pd.DataFrame) -> pd.DataFrame:
    out = cascade_df.copy()
    out["recommended_threshold_pair"] = ""
    out["recommendation_reason"] = ""
    if out.empty:
        return out

    out["candidate_score"] = out.apply(_cascade_candidate_score, axis=1)
    feasible = out[out.apply(_cascade_meets_constraints, axis=1)].copy()
    if feasible.empty:
        out.loc[out.index[0], "recommendation_reason"] = MANUAL_REVIEW_ONLY_MESSAGE
        return out

    best = feasible.sort_values("candidate_score", ascending=False).iloc[0]
    pair = (
        f"file_gate={best['file_gate_threshold']},segment={best['segment_threshold']},"
        f"contrast={best['contrast_threshold']},broad_limit={best['broad_limit']}"
    )
    reason = (
        "Passes shared cascade acceptance rules (direct/replay/mixer/broad/file_gate); "
        "prefers high partial recall and top-5 hit with low non-partial false alarms"
    )
    best_idx = feasible.sort_values("candidate_score", ascending=False).index[0]
    out.loc[best_idx, "recommended_threshold_pair"] = pair
    out.loc[best_idx, "recommendation_reason"] = reason
    return out


def compute_classification_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_proba: np.ndarray) -> dict[str, Any]:
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    out: dict[str, Any] = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }
    if len(np.unique(y_true)) > 1 and np.isfinite(y_proba).all():
        out["roc_auc"] = float(roc_auc_score(y_true, y_proba))
        out["average_precision"] = float(average_precision_score(y_true, y_proba))
        out["brier_score"] = float(brier_score_loss(y_true, y_proba))
    else:
        out["roc_auc"] = np.nan
        out["average_precision"] = np.nan
        out["brier_score"] = np.nan
    return out


def threshold_grid_rows(
    task_name: str,
    feature_set: str,
    y_true: np.ndarray,
    y_proba: np.ndarray,
    *,
    file_level: bool,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for th in np.arange(0.10, 0.901, 0.05):
        y_pred = (y_proba >= th).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
        pos_total = tp + fn
        neg_total = tn + fp
        fpr = fp / neg_total if neg_total else np.nan
        fnr = fn / pos_total if pos_total else np.nan
        row = {
            "task_name": task_name,
            "feature_set": feature_set,
            "threshold": round(float(th), 2),
            "precision": float(precision_score(y_true, y_pred, zero_division=0)),
            "recall": float(recall_score(y_true, y_pred, zero_division=0)),
            "f1": float(f1_score(y_true, y_pred, zero_division=0)),
            "false_positive_rate": fpr,
            "false_negative_rate": fnr,
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp),
        }
        if file_level:
            row["partial_detected_rate"] = row["recall"]
            row["non_partial_false_alarm_rate"] = fpr
        else:
            row["fabricated_segment_detected_rate"] = row["recall"]
            row["outside_false_fabricated_rate"] = fpr
        rows.append(row)
    return rows


def precision_at_top_k_per_file(oof_df: pd.DataFrame, k: int = 5) -> float:
    hits = []
    for _, g in oof_df.groupby("file_id"):
        g = g.sort_values("y_proba_experimental", ascending=False)
        pos_files = g[g["y_true"].astype(int) == 1]
        if pos_files.empty:
            continue
        top = g.head(k)
        hits.append(float((top["y_true"].astype(int) == 1).sum()) / k)
    return float(np.mean(hits)) if hits else np.nan


def recall_at_max_fpr(y_true: np.ndarray, y_proba: np.ndarray, max_fpr: float = 0.10) -> float:
    best_recall = np.nan
    for th in np.arange(0.01, 1.0, 0.01):
        y_pred = (y_proba >= th).astype(int)
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
        neg_total = tn + fp
        if neg_total == 0:
            continue
        fpr = fp / neg_total
        if fpr <= max_fpr:
            rec = tp / (tp + fn) if (tp + fn) else np.nan
            if np.isnan(best_recall) or rec > best_recall:
                best_recall = rec
    return float(best_recall) if np.isfinite(best_recall) else np.nan


def verify_group_integrity(
    df: pd.DataFrame,
    groups: np.ndarray,
    splitter: Any,
    split_method: str,
    y: np.ndarray,
) -> dict[str, Any]:
    violations = 0
    if split_method in {"StratifiedGroupKFold", "GroupKFold"}:
        split_iter = splitter.split(df, y, groups)
    else:
        split_iter = splitter.split(df, y)
    for _fold, (tr, te) in enumerate(split_iter, start=1):
        train_groups = set(groups[tr].astype(str))
        test_groups = set(groups[te].astype(str))
        overlap = train_groups & test_groups
        violations += len(overlap)
    return {
        "split_method": split_method,
        "group_integrity_violations": violations,
        "group_integrity_status": "passed" if violations == 0 else "failed",
    }


def run_task_cv(
    df: pd.DataFrame,
    *,
    task_name: str,
    target_col: str,
    feature_set: str,
    feature_columns: list[str],
    group_col: str,
    cv_folds: int,
    random_seed: int,
    max_selected_features: int,
    model_type: str,
) -> dict[str, Any]:
    raw_features = select_features_for_set(feature_columns, feature_set, task_name)
    forbidden_hits = [c for c in raw_features if is_forbidden_feature(c, task_name)]
    raw_features = [c for c in raw_features if c not in forbidden_hits]
    if not raw_features:
        raise ValueError(f"No features for task={task_name}, feature_set={feature_set}")

    missing = [c for c in raw_features if c not in df.columns]
    if missing:
        raise ValueError(f"Missing feature columns in dataset: {missing[:10]}")

    x, usable, dropped_missing, dropped_non_numeric = clean_feature_matrix(df, raw_features)
    if not usable:
        raise ValueError(f"No usable features after cleaning for task={task_name}, feature_set={feature_set}")
    post_forbidden = [c for c in usable if is_forbidden_feature(c, task_name)]
    if post_forbidden:
        raise ValueError(f"Forbidden features survived filtering: {post_forbidden[:10]}")

    y = parse_binary_target(df[target_col], target_col)
    groups = df[group_col].astype(str).to_numpy()
    split_choice = choose_group_splitter(y, groups, cv_folds, random_seed, require_groups=True)
    split_choice = SplitChoice(
        splitter=split_choice.splitter,
        split_method=split_choice.split_method,
        used_folds=split_choice.used_folds,
        group_column=group_col,
    )
    integrity = verify_group_integrity(df, groups, split_choice.splitter, split_choice.split_method, y)

    fold_metrics: list[dict[str, Any]] = []
    oof_rows: list[dict[str, Any]] = []

    if split_choice.split_method == "StratifiedGroupKFold":
        split_iter = split_choice.splitter.split(x, y, groups)
    elif split_choice.split_method == "GroupKFold":
        split_iter = split_choice.splitter.split(x, y, groups)
    else:
        split_iter = split_choice.splitter.split(x, y)

    safe_k = min(max_selected_features, len(usable))

    for fold_idx, (train_idx, test_idx) in enumerate(split_iter, start=1):
        model = clone(build_pipeline(safe_k, random_seed))
        model.fit(x.iloc[train_idx], y[train_idx])
        y_pred = model.predict(x.iloc[test_idx]).astype(int)
        y_proba = safe_predict_proba(model, x.iloc[test_idx])

        metrics = compute_classification_metrics(y[test_idx], y_pred, y_proba)
        metrics.update(
            {
                "task_name": task_name,
                "feature_set": feature_set,
                "fold": fold_idx,
                "split_method": split_choice.split_method,
                "group_column": group_col,
                "used_folds": split_choice.used_folds,
                "model_type": model_type,
            }
        )
        fold_metrics.append(metrics)

        for local_i, global_i in enumerate(test_idx):
            row = {
                "task_name": task_name,
                "feature_set": feature_set,
                "file_id": str(df.iloc[global_i].get("file_id", "")),
                "y_true": int(y[test_idx][local_i]),
                "y_pred_experimental": int(y_pred[local_i]),
                "y_proba_experimental": float(y_proba[local_i]),
                "fold": fold_idx,
                "split_method": split_choice.split_method,
                "model_type": model_type,
            }
            if task_name == TASK_FILE_GATE:
                row["file_category"] = str(df.iloc[global_i].get("file_category", ""))
                row["leakage_group_id"] = str(df.iloc[global_i].get("leakage_group_id", ""))
            else:
                row["segment_id"] = str(df.iloc[global_i].get("segment_id", ""))
                row["start_sec"] = str(df.iloc[global_i].get("start_sec", ""))
                row["end_sec"] = str(df.iloc[global_i].get("end_sec", ""))
                row["segment_source_type"] = str(df.iloc[global_i].get("segment_source_type", ""))
                row["file_category"] = str(df.iloc[global_i].get("file_category", ""))
                row["timestamp_region_label"] = str(df.iloc[global_i].get("timestamp_region_label", ""))
            oof_rows.append(row)

    oof_df = pd.DataFrame(oof_rows)
    metrics_df = pd.DataFrame(fold_metrics)
    agg = (
        metrics_df.drop(columns=["fold"])
        .groupby(["task_name", "feature_set", "split_method", "group_column", "used_folds", "model_type"], as_index=False)
        .mean(numeric_only=True)
    )
    agg["metric_scope"] = "cross_validated_experimental_mean"

    y_true_all = oof_df["y_true"].astype(int).to_numpy()
    y_proba_all = pd.to_numeric(oof_df["y_proba_experimental"], errors="coerce").to_numpy(dtype=float)
    y_pred_all = oof_df["y_pred_experimental"].astype(int).to_numpy()
    overall = compute_classification_metrics(y_true_all, y_pred_all, y_proba_all)
    for k, v in overall.items():
        agg[f"oof_{k}"] = v

    if task_name == TASK_SEGMENT_LOCALIZER:
        agg["precision_at_top5_per_file"] = precision_at_top_k_per_file(oof_df, k=5)
        agg["recall_at_fpr_10pct"] = recall_at_max_fpr(y_true_all, y_proba_all, max_fpr=0.10)

    audit = audit_features(
        task_name,
        feature_set,
        raw_features,
        usable,
        dropped_missing,
        dropped_non_numeric,
        forbidden_hits,
    )
    audit["split_method"] = split_choice.split_method
    audit["group_column"] = group_col
    audit["group_integrity_status"] = integrity["group_integrity_status"]
    audit["group_integrity_violations"] = integrity["group_integrity_violations"]

    thresh_rows = threshold_grid_rows(
        task_name,
        feature_set,
        y_true_all,
        y_proba_all,
        file_level=(task_name == TASK_FILE_GATE),
    )

    return {
        "metrics_fold": metrics_df,
        "metrics_mean": agg,
        "oof": oof_df,
        "threshold_grid": pd.DataFrame(thresh_rows),
        "feature_audit": audit,
        "split_method": split_choice.split_method,
        "group_column": group_col,
        "usable_features": usable,
    }


def compute_segment_file_localization(
    oof_df: pd.DataFrame,
    *,
    segment_threshold: float = 0.50,
    broad_activation_fraction: float = 0.40,
    top_k: int = 5,
) -> pd.DataFrame:
    """Per-file localization metrics to assess broad activation vs true-region hits."""
    rows: list[dict[str, Any]] = []
    df = oof_df.copy()
    df["y_true"] = pd.to_numeric(df["y_true"], errors="coerce").astype(int)
    df["y_proba_experimental"] = pd.to_numeric(df["y_proba_experimental"], errors="coerce")

    for (feature_set, file_id), g in df.groupby(["feature_set", "file_id"], dropna=False):
        g = g.sort_values(["y_proba_experimental", "start_sec"], ascending=[False, True]).reset_index(drop=True)
        file_cat = str(g["file_category"].iloc[0]) if "file_category" in g.columns else ""
        is_partial = file_cat in PARTIAL_FILE_CATEGORIES

        inside = g[g["y_true"] == 1]
        outside = g[g["y_true"] == 0]
        high_frac = float((g["y_proba_experimental"] >= segment_threshold).mean()) if len(g) else np.nan

        top = g.head(top_k)
        top1 = g.head(1)
        ranks_inside = g.index[g["y_true"] == 1].tolist()
        best_rank = (min(ranks_inside) + 1) if ranks_inside else np.nan

        row: dict[str, Any] = {
            "task_name": TASK_SEGMENT_LOCALIZER,
            "feature_set": feature_set,
            "file_id": file_id,
            "file_category": file_cat,
            "is_partial_file": str(is_partial).lower(),
            "segment_count": len(g),
            "segment_threshold": segment_threshold,
            "high_segment_fraction_at_threshold": high_frac,
            "top1_inside_true_region": str(bool((top1["y_true"] == 1).any())).lower() if is_partial else "",
            "top3_any_inside_true_region": str(bool(g.head(3)["y_true"].eq(1).any())).lower() if is_partial else "",
            "top5_any_inside_true_region": str(bool((top["y_true"] == 1).any())).lower() if is_partial else "",
            "top5_inside_count": int((top["y_true"] == 1).sum()) if is_partial else "",
            "best_rank_inside_region": best_rank if is_partial else "",
            "max_prob_inside": float(inside["y_proba_experimental"].max()) if not inside.empty else np.nan,
            "mean_prob_inside": float(inside["y_proba_experimental"].mean()) if not inside.empty else np.nan,
            "max_prob_outside": float(outside["y_proba_experimental"].max()) if not outside.empty else np.nan,
            "mean_prob_outside": float(outside["y_proba_experimental"].mean()) if not outside.empty else np.nan,
        }
        if not inside.empty and not outside.empty:
            row["inside_minus_outside_mean"] = row["mean_prob_inside"] - row["mean_prob_outside"]
        else:
            row["inside_minus_outside_mean"] = np.nan

        if is_partial:
            row["broad_activation_flag"] = str(high_frac >= broad_activation_fraction).lower()
            row["localized_pattern_supported"] = str(
                bool(row["top5_any_inside_true_region"] == "true" and high_frac < broad_activation_fraction)
            ).lower()
            row["false_high_segment_count"] = ""
            row["false_high_segment_rate"] = ""
            row["broad_false_activation_flag"] = ""
        else:
            high_count = int((g["y_proba_experimental"] >= segment_threshold).sum())
            row["false_high_segment_count"] = high_count
            row["false_high_segment_rate"] = high_count / len(g) if len(g) else np.nan
            row["broad_false_activation_flag"] = str(high_frac >= broad_activation_fraction).lower()
            row["broad_activation_flag"] = row["broad_false_activation_flag"]
            row["localized_pattern_supported"] = ""

        rows.append(row)
    return pd.DataFrame(rows)


def run_cascade_simulation(
    file_oof: pd.DataFrame,
    segment_oof: pd.DataFrame,
    *,
    file_gate_feature_set: str,
    segment_feature_set: str,
) -> pd.DataFrame:
    """Two-stage cascade: file gate + segment localized evidence (segment threshold matters)."""
    fg = file_oof[file_oof["feature_set"] == file_gate_feature_set].copy()
    sg = segment_oof[segment_oof["feature_set"] == segment_feature_set].copy()
    if fg.empty or sg.empty:
        raise ValueError("Cascade simulation requires non-empty OOF for selected feature sets.")

    fg["y_proba_experimental"] = pd.to_numeric(fg["y_proba_experimental"], errors="coerce")
    fg["y_true"] = pd.to_numeric(fg["y_true"], errors="coerce").astype(int)
    sg["y_proba_experimental"] = pd.to_numeric(sg["y_proba_experimental"], errors="coerce")
    sg["y_true"] = pd.to_numeric(sg["y_true"], errors="coerce").astype(int)

    sg_by_file: dict[str, pd.DataFrame] = {str(k): v for k, v in sg.groupby("file_id", sort=False)}

    rows: list[dict[str, Any]] = []
    for gt in CASCADE_GATE_THRESHOLDS:
        for st in CASCADE_SEGMENT_THRESHOLDS:
            for ct in CASCADE_CONTRAST_THRESHOLDS:
                for bl in CASCADE_BROAD_LIMITS:
                    partial_total = 0
                    partial_cascade_pos = 0
                    non_partial_total = 0
                    non_partial_fa = 0
                    direct_total = 0
                    direct_fa = 0
                    replay_total = 0
                    replay_fa = 0
                    mixer_total = 0
                    mixer_fa = 0
                    top1_hits: list[bool] = []
                    top3_hits: list[bool] = []
                    top5_hits: list[bool] = []
                    broad_flags: list[bool] = []

                    for _, frow in fg.iterrows():
                        fid = str(frow["file_id"])
                        file_cat = str(frow.get("file_category", ""))
                        gate_pass = bool(frow["y_proba_experimental"] >= gt)
                        seg_g = sg_by_file.get(fid, pd.DataFrame())
                        seg_ev = _segment_localized_evidence(
                            seg_g,
                            segment_threshold=st,
                            broad_limit=bl,
                            contrast_threshold=ct,
                        )
                        cascade_pos = gate_pass and seg_ev["localized_evidence"]

                        is_partial = bool(frow["y_true"] == 1 or file_cat in PARTIAL_FILE_CATEGORIES)
                        is_direct = file_cat in DIRECT_CATEGORIES
                        is_replay = file_cat in REPLAY_CATEGORIES
                        is_mixer = file_cat in MIXER_CATEGORIES

                        if is_partial:
                            partial_total += 1
                            if cascade_pos:
                                partial_cascade_pos += 1
                                top1_hits.append(bool(seg_ev["top1_hit"]))
                                top3_hits.append(bool(seg_ev["top3_hit"]))
                                top5_hits.append(bool(seg_ev["top5_hit"]))
                                broad_flags.append(bool(seg_ev["broad_activation"]))
                        else:
                            non_partial_total += 1
                            if cascade_pos:
                                non_partial_fa += 1
                        if is_direct:
                            direct_total += 1
                            if cascade_pos:
                                direct_fa += 1
                        if is_replay:
                            replay_total += 1
                            if cascade_pos:
                                replay_fa += 1
                        if is_mixer:
                            mixer_total += 1
                            if cascade_pos:
                                mixer_fa += 1

                    rows.append(
                        {
                            "file_gate_feature_set": file_gate_feature_set,
                            "segment_feature_set": segment_feature_set,
                            "file_gate_threshold": gt,
                            "segment_threshold": st,
                            "contrast_threshold": ct,
                            "broad_limit": bl,
                            "partial_file_recall": partial_cascade_pos / partial_total if partial_total else np.nan,
                            "non_partial_false_alarm_rate": non_partial_fa / non_partial_total if non_partial_total else np.nan,
                            "direct_false_partial_rate": direct_fa / direct_total if direct_total else np.nan,
                            "replay_false_partial_rate": replay_fa / replay_total if replay_total else np.nan,
                            "mixer_false_partial_rate": mixer_fa / mixer_total if mixer_total else np.nan,
                            "top1_hit_rate_when_positive": float(np.mean(top1_hits)) if top1_hits else np.nan,
                            "top3_hit_rate_when_positive": float(np.mean(top3_hits)) if top3_hits else np.nan,
                            "top5_hit_rate_when_positive": float(np.mean(top5_hits)) if top5_hits else np.nan,
                            "broad_activation_rate_when_positive": float(np.mean(broad_flags)) if broad_flags else np.nan,
                            "gated_partial_file_count": partial_cascade_pos,
                        }
                    )

    out = pd.DataFrame(rows)
    return _apply_cascade_recommendations(out)


def recompute_p5b_derived_outputs(
    *,
    file_oof_df: pd.DataFrame,
    segment_oof_df: pd.DataFrame,
    file_results_summary: dict[str, pd.DataFrame],
    segment_results_summary: dict[str, pd.DataFrame],
    out_dir: Path,
    args: Any,
    cascade_file_gate_feature_set: str | None = None,
    cascade_segment_feature_set: str | None = None,
    selected_segment_feature_set: str = "combined",
    selected_segment_threshold: float = 0.50,
    training_performed: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Recompute cascade, localization summary, and report without retraining."""
    cascade_fg = cascade_file_gate_feature_set or ("combined" if "combined" in file_results_summary else next(iter(file_results_summary)))
    cascade_sg = cascade_segment_feature_set or (
        "combined" if "combined" in segment_results_summary else next(iter(segment_results_summary))
    )

    cascade_df = run_cascade_simulation(
        file_oof_df,
        segment_oof_df,
        file_gate_feature_set=cascade_fg,
        segment_feature_set=cascade_sg,
    )

    file_loc_df = compute_segment_file_localization(
        segment_oof_df[segment_oof_df["feature_set"] == selected_segment_feature_set],
        segment_threshold=selected_segment_threshold,
    )
    broad_summary = compute_broad_activation_summary(
        segment_oof_df,
        feature_set=selected_segment_feature_set,
        segment_threshold=selected_segment_threshold,
    )

    cascade_df.to_csv(out_dir / "phase9d_p5b_cascade_simulation_results.csv", index=False)
    file_loc_df.to_csv(out_dir / "phase9d_p5b_segment_file_localization_metrics.csv", index=False)

    write_training_report(
        out_dir / "phase9d_p5b_training_report.md",
        file_results=file_results_summary,
        segment_results=segment_results_summary,
        cascade_df=cascade_df,
        broad_summary=broad_summary,
        args=args,
        training_performed=training_performed,
    )

    return cascade_df, file_loc_df, broad_summary


def write_training_report(
    path: Path,
    *,
    file_results: dict[str, Any],
    segment_results: dict[str, Any],
    cascade_df: pd.DataFrame,
    broad_summary: dict[str, Any],
    args: Any,
    training_performed: bool = True,
) -> None:
    now = now_utc_str()
    train_line = "YES (manual run — experimental P5B only)" if training_performed else "NO — reused existing OOF predictions (P5B-P1 recompute only)"
    n_partial = broad_summary.get("partial_file_count", 0)
    cascade_diagnostics = compute_cascade_acceptance_diagnostics(cascade_df)
    body = f"""# Phase 9D-P5B Training Report (Experimental)

Generated: {now}

**Training performed:** {train_line}

**Release packaging performed:** NO — nothing written to `release/models/` or `models_saved/active/`.

**Production claim:** NO — these are experimental redesign candidates only.

## Purpose of P5B

Train and evaluate redesigned partial-fabrication models to address Phase 9D-P4 broad activation:
- Stage 1 file gate: `partial_file_candidate_model`
- Stage 2 segment localizer v2: `partial_segment_localizer_v2`
- Cascade simulation to estimate two-stage live behavior

## Why the old partial model failed (P4 reference)

- Top-5 timestamp hit: 36/46 fabricated files
- Localized success: 0/46
- Broad activation: 46/46 fabricated files

## File gate results (OOF mean)

{_format_metrics_table(file_results)}

## Segment localizer v2 results (OOF mean)

{_format_metrics_table(segment_results)}

## Cascade simulation (selected feature sets)

{_format_cascade_summary(cascade_df)}

{format_cascade_acceptance_diagnostics(cascade_diagnostics)}

## Broad activation comparison (selected segment model only)

Selected configuration: feature_set=`{broad_summary.get('selected_feature_set', 'combined')}`, segment_threshold=`{broad_summary.get('selected_segment_threshold', 0.50)}`

| Metric | Value |
|--------|------:|
| Partial file count (unique) | {n_partial} |
| Broad activation count | {broad_summary.get('broad_activation_count_selected', 0)} |
| Localized pattern supported | {broad_summary.get('localized_pattern_supported_count_selected', 0)} |
| Top-1 hit count | {broad_summary.get('top1_hit_count_selected', 0)} |
| Top-3 hit count | {broad_summary.get('top3_hit_count_selected', 0)} |
| Top-5 hit count | {broad_summary.get('top5_hit_count_selected', 0)} |

- P4 broad activation reference: {broad_summary.get('p4_broad_activation_reference', '46/46')}
- P5B broad activation (selected): {broad_summary.get('p5b_broad_activation_selected', 'n/a')}

## False positives on replay / mixer / direct (cascade)

See cascade simulation columns `replay_false_partial_rate`, `mixer_false_partial_rate`, `direct_false_partial_rate`.

## Recommended next action

{_recommendation(cascade_df)}

## Limitations

- Logistic regression on hand-crafted features only; no end-to-end audio modeling.
- Cross-validated OOF estimates; no held-out deployment set in this phase.
- Cascade simulation uses OOF probabilities (optimistic bias vs nested deployment).
- Timestamp labels used for segment targets/evaluation only — never as model features.

## Configuration

- CV folds: {getattr(args, 'cv_folds', 'n/a')}
- File feature sets: {getattr(args, 'file_feature_sets', 'n/a')}
- Segment feature sets: {getattr(args, 'segment_feature_sets', 'n/a')}
- Model type: {getattr(args, 'model_type', 'n/a')}
- Random seed: {getattr(args, 'random_seed', 'n/a')}
"""
    path.write_text(body, encoding="utf-8")


def _format_metrics_table(results: dict[str, list[pd.DataFrame]]) -> str:
    lines = ["| feature_set | balanced_accuracy | average_precision | roc_auc | f1 |", "|---|---:|---:|---:|---:|"]
    for fs, agg in results.items():
        if agg.empty:
            continue
        row = agg.iloc[0]
        lines.append(
            f"| {fs} | {row.get('balanced_accuracy', np.nan):.4f} | "
            f"{row.get('average_precision', np.nan):.4f} | {row.get('roc_auc', np.nan):.4f} | "
            f"{row.get('f1', np.nan):.4f} |"
        )
    return "\n".join(lines) if len(lines) > 2 else "No metrics available."


def _format_cascade_summary(cascade_df: pd.DataFrame) -> str:
    if cascade_df.empty:
        return "No cascade results."
    recommended = get_recommended_cascade_rows(cascade_df)
    if recommended.empty:
        manual_msg = MANUAL_REVIEW_ONLY_MESSAGE
        if "recommendation_reason" in cascade_df.columns:
            reasons = cascade_df["recommendation_reason"].astype(str)
            manual_rows = reasons.str.contains("No release-ready", na=False)
            if manual_rows.any():
                manual_msg = str(cascade_df.loc[manual_rows.idxmax(), "recommendation_reason"])
        return manual_msg

    best = recommended.iloc[0]
    passed, failures = evaluate_cascade_acceptance(best)
    if not passed:
        fail_text = "; ".join(failures) if failures else "acceptance rules not met"
        return f"{MANUAL_REVIEW_ONLY_MESSAGE} (CSV recommendation failed: {fail_text})"

    return (
        f"Release-ready pair: {best.get('recommended_threshold_pair', 'n/a')} — "
        f"partial recall={_row_metric(best, 'partial_file_recall'):.3f}, "
        f"non-partial FA={_row_metric(best, 'non_partial_false_alarm_rate'):.3f}, "
        f"top5 hit (cascade+)={_row_metric(best, 'top5_hit_rate_when_positive'):.3f}, "
        f"broad activation (cascade+)={_row_metric(best, 'broad_activation_rate_when_positive'):.3f}, "
        f"direct FP={_row_metric(best, 'direct_false_partial_rate'):.3f}"
    )


def _recommendation(cascade_df: pd.DataFrame) -> str:
    if cascade_df.empty:
        return MANUAL_REVIEW_NEXT_STEP
    recommended = get_recommended_cascade_rows(cascade_df)
    if recommended.empty:
        return MANUAL_REVIEW_NEXT_STEP
    best = recommended.iloc[0]
    passed, _ = evaluate_cascade_acceptance(best)
    if not passed:
        return MANUAL_REVIEW_NEXT_STEP
    return (
        "Experimental cascade thresholds pass shared acceptance rules. "
        "Outputs remain manual-review support only — do not package into release yet without P5C evaluation."
    )


def maybe_save_plots(
    output_dir: Path,
    file_oof: pd.DataFrame,
    segment_oof: pd.DataFrame,
) -> None:
    try:
        import matplotlib.pyplot as plt
        from sklearn.metrics import PrecisionRecallDisplay, RocCurveDisplay
    except ImportError:
        return

    fig_dir = output_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    for task_name, oof, prefix in (
        (TASK_FILE_GATE, file_oof, "file_gate"),
        (TASK_SEGMENT_LOCALIZER, segment_oof, "segment"),
    ):
        for fs in sorted(oof["feature_set"].unique()):
            g = oof[oof["feature_set"] == fs]
            y_true = g["y_true"].astype(int).to_numpy()
            y_proba = pd.to_numeric(g["y_proba_experimental"], errors="coerce").to_numpy(dtype=float)
            if len(np.unique(y_true)) < 2:
                continue
            fig, ax = plt.subplots(figsize=(5, 4))
            RocCurveDisplay.from_predictions(y_true, y_proba, ax=ax, name=fs)
            ax.set_title(f"{prefix} ROC — {fs}")
            fig.tight_layout()
            fig.savefig(fig_dir / f"phase9d_p5b_{prefix}_roc_{fs}.png", dpi=120)
            plt.close(fig)

            fig, ax = plt.subplots(figsize=(5, 4))
            PrecisionRecallDisplay.from_predictions(y_true, y_proba, ax=ax, name=fs)
            ax.set_title(f"{prefix} PR — {fs}")
            fig.tight_layout()
            fig.savefig(fig_dir / f"phase9d_p5b_{prefix}_pr_{fs}.png", dpi=120)
            plt.close(fig)


def maybe_save_artifacts(
    artifacts_dir: Path,
    df: pd.DataFrame,
    *,
    task_name: str,
    feature_set: str,
    target_col: str,
    feature_columns: list[str],
    group_col: str,
    random_seed: int,
    max_selected_features: int,
) -> None:
    import joblib

    artifacts_dir.mkdir(parents=True, exist_ok=True)
    raw_features = select_features_for_set(feature_columns, feature_set, task_name)
    raw_features = [c for c in raw_features if not is_forbidden_feature(c, task_name)]
    x, usable, _, _ = clean_feature_matrix(df, raw_features)
    y = parse_binary_target(df[target_col], target_col)
    model = build_pipeline(min(max_selected_features, len(usable)), random_seed)
    model.fit(x, y)
    out = artifacts_dir / f"phase9d_p5b_{task_name}_{feature_set}_full_fit.joblib"
    joblib.dump({"model": model, "features": usable, "task_name": task_name}, out)


# --- Phase 9D-P5C controlled evaluation (experimental) ---

P5C_ACCEPTED_CASCADE_THRESHOLDS: dict[str, float] = {
    "file_gate_threshold": 0.50,
    "segment_threshold": 0.90,
    "contrast_threshold": 0.25,
    "broad_limit": 0.45,
}

P5C_FILE_GATE_FEATURE_SET = "ssl"
P5C_SEGMENT_FEATURE_SET = "combined"

P5C_CANDIDATE_MODEL_NAMES = {
    "file_gate": "partial_file_gate__ssl__p5b_experimental_candidate.joblib",
    "segment_localizer": "partial_segment_localizer_v2__combined__p5b_experimental_candidate.joblib",
    "cascade_config": "partial_cascade_config__p5b_experimental_candidate.json",
}

P5C_RELEASE_READINESS_CONFIG: dict[str, float | int | None] = {
    "max_direct_false_partial_rate": 0.20,
    "max_replay_false_partial_rate": 0.05,
    "max_mixer_false_partial_rate": 0.05,
    "max_broad_activation_rate_when_positive": 0.10,
    "min_partial_evidence_recall": 0.65,
    "min_top5_hit_rate_when_positive": 0.80,
    "min_independent_holdout_count": 1,
}

P5C_SKIP_SCAN_DIR_NAMES = frozenset(
    {
        "noise_rir",
        "augmented",
        "__pycache__",
        ".git",
    }
)


def p5c_candidate_models_dir(p5b_dir: Path) -> Path:
    return p5b_dir / "candidate_models"


def fit_p5b_experimental_candidate_models(
    *,
    file_gate_df: pd.DataFrame,
    segment_df: pd.DataFrame,
    file_feature_columns: list[str],
    segment_feature_columns: list[str],
    out_dir: Path,
    random_seed: int = 42,
    max_selected_features_file: int = 75,
    max_selected_features_segment: int = 100,
    force: bool = False,
) -> dict[str, Path]:
    """Fit final experimental candidate models; save only under phase9d_p5b/candidate_models/."""
    import joblib

    cand_dir = p5c_candidate_models_dir(out_dir)
    cand_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "file_gate": cand_dir / P5C_CANDIDATE_MODEL_NAMES["file_gate"],
        "segment_localizer": cand_dir / P5C_CANDIDATE_MODEL_NAMES["segment_localizer"],
        "cascade_config": cand_dir / P5C_CANDIDATE_MODEL_NAMES["cascade_config"],
    }
    if (
        paths["file_gate"].is_file()
        and paths["segment_localizer"].is_file()
        and paths["cascade_config"].is_file()
        and not force
    ):
        return paths

    fg_features = select_features_for_set(file_feature_columns, P5C_FILE_GATE_FEATURE_SET, TASK_FILE_GATE)
    fg_features = [c for c in fg_features if not is_forbidden_feature(c, TASK_FILE_GATE)]
    x_fg, fg_usable, _, _ = clean_feature_matrix(file_gate_df, fg_features)
    y_fg = parse_binary_target(file_gate_df["target_is_partial_fabrication_file"], "target_is_partial_fabrication_file")
    fg_model = build_pipeline(min(max_selected_features_file, len(fg_usable)), random_seed)
    fg_model.fit(x_fg, y_fg)
    joblib.dump(
        {
            "model": fg_model,
            "features": fg_usable,
            "task_name": TASK_FILE_GATE,
            "feature_set": P5C_FILE_GATE_FEATURE_SET,
            "experimental": True,
        },
        paths["file_gate"],
    )

    sg_features = select_features_for_set(
        segment_feature_columns, P5C_SEGMENT_FEATURE_SET, TASK_SEGMENT_LOCALIZER
    )
    sg_features = [c for c in sg_features if not is_forbidden_feature(c, TASK_SEGMENT_LOCALIZER)]
    x_sg, sg_usable, _, _ = clean_feature_matrix(segment_df, sg_features)
    y_sg = parse_binary_target(segment_df["target_is_fabricated_segment"], "target_is_fabricated_segment")
    sg_model = build_pipeline(min(max_selected_features_segment, len(sg_usable)), random_seed)
    sg_model.fit(x_sg, y_sg)
    joblib.dump(
        {
            "model": sg_model,
            "features": sg_usable,
            "task_name": TASK_SEGMENT_LOCALIZER,
            "feature_set": P5C_SEGMENT_FEATURE_SET,
            "experimental": True,
        },
        paths["segment_localizer"],
    )

    paths["cascade_config"].write_text(
        json.dumps(
            {
                "schema": "phase9d_p5c_cascade_config_v1",
                "experimental_only": True,
                "file_gate_feature_set": P5C_FILE_GATE_FEATURE_SET,
                "segment_feature_set": P5C_SEGMENT_FEATURE_SET,
                "thresholds": P5C_ACCEPTED_CASCADE_THRESHOLDS,
                "model_artifacts": {k: v.name for k, v in paths.items() if k != "cascade_config"},
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return paths


def load_p5b_candidate_artifacts(p5b_dir: Path) -> dict[str, Any]:
    import joblib

    cand_dir = p5c_candidate_models_dir(p5b_dir)
    fg_path = cand_dir / P5C_CANDIDATE_MODEL_NAMES["file_gate"]
    sg_path = cand_dir / P5C_CANDIDATE_MODEL_NAMES["segment_localizer"]
    cfg_path = cand_dir / P5C_CANDIDATE_MODEL_NAMES["cascade_config"]
    if not fg_path.is_file() or not sg_path.is_file():
        raise FileNotFoundError(
            f"P5B experimental candidate models missing under {cand_dir}. "
            "Run train_phase9d_p5_partial_models.py --fit_final_candidate_models first."
        )
    cascade_cfg = json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.is_file() else {}
    thresholds = cascade_cfg.get("thresholds", P5C_ACCEPTED_CASCADE_THRESHOLDS)
    return {
        "file_gate_bundle": joblib.load(fg_path),
        "segment_bundle": joblib.load(sg_path),
        "cascade_config": cascade_cfg,
        "thresholds": thresholds,
        "paths": {"file_gate": fg_path, "segment_localizer": sg_path, "cascade_config": cfg_path},
    }


def predict_candidate_proba(bundle: dict[str, Any], feature_df: pd.DataFrame) -> np.ndarray:
    """Predict positive-class probability using a saved candidate bundle."""
    model = bundle["model"]
    features: list[str] = list(bundle["features"])
    x, usable, _, _ = clean_feature_matrix(feature_df, features)
    for c in features:
        if c not in x.columns:
            x[c] = np.nan
    x = x.reindex(columns=features)
    if not usable:
        return np.zeros(len(x), dtype=float)
    return model.predict_proba(x)[:, 1]


def apply_p5c_cascade_rule(
    *,
    file_gate_probability: float,
    segment_probs: np.ndarray,
    thresholds: dict[str, float] | None = None,
    top_k: int = 5,
) -> dict[str, Any]:
    """Apply accepted P5B cascade rule for one file."""
    th = thresholds or P5C_ACCEPTED_CASCADE_THRESHOLDS
    gt = float(th["file_gate_threshold"])
    st = float(th["segment_threshold"])
    ct = float(th["contrast_threshold"])
    bl = float(th["broad_limit"])

    probs = np.asarray(segment_probs, dtype=float)
    probs = np.nan_to_num(probs, nan=0.0)
    gate_pass = bool(file_gate_probability >= gt)
    if len(probs) == 0:
        return {
            "file_gate_positive": gate_pass,
            "max_segment_probability": np.nan,
            "segment_threshold_positive": False,
            "high_segment_fraction": np.nan,
            "topk_minus_rest_probability": np.nan,
            "contrast_positive": False,
            "partial_evidence_positive": False,
            "broad_activation_flag": False,
        }

    high_frac = float((probs >= st).mean())
    has_high = bool((probs >= st).any())
    topk_probs = np.sort(probs)[::-1][:top_k]
    rest_probs = np.sort(probs)[::-1][top_k:]
    topk_minus_rest = float(topk_probs.mean() - rest_probs.mean()) if len(rest_probs) else float(topk_probs.mean())
    contrast_pos = topk_minus_rest >= ct
    localized = bool(has_high and high_frac <= bl and contrast_pos)
    cascade_pos = gate_pass and localized
    broad_activation_fraction = 0.40
    broad = high_frac >= broad_activation_fraction

    return {
        "file_gate_positive": gate_pass,
        "max_segment_probability": float(probs.max()),
        "segment_threshold_positive": has_high,
        "high_segment_fraction": high_frac,
        "topk_minus_rest_probability": topk_minus_rest,
        "contrast_positive": contrast_pos,
        "partial_evidence_positive": cascade_pos,
        "broad_activation_flag": broad,
    }


def assess_p5c_release_readiness(metrics: dict[str, Any]) -> tuple[bool, list[str]]:
    """Return (ready_for_packaging_evaluation, reasons)."""
    cfg = P5C_RELEASE_READINESS_CONFIG
    failures: list[str] = []
    min_holdout = int(cfg.get("min_independent_holdout_count") or 0)
    if int(metrics.get("independent_holdout_count", 0)) < min_holdout:
        failures.append(
            f"independent_holdout_count {metrics.get('independent_holdout_count', 0)} < {min_holdout}"
        )

    for key, col in (
        ("max_direct_false_partial_rate", "direct_false_partial_rate"),
        ("max_replay_false_partial_rate", "replay_false_partial_rate"),
        ("max_mixer_false_partial_rate", "mixer_false_partial_rate"),
        ("max_broad_activation_rate_when_positive", "broad_activation_rate_when_positive"),
    ):
        limit = cfg.get(key)
        if limit is None:
            continue
        val = metrics.get(col, np.nan)
        if np.isfinite(val) and float(val) > float(limit):
            failures.append(f"{col} {float(val):.4f} > {float(limit):.4f}")

    min_recall = cfg.get("min_partial_evidence_recall")
    if min_recall is not None and int(metrics.get("partial_file_count", 0)) > 0:
        val = metrics.get("partial_evidence_recall", np.nan)
        if not np.isfinite(val) or float(val) < float(min_recall):
            failures.append(f"partial_evidence_recall {val} < {float(min_recall):.4f}")

    min_top5 = cfg.get("min_top5_hit_rate_when_positive")
    if min_top5 is not None and int(metrics.get("timestamp_positive_count", 0)) > 0:
        val = metrics.get("top5_hit_rate_when_positive", np.nan)
        if not np.isfinite(val) or float(val) < float(min_top5):
            failures.append(f"top5_hit_rate_when_positive {val} < {float(min_top5):.4f}")

    invalid_rate = metrics.get("invalid_file_handling_pass_rate", np.nan)
    if np.isfinite(invalid_rate) and float(invalid_rate) < 1.0:
        failures.append(f"invalid_file_handling_pass_rate {float(invalid_rate):.4f} < 1.0")

    return len(failures) == 0, failures


P5D_ALLOWED_TEST_GROUPS = frozenset({"t1", "t2", "t3", "t4", "t5", "fabricated"})

P5D_TIMESTAMP_OVERLAP_THRESHOLD = 0.10

P5D_RELEASE_READINESS_CONFIG: dict[str, float | int | None] = {
    **dict(P5C_RELEASE_READINESS_CONFIG),
    "max_non_partial_false_alarm_rate": 0.20,
    "min_partial_file_count_for_packaging": 5,
}

P5D_RUN_STATUS_FILENAME = "phase9d_p5d_run_status.json"


def evaluate_p5d_release_gates(
    metrics: dict[str, Any],
    *,
    labels_complete: bool,
    has_partial_positives: bool,
    has_timestamp_positives: bool,
) -> dict[str, Any]:
    """Structured release-packaging gate evaluation for P5D independent holdout."""
    cfg = P5D_RELEASE_READINESS_CONFIG
    failures: list[str] = []

    holdout = int(metrics.get("independent_holdout_count", 0))
    evaluated = int(metrics.get("evaluated_files", 0))
    failed_files = int(metrics.get("failed_files", 0))
    partial_count = int(metrics.get("partial_file_count", 0))
    non_partial_count = int(metrics.get("non_partial_file_count", 0))
    ts_pos = int(metrics.get("timestamp_positive_count", 0))

    if holdout <= 0:
        failures.append("independent_holdout_count <= 0")
    if evaluated <= 0:
        failures.append("evaluated_files <= 0")
    if failed_files > 0:
        failures.append(f"failed_files={failed_files} > 0 (robustness limitation; packaging blocked)")

    min_partial = int(cfg.get("min_partial_file_count_for_packaging") or 5)
    if partial_count < min_partial:
        failures.append(f"partial_file_count={partial_count} < {min_partial}")

    if not labels_complete:
        failures.append("labels/conditions incomplete for direct/replay/mixer assessment")
    else:
        for col in ("direct_false_partial_rate", "replay_false_partial_rate", "mixer_false_partial_rate"):
            if not np.isfinite(metrics.get(col, np.nan)):
                failures.append(f"{col} unavailable (condition strata not assessable)")

    if not has_partial_positives:
        failures.append("no labelled partial-positive files for recall assessment")
    else:
        min_recall = cfg.get("min_partial_evidence_recall")
        if min_recall is not None:
            val = metrics.get("partial_evidence_recall", np.nan)
            if not np.isfinite(val) or float(val) < float(min_recall):
                failures.append(f"partial_evidence_recall {val} < {float(min_recall):.4f}")

    if non_partial_count > 0:
        max_fa = cfg.get("max_non_partial_false_alarm_rate")
        val = metrics.get("non_partial_false_alarm_rate", np.nan)
        if max_fa is not None and np.isfinite(val) and float(val) > float(max_fa):
            failures.append(f"non_partial_false_alarm_rate {float(val):.4f} > {float(max_fa):.4f}")

    for key, col in (
        ("max_direct_false_partial_rate", "direct_false_partial_rate"),
        ("max_replay_false_partial_rate", "replay_false_partial_rate"),
        ("max_mixer_false_partial_rate", "mixer_false_partial_rate"),
        ("max_broad_activation_rate_when_positive", "broad_activation_rate_when_positive"),
    ):
        limit = cfg.get(key)
        if limit is None:
            continue
        val = metrics.get(col, np.nan)
        if labels_complete and not np.isfinite(val):
            continue
        if np.isfinite(val) and float(val) > float(limit):
            failures.append(f"{col} {float(val):.4f} > {float(limit):.4f}")

    if ts_pos <= 0:
        failures.append(
            "timestamp_positive_count == 0 (localization packaging evidence unavailable)"
        )
    elif has_timestamp_positives:
        min_top5 = cfg.get("min_top5_hit_rate_when_positive")
        if min_top5 is not None:
            val = metrics.get("top5_hit_rate_when_positive", np.nan)
            if not np.isfinite(val) or float(val) < float(min_top5):
                failures.append(f"top5_hit_rate_when_positive {val} < {float(min_top5):.4f}")

    invalid_rate = metrics.get("invalid_file_handling_pass_rate", np.nan)
    if np.isfinite(invalid_rate) and float(invalid_rate) < 1.0:
        failures.append(f"invalid_file_handling_pass_rate {float(invalid_rate):.4f} < 1.0")

    ready = len(failures) == 0
    return {
        "release_packaging_ready": ready,
        "failure_reasons": failures,
        "independent_holdout_count": holdout,
        "evaluated_files": evaluated,
        "failed_files": failed_files,
        "partial_file_count": partial_count,
        "labels_complete": labels_complete,
        "timestamp_positive_count": ts_pos,
    }


def assess_p5d_release_readiness(
    metrics: dict[str, Any],
    *,
    labels_complete: bool,
    has_partial_positives: bool,
    has_timestamp_positives: bool,
) -> tuple[str, bool, list[str]]:
    """
    Return (assessment_message, ready_for_packaging_evaluation, failure_reasons).

    Forensic-safe wording only — not a production or court claim.
    """
    gates = evaluate_p5d_release_gates(
        metrics,
        labels_complete=labels_complete,
        has_partial_positives=has_partial_positives,
        has_timestamp_positives=has_timestamp_positives,
    )
    failures = list(gates["failure_reasons"])
    ready = bool(gates["release_packaging_ready"])

    if int(gates.get("independent_holdout_count", 0)) == 0:
        return (
            "P5D completed, but release packaging evaluation is blocked because "
            "no independent holdout files were available.",
            False,
            failures or ["independent_holdout_count == 0"],
        )

    if ready:
        return (
            "Candidate acceptable for release packaging evaluation (experimental partial-fabrication "
            "candidate only; manual review recommended; not production-ready).",
            True,
            [],
        )

    if not labels_complete:
        return (
            "Independent evaluation completed, but release packaging decision is limited "
            "because labels/conditions are incomplete.",
            False,
            failures,
        )

    if not has_partial_positives or int(gates.get("partial_file_count", 0)) < int(
        P5D_RELEASE_READINESS_CONFIG.get("min_partial_file_count_for_packaging") or 5
    ):
        return (
            "Independent evaluation completed, but partial recall coverage is too limited "
            "for release packaging recommendation (insufficient labelled partial-positive files).",
            False,
            failures,
        )

    if int(gates.get("timestamp_positive_count", 0)) == 0:
        return (
            "Independent evaluation completed, but release packaging evaluation is blocked because "
            "timestamp localization quality cannot be assessed on this holdout.",
            False,
            failures,
        )

    if int(gates.get("failed_files", 0)) > 0:
        return (
            "Independent evaluation completed, but release packaging evaluation is blocked because "
            "some holdout files failed during inference (see error cases).",
            False,
            failures,
        )

    return (
        "Independent holdout evaluation completed; release packaging evaluation is blocked "
        "pending threshold and coverage review (see metrics).",
        False,
        failures,
    )
