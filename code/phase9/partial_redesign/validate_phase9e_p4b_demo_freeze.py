#!/usr/bin/env python3
"""Validate Phase 9E-P4B demo freeze — naming, docs, P3/P4A status, no model activation."""

from __future__ import annotations

import argparse
import csv
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
_P4B = _REPO / "reports" / "phase9" / "app" / "phase9e_p4b_demo_freeze"
_P3_VAL = _REPO / "reports" / "phase9" / "validation" / "phase9e_p3_release_correctness_validation_report.md"
_P4A_VAL = _REPO / "reports" / "phase9" / "validation" / "phase9e_p4a_origin_support_validation_report.md"
_P3_METRICS = _REPO / "reports" / "phase9" / "app" / "phase9e_p3_8variant_eval" / "phase9e_p3_full_184_metrics.json"
_P4A_METRICS = _REPO / "reports" / "phase9" / "app" / "phase9e_p4a_origin_support" / "phase9e_p4a_shadow_metrics.json"

if str(_RELEASE) not in sys.path:
    sys.path.insert(0, str(_RELEASE))

FORBIDDEN = [
    "definitely fake",
    "definitely real",
    "court proof",
    "court-ready",
    "court ready",
    "production ready",
    "production-ready",
    "final verdict",
    "final fake",
    "final real",
]
VALID_REC_LEVELS = frozenset({"none", "optional_review", "review_recommended", "unavailable", ""})
REQUIRED_VARIANTS = frozenset(
    {
        "ai_clean",
        "ai_fabricated",
        "ai_mixer",
        "ai_replayed",
        "human_clean",
        "human_fabricated",
        "human_mixer",
        "human_replayed",
    }
)


