"""Load active Phase 9B packaged models (reference models excluded by default)."""

from __future__ import annotations

import json
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib

from .utils import read_yaml_safe, release_root

REQUIRED_STATUS = "experimental_forensic_prototype"
ACTIVE_KEYS = ("origin", "replay", "mixer", "partial_segment")

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


def _paths_config() -> dict[str, str]:
    cfg = read_yaml_safe(release_root() / "config" / "model_paths.yaml")
    return {str(k): str(v) for k, v in cfg.items()}


def _resolve_artifact(rel_path: str) -> Path:
    rel = Path(rel_path.replace("\\", "/"))
    if rel.parts and rel.parts[0] == "release":
        return (release_root().parent / rel).resolve()
    return (release_root() / rel).resolve()


def load_model_metadata(model_key: str) -> dict[str, Any]:
    if model_key not in ACTIVE_KEYS:
        raise ValueError(f"Unknown active model key: {model_key}")
    artifact = _resolve_artifact(_paths_config()[model_key])
    meta_path = artifact.with_name(
        artifact.name.replace("__experimental.joblib", "__metadata.json")
    )
    if not meta_path.is_file():
        raise FileNotFoundError(f"Metadata missing: {meta_path}")
    return json.loads(meta_path.read_text(encoding="utf-8"))


def validate_metadata_for_inference(metadata: dict[str, Any]) -> None:
    if metadata.get("status") != REQUIRED_STATUS:
        raise ValueError("Model metadata status must be experimental_forensic_prototype")
    if metadata.get("active_production_model") is True:
        raise ValueError("active_production_model must be false")
    if metadata.get("not_final_forensic_decision") is not True:
        raise ValueError("not_final_forensic_decision must be true")
    if "reference" in str(metadata.get("model_name", "")).lower():
        raise ValueError("Reference models cannot be loaded as active inference models")


def get_threshold(metadata: dict[str, Any]) -> float:
    return float(metadata.get("threshold_candidate", 0.5))


def _import_phase8c_feature_utils():
    feat_dir = release_root().parent / "code" / "phase8" / "features"
    if str(feat_dir) not in sys.path:
        sys.path.insert(0, str(feat_dir))
    import phase8c_feature_utils as p8c  # type: ignore

    return p8c


def _reconstruct_ssl_feature_names(count: int = 768) -> list[str]:
    return [f"ssl_emb_{i:03d}" for i in range(int(count))]


def _reconstruct_from_metadata_hint(metadata: dict[str, Any]) -> list[str] | None:
    feature_set = str(metadata.get("feature_set", "")).lower()
    summary = metadata.get("excluded_feature_summary") or {}
    input_count = summary.get("input_feature_count") or summary.get("usable_feature_count")

    if feature_set == "ssl":
        n = int(input_count) if input_count else 768
        return _reconstruct_ssl_feature_names(n)

    if feature_set == "acoustic":
        try:
            p8c = _import_phase8c_feature_utils()
            return list(p8c.FILE_FEATURE_NAMES)
        except Exception:
            return None

    if feature_set == "combined":
        return _reconstruct_combined_segment_feature_names()

    return None


def _reconstruct_combined_segment_feature_names() -> list[str]:
    """Full segment-level combined schema used at Phase 8E-3 fit time (pre-SelectKBest)."""
    try:
        p8c = _import_phase8c_feature_utils()
        acoustic = list(p8c.SEGMENT_FEATURE_NAMES)
    except Exception:
        acoustic = []
    ssl = _reconstruct_ssl_feature_names(768)
    return sorted(set(acoustic + ssl + SAFE_LOCALIZATION_FEATURES))


def _metadata_doc_feature_names(metadata: dict[str, Any]) -> list[str]:
    return [str(n) for n in metadata.get("feature_names", [])]


def _is_selected_subset_documentation(metadata: dict[str, Any], names: list[str]) -> bool:
    summary = metadata.get("excluded_feature_summary") or {}
    input_count = summary.get("input_feature_count") or summary.get("usable_feature_count")
    if input_count and names and len(names) < int(input_count):
        return True
    feature_count = metadata.get("feature_count")
    if feature_count and names and len(names) < int(feature_count):
        # metadata feature_count is often selected-feature count from SelectKBest
        reconstructed = _reconstruct_from_metadata_hint(metadata)
        if reconstructed and len(names) < len(reconstructed):
            return True
    return False


def get_model_input_feature_names(model: Any, metadata: dict[str, Any]) -> list[str]:
    """
    Resolve fit-time sklearn Pipeline input columns.

    metadata['feature_names'] is documentation for selected features and must not
    be used for prediction alignment unless all higher-priority sources fail.
    """
    # Priority 1: fitted sklearn Pipeline attribute
    if hasattr(model, "feature_names_in_"):
        names_in = getattr(model, "feature_names_in_", None)
        if names_in is not None and len(names_in) > 0:
            return [str(n) for n in list(names_in)]

    # Priority 2: first pipeline step with feature_names_in_
    if hasattr(model, "steps"):
        for _, step in model.steps:
            if hasattr(step, "feature_names_in_"):
                step_names = getattr(step, "feature_names_in_", None)
                if step_names is not None and len(step_names) > 0:
                    return [str(n) for n in list(step_names)]

    # Priority 3: explicit metadata input names
    for key in ("input_feature_names", "training_input_feature_names", "fit_feature_names"):
        if metadata.get(key):
            return [str(n) for n in list(metadata[key])]

    # Priority 4: reconstruct full pre-selection schema from feature_set hints
    reconstructed = _reconstruct_from_metadata_hint(metadata)
    if reconstructed:
        return reconstructed

    # Last fallback only (and never when clearly a selected-feature doc list)
    doc_names = _metadata_doc_feature_names(metadata)
    if doc_names and not _is_selected_subset_documentation(metadata, doc_names):
        return doc_names

    if doc_names and _is_selected_subset_documentation(metadata, doc_names):
        # Do not align to selected subset when fit-time schema can be reconstructed.
        retry = _reconstruct_from_metadata_hint(metadata)
        if retry:
            return retry

    return doc_names


def load_model_artifact(model_key: str):
    if model_key not in ACTIVE_KEYS:
        raise ValueError(f"Unknown active model key: {model_key}")
    artifact = _resolve_artifact(_paths_config()[model_key])
    if not artifact.is_file():
        raise FileNotFoundError(f"Model artifact missing: {artifact}")
    meta = load_model_metadata(model_key)
    validate_metadata_for_inference(meta)
    return joblib.load(artifact), meta


@lru_cache(maxsize=1)
def load_all_active_models() -> dict[str, dict[str, Any]]:
    """Load active joblib models once per process (release app cache)."""
    out: dict[str, dict[str, Any]] = {}
    for key in ACTIVE_KEYS:
        model, meta = load_model_artifact(key)
        validate_metadata_for_inference(meta)
        out[key] = {
            "model": model,
            "metadata": meta,
            "artifact_path": str(_resolve_artifact(_paths_config()[key])),
            "input_feature_names_resolved": get_model_input_feature_names(model, meta),
        }
    return out


def clear_active_model_cache() -> None:
    """Test/diagnostic hook — normally not needed in release app."""
    load_all_active_models.cache_clear()
