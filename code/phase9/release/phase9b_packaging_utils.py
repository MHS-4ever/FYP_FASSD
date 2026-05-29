"""Phase 9B release model packaging utilities (experimental forensic prototype only)."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_selection import SelectKBest, VarianceThreshold, f_classif
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

RELEASE_STATUS = "experimental_forensic_prototype"
ARTIFACT_SCHEMA_VERSION = "phase9b_release_v1"
INVENTORY_SCHEMA_VERSION = "phase9b_inventory_v1"
SCRIPT_NAME = "package_phase9b_release_models.py"

FORBIDDEN_SCORE_FIELDS = {"fake_score", "real_score"}

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

IDENTITY_EXCLUDE_PREFIXES = ("target_", "eligible_")

FORBIDDEN_PARTIAL_FEATURE_EXACT = {
    "timestamp_segment_label",
    "training_label_available",
    "max_fabricated_overlap_sec",
    "max_fabricated_overlap_ratio",
    "total_fabricated_overlap_sec",
    "overlaps_true_fabricated_region",
    "candidate_type",
    "candidate_reason",
    "allowed_use",
    "segment_label_source",
    "has_true_timestamp_labels",
}

FORBIDDEN_PARTIAL_FEATURE_SUBSTRINGS = (
    "fabricated_baseline",
    "outside_baseline",
    "inside_outside_margin",
    "inside_outside_separation",
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

ACOUSTIC_EXACT = {
    "peak_amplitude",
    "mean_amplitude",
    "std_amplitude",
    "dc_offset",
    "clipping_ratio",
    "silence_ratio",
    "active_audio_ratio",
    "noise_floor_proxy",
    "snr_proxy",
    "dynamic_range_proxy",
    "bandwidth_occupied_95",
    "high_freq_rolloff_ratio",
    "low_band_energy_ratio",
    "mid_band_energy_ratio",
    "high_band_energy_ratio",
    "very_high_band_energy_ratio",
}


@dataclass(frozen=True)
class ReleaseModelSpec:
    model_name: str
    task_name: str
    evidence_axis: str
    feature_set: str
    target_column: str
    positive_label: str
    negative_label: str
    phase_trained: str
    artifact_rel: str
    metadata_rel: str
    threshold_candidate: float
    threshold_source: str
    metrics_reference: str
    max_selected_features: int
    allowed_use: str
    forbidden_use: str
    limitations: list[str]
    output_meaning: str
    replay_mixer_note: str | None = None


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def repo_root_from_here(here: Path) -> Path:
    return here.resolve().parents[3]


def resolve_path(root: Path, path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else (root / p).resolve()


def load_csv_required(path: Path) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(f"Required CSV missing: {path}")
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def is_acoustic_column(col: str) -> bool:
    return (
        col in ACOUSTIC_EXACT
        or col.startswith("rms_")
        or col.startswith("spectral_")
        or col.startswith("mfcc_")
        or col.startswith("zero_crossing_rate_")
        or col.endswith("_band_energy_ratio")
    )


def is_ssl_column(col: str) -> bool:
    return col.startswith("ssl_emb_")


def is_forbidden_partial_feature(col: str) -> bool:
    c = col.strip().lower()
    if c in FORBIDDEN_PARTIAL_FEATURE_EXACT:
        return True
    return any(tok in c for tok in FORBIDDEN_PARTIAL_FEATURE_SUBSTRINGS)


def select_file_level_features(df: pd.DataFrame, feature_set: str) -> list[str]:
    cols: list[str] = []
    for c in df.columns:
        if c in FORBIDDEN_SCORE_FIELDS or c in IDENTITY_EXCLUDE_EXACT:
            continue
        if any(c.startswith(p) for p in IDENTITY_EXCLUDE_PREFIXES):
            continue
        if feature_set == "acoustic" and is_acoustic_column(c):
            cols.append(c)
        elif feature_set == "ssl" and is_ssl_column(c):
            cols.append(c)
        elif feature_set == "combined" and (is_acoustic_column(c) or is_ssl_column(c)):
            cols.append(c)
    if not cols:
        raise ValueError(f"No features selected for feature_set={feature_set}")
    return cols


def select_partial_combined_features(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    acoustic = [c for c in df.columns if is_acoustic_column(c)]
    ssl = [c for c in df.columns if is_ssl_column(c)]
    localization = [c for c in SAFE_LOCALIZATION_FEATURES if c in df.columns]
    raw = sorted(set(acoustic + ssl + localization))
    forbidden = [c for c in raw if is_forbidden_partial_feature(c)]
    allowed = [c for c in raw if c not in forbidden]
    if forbidden:
        # Fail hard if any forbidden column would be used.
        raise ValueError(
            "Forbidden label-derived features detected in candidate list: "
            + ";".join(forbidden[:20])
        )
    if not allowed:
        raise ValueError("No usable combined partial-segment features found.")
    return allowed, forbidden


def clean_numeric_matrix(df: pd.DataFrame, features: list[str]) -> tuple[pd.DataFrame, list[str], dict[str, list[str]]]:
    raw = df[features].copy().mask(df[features].eq(""))
    excluded: dict[str, list[str]] = {"all_missing": [], "non_numeric": []}
    numeric_cols: list[str] = []
    for c in raw.columns:
        vals = pd.to_numeric(raw[c], errors="coerce")
        if vals.notna().sum() == 0 and raw[c].astype(str).str.strip().ne("").any():
            excluded["non_numeric"].append(c)
        else:
            raw[c] = vals
            numeric_cols.append(c)
    x = raw[numeric_cols]
    all_missing = [c for c in x.columns if x[c].notna().sum() == 0]
    excluded["all_missing"] = all_missing
    usable = [c for c in x.columns if c not in all_missing]
    return x[usable], usable, excluded


def parse_binary_target(series: pd.Series, target_name: str) -> np.ndarray:
    vals = series.astype(str).str.strip()
    if not set(vals.unique()).issubset({"0", "1"}):
        bad = sorted(set(vals) - {"0", "1"})[:5]
        raise ValueError(f"Target '{target_name}' must be binary 0/1. Found: {bad}")
    return vals.astype(int).to_numpy()


def build_release_pipeline(max_selected_features: int, random_seed: int) -> Pipeline:
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


def fit_full_dataset_pipeline(
    df: pd.DataFrame,
    features: list[str],
    target_col: str,
    max_selected_features: int,
    random_seed: int,
) -> tuple[Pipeline, list[str], dict[str, Any]]:
    x, usable, excluded = clean_numeric_matrix(df, features)
    if not usable:
        raise ValueError("No usable features after cleaning.")
    y = parse_binary_target(df[target_col], target_col)
    safe_k = min(max_selected_features, len(usable))
    pipe = build_release_pipeline(max_selected_features=safe_k, random_seed=random_seed)
    pipe.fit(x, y)
    selector = pipe.named_steps["select"]
    mask = selector.get_support()
    selected = [usable[i] for i, m in enumerate(mask) if bool(m)]
    summary = {
        "input_feature_count": len(features),
        "usable_feature_count": len(usable),
        "selected_feature_count": len(selected),
        "selected_feature_names": selected,
        "excluded_all_missing": excluded.get("all_missing", []),
        "excluded_non_numeric": excluded.get("non_numeric", []),
        "class_counts": {
            "negative_0": int((y == 0).sum()),
            "positive_1": int((y == 1).sum()),
        },
        "row_count": int(len(df)),
    }
    return pipe, selected, summary


def resolve_merged_column(df: pd.DataFrame, base_name: str) -> str:
    """Return actual column name after pandas merge suffix collisions."""
    if base_name in df.columns:
        return base_name
    for suffix in ("_x", "_io", "_y", "_ng", "_sm"):
        candidate = f"{base_name}{suffix}"
        if candidate in df.columns:
            return candidate
    raise KeyError(
        f"Required column '{base_name}' not found after merge. "
        f"Available label-like columns: "
        f"{[c for c in df.columns if 'label' in c.lower() or 'training' in c.lower()]}"
    )


def _coalesce_duplicate_suffix_columns(df: pd.DataFrame, suffix: str) -> pd.DataFrame:
    out = df.copy()
    token = f"_{suffix}"
    dup_cols = [c for c in out.columns if c.endswith(token)]
    for c in dup_cols:
        base = c[: -len(token)]
        if base not in out.columns:
            out.rename(columns={c: base}, inplace=True)
            continue
        out[base] = out[base].mask(out[base].astype(str).str.strip().eq(""), out[c])
        out.drop(columns=[c], inplace=True)
    return out


def join_partial_segment_datasets(
    seg_table: pd.DataFrame,
    inside: pd.DataFrame,
    neigh: pd.DataFrame,
    segment_master: pd.DataFrame,
) -> pd.DataFrame:
    # Match Phase 8E-3 join semantics to avoid timestamp_segment_label -> _x/_y collisions.
    overlap_meta = {
        "timestamp_segment_label",
        "training_label_available",
        "mode",
        "interpretation_note",
    }
    inside_cols = [
        c
        for c in inside.columns
        if c not in {"start_sec", "end_sec"} and c not in (overlap_meta & set(seg_table.columns))
    ]
    merged = seg_table.merge(
        inside[inside_cols],
        on=["file_id", "segment_id"],
        how="left",
        suffixes=("", "_io"),
    )
    merged = _coalesce_duplicate_suffix_columns(merged, "io")
    neigh_cols = [c for c in neigh.columns if c not in {"start_sec", "end_sec"}]
    merged = merged.merge(
        neigh[neigh_cols],
        on=["file_id", "segment_id"],
        how="left",
        suffixes=("", "_ng"),
    )
    merged = _coalesce_duplicate_suffix_columns(merged, "ng")
    drop_from_master = {
        "schema_version",
        "audio_path",
        "start_sec",
        "end_sec",
        "segment_duration_sec",
        "known_origin_label",
        "known_manipulation_labels",
        "segment_label_source",
        "inherited_target_origin_multiclass",
        "inherited_target_is_replay",
        "inherited_target_is_mixer_channel",
        "inherited_target_is_partial_fabrication_file",
        "inherited_target_is_clean",
        "eligible_segment_origin_context",
        "eligible_segment_replay_context",
        "eligible_segment_mixer_context",
        "eligible_partial_segment_training",
    }
    master_payload = segment_master[[c for c in segment_master.columns if c not in drop_from_master]]
    merged = merged.merge(master_payload, on=["file_id", "segment_id"], how="left", suffixes=("", "_sm"))
    merged = _coalesce_duplicate_suffix_columns(merged, "sm")
    # Clean any remaining pandas default _x/_y collisions.
    for base in ("timestamp_segment_label", "training_label_available"):
        if base not in merged.columns:
            if f"{base}_x" in merged.columns:
                merged[base] = merged[f"{base}_x"]
                for drop_col in (f"{base}_x", f"{base}_y"):
                    if drop_col in merged.columns:
                        merged.drop(columns=[drop_col], inplace=True)
    return merged


def prepare_partial_training_rows(df: pd.DataFrame) -> pd.DataFrame:
    label_col = resolve_merged_column(df, "timestamp_segment_label")
    train_col = resolve_merged_column(df, "training_label_available")
    ok = df[
        (df[train_col].astype(str).str.lower() == "true")
        & (df[label_col].isin(["fabricated_region", "outside_fabricated_region"]))
    ].copy()
    if len(ok) == 0:
        raise ValueError("No trainable partial-segment rows found.")
    ok["target_partial_fabricated"] = np.where(ok[label_col] == "fabricated_region", "1", "0")
    return ok


def build_metadata(
    spec: ReleaseModelSpec,
    source_dataset_paths: list[str],
    feature_names: list[str],
    excluded_summary: dict[str, Any],
    target_mapping: dict[str, int],
    random_seed: int,
) -> dict[str, Any]:
    return {
        "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
        "model_name": spec.model_name,
        "task_name": spec.task_name,
        "evidence_axis": spec.evidence_axis,
        "phase_trained": spec.phase_trained,
        "source_dataset_paths": source_dataset_paths,
        "feature_set": spec.feature_set,
        "feature_count": len(feature_names),
        "feature_names": feature_names,
        "excluded_feature_summary": excluded_summary,
        "target_column": spec.target_column,
        "target_mapping": target_mapping,
        "model_type": "sklearn_pipeline_logistic_regression_l2",
        "pipeline_steps": [
            "SimpleImputer(median)",
            "VarianceThreshold",
            "StandardScaler",
            "SelectKBest(f_classif)",
            "LogisticRegression(l2, balanced)",
        ],
        "threshold_candidate": spec.threshold_candidate,
        "threshold_source": spec.threshold_source,
        "metrics_reference": spec.metrics_reference,
        "status": RELEASE_STATUS,
        "active_production_model": False,
        "not_final_forensic_decision": True,
        "allowed_use": spec.allowed_use,
        "forbidden_use": spec.forbidden_use,
        "limitations": spec.limitations,
        "created_at": now_iso(),
        "created_by_script": SCRIPT_NAME,
        "code_version_note": "Phase 9B experimental packaging from accepted Phase 8 datasets.",
        "expected_input_schema": {
            "type": "tabular_features",
            "feature_set": spec.feature_set,
            "required_feature_names": feature_names,
        },
        "expected_output_schema": {
            "probability_positive_class": "float in [0,1]",
            "predicted_label_at_threshold": "0 or 1 using threshold_candidate",
            "evidence_axis": spec.evidence_axis,
            "output_meaning": spec.output_meaning,
        },
        "random_seed": random_seed,
        "replay_mixer_note": spec.replay_mixer_note,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def save_joblib_artifact(path: Path, pipeline: Pipeline, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"Artifact exists (use --force): {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, path)


def write_model_card(path: Path, spec: ReleaseModelSpec, summary: dict[str, Any]) -> None:
    lines = [
        f"# {spec.model_name} (experimental release card)",
        "",
        f"- status: {RELEASE_STATUS}",
        f"- evidence_axis: {spec.evidence_axis}",
        f"- feature_set: {spec.feature_set}",
        f"- threshold_candidate: {spec.threshold_candidate}",
        f"- rows packaged: {summary.get('row_count', 'n/a')}",
        f"- selected features: {summary.get('selected_feature_count', 'n/a')}",
        "",
        "## Allowed use",
        spec.allowed_use,
        "",
        "## Forbidden use",
        spec.forbidden_use,
        "",
        "## Limitations",
    ]
    for item in spec.limitations:
        lines.append(f"- {item}")
    if spec.replay_mixer_note:
        lines.extend(["", "## Important note", spec.replay_mixer_note])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_model_inventory(models: list[dict[str, Any]], warnings: list[str]) -> dict[str, Any]:
    missing = []
    for m in models:
        art = Path(m["artifact_path"])
        meta = Path(m["metadata_path"])
        if not art.is_file():
            missing.append(str(art))
        if not meta.is_file():
            missing.append(str(meta))
    return {
        "inventory_schema_version": INVENTORY_SCHEMA_VERSION,
        "created_at": now_iso(),
        "status": RELEASE_STATUS,
        "models": models,
        "missing_artifacts": missing,
        "warnings": warnings,
    }


def validate_no_forbidden_fields_in_metadata(metadata: dict[str, Any]) -> list[str]:
    text = json.dumps(metadata).lower()
    issues = []
    if metadata.get("status") != RELEASE_STATUS:
        issues.append("status must be experimental_forensic_prototype")
    if metadata.get("active_production_model") is not False:
        issues.append("active_production_model must be false")
    if metadata.get("not_final_forensic_decision") is not True:
        issues.append("not_final_forensic_decision must be true")
    # Allow fake_score/real_score only inside forbidden_use wording.
    forbidden_use = str(metadata.get("forbidden_use", "")).lower()
    scrubbed = text.replace(forbidden_use, "")
    if "fake_score" in scrubbed or "real_score" in scrubbed:
        issues.append("fake_score/real_score found outside forbidden_use text")
    return issues


def load_threshold_from_csv(path: Path, task_name: str, feature_set: str, default: float) -> float:
    if not path.is_file():
        return default
    df = pd.read_csv(path)
    if "task_name" not in df.columns or "feature_set" not in df.columns:
        return default
    sub = df[(df["task_name"] == task_name) & (df["feature_set"] == feature_set)]
    if len(sub) == 0:
        return default
    col = "recommended_threshold_candidate" if "recommended_threshold_candidate" in sub.columns else None
    if not col:
        return default
    try:
        return float(sub.iloc[0][col])
    except Exception:
        return default


def sanitize_for_report(v: Any) -> Any:
    if isinstance(v, float) and not math.isfinite(v):
        return ""
    return v


def default_release_model_specs() -> list[ReleaseModelSpec]:
    common_limits = [
        "experimental prototype only",
        "manual review required",
        "not final forensic proof",
        "small accepted Phase 8 dataset",
    ]
    return [
        ReleaseModelSpec(
            model_name="origin_file_model",
            task_name="origin_file_model",
            evidence_axis="origin_evidence",
            feature_set="ssl",
            target_column="target_is_ai_synthetic",
            positive_label="clean_ai_synthetic (1)",
            negative_label="clean_human (0)",
            phase_trained="Phase 8E-1 / 8E-1A",
            artifact_rel="origin/origin_file_model__ssl__experimental.joblib",
            metadata_rel="origin/origin_file_model__ssl__metadata.json",
            threshold_candidate=0.20,
            threshold_source="Phase 8E-1A threshold recommendations (ssl)",
            metrics_reference="reports/phase8/models/phase8e1/phase8e1_metrics_summary.csv",
            max_selected_features=50,
            allowed_use="origin evidence indicator for experimental review workflow",
            forbidden_use=(
                "final fake/real decision; court-ready proof; production deployment without "
                "validation; replacing human forensic analyst"
            ),
            limitations=common_limits,
            output_meaning="Higher score suggests stronger origin-axis synthetic indicator (experimental).",
        ),
        ReleaseModelSpec(
            model_name="replay_file_model",
            task_name="replay_file_model",
            evidence_axis="replay_evidence",
            feature_set="acoustic",
            target_column="target_is_replay",
            positive_label="replay_positive (1)",
            negative_label="clean_negative (0)",
            phase_trained="Phase 8E-1 / 8E-1A",
            artifact_rel="replay/replay_file_model__acoustic__experimental.joblib",
            metadata_rel="replay/replay_file_model__acoustic__metadata.json",
            threshold_candidate=0.65,
            threshold_source="Phase 8E-1A threshold recommendations (acoustic)",
            metrics_reference="reports/phase8/models/phase8e1/phase8e1_metrics_summary.csv",
            max_selected_features=50,
            allowed_use="replay/rerecording evidence indicator (does not mean AI-generated)",
            forbidden_use=(
                "claiming replay means AI-generated; final fake/real decision; court-ready proof; "
                "production deployment without validation"
            ),
            limitations=common_limits + ["replay evidence is not AI-generation evidence"],
            output_meaning="Higher score suggests stronger replay/rerecording indicator (experimental).",
            replay_mixer_note="Replay evidence does not mean AI-generated.",
        ),
        ReleaseModelSpec(
            model_name="mixer_file_model",
            task_name="mixer_file_model",
            evidence_axis="mixer_channel_evidence",
            feature_set="acoustic",
            target_column="target_is_mixer_channel",
            positive_label="mixer_positive (1)",
            negative_label="clean_negative (0)",
            phase_trained="Phase 8E-1 / 8E-1A",
            artifact_rel="mixer/mixer_file_model__acoustic__experimental.joblib",
            metadata_rel="mixer/mixer_file_model__acoustic__metadata.json",
            threshold_candidate=0.75,
            threshold_source="Phase 8E-1A threshold recommendations (acoustic)",
            metrics_reference="reports/phase8/models/phase8e1/phase8e1_metrics_summary.csv",
            max_selected_features=50,
            allowed_use="mixer/channel processing evidence indicator (does not mean AI-generated)",
            forbidden_use=(
                "claiming mixer/channel means AI-generated; final fake/real decision; court-ready proof; "
                "production deployment without validation"
            ),
            limitations=common_limits + ["mixer/channel evidence is not AI-generation evidence"],
            output_meaning="Higher score suggests stronger mixer/channel indicator (experimental).",
            replay_mixer_note="Mixer/channel evidence does not mean AI-generated.",
        ),
        ReleaseModelSpec(
            model_name="partial_fabrication_segment_model",
            task_name="partial_fabrication_segment_model",
            evidence_axis="partial_fabrication_evidence",
            feature_set="combined",
            target_column="target_partial_fabricated",
            positive_label="fabricated_region (1)",
            negative_label="outside_fabricated_region (0)",
            phase_trained="Phase 8E-3",
            artifact_rel="partial_segment/partial_segment_model__combined__experimental.joblib",
            metadata_rel="partial_segment/partial_segment_model__combined__metadata.json",
            threshold_candidate=0.50,
            threshold_source="Phase 8E-3 review candidate threshold",
            metrics_reference="reports/phase8/models/phase8e3/phase8e3_partial_segment_metrics_summary.csv",
            max_selected_features=75,
            allowed_use="partial segment localization support indicator",
            forbidden_use=(
                "final fabrication proof; court-ready proof; production deployment without validation; "
                "replacing human forensic analyst"
            ),
            limitations=common_limits
            + [
                "timestamp labels used as targets only",
                "label-derived baseline features excluded from inputs",
            ],
            output_meaning=(
                "Segment-level candidate indicator for fabricated-region support (experimental)."
            ),
        ),
    ]
