"""Release model loader skeleton."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .utils import read_yaml_safe


def load_model_metadata(config_path: str = "release/config/runtime_config.yaml") -> dict[str, Any]:
    return read_yaml_safe(config_path) or {}


def validate_model_status(metadata: dict[str, Any]) -> tuple[bool, str]:
    status = metadata.get("status")
    if status != "experimental_forensic_prototype":
        return False, "Rejected: model/runtime status must be experimental_forensic_prototype"
    return True, "status accepted"


def load_release_model(model_path: str, metadata: dict[str, Any]):
    ok, msg = validate_model_status(metadata)
    if not ok:
        raise ValueError(msg)
    path = Path(model_path)
    if not path.exists():
        return None
    # TODO(Phase 9B/9C): load artifact via joblib/torch with strict metadata checks.
    return {"model_path": model_path, "loaded": False, "note": "skeleton"}
