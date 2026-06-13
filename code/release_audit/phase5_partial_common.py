"""Shared constants and helpers for Phase 5 partial segment redesign."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / "release"
PHASE9_PARTIAL = ROOT / "code" / "phase9" / "partial_redesign"
DEFAULT_OUT = ROOT / "reports" / "release_audit" / "phase5_partial_redesign_2026-06-13"

LEAKAGE_MANIFEST = (
    ROOT
    / "reports"
    / "release_audit"
    / "leakage_safe_eval_2026-06-13"
    / "leakage_safe_file_manifest.csv"
)
TESTING_MANIFEST = (
    ROOT
    / "reports"
    / "phase7"
    / "phase7_forensic_tests"
    / "forensic_test_manifest_backup_before_T4_3_timestamp.csv"
)
P5_SEGMENT_DATASET = (
    ROOT / "reports" / "phase9" / "partial_redesign" / "phase9d_p5_segment_partial_localizer_dataset.csv"
)
P5_SEGMENT_FEATURE_JSON = (
    ROOT / "reports" / "phase9" / "partial_redesign" / "phase9d_p5_segment_localizer_feature_columns.json"
)

# Audit F9 — within-file percentile / max-normalized features (forced contrast).
F9_FORBIDDEN_FEATURES = frozenset(
    {
        "acoustic_deviation_percentile_within_file",
        "ssl_deviation_percentile_within_file",
        "within_file_acoustic_deviation_score",
        "within_file_ssl_deviation_score",
        "combined_within_file_deviation_score",
    }
)

PHASE5_LOCALIZATION_FEATURES = [
    "acoustic_distance_from_file_median",
    "ssl_distance_from_file_median",
    "neighbor_acoustic_transition_score",
    "neighbor_ssl_transition_score",
    "combined_neighbor_transition_score",
]

PARTIAL_FILE_CATEGORIES = frozenset({"ai_fabricated", "human_fabricated"})

TESTING_PARTIAL_IDS = ["T4.3", "T5_FAB_001"]
TESTING_NEGATIVE_IDS = ["T1.1", "T1.2", "T1.3", "T2.3", "T3.2"]

# Gating (cascade) — reconnect after oracle passes; eval only in Phase 5.
CASCADE_GATING = {
    "segment_threshold": 0.50,
    "broad_limit": 0.45,
    "topk_minus_rest_min": 0.20,
    "localization_hsf_max": 0.35,
}

STOP_RULE_MIN_ORACLE_TOP5_RATE = 0.50


def setup_import_paths() -> None:
    if str(RELEASE) not in sys.path:
        sys.path.insert(0, str(RELEASE))
    if str(PHASE9_PARTIAL) not in sys.path:
        sys.path.insert(0, str(PHASE9_PARTIAL))


def progress(msg: str) -> None:
    print(msg, flush=True)


def normalized_path(path: str) -> str:
    return str(path).replace("\\", "/").lower()


def attach_leakage_safe_split(df: pd.DataFrame, manifest: pd.DataFrame | None = None) -> pd.DataFrame:
    """Join leakage_safe_split from Phase 7 manifest on audio_path."""
    out = df.copy()
    if "leakage_safe_split" in out.columns and out["leakage_safe_split"].astype(str).str.strip().ne("").any():
        return out
    man = manifest if manifest is not None else pd.read_csv(LEAKAGE_MANIFEST, dtype=str, keep_default_na=False)
    man = man.copy()
    man["_np"] = man["audio_path"].map(normalized_path)
    split_map = man.set_index("_np")["leakage_safe_split"].to_dict()
    out["_np"] = out["audio_path"].astype(str).map(normalized_path)
    out["leakage_safe_split"] = out["_np"].map(split_map).fillna("")
    out.drop(columns=["_np"], inplace=True)
    return out


def load_p5_feature_columns() -> list[str]:
    cols = json.loads(P5_SEGMENT_FEATURE_JSON.read_text(encoding="utf-8"))
    return [str(c) for c in cols]


def build_phase5_model_features(all_columns: list[str] | None = None) -> list[str]:
    """Acoustic + SSL + safe localization; excludes F9."""
    setup_import_paths()
    from phase9d_p5_partial_utils import (  # noqa: E402
        build_segment_localizer_feature_columns,
        is_forbidden_feature,
    )

    cols = all_columns if all_columns is not None else load_p5_feature_columns()
    base = build_segment_localizer_feature_columns(cols)
    return [c for c in base if c not in F9_FORBIDDEN_FEATURES and not is_forbidden_feature(c)]


def write_f9_audit(out_dir: Path, model_features: list[str]) -> None:
    removed = sorted(F9_FORBIDDEN_FEATURES)
    kept_loc = [c for c in PHASE5_LOCALIZATION_FEATURES if c in model_features]
    lines = [
        "# Phase 5 — F9 feature audit",
        "",
        "## Removed from model inputs (audit F9)",
        "",
    ]
    lines.extend(f"- `{c}`" for c in removed)
    lines.extend(
        [
            "",
            "## Kept localization features",
            "",
        ]
    )
    lines.extend(f"- `{c}`" for c in kept_loc)
    lines.append("")
    lines.append(f"Total model features: **{len(model_features)}**")
    (out_dir / "phase5_f9_feature_audit.md").write_text("\n".join(lines), encoding="utf-8")
    (out_dir / "phase5_segment_feature_columns_no_f9.json").write_text(
        json.dumps(model_features, indent=2), encoding="utf-8"
    )
