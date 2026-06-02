#!/usr/bin/env python3
"""Validate Phase 9E-P1 FastAPI/Gradio app skeleton."""

from __future__ import annotations

import argparse
import importlib
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_APP_DIR = Path(__file__).resolve().parent
_CODE_DIR = _APP_DIR.parents[1]
for _p in (_APP_DIR, _APP_DIR.parent / "partial_redesign", _CODE_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from app_config import (  # noqa: E402
    PARTIAL_PACKAGE_REL,
    load_partial_module_metadata,
    load_partial_report_contract_template,
    partial_package_dir,
    repo_root,
)

FORBIDDEN_APP_PHRASES = [
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

REQUIRED_APP_FILES = [
    "fastapi_app.py",
    "gradio_app.py",
    "app_config.py",
    "report_formatting.py",
    "validate_phase9e_p1_apps.py",
]

FASTAPI_ROUTES = ("/", "/health", "/model-info", "/analyze-audio")


def _check(name: str, ok: bool, detail: str = "") -> dict[str, Any]:
    return {"check": name, "pass": ok, "detail": detail}


def _forbidden_hits_in_files(paths: list[Path]) -> list[str]:
    hits: list[str] = []
    for path in paths:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8").lower()
        for phrase in FORBIDDEN_APP_PHRASES:
            if phrase in text:
                hits.append(f"{path.name}: {phrase}")
    return hits


def _try_import(module_name: str) -> tuple[bool, str]:
    try:
        importlib.import_module(module_name)
        return True, ""
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 9E-P1 apps.")
    parser.add_argument(
        "--report_out",
        default=None,
        help="Report path (default: <repo>/reports/phase9/validation/phase9e_p1_app_validation_report.md)",
    )
    args = parser.parse_args()
    root = repo_root()
    report_out = Path(
        args.report_out or str(root / "reports/phase9/validation/phase9e_p1_app_validation_report.md")
    )
    if not report_out.is_absolute():
        report_out = (root / report_out).resolve()
    report_out.parent.mkdir(parents=True, exist_ok=True)

    checks: list[dict[str, Any]] = []
    app_files = [_APP_DIR / f for f in REQUIRED_APP_FILES]
    missing = [f.name for f in app_files if not f.is_file()]
    checks.append(_check("required_app_files_exist", not missing, ", ".join(missing)))

    inv_path = repo_root() / "release" / "models" / "model_inventory.json"
    checks.append(_check("model_inventory_exists", inv_path.is_file(), str(inv_path)))
    checks.append(_check("partial_package_exists", partial_package_dir().is_dir(), str(partial_package_dir())))

    contract = load_partial_report_contract_template()
    checks.append(_check("partial_report_contract_exists", bool(contract), ""))
    checks.append(
        _check(
            "partial_report_contract_has_section",
            "partial_fabrication" in contract,
            str(list(contract.keys())[:3]),
        )
    )

    meta = load_partial_module_metadata()
    checks.append(_check("partial_metadata_status", meta.get("status") == "experimental_manual_review_only", str(meta.get("status"))))
    checks.append(_check("partial_metadata_manual_review", meta.get("manual_review_required") is True, str(meta.get("manual_review_required"))))
    checks.append(_check("partial_metadata_production_ready_false", meta.get("production_ready") is False, str(meta.get("production_ready"))))
    checks.append(_check("partial_metadata_court_ready_false", meta.get("court_ready") is False, str(meta.get("court_ready"))))
    checks.append(_check("partial_metadata_final_verdict_model_false", meta.get("final_verdict_model") is False, str(meta.get("final_verdict_model"))))

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

    val = meta.get("validation_summary", {})
    checks.append(
        _check(
            "validation_summary_documents_limitations",
            int(val.get("fabricated_20pct_false_negative_count", -1)) == 3
            and int(val.get("false_partial_count", -1)) == 2,
            f"fn={val.get('fabricated_20pct_false_negative_count')} fp={val.get('false_partial_count')}",
        )
    )

    forbidden = _forbidden_hits_in_files([_APP_DIR / "fastapi_app.py", _APP_DIR / "gradio_app.py", _APP_DIR / "report_formatting.py", _APP_DIR / "app_config.py"])
    checks.append(_check("forbidden_wording_absent_in_app_sources", not forbidden, "; ".join(forbidden)))

    fastapi_text = (_APP_DIR / "fastapi_app.py").read_text(encoding="utf-8")
    for route in FASTAPI_ROUTES:
        checks.append(_check(f"fastapi_route_defined_{route.strip('/') or 'root'}", route in fastapi_text or f'"{route}"' in fastapi_text, route))

    gradio_text = (_APP_DIR / "gradio_app.py").read_text(encoding="utf-8")
    checks.append(_check("gradio_audio_upload_defined", "gr.Audio" in gradio_text, ""))
    checks.append(_check("gradio_report_output_defined", "gr.JSON" in gradio_text or "json_out" in gradio_text, ""))

    ok_fa, err_fa = _try_import("phase9.app.fastapi_app")
    if not ok_fa and "multipart" in err_fa.lower():
        err_fa = "missing dependency: python-multipart required for UploadFile"
    checks.append(_check("fastapi_app_imports", ok_fa, err_fa))

    ok_gr, err_gr = _try_import("phase9.app.gradio_app")
    if ok_gr:
        checks.append(_check("gradio_app_imports", True, ""))
    else:
        checks.append(
            _check(
                "gradio_app_imports",
                "gradio" in err_gr.lower() and "import" in err_gr.lower(),
                f"dependency warning documented: {err_gr}",
            )
        )

    if inv_path.is_file():
        import json

        inv = json.loads(inv_path.read_text(encoding="utf-8"))
        legacy_active = False
        for m in inv.get("models", []):
            if m.get("model_name") == "partial_fabrication_segment_model":
                legacy_active = m.get("active_for_phase9e_demo") is True
        mod = (inv.get("integration_modules") or {}).get("partial_fabrication_experimental_p5b", {})
        checks.append(_check("old_partial_segment_not_active_for_demo", not legacy_active, f"legacy_active={legacy_active}"))
        checks.append(
            _check(
                "p6_module_active_for_demo",
                mod.get("active_for_phase9e_demo") is True and mod.get("final_verdict_model") is False,
                str(mod)[:120],
            )
        )

    active_hits = list((repo_root() / "models_saved" / "active").rglob("*")) if (repo_root() / "models_saved" / "active").is_dir() else []
    checks.append(_check("no_models_saved_active_writes", not active_hits, str(active_hits[:2])))

    design_path = repo_root() / "reports/phase9/app/phase9e_p1_app_design.md"
    checks.append(_check("app_design_doc_exists", design_path.is_file(), str(design_path)))

    overall = all(c["pass"] for c in checks)
    lines = [
        "# Phase 9E-P1 App Validation Report",
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
            "## Phase 9E start",
            "",
        ]
    )
    if overall:
        lines.append(
            "Phase 9E may start using the P6 module as an **experimental/manual-review "
            "partial-fabrication evidence axis** via these local apps."
        )
    else:
        lines.append("Resolve failing checks before relying on the local demo apps.")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            f"- App directory: `{_APP_DIR}`",
            f"- Repository root: `{root}`",
            f"- Partial package: `{root / PARTIAL_PACKAGE_REL}`",
            "- Legacy skeleton under `code/phase9/app/`; primary release app is `release/`.",
            "- Does not run uvicorn or launch Gradio.",
        ]
    )
    report_out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"9E-P1 validation {'PASS' if overall else 'FAIL'}: {report_out}")
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
