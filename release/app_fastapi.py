"""Phase 9A FastAPI skeleton for experimental forensic prototype."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, File, Form, UploadFile

from src.inference_pipeline import run_inference_pipeline

app = FastAPI(title="Audio Forensic Prototype API", version="phase9a-skeleton")


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "Phase 9A release skeleton",
        "status": "experimental_forensic_prototype",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "skeleton_only"}


@app.get("/model-info")
def model_info() -> dict[str, Any]:
    return {
        "status": "experimental_forensic_prototype",
        "message": "Model packaging pending Phase 9B",
        "models": {
            "origin": "pending_artifact",
            "replay": "pending_artifact",
            "mixer": "pending_artifact",
            "partial_segment": "pending_artifact",
        },
    }


@app.post("/analyze-audio")
async def analyze_audio(
    audio_file: UploadFile = File(...), case_id: str | None = Form(default=None)
) -> dict[str, Any]:
    # Phase 9A: placeholder route. Full live inference is out of scope.
    return run_inference_pipeline(audio_path=audio_file.filename or "", case_id=case_id)
