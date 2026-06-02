#!/usr/bin/env python3
"""Phase 9E-P1 FastAPI local demo over Phase 9C inference + P6 partial contract."""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

_APP_DIR = Path(__file__).resolve().parent
for _p in (_APP_DIR, _APP_DIR.parent / "partial_redesign"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from fastapi import FastAPI, File, Query, UploadFile

from app_config import (
    APP_NAME,
    APP_PHASE,
    check_phase9c_models_available,
    get_analyze_audio_file,
    load_model_inventory,
    load_partial_module_metadata,
    load_partial_validation_summary,
    partial_package_dir,
    repo_root,
    safety_banner,
)
from report_formatting import build_app_analyze_response

app = FastAPI(
    title=APP_NAME,
    version="phase9e-p1",
    description="Experimental forensic evidence demo — manual review required.",
)

_models_checked = False
_models_ok = False
_models_err = ""


def _ensure_models_checked() -> None:
    global _models_checked, _models_ok, _models_err
    if not _models_checked:
        _models_ok, _models_err = check_phase9c_models_available()
        _models_checked = True


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "app_name": APP_NAME,
        "phase": APP_PHASE,
        "status": "experimental_forensic_demo",
        "endpoints": ["/", "/health", "/model-info", "/analyze-audio"],
        "safety": safety_banner(),
        "documentation": "reports/phase9/app/phase9e_p1_app_design.md",
    }


@app.get("/health")
def health() -> dict[str, Any]:
    _ensure_models_checked()
    meta = load_partial_module_metadata()
    return {
        "status": "ok",
        "phase": APP_PHASE,
        "models_loaded": _models_ok,
        "models_load_error": _models_err if not _models_ok else "",
        "partial_module_status": meta.get("status", "experimental_manual_review_only"),
        "manual_review_required": bool(meta.get("manual_review_required", True)),
        "conclusive_authenticity_decision": False,
    }


@app.get("/model-info")
def model_info() -> dict[str, Any]:
    _ensure_models_checked()
    meta = load_partial_module_metadata()
    inv = load_model_inventory()
    val = load_partial_validation_summary()
    return {
        "phase": APP_PHASE,
        "models_loaded": _models_ok,
        "model_inventory_summary": {
            "status": inv.get("status"),
            "model_count": len(inv.get("models", [])),
            "integration_modules": list((inv.get("integration_modules") or {}).keys()),
            "warnings": inv.get("warnings", [])[:5],
        },
        "partial_fabrication_experimental_p5b": {
            "package_path": str(partial_package_dir()),
            "metadata": meta,
            "thresholds": meta.get("thresholds", {}),
            "limitations": meta.get("limitations", []),
            "validation_summary": val,
        },
        "manual_review_required": True,
        "conclusive_authenticity_decision": False,
        "operational_deployment_claim": False,
        "legal_evidence_claim": False,
        "safety": safety_banner(),
    }


@app.post("/analyze-audio")
async def analyze_audio(
    audio_file: UploadFile = File(...),
    return_top_segments: bool = Query(default=True),
    save_report: bool = Query(default=False),
) -> dict[str, Any]:
    _ensure_models_checked()
    if not _models_ok:
        return {
            "processing_status": "error",
            "error_message": f"Phase 9C models not loaded: {_models_err}",
            "manual_review_required": True,
            "partial_fabrication": {
                "module_status": "experimental_manual_review_only",
                "evidence_label": "partial_fabrication_analysis_unavailable",
                "user_facing_message": (
                    "Partial-fabrication analysis was unavailable for this file. "
                    "Manual forensic review is recommended if partial manipulation is suspected."
                ),
            },
        }

    suffix = Path(audio_file.filename or "upload.wav").suffix or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(audio_file.file, tmp)
        tmp_path = Path(tmp.name)

    analyze_fn = get_analyze_audio_file()
    save_path: str | None = None
    output_dir = None
    if save_report:
        output_dir = repo_root() / "reports" / "phase9" / "app" / "sample_outputs"
        output_dir.mkdir(parents=True, exist_ok=True)

    try:
        phase9c = analyze_fn(
            audio_path=str(tmp_path),
            output_dir=output_dir,
            device="auto",
            return_debug=return_top_segments,
        )
        if save_report and output_dir and phase9c.get("case_id"):
            save_path = str(output_dir / f"{phase9c['case_id']}_analysis.json")
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass

    return build_app_analyze_response(
        file_name=audio_file.filename or tmp_path.name,
        phase9c_result=phase9c,
        return_top_segments=return_top_segments,
        save_report_path=save_path,
    )
