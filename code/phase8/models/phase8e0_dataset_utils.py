"""
Phase 8E-0 dataset assembly helpers.

Dataset assembly and leakage audit only. No model training or predictions.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


def load_csv_required(path: str | Path) -> pd.DataFrame:
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Required CSV missing: {p}")
    return pd.read_csv(p, dtype=str, keep_default_na=False)


def check_required_columns(df: pd.DataFrame, required: list[str], table_name: str) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"{table_name} missing columns: {missing}")


def find_feature_columns(df: pd.DataFrame) -> list[str]:
    deny = {
        "schema_version",
        "file_id",
        "segment_id",
        "audio_path",
        "source_dataset",
        "split",
        "known_origin_label",
        "known_manipulation_labels",
        "duration_sec",
        "sample_rate",
        "start_sec",
        "end_sec",
        "segment_duration_sec",
        "feature_source",
        "extraction_status",
        "warning_message",
    }
    return [c for c in df.columns if c not in deny and not c.startswith("ssl_emb_")]


def find_ssl_embedding_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c.startswith("ssl_emb_")]


def normalize_bool_label(value: Any) -> str:
    v = str(value).strip().lower()
    if v in {"1", "true", "yes", "y"}:
        return "1"
    if v in {"0", "false", "no", "n"}:
        return "0"
    return ""


def _split_labels(label_string: Any) -> set[str]:
    if label_string is None:
        return set()
    val = str(label_string).strip()
    if not val or val.lower() in {"nan", "none", "null", "na"}:
        return set()
    parts = [p.strip().lower() for p in val.replace(",", ";").split(";")]
    return {p for p in parts if p and p != "na"}


def has_label(label_string: Any, label: str) -> bool:
    return label.strip().lower() in _split_labels(label_string)


def derive_file_targets(row: pd.Series) -> dict[str, str]:
    origin = str(row.get("known_origin_label", "")).strip().lower()
    manip = _split_labels(row.get("known_manipulation_labels", ""))
    mixed = "mixed" in origin or has_label(row.get("known_manipulation_labels", ""), "mixed")
    unknown = origin in {"", "unknown"}

    is_replay = "1" if "replay_rerecorded" in manip else "0"
    is_mixer = "1" if "mixer_channel_processed" in manip else "0"
    is_partial = "1" if "partial_fabrication" in manip else "0"
    is_clean = "1" if "clean" in manip else "0"
    has_other_manip = bool(
        manip.intersection({"edited_spliced", "unknown_manipulation", "compressed_low_quality"})
    )

    target_origin_multiclass = "unknown"
    if mixed:
        target_origin_multiclass = "mixed"
    elif origin in {"human", "ai_synthetic"}:
        target_origin_multiclass = origin

    target_is_ai = ""
    if target_origin_multiclass == "human":
        target_is_ai = "0"
    elif target_origin_multiclass == "ai_synthetic":
        target_is_ai = "1"

    eligible_origin = (
        "true"
        if target_origin_multiclass in {"human", "ai_synthetic"}
        and is_clean == "1"
        and not mixed
        and not unknown
        else "false"
    )
    eligible_replay = (
        "true"
        if (is_replay == "1" or is_clean == "1")
        and is_mixer == "0"
        and is_partial == "0"
        and not has_other_manip
        and not mixed
        else "false"
    )
    eligible_mixer = (
        "true"
        if (is_mixer == "1" or is_clean == "1")
        and is_replay == "0"
        and is_partial == "0"
        and not has_other_manip
        and not mixed
        else "false"
    )
    eligible_partial_context = "true" if is_partial == "1" else "false"

    return {
        "target_origin_multiclass": target_origin_multiclass,
        "target_is_ai_synthetic": target_is_ai,
        "target_is_replay": is_replay,
        "target_is_mixer_channel": is_mixer,
        "target_is_partial_fabrication_file": is_partial,
        "target_is_clean": is_clean,
        "eligible_origin_file_model": eligible_origin,
        "eligible_replay_file_model": eligible_replay,
        "eligible_mixer_file_model": eligible_mixer,
        "eligible_partial_file_context_only": eligible_partial_context,
        "eligible_partial_segment_training": "false",
    }


def derive_segment_targets(row: pd.Series) -> dict[str, str]:
    base = derive_file_targets(row)
    source = "file_level_inherited"
    if str(row.get("segment_label_source", "")).strip():
        source = str(row.get("segment_label_source", "")).strip()
    elif str(row.get("fabrication_timestamp_start_sec", "")).strip() or str(
        row.get("fabrication_timestamp_end_sec", "")
    ).strip():
        source = "true_segment_timestamp"

    eligible_partial_train = "true" if source == "true_segment_timestamp" else "false"
    return {
        "inherited_target_origin_multiclass": base["target_origin_multiclass"],
        "inherited_target_is_replay": base["target_is_replay"],
        "inherited_target_is_mixer_channel": base["target_is_mixer_channel"],
        "inherited_target_is_partial_fabrication_file": base["target_is_partial_fabrication_file"],
        "inherited_target_is_clean": base["target_is_clean"],
        "segment_label_source": source if source in {"file_level_inherited", "true_segment_timestamp", "unknown"} else "unknown",
        "eligible_segment_origin_context": "true" if base["target_origin_multiclass"] in {"human", "ai_synthetic"} else "false",
        "eligible_segment_replay_context": "true" if base["target_is_replay"] in {"0", "1"} else "false",
        "eligible_segment_mixer_context": "true" if base["target_is_mixer_channel"] in {"0", "1"} else "false",
        "eligible_partial_segment_training": eligible_partial_train if base["target_is_partial_fabrication_file"] == "1" else "false",
    }


def infer_source_group_id(row: pd.Series) -> str:
    for key in ("source_id", "base_id", "original_file_id", "parent_file_id", "recording_id", "speaker_id"):
        val = str(row.get(key, "")).strip()
        if val:
            return val.lower()
    seed = str(row.get("file_id", "")).strip() or str(row.get("audio_path", "")).strip()
    seed = seed.lower()
    seed = re.sub(r"\.(wav|mp3|flac|m4a|ogg)$", "", seed)
    seed = re.sub(
        r"(replay|mixer|mix|partial|fabricated|ai|human|clean|segment|chunk|aug|copy|version|v[0-9]+)",
        "",
        seed,
    )
    seed = re.sub(r"[_\-/\s]+", "_", seed).strip("_")
    return seed or "unknown_group"


def safe_join(left: pd.DataFrame, right: pd.DataFrame, keys: list[str], name: str) -> pd.DataFrame:
    merged = left.merge(right, on=keys, how="inner", suffixes=("", "_dup"))
    dup_cols = [c for c in merged.columns if c.endswith("_dup")]
    if dup_cols:
        merged = merged.drop(columns=dup_cols)
    if len(merged) != len(left):
        raise ValueError(f"Join '{name}' changed row count: left={len(left)} joined={len(merged)}")
    return merged


def cleanup_merge_artifact_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove obvious duplicate merge artifacts while preserving useful provenance fields.
    """
    drop_cols = []
    schema_aliases = {
        "schema_version_x",
        "schema_version_y",
        "schema_version_file",
        "schema_version_segment",
        "schema_version_acoustic",
        "schema_version_ssl",
    }
    for col in df.columns:
        if col in schema_aliases:
            drop_cols.append(col)
        elif col.endswith("_dup"):
            drop_cols.append(col)
        elif col in {"feature_source_x", "feature_source_y"} and "feature_source" in df.columns:
            drop_cols.append(col)
        elif col in {"extraction_status_x", "extraction_status_y"} and "extraction_status" in df.columns:
            drop_cols.append(col)
    if drop_cols:
        df = df.drop(columns=sorted(set(drop_cols)), errors="ignore")
    return df


