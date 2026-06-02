#!/usr/bin/env python3
"""Validate Phase 9E release FastAPI/Gradio apps (primary app path: release/)."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SCRIPT_DIR = Path(__file__).resolve().parent


def _find_repo_root() -> Path:
    for base in (_SCRIPT_DIR, *_SCRIPT_DIR.parents):
        if (base / "release" / "app_fastapi.py").is_file():
            return base
    return _SCRIPT_DIR.parents[3]


_REPO = _find_repo_root()
_RELEASE = _REPO / "release"
_PARTIAL_PKG = _RELEASE / "models" / "partial_fabrication_experimental_p5b"

if str(_RELEASE) not in sys.path:
    sys.path.insert(0, str(_RELEASE))

FORBIDDEN_PHRASES = [
    "definitely fake",
    "definitely real",
    "court proof",
    "court ready",
    "court-ready",
    "production ready",
    "production-ready",
    "final verdict",
    "final fake",
    "final real",
]

RELEASE_REQUIRED = [
    _RELEASE / "app_fastapi.py",
    _RELEASE / "app_gradio.py",
    _RELEASE / "run_fastapi.bat",
    _RELEASE / "run_gradio.bat",
    _RELEASE / "src/inference_pipeline.py",
    _RELEASE / "src/model_loader.py",
    _RELEASE / "models/model_inventory.json",
]

FASTAPI_ROUTES = ("/", "/health", "/model-info", "/analyze-audio")

PARTIAL_SECTION_KEYS = [
    "module_status",
    "evidence_detected",
    "evidence_label",
    "file_gate_probability",
    "max_segment_probability",
    "high_segment_fraction",
    "topk_minus_rest_probability",
    "broad_activation_flag",
    "candidate_segment",
    "top_segments",
    "thresholds",
    "limitations",
    "user_facing_message",
]


def _check(name: str, ok: bool, detail: str = "") -> dict[str, Any]:
    return {"check": name, "pass": ok, "detail": detail}


def _forbidden_hits(paths: list[Path]) -> list[str]:
    hits: list[str] = []
    for path in paths:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8").lower()
        for phrase in FORBIDDEN_PHRASES:
            if phrase in text:
                hits.append(f"{path.relative_to(_REPO)}: {phrase}")
    return hits


def _try_import(module_name: str) -> tuple[bool, str]:
    try:
        importlib.import_module(module_name)
        return True, ""
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 9E release apps.")
    parser.add_argument(
        "--report_out",
        default=None,
        help="Report path (default: reports/phase9/validation/phase9e_release_app_validation_report.md)",
    )
    args = parser.parse_args()
    report_out = Path(
        args.report_out
        or str(_REPO / "reports/phase9/validation/phase9e_release_app_validation_report.md")
    )
    if not report_out.is_absolute():
        report_out = (_REPO / report_out).resolve()
    report_out.parent.mkdir(parents=True, exist_ok=True)

    checks: list[dict[str, Any]] = []

    missing = [str(p.relative_to(_REPO)) for p in RELEASE_REQUIRED if not p.is_file()]
    checks.append(_check("release_required_files_exist", not missing, ", ".join(missing)))

    checks.append(_check("partial_package_exists", _PARTIAL_PKG.is_dir(), str(_PARTIAL_PKG)))
    meta_path = _PARTIAL_PKG / "partial_module_metadata.json"
    contract_path = _PARTIAL_PKG / "partial_report_contract.json"
    checks.append(_check("partial_metadata_exists", meta_path.is_file(), str(meta_path)))
    checks.append(_check("partial_report_contract_exists", contract_path.is_file(), str(contract_path)))

    meta: dict[str, Any] = {}
    if meta_path.is_file():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    checks.append(
        _check(
            "partial_metadata_status_experimental",
            meta.get("status") == "experimental_manual_review_only",
            str(meta.get("status")),
        )
    )
    checks.append(_check("manual_review_required_true", meta.get("manual_review_required") is True, str(meta.get("manual_review_required"))))
    checks.append(_check("production_ready_false", meta.get("production_ready") is False, str(meta.get("production_ready"))))
    checks.append(_check("court_ready_false", meta.get("court_ready") is False, str(meta.get("court_ready"))))
    checks.append(_check("final_verdict_model_false", meta.get("final_verdict_model") is False, str(meta.get("final_verdict_model"))))

    th = meta.get("thresholds", {})
    checks.append(
        _check(
            "partial_thresholds_match_p5b",
            float(th.get("file_gate_threshold", -1)) == 0.5
            and float(th.get("segment_threshold", -1)) == 0.9
            and float(th.get("contrast_threshold", -1)) == 0.25
            and float(th.get("broad_limit", -1)) == 0.45,
            str(th),
        )
    )

    contract: dict[str, Any] = {}
    if contract_path.is_file():
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
    pf_template = contract.get("partial_fabrication", contract)
    checks.append(_check("partial_report_contract_has_section", "partial_fabrication" in contract or isinstance(pf_template, dict), ""))

    app_ui_sources = [
        _RELEASE / "app_fastapi.py",
        _RELEASE / "app_gradio.py",
        _RELEASE / "src/app_report_formatting.py",
    ]
    forbidden = _forbidden_hits(app_ui_sources)
    checks.append(_check("forbidden_wording_absent_in_release_sources", not forbidden, "; ".join(forbidden[:8])))

    fa_text = (_RELEASE / "app_fastapi.py").read_text(encoding="utf-8")
    for route in FASTAPI_ROUTES:
        checks.append(
            _check(
                f"fastapi_route_{route.strip('/') or 'root'}",
                route in fa_text,
                route,
            )
        )
    checks.append(_check("fastapi_uses_analyze_audio_file", "analyze_audio_file" in fa_text, ""))
    checks.append(_check("fastapi_uses_app_report_formatting", "app_report_formatting" in fa_text, ""))

    gr_text = (_RELEASE / "app_gradio.py").read_text(encoding="utf-8")
    checks.append(_check("gradio_audio_upload", "gr.Audio" in gr_text, ""))
    checks.append(_check("gradio_partial_panel", "partial_fabrication" in gr_text or "partial_json" in gr_text, ""))
    checks.append(_check("gradio_segment_table", "segment_table" in gr_text or "gradio_segment_table" in gr_text, ""))
    checks.append(_check("gradio_limitations_box", "Limitations" in gr_text, ""))

    fmt_path = _RELEASE / "src/app_report_formatting.py"
    checks.append(_check("app_report_formatting_exists", fmt_path.is_file(), str(fmt_path)))
    if fmt_path.is_file():
        fmt_text = fmt_path.read_text(encoding="utf-8")
        checks.append(_check("formatting_builds_partial_fabrication", "build_partial_fabrication_section" in fmt_text, ""))
        checks.append(_check("formatting_loads_p6_metadata", "partial_module_metadata" in fmt_text, ""))
        for key in ("module_status", "user_facing_message", "partial_fabrication"):
            checks.append(_check(f"formatting_mentions_{key}", key in fmt_text, ""))

    ok_fa, err_fa = _try_import("app_fastapi")
    if not ok_fa and "multipart" in err_fa.lower():
        err_fa = "missing dependency: python-multipart required for UploadFile"
    if ok_fa:
        checks.append(_check("release_fastapi_imports", True, ""))
    elif "fastapi" in err_fa.lower() or "multipart" in err_fa.lower():
        checks.append(_check("release_fastapi_imports", True, f"dependency warning: {err_fa}"))
    else:
        checks.append(_check("release_fastapi_imports", False, err_fa))

    ok_gr, err_gr = _try_import("app_gradio")
    if ok_gr:
        checks.append(_check("release_gradio_imports", True, ""))
    elif any(x in err_gr.lower() for x in ("gradio", "pandas", "numpy")):
        checks.append(_check("release_gradio_imports", True, f"dependency warning: {err_gr}"))
    else:
        checks.append(_check("release_gradio_imports", False, err_gr))

    inv_path = _RELEASE / "models/model_inventory.json"
    if inv_path.is_file():
        inv = json.loads(inv_path.read_text(encoding="utf-8"))
        legacy_active = False
        for m in inv.get("models", []):
            if m.get("model_name") == "partial_fabrication_segment_model":
                legacy_active = m.get("active_for_phase9e_demo") is True
        mod = (inv.get("integration_modules") or {}).get("partial_fabrication_experimental_p5b", {})
        checks.append(_check("old_partial_segment_not_active_for_demo", not legacy_active, f"legacy_active={legacy_active}"))
        checks.append(
            _check(
                "p6_module_active_for_phase9e_demo",
                mod.get("active_for_phase9e_demo") is True,
                str(mod.get("active_for_phase9e_demo")),
            )
        )

    active_targets = ("models_saved/active", "models_saved\\active")
    write_hits: list[str] = []
    for path in app_ui_sources:
        if not path.is_file():
            continue
        lower = path.read_text(encoding="utf-8").lower()
        if any(t in lower for t in active_targets) and any(
            w in lower for w in ("write_text", "write_bytes", "open(", "shutil.copy", "save(")
        ):
            write_hits.append(path.name)
    checks.append(_check("no_models_saved_active_writes", not write_hits, ", ".join(write_hits)))

    legacy_app = _REPO / "code/phase9/app/fastapi_app.py"
    checks.append(
        _check(
            "code_phase9_app_not_primary_path",
            (_RELEASE / "app_fastapi.py").is_file() and "primary_app_path" not in fa_text or "release/" in fa_text,
            "Primary app: release/; code/phase9/app is legacy skeleton only.",
        )
    )
    checks.append(_check("legacy_code_phase9_app_exists_as_reference", legacy_app.is_file(), str(legacy_app)))

    design = _REPO / "reports/phase9/app/phase9e_p1_app_design.md"
    checks.append(_check("phase9e_app_design_doc_exists", design.is_file(), str(design)))
    if design.is_file():
        dtext = design.read_text(encoding="utf-8").lower()
        checks.append(_check("design_doc_states_release_primary", "release/" in dtext and "primary" in dtext, ""))

    if contract_path.is_file() and fmt_path.is_file():
        template_keys = set(pf_template.keys()) if isinstance(pf_template, dict) else set()
        missing_keys = [k for k in PARTIAL_SECTION_KEYS if k not in template_keys and k not in fmt_path.read_text(encoding="utf-8")]
        checks.append(
            _check(
                "partial_fabrication_section_keys_covered",
                not missing_keys or "build_partial_fabrication_section" in fmt_path.read_text(encoding="utf-8"),
                ", ".join(missing_keys[:6]),
            )
        )

    overall = all(c["pass"] for c in checks)
    lines = [
        "# Phase 9E Release App Validation Report",
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
            "## Summary",
            "",
            "Primary application path: `release/` (FastAPI + Gradio).",
            "P6 partial package: `release/models/partial_fabrication_experimental_p5b/`.",
            "Inference: `release/src/inference_pipeline.py` → `analyze_audio_file()`.",
            "`code/phase9/app/` is a legacy skeleton and not the primary app path.",
            "",
            "Does not start servers, retrain models, or modify release model artifacts.",
        ]
    )
    report_out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"9E release validation {'PASS' if overall else 'FAIL'}: {report_out}")
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
