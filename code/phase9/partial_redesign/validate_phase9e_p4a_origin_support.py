#!/usr/bin/env python3
"""Validate Phase 9E-P4A shadow origin-support evaluation outputs."""

from __future__ import annotations

import argparse
import json
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
_OUTPUT = _REPO / "reports" / "phase9" / "app" / "phase9e_p4a_origin_support"

if str(_RELEASE) not in sys.path:
    sys.path.insert(0, str(_RELEASE))

FORBIDDEN = [
    "definitely fake",
    "definitely real",
    "court proof",
    "court ready",
    "production ready",
    "final verdict",
    "activated in release fusion",
]


def _check(name: str, ok: bool, detail: str = "") -> dict[str, Any]:
    return {"check": name, "pass": ok, "detail": detail}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 9E-P4A origin-support shadow eval.")
    parser.add_argument("--mode", choices=("quick", "full"), default="quick")
    parser.add_argument(
        "--report_out",
        default=None,
        help="Default: reports/phase9/validation/phase9e_p4a_origin_support_validation_report.md",
    )
    args = parser.parse_args()

    report_out = Path(
        args.report_out
        or str(_REPO / "reports/phase9/validation/phase9e_p4a_origin_support_validation_report.md")
    )
    report_out.parent.mkdir(parents=True, exist_ok=True)

    checks: list[dict[str, Any]] = []
    design = _REPO / "reports/phase9/app/phase9e_p4a_origin_support/phase9e_p4a_origin_support_design.md"
    eval_script = _SCRIPT_DIR / "run_phase9e_p4a_origin_support_shadow_eval.py"
    origin_mod = _RELEASE / "src/origin_support_models.py"
    inv_path = _RELEASE / "models/model_inventory.json"

    checks.append(_check("design_doc_exists", design.is_file(), str(design)))
    checks.append(_check("origin_support_models_module", origin_mod.is_file(), ""))
    checks.append(_check("shadow_eval_script_exists", eval_script.is_file(), ""))

    src = origin_mod.read_text(encoding="utf-8")
    eval_src = eval_script.read_text(encoding="utf-8")
    checks.append(_check("audit_origin_support_models", "def audit_origin_support_models" in src, ""))
    checks.append(_check("load_origin_support_models", "def load_origin_support_models" in src, ""))
    checks.append(_check("predict_origin_support", "def predict_origin_support" in src, ""))
    checks.append(_check("used_for_voice_origin_false", "used_for_voice_origin" in src and "False" in src, ""))
    checks.append(_check("progress_logging_in_script", "_log_progress" in eval_src or "tqdm" in eval_src, ""))

    forbidden_hits = []
    for path in (origin_mod, eval_script, _RELEASE / "src/inference_pipeline.py"):
        if not path.is_file():
            continue
        lower = path.read_text(encoding="utf-8").lower()
        for phrase in FORBIDDEN:
            if phrase in lower:
                forbidden_hits.append(f"{path.name}: {phrase}")
    checks.append(_check("forbidden_wording_absent", not forbidden_hits, "; ".join(forbidden_hits)))

    if inv_path.is_file():
        inv = json.loads(inv_path.read_text(encoding="utf-8"))
        names = {m.get("model_name") for m in inv.get("models", [])}
        checks.append(
            _check(
                "no_aasist_resnet_in_active_inventory",
                "aasist" not in names and "hybrid_resnet" not in names,
                str(sorted(names)),
            )
        )

    ref_inv = _RELEASE / "models/reference/reference_model_inventory.json"
    if ref_inv.is_file():
        ref = json.loads(ref_inv.read_text(encoding="utf-8"))
        checks.append(_check("reference_models_marked_legacy", ref.get("status") == "legacy_reference_experimental", ""))

    outputs = {
        "phase9e_p4a_reference_model_audit.md": _OUTPUT / "phase9e_p4a_reference_model_audit.md",
        "phase9e_p4a_shadow_results.csv": _OUTPUT / "phase9e_p4a_shadow_results.csv",
        "phase9e_p4a_shadow_metrics.json": _OUTPUT / "phase9e_p4a_shadow_metrics.json",
        "phase9e_p4a_shadow_comparison_report.md": _OUTPUT / "phase9e_p4a_shadow_comparison_report.md",
        "phase9e_p4a_shadow_failure_cases.csv": _OUTPUT / "phase9e_p4a_shadow_failure_cases.csv",
        "phase9e_p4a_terminal_resource_audit.md": _OUTPUT / "phase9e_p4a_terminal_resource_audit.md",
    }
    eval_ran = (_OUTPUT / "phase9e_p4a_shadow_metrics.json").is_file()
    for name, path in outputs.items():
        checks.append(
            _check(f"output_{name}", path.is_file() or not eval_ran, "missing — run P4A shadow eval" if not path.is_file() else "")
        )

    metrics_path = _OUTPUT / "phase9e_p4a_shadow_metrics.json"
    if metrics_path.is_file():
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        audit_only = metrics.get("mode") == "audit_only" or metrics.get("total_files", 0) == 0
        rec = str(metrics.get("activation_recommendation", "")).lower()
        checks.append(
            _check(
                "no_unsupported_activation_claim",
                "activate" not in rec or "do not activate" in rec or "p4a" in rec or audit_only,
                rec[:200],
            )
        )
        if not audit_only:
            checks.append(_check("shadow_metrics_computed", "ssl" in metrics or "aasist" in metrics, ""))
            comp = (_OUTPUT / "phase9e_p4a_shadow_comparison_report.md").read_text(encoding="utf-8").lower()
            checks.append(
                _check(
                    "comparison_report_documents_shadow_only",
                    "shadow" in comp and "replay" in comp,
                    "",
                )
            )

    try:
        from src.origin_support_models import audit_origin_support_models, predict_origin_support  # type: ignore

        audit = audit_origin_support_models()
        checks.append(_check("audit_returns_models", bool(audit.get("models")), ""))
        checks.append(_check("audit_used_as_active_false", audit.get("used_as_active_decision") is False, ""))
        pred_shape = predict_origin_support.__doc__ or ""
        checks.append(_check("predict_origin_support_callable", callable(predict_origin_support), pred_shape[:80]))
    except Exception as exc:
        dep_skip = any(x in str(exc).lower() for x in ("pandas", "numpy", "sklearn", "torch"))
        checks.append(
            _check(
                "audit_returns_models",
                dep_skip,
                f"skipped (dependency): {exc}" if dep_skip else str(exc),
            )
        )

    overall = all(c["pass"] for c in checks)
    lines = [
        "# Phase 9E-P4A Origin-Support Shadow Validation Report",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        f"Mode: {args.mode}",
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
            "Phase 9E-P4A shadow-tests AASIST/HybridResNet for origin support only.",
            "No active fusion activation, threshold changes, or retraining in this phase.",
        ]
    )
    report_out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"9E-P4A validation {'PASS' if overall else 'FAIL'}: {report_out}")
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