def drop_phase8b_placeholder_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove Phase 8B placeholder evidence/fusion/decision columns from Phase 8E datasets.
    """
    forbidden_cols = {
        # file-level placeholders
        "evidence_origin_human_score",
        "evidence_origin_ai_score",
        "evidence_origin_mixed_score",
        "evidence_origin_unknown_score",
        "evidence_replay_score",
        "evidence_mixer_channel_score",
        "evidence_partial_fabrication_score",
        "evidence_splice_score",
        "evidence_quality_score",
        "calibrated_origin_label",
        "calibrated_manipulation_labels",
        "final_forensic_status",
        "forensic_risk_level",
        "manual_review_required",
        "manual_review_reason",
        "fusion_trace",
        "forensic_summary",
        "evidence_source_paths",
        # segment-level placeholders
        "segment_origin_human_score",
        "segment_origin_ai_score",
        "segment_origin_mixed_score",
        "segment_origin_unknown_score",
        "replay_score",
        "mixer_channel_score",
        "partial_fabrication_score",
        "splice_score",
        "quality_score",
        "suspicious_segment_flag",
        "segment_reason",
        "segment_evidence_source",
    }
    keep = [c for c in df.columns if c not in forbidden_cols]
    return df[keep]


def ensure_schema_version_column(df: pd.DataFrame, schema_version: str) -> pd.DataFrame:
    """
    Ensure exactly one schema_version column, normalized to requested value.
    """
    df = cleanup_merge_artifact_columns(df)

    # Remove any remaining schema_version-like variants except canonical name.
    schema_like = [c for c in df.columns if c.startswith("schema_version") and c != "schema_version"]
    if schema_like:
        df = df.drop(columns=schema_like, errors="ignore")

    if "schema_version" in df.columns:
        df["schema_version"] = schema_version
        cols = ["schema_version"] + [c for c in df.columns if c != "schema_version"]
        return df[cols]

    df.insert(0, "schema_version", schema_version)
    return df


def make_leakage_audit(file_df: pd.DataFrame, segment_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, str]] = []

    def add(item: str, severity: str, count: int, ids: list[str], explanation: str, recommendation: str) -> None:
        rows.append(
            {
                "audit_item": item,
                "severity": severity,
                "affected_count": str(count),
                "affected_ids": ";".join(ids[:25]),
                "explanation": explanation,
                "recommendation": recommendation,
            }
        )

    dup_file = file_df[file_df["file_id"].duplicated(keep=False)] if "file_id" in file_df.columns else pd.DataFrame()
    add(
        "duplicate_file_id",
        "blocking" if len(dup_file) else "info",
        len(dup_file),
        sorted(set(dup_file.get("file_id", pd.Series(dtype=str)).astype(str))),
        "Duplicate file_id values can leak labels and corrupt joins.",
        "Deduplicate file-level rows before training.",
    )

    dup_path = file_df[file_df["audio_path"].duplicated(keep=False)] if "audio_path" in file_df.columns else pd.DataFrame()
    add(
        "duplicate_audio_path",
        "warning" if len(dup_path) else "info",
        len(dup_path),
        sorted(set(dup_path.get("file_id", pd.Series(dtype=str)).astype(str))),
        "Same audio path appears multiple times.",
        "Group duplicates in same split/fold.",
    )

    cross_labels = file_df[
        (file_df.get("target_is_clean", "") == "1")
        & (
            (file_df.get("target_is_replay", "") == "1")
            | (file_df.get("target_is_mixer_channel", "") == "1")
            | (file_df.get("target_is_partial_fabrication_file", "") == "1")
        )
    ]
    add(
        "conflicting_task_labels",
        "blocking" if len(cross_labels) else "info",
        len(cross_labels),
        sorted(set(cross_labels.get("file_id", pd.Series(dtype=str)).astype(str))),
        "Rows marked clean and manipulated simultaneously.",
        "Fix manipulation labeling before modeling.",
    )

    by_group = file_df.groupby("source_group_id", dropna=False).size() if "source_group_id" in file_df.columns else pd.Series(dtype=int)
    multi_variant_groups = by_group[by_group > 1]
    add(
        "source_group_multiple_variants",
        "warning" if len(multi_variant_groups) else "info",
        int(len(multi_variant_groups)),
        [str(x) for x in multi_variant_groups.index.tolist()[:25]],
        "Likely variants share same source and can leak across train/test.",
        "Use group-aware split by source_group_id.",
    )

    if "split" in file_df.columns and "source_group_id" in file_df.columns:
        split_groups = file_df.groupby("source_group_id")["split"].nunique()
        cross_split = split_groups[split_groups > 1]
        add(
            "source_group_cross_split",
            "blocking" if len(cross_split) else "info",
            int(len(cross_split)),
            [str(x) for x in cross_split.index.tolist()[:25]],
            "Same source group appears in multiple splits.",
            "Rebuild split constraints using source_group_id.",
        )
    else:
        add(
            "source_group_cross_split",
            "info",
            0,
            [],
            "Split column unavailable; cross-split audit limited.",
            "Provide split metadata for stronger leakage checks.",
        )

    seg_by_file = segment_df.groupby("file_id", dropna=False).size() if "file_id" in segment_df.columns else pd.Series(dtype=int)
    split_risk = seg_by_file[seg_by_file > 1]
    add(
        "segment_same_file_split_risk",
        "warning" if len(split_risk) else "info",
        int(len(split_risk)),
        [str(x) for x in split_risk.index.tolist()[:25]],
        "Segments from same file can be split apart and leak content.",
        "Keep all segments from a file in same fold.",
    )

    origin_leak = file_df[
        (file_df.get("target_origin_multiclass", "") == "ai_synthetic")
        & ((file_df.get("target_is_replay", "") == "1") | (file_df.get("target_is_mixer_channel", "") == "1"))
    ]
    add(
        "origin_vs_manipulation_coupling",
        "warning" if len(origin_leak) else "info",
        len(origin_leak),
        sorted(set(origin_leak.get("file_id", pd.Series(dtype=str)).astype(str))),
        "Origin and manipulation can become shortcut features.",
        "Balance manipulations across origin classes in later training.",
    )

    partial_inherited = segment_df[
        (segment_df.get("inherited_target_is_partial_fabrication_file", "") == "1")
        & (segment_df.get("segment_label_source", "") != "true_segment_timestamp")
    ]
    add(
        "partial_inherited_label_risk",
        "warning" if len(partial_inherited) else "info",
        len(partial_inherited),
        sorted(set(partial_inherited.get("file_id", pd.Series(dtype=str)).astype(str))),
        "Partial fabrication segment labels are inherited, not true timestamps.",
        "Keep partial segment training blocked until true timestamps exist.",
    )

    return pd.DataFrame(rows)


def summarize_dataset(df: pd.DataFrame, label_cols: list[str]) -> pd.DataFrame:
    rows: list[dict[str, str]] = [{"metric": "row_count", "key": "rows", "value": str(len(df))}]
    for col in label_cols:
        if col in df.columns:
            vc = df[col].astype(str).value_counts(dropna=False)
            for k, v in vc.items():
                rows.append({"metric": "label_count", "key": f"{col}={k}", "value": str(int(v))})
    return pd.DataFrame(rows)


def write_markdown_report(
    path: str | Path,
    summary: pd.DataFrame,
    audit: pd.DataFrame,
    *,
    file_master: pd.DataFrame | None = None,
    origin_df: pd.DataFrame | None = None,
    replay_df: pd.DataFrame | None = None,
    mixer_df: pd.DataFrame | None = None,
    partial_loc: pd.DataFrame | None = None,
) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        "# Phase 8E-0 Dataset Assembly Report",
        "",
        f"**Generated:** {now}",
        "",
        "> Phase 8E-0 is dataset assembly + leakage audit only (no training, no prediction).",
        "",
        "## Dataset Summary",
        "",
    ]
    for _, row in summary.iterrows():
        lines.append(f"- {row['dataset']}: {row['metric']}={row['value']}")
    if file_master is not None:
        clean_counts = file_master.get("target_is_clean", pd.Series(dtype=str)).value_counts().to_dict()
        lines.extend(
            [
                "",
                "## Task-Specific Counts",
                "",
                f"- target_is_clean counts: {clean_counts}",
                f"- origin dataset rows: {len(origin_df) if origin_df is not None else 0}",
            ]
        )
    if replay_df is not None:
        lines.append(
            f"- replay dataset target_is_replay counts: {replay_df.get('target_is_replay', pd.Series(dtype=str)).value_counts().to_dict()}"
        )
    if mixer_df is not None:
        lines.append(
            f"- mixer dataset target_is_mixer_channel counts: {mixer_df.get('target_is_mixer_channel', pd.Series(dtype=str)).value_counts().to_dict()}"
        )
    if partial_loc is not None:
        blocked = int((partial_loc.get("eligible_partial_segment_training", pd.Series(dtype=str)) == "false").sum())
        lines.append(f"- partial localization prep rows: {len(partial_loc)}")
        lines.append(f"- partial segment training blocked rows: {blocked}")
    lines.extend(["", "## Leakage Audit", ""])
    for _, row in audit.iterrows():
        lines.append(
            f"- [{row['severity']}] {row['audit_item']} | affected={row['affected_count']} | {row['explanation']}"
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- `source_group_id` can be heuristic when explicit source metadata is absent.",
            "- `eligible_partial_segment_training` remains false for inherited partial labels.",
            "- No model training, fitting, or predictions are performed in Phase 8E-0.",
        ]
    )
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