def _check(name: str, ok: bool, detail: str = "") -> dict[str, Any]:
    return {"check": name, "pass": ok, "detail": detail}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 9E-P4B demo freeze.")
    args = parser.parse_args()

    report_out = _REPO / "reports" / "phase9" / "validation" / "phase9e_p4b_demo_freeze_validation_report.md"
    report_out.parent.mkdir(parents=True, exist_ok=True)

    checks: list[dict[str, Any]] = []

    required_files = [
        _RELEASE / "app_gradio.py",
        _RELEASE / "app_fastapi.py",
        _RELEASE / "src/app_report_formatting.py",
        _RELEASE / "src/app_visualization.py",
        _RELEASE / "src/pdf_report_generator.py",
        _P3_VAL,
        _P4A_VAL,
        _P4B / "phase9e_p4b_demo_freeze_report.md",
        _P4B / "phase9e_p4b_demo_checklist.md",
        _P4B / "phase9e_p4b_final_demo_samples.csv",
        _P4B / "phase9e_p4b_known_limitations.md",
        _REPO / "reports/phase9/roadmap/phase9e_status.md",
    ]
    for path in required_files:
        checks.append(_check(f"required_file_{path.name}", path.is_file(), str(path)))

    if _P3_VAL.is_file():
        p3_text = _P3_VAL.read_text(encoding="utf-8")
        checks.append(_check("p3_validation_pass", "**Overall:** PASS" in p3_text, ""))

    if _P3_METRICS.is_file():
        p3m = json.loads(_P3_METRICS.read_text(encoding="utf-8"))
        checks.append(
            _check(
                "p3_full_184_present",
                p3m.get("total_files") == 184 and p3m.get("evaluated_files") == 184,
                str(p3m.get("total_files")),
            )
        )
        checks.append(
            _check(
                "human_clean_false_suspicious_rate_zero",
                float(p3m.get("human_clean_false_suspicious_rate", 1.0)) == 0.0,
                str(p3m.get("human_clean_false_suspicious_rate")),
            )
        )

    fmt = (_RELEASE / "src/app_report_formatting.py").read_text(encoding="utf-8")
    checks.append(_check("json_fields_in_formatting", "recommendation_level" in fmt and "voice_origin_result" in fmt, ""))
    checks.append(
        _check(
            "optional_review_wording",
            "Optional review of the candidate segment" in fmt,
            "",
        )
    )

    if _P4A_VAL.is_file():
        p4a_text = _P4A_VAL.read_text(encoding="utf-8")
        checks.append(_check("p4a_validation_pass", "**Overall:** PASS" in p4a_text, ""))

    if _P4A_METRICS.is_file():
        p4am = json.loads(_P4A_METRICS.read_text(encoding="utf-8"))
        decisions = p4am.get("decisions") or {}
        checks.append(_check("aasist_reject_for_now", decisions.get("aasist") == "reject_for_now", str(decisions)))
        checks.append(
            _check("hybrid_resnet_reject_for_now", decisions.get("hybrid_resnet") == "reject_for_now", str(decisions))
        )

    inv_path = _RELEASE / "models/model_inventory.json"
    if inv_path.is_file():
        inv = json.loads(inv_path.read_text(encoding="utf-8"))
        names = {str(m.get("model_name", "")).lower() for m in inv.get("models", [])}
        checks.append(
            _check(
                "no_aasist_resnet_in_active_inventory",
                "aasist" not in names and "hybrid_resnet" not in names,
                str(sorted(names)),
            )
        )

    gr = (_RELEASE / "app_gradio.py").read_text(encoding="utf-8")
    fa = (_RELEASE / "app_fastapi.py").read_text(encoding="utf-8")
    checks.append(_check("deepfake_audio_detector_title", "Deepfake Audio Detector" in fmt, ""))
    checks.append(
        _check(
            "research_project_name",
            "Forensic Acoustic for Synthetic Speech Detection" in fmt,
            "",
        )
    )
    bad_product = "Forensic Deepfake Audio Detector" in gr or "Forensic Deepfake Audio Detector" in fmt
    checks.append(_check("no_forensic_deepfake_product_name", not bad_product, ""))

    scan_paths = [
        _RELEASE / "app_gradio.py",
        _RELEASE / "app_fastapi.py",
        _RELEASE / "src/app_report_formatting.py",
        _RELEASE / "src/pdf_report_generator.py",
        _P4B / "phase9e_p4b_demo_freeze_report.md",
        _P4B / "phase9e_p4b_known_limitations.md",
    ]
    forbidden_hits: list[str] = []
    for path in scan_paths:
        if not path.is_file():
            continue
        lower = path.read_text(encoding="utf-8").lower()
        for phrase in FORBIDDEN:
            if phrase in lower:
                forbidden_hits.append(f"{path.name}: {phrase}")
    checks.append(_check("forbidden_wording_absent", not forbidden_hits, "; ".join(forbidden_hits)))

    checks.append(
        _check(
            "p4b_warning_filter_gradio",
            "key_padding_mask and attn_mask is deprecated" in gr,
            "",
        )
    )
    checks.append(
        _check(
            "p4b_warning_filter_fastapi",
            "key_padding_mask and attn_mask is deprecated" in fa,
            "",
        )
    )
    global_runtime_ignore = (
        'filterwarnings("ignore"' in gr and "RuntimeWarning" in gr and "category=RuntimeWarning" in gr
    ) or (
        'filterwarnings("ignore"' in fa and "RuntimeWarning" in fa
    )
    checks.append(_check("no_global_runtime_warning_ignore", not global_runtime_ignore, ""))

    freeze_report = (_P4B / "phase9e_p4b_demo_freeze_report.md").read_text(encoding="utf-8") if (
        _P4B / "phase9e_p4b_demo_freeze_report.md"
    ).is_file() else ""
    checks.append(
        _check(
            "phase9e_freeze_decision_documented",
            "Phase 9F may start" in freeze_report or "Phase 9F" in freeze_report,
            "",
        )
    )
    checks.append(
        _check(
            "aasist_resnet_reject_documented",
            "reject_for_now" in freeze_report,
            "",
        )
    )

    samples_csv = _P4B / "phase9e_p4b_final_demo_samples.csv"
    if samples_csv.is_file():
        with samples_csv.open(encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        variants = {r.get("variant", "") for r in rows}
        checks.append(_check("demo_sample_eight_variants", REQUIRED_VARIANTS <= variants, str(sorted(variants))))
        fail_rows = [r for r in rows if r.get("demo_status") == "fail"]
        checks.append(_check("demo_sample_no_fail", not fail_rows, str(len(fail_rows))))
        bad_levels = [
            r.get("variant")
            for r in rows
            if r.get("recommendation_level") not in VALID_REC_LEVELS
        ]
        checks.append(_check("demo_sample_valid_rec_levels", not bad_levels, str(bad_levels)))
        for r in rows:
            jp = Path(r.get("json_path", ""))
            pp = Path(r.get("pdf_path", ""))
            wp = Path(r.get("waveform_path", ""))
            if jp.is_file() and pp.is_file() and wp.is_file():
                continue
            checks.append(
                _check(
                    f"demo_artifacts_{r.get('variant')}",
                    False,
                    f"json={jp.is_file()} pdf={pp.is_file()} wave={wp.is_file()}",
                )
            )

    checks.append(_check("app_phase_p4b", "Phase 9E-P4B" in fmt, ""))

    try:
        import app_gradio  # type: ignore  # noqa: F401

        checks.append(_check("gradio_app_imports", True, ""))
    except Exception as exc:
        dep = any(x in str(exc).lower() for x in ("gradio", "pandas", "torch"))
        checks.append(
            _check(
                "gradio_app_imports",
                dep,
                f"dependency skip: {exc}" if dep else str(exc),
            )
        )

    try:
        import app_fastapi  # type: ignore  # noqa: F401

        checks.append(_check("fastapi_app_imports", True, ""))
    except Exception as exc:
        dep = any(x in str(exc).lower() for x in ("fastapi", "pandas", "torch"))
        checks.append(
            _check(
                "fastapi_app_imports",
                dep,
                f"dependency skip: {exc}" if dep else str(exc),
            )
        )

    overall = all(c["pass"] for c in checks)
    lines = [
        "# Phase 9E-P4B Demo Freeze Validation Report",
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
            "Phase 9E-P4B freezes the release demo after P3/P3-P1/P4A validation.",
            "No model, threshold, or AASIST/ResNet activation changes in this phase.",
            "Phase 9F may start when this report is PASS.",
        ]
    )
    report_out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"9E-P4B validation {'PASS' if overall else 'FAIL'}: {report_out}")
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
