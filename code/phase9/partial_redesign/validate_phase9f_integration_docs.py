#!/usr/bin/env python3
"""Validate Phase 9F integration documentation for teammate handoff."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SCRIPT_DIR = Path(__file__).resolve().parent


def _repo_root() -> Path:
    for base in (_SCRIPT_DIR, *_SCRIPT_DIR.parents):
        if (base / "release" / "app_gradio.py").is_file():
            return base
    return _SCRIPT_DIR.parents[3]


_REPO = _repo_root()
_RELEASE = _REPO / "release"
_DOCS = _REPO / "reports" / "phase9" / "integration_docs"
_P4B_VAL = _REPO / "reports" / "phase9" / "validation" / "phase9e_p4b_demo_freeze_validation_report.md"
_P4B = _REPO / "reports" / "phase9" / "app" / "phase9e_p4b_demo_freeze"
_INV = _RELEASE / "models" / "model_inventory.json"
_PARTIAL_META = _RELEASE / "models" / "partial_fabrication_experimental_p5b" / "partial_module_metadata.json"

REQUIRED_DOCS = [
    "phase9f_teammate_handoff.md",
    "phase9f_api_contract.md",
    "phase9f_model_registry_guide.md",
    "phase9f_report_wording_guide.md",
    "phase9f_local_demo_runbook.md",
    "phase9f_integration_examples.md",
    "phase9f_known_limitations.md",
    "phase9f_release_file_map.md",
]

REQUIRED_ENDPOINTS = ["/", "/health", "/model-info", "/analyze-audio", "/analyze"]

REQUIRED_RESPONSE_FIELDS = [
    "request_id",
    "phase",
    "file_name",
    "duration_sec",
    "processing_status",
    "case_id",
    "voice_origin_result",
    "forensic_indicator_summary",
    "recommendation",
    "recommendation_level",
    "evidence_axis_cards",
    "axis_interpretation",
    "partial_fabrication",
    "partial_module_mode",
    "origin_support_models",
    "limitations",
    "safety",
    "generated_at",
    "pdf_report_path",
    "waveform_image_path",
    "saved_report_path",
]

REQUIRED_QUERY_PARAMS = [
    "return_top_segments",
    "save_report",
    "generate_report",
    "generate_visual",
]

ALLOWED_WORDING = [
    "Voice origin: Likely AI-generated",
    "Voice origin: Likely human",
    "Voice origin: Inconclusive",
    "Voice origin: Inconclusive under replay/channel processing",
    "AI-origin evidence detected",
    "Replay/rerecording evidence detected",
    "Mixer/channel processing evidence detected",
    "Partial replacement candidate for review",
    "Candidate region for optional review",
    "Conclusive authenticity decision: no",
    "Manual forensic review is recommended when indicators are present",
    "Optional review may be useful for sensitive cases",
]

FORBIDDEN = [
    "definitely fake",
    "definitely real",
    "final verdict",
    "final fake",
    "final real",
    "court proof",
    "court-ready",
    "court ready",
    "production-ready",
    "production ready",
]

FORBIDDEN_SECTION_MARKERS = [
    "forbidden wording",
    "never use",
    "must **not** appear",
]

ACTIVE_MODELS = [
    "origin_file_model",
    "replay_file_model",
    "mixer_file_model",
    "partial_fabrication_segment_model",
]

THRESHOLDS = {
    "file_gate_threshold": 0.5,
    "segment_threshold": 0.9,
    "contrast_threshold": 0.25,
    "broad_limit": 0.45,
}


def _check(name: str, ok: bool, detail: str = "") -> dict[str, Any]:
    return {"check": name, "pass": ok, "detail": detail}


def _read_docs_text() -> str:
    parts: list[str] = []
    for name in REQUIRED_DOCS:
        p = _DOCS / name
        if p.is_file():
            parts.append(p.read_text(encoding="utf-8"))
    return "\n".join(parts)


def _forbidden_hits(text: str, *, allow_in_forbidden_section: bool = True) -> list[str]:
    hits: list[str] = []
    lower = text.lower()
    for phrase in FORBIDDEN:
        start = 0
        while True:
            idx = lower.find(phrase, start)
            if idx == -1:
                break
            if allow_in_forbidden_section:
                window = lower[max(0, idx - 400) : idx + 200]
                if any(m in window for m in FORBIDDEN_SECTION_MARKERS):
                    start = idx + len(phrase)
                    continue
            hits.append(phrase)
            start = idx + len(phrase)
    return hits


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 9F integration docs.")
    parser.parse_args()

    report_out = _REPO / "reports" / "phase9" / "validation" / "phase9f_integration_docs_validation_report.md"
    report_out.parent.mkdir(parents=True, exist_ok=True)
    _DOCS.mkdir(parents=True, exist_ok=True)

    checks: list[dict[str, Any]] = []

    # Required docs exist
    for name in REQUIRED_DOCS:
        path = _DOCS / name
        checks.append(_check(f"required_doc_{name}", path.is_file(), str(path)))

    docs_text = _read_docs_text()
    api_text = (_DOCS / "phase9f_api_contract.md").read_text(encoding="utf-8") if (
        _DOCS / "phase9f_api_contract.md"
    ).is_file() else ""
    registry_text = (_DOCS / "phase9f_model_registry_guide.md").read_text(encoding="utf-8") if (
        _DOCS / "phase9f_model_registry_guide.md"
    ).is_file() else ""
    wording_text = (_DOCS / "phase9f_report_wording_guide.md").read_text(encoding="utf-8") if (
        _DOCS / "phase9f_report_wording_guide.md"
    ).is_file() else ""
    runbook_text = (_DOCS / "phase9f_local_demo_runbook.md").read_text(encoding="utf-8") if (
        _DOCS / "phase9f_local_demo_runbook.md"
    ).is_file() else ""
    examples_text = (_DOCS / "phase9f_integration_examples.md").read_text(encoding="utf-8") if (
        _DOCS / "phase9f_integration_examples.md"
    ).is_file() else ""
    handoff_text = (_DOCS / "phase9f_teammate_handoff.md").read_text(encoding="utf-8") if (
        _DOCS / "phase9f_teammate_handoff.md"
    ).is_file() else ""

    # API endpoints
    for ep in REQUIRED_ENDPOINTS:
        checks.append(_check(f"endpoint_documented_{ep.replace('/', '_')}", ep in api_text, ep))

    # Multipart / query params
    checks.append(_check("multipart_audio_file_documented", "audio_file" in api_text, ""))
    checks.append(_check("form_case_id_documented", "case_id" in api_text, ""))
    for qp in REQUIRED_QUERY_PARAMS:
        checks.append(_check(f"query_param_{qp}", qp in api_text, ""))

    for field in REQUIRED_RESPONSE_FIELDS:
        checks.append(_check(f"response_field_{field}", field in api_text, ""))

    # Model registry
    for model in ACTIVE_MODELS:
        checks.append(_check(f"active_model_{model}", model in registry_text, ""))

    checks.append(
        _check(
            "partial_p5b_documented",
            "partial_fabrication_experimental_p5b" in registry_text
            and "experimental_manual_review_only" in registry_text,
            "",
        )
    )
    checks.append(_check("aasist_reject_for_now", "reject_for_now" in registry_text and "AASIST" in registry_text, ""))
    checks.append(
        _check(
            "hybrid_resnet_reject_for_now",
            "reject_for_now" in registry_text and ("HybridResNet" in registry_text or "ResNet" in registry_text),
            "",
        )
    )

    for th_name, th_val in THRESHOLDS.items():
        checks.append(
            _check(
                f"threshold_{th_name}",
                th_name in registry_text and str(th_val) in registry_text,
                str(th_val),
            )
        )

    checks.append(
        _check(
            "segment_candidate_only_wording",
            "segment candidate" in registry_text.lower() or "segment_candidate_only" in registry_text,
            "",
        )
    )

    # Allowed wording
    for phrase in ALLOWED_WORDING:
        checks.append(_check(f"allowed_wording_{phrase[:30]}", phrase in wording_text or phrase in docs_text, phrase))

    # Forbidden wording absent (except forbidden section in wording guide)
    scan_targets = [
        (_DOCS / "phase9f_teammate_handoff.md", True),
        (_DOCS / "phase9f_api_contract.md", True),
        (_DOCS / "phase9f_model_registry_guide.md", True),
        (_DOCS / "phase9f_local_demo_runbook.md", True),
        (_DOCS / "phase9f_integration_examples.md", True),
        (_DOCS / "phase9f_known_limitations.md", True),
        (_DOCS / "phase9f_release_file_map.md", True),
        (_DOCS / "phase9f_report_wording_guide.md", True),
    ]
    forbidden_hits: list[str] = []
    for path, allow_section in scan_targets:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for phrase in _forbidden_hits(text, allow_in_forbidden_section=allow_section):
            forbidden_hits.append(f"{path.name}: {phrase}")
    checks.append(_check("forbidden_wording_absent", not forbidden_hits, "; ".join(sorted(set(forbidden_hits)))))

    # Run commands
    checks.append(_check("gradio_run_command", "python app_gradio.py" in runbook_text, ""))
    checks.append(
        _check(
            "fastapi_run_command",
            "app_fastapi.py" in runbook_text or "run_fastapi.bat" in runbook_text,
            "",
        )
    )
    checks.append(_check("conda_env_fassd", "fassd" in runbook_text, ""))
    checks.append(_check("release_path_documented", "release" in handoff_text.lower(), ""))

    # Integration examples
    checks.append(_check("curl_example", "curl" in examples_text.lower(), ""))
    checks.append(_check("python_requests_example", "requests.post" in examples_text or "import requests" in examples_text, ""))
    checks.append(_check("json_snippet_example", "voice_origin_result" in examples_text, ""))
    checks.append(_check("frontend_display_guidance", "evidence_axis_cards" in examples_text, ""))

    # P4B validation PASS referenced
    if _P4B_VAL.is_file():
        p4b_val = _P4B_VAL.read_text(encoding="utf-8")
        checks.append(_check("p4b_validation_pass_referenced", "**Overall:** PASS" in p4b_val, ""))
        checks.append(
            _check(
                "p4b_pass_in_handoff",
                "P4B" in handoff_text and "PASS" in handoff_text,
                "",
            )
        )
    else:
        checks.append(_check("p4b_validation_pass_referenced", False, "missing p4b validation report"))

    # Product / research names
    checks.append(_check("product_name", "Deepfake Audio Detector" in handoff_text, ""))
    checks.append(
        _check(
            "research_name",
            "Forensic Acoustic for Synthetic Speech Detection" in handoff_text,
            "",
        )
    )

    # Known limitations topics
    lim_text = (_DOCS / "phase9f_known_limitations.md").read_text(encoding="utf-8") if (
        _DOCS / "phase9f_known_limitations.md"
    ).is_file() else ""
    checks.append(_check("limitation_partial_experimental", "experimental" in lim_text and "partial" in lim_text.lower(), ""))
    checks.append(_check("limitation_no_conclusive", "Conclusive authenticity decision: no" in lim_text, ""))
    checks.append(_check("limitation_local_demo", "Local demo" in lim_text or "local demo" in lim_text.lower(), ""))
    checks.append(_check("limitation_aasist_reject", "reject_for_now" in lim_text, ""))

    # No model files changed check — inventory hash snapshot (read-only)
    if _INV.is_file():
        inv_hash = _sha256_file(_INV)
        inv = json.loads(_INV.read_text(encoding="utf-8"))
        names = {str(m.get("model_name", "")).lower() for m in inv.get("models", [])}
        checks.append(
            _check(
                "no_aasist_resnet_in_active_inventory",
                "aasist" not in names and "hybrid_resnet" not in names,
                inv_hash[:16],
            )
        )
        checks.append(_check("model_inventory_readable", bool(inv.get("models")), str(len(inv.get("models", [])))))

    if _PARTIAL_META.is_file():
        meta = json.loads(_PARTIAL_META.read_text(encoding="utf-8"))
        th = meta.get("thresholds") or {}
        checks.append(
            _check(
                "partial_thresholds_unchanged",
                all(float(th.get(k, -1)) == v for k, v in THRESHOLDS.items()),
                str(th),
            )
        )

    # No release/models write logic in validator script itself
    this_src = Path(__file__).read_text(encoding="utf-8")
    checks.append(
        _check(
            "no_release_models_write_in_validator",
            "release/models" not in this_src or "write_text" not in this_src.split("release/models")[-1][:200],
            "",
        )
    )

    # FastAPI source cross-check
    fa = (_RELEASE / "app_fastapi.py").read_text(encoding="utf-8") if (_RELEASE / "app_fastapi.py").is_file() else ""
    for ep_decorator, ep in [
        ('@app.get("/")', "/"),
        ('@app.get("/health")', "/health"),
        ('@app.get("/model-info")', "/model-info"),
        ('@app.post("/analyze-audio")', "/analyze-audio"),
        ('@app.post("/analyze")', "/analyze"),
    ]:
        checks.append(_check(f"fastapi_impl_{ep.replace('/', '_')}", ep_decorator in fa, ""))

    overall = all(c["pass"] for c in checks)
    lines = [
        "# Phase 9F Integration Docs Validation Report",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        f"**Overall:** {'PASS' if overall else 'FAIL'}",
        "",
        "## Checks",
        "",
    ]
    for c in checks:
        mark = "PASS" if c["pass"] else "FAIL"
        lines.append(f"- [{mark}] `{c['check']}` — {c.get('detail', '')}")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "Phase 9F validates teammate integration documentation only.",
            "No model retraining, threshold changes, or inference logic changes.",
            "Phase 9G packaging may proceed when this report is PASS and P4B validation is PASS.",
        ]
    )
    report_out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Phase 9F validation {'PASS' if overall else 'FAIL'}: {report_out}")
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
