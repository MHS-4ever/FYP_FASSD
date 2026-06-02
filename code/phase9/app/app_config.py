"""
Phase 9E-P1 application configuration: paths, P6 partial module, Phase 9C release roots.
"""

from __future__ import annotations

import json
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

APP_PHASE = "Phase 9E-P1"
APP_NAME = "Forensic Deepfake Audio Detector — Local Demo"
PARTIAL_MODULE_KEY = "partial_fabrication_experimental_p5b"
PARTIAL_PACKAGE_REL = Path("release/models/partial_fabrication_experimental_p5b")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def release_root() -> Path:
    return repo_root() / "release"


def _ensure_release_on_path() -> None:
    rel = release_root()
    if str(rel) not in sys.path:
        sys.path.insert(0, str(rel))


def _ensure_partial_redesign_on_path() -> None:
    pr = repo_root() / "code" / "phase9" / "partial_redesign"
    if str(pr) not in sys.path:
        sys.path.insert(0, str(pr))


@lru_cache(maxsize=1)
def load_model_inventory() -> dict[str, Any]:
    path = repo_root() / "release" / "models" / "model_inventory.json"
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def partial_package_dir() -> Path:
    return (repo_root() / PARTIAL_PACKAGE_REL).resolve()


@lru_cache(maxsize=1)
def load_partial_module_metadata() -> dict[str, Any]:
    path = partial_package_dir() / "partial_module_metadata.json"
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_partial_report_contract_template() -> dict[str, Any]:
    path = partial_package_dir() / "partial_report_contract.json"
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_partial_validation_summary() -> dict[str, Any]:
    path = partial_package_dir() / "partial_validation_summary.json"
    if not path.is_file():
        meta = load_partial_module_metadata()
        return dict(meta.get("validation_summary", {}))
    return json.loads(path.read_text(encoding="utf-8"))


def check_phase9c_models_available() -> tuple[bool, str]:
    """Try loading active Phase 9C models (origin/replay/mixer/partial_segment)."""
    try:
        _ensure_release_on_path()
        from src.model_loader import load_all_active_models  # type: ignore

        load_all_active_models()
        return True, ""
    except Exception as exc:
        return False, str(exc)


def get_analyze_audio_file():
    _ensure_release_on_path()
    from src.inference_pipeline import analyze_audio_file  # type: ignore

    return analyze_audio_file


def safety_banner() -> dict[str, str]:
    return {
        "app_status": "experimental_forensic_demo",
        "partial_module_status": "experimental_manual_review_only",
        "manual_review_required": "true",
        "conclusive_authenticity_decision": "no",
        "operational_deployment_claim": "no",
        "legal_evidence_claim": "no",
        "wording": (
            "Experimental forensic evidence indicators only. "
            "Manual forensic review is recommended. "
            "Conclusive authenticity decision: no."
        ),
    }
