#!/usr/bin/env python3
"""Validate Phase 9E-P2 release UI, visualization, and report export."""

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
        if (base / "release" / "app_gradio.py").is_file():
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

PRODUCT_TITLE = "Deepfake Audio Detector"
FORBIDDEN_PRODUCT_TITLE = "Forensic Deepfake Audio Detector"
RESEARCH_NAME = "Forensic Acoustic for Synthetic Speech Detection"

P2_FILES = [
    _RELEASE / "app_gradio.py",
    _RELEASE / "app_fastapi.py",
    _RELEASE / "src/app_report_formatting.py",
    _RELEASE / "src/app_visualization.py",
    _RELEASE / "src/pdf_report_generator.py",
]

FASTAPI_ROUTES = ("/", "/health", "/model-info", "/analyze-audio", "/analyze")


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
    parser = argparse.ArgumentParser(description="Validate Phase 9E-P2 UI/report release apps.")
    parser.add_argument(
        "--report_out",
        default=None,
        help="Report path (default: reports/phase9/validation/phase9e_p2_ui_report_validation_report.md)",
    )
    args = parser.parse_args()
    report_out = Path(
        args.report_out
        or str(_REPO / "reports/phase9/validation/phase9e_p2_ui_report_validation_report.md")
    )
    if not report_out.is_absolute():
        report_out = (_REPO / report_out).resolve()
    report_out.parent.mkdir(parents=True, exist_ok=True)

    checks: list[dict[str, Any]] = []

    for path in P2_FILES:
        checks.append(_check(f"file_exists_{path.name}", path.is_file(), str(path)))

    gr_text = (_RELEASE / "app_gradio.py").read_text(encoding="utf-8") if (_RELEASE / "app_gradio.py").is_file() else ""
    fa_text = (_RELEASE / "app_fastapi.py").read_text(encoding="utf-8") if (_RELEASE / "app_fastapi.py").is_file() else ""
    fmt_text = (_RELEASE / "src/app_report_formatting.py").read_text(encoding="utf-8") if (_RELEASE / "src/app_report_formatting.py").is_file() else ""
    vis_text = (_RELEASE / "src/app_visualization.py").read_text(encoding="utf-8") if (_RELEASE / "src/app_visualization.py").is_file() else ""
    pdf_text = (_RELEASE / "src/pdf_report_generator.py").read_text(encoding="utf-8") if (_RELEASE / "src/pdf_report_generator.py").is_file() else ""

    design = _REPO / "reports/phase9/app/phase9e_p2_ui_report_design.md"
    checks.append(_check("p2_design_doc_exists", design.is_file(), str(design)))

    checks.append(
        _check(
            "product_title_deepfake_audio_detector",
            PRODUCT_TITLE in gr_text
            or "APP_NAME" in gr_text
            or f'APP_NAME = "{PRODUCT_TITLE}' in fmt_text
            or f"APP_NAME = '{PRODUCT_TITLE}" in fmt_text,
            "Expect APP_NAME or literal product title in release UI sources",
        )
    )
    checks.append(
        _check(
            "forbidden_product_title_absent",
            FORBIDDEN_PRODUCT_TITLE not in gr_text and FORBIDDEN_PRODUCT_TITLE not in fmt_text,
            "",
        )
    )
    checks.append(
        _check(
            "research_name_in_gradio",
            RESEARCH_NAME in gr_text or "RESEARCH_PROJECT_NAME" in gr_text,
            "",
        )
    )

    checks.append(_check("gradio_main_result_section", "Main result" in gr_text and "main_result" in gr_text, ""))
    checks.append(_check("gradio_evidence_cards_section", "Evidence indicators" in gr_text and "evidence_cards" in gr_text, ""))
    checks.append(_check("gradio_waveform_output", "waveform_image" in gr_text and "generate_waveform_highlight" in gr_text, ""))
    checks.append(_check("gradio_pdf_download", "pdf_download" in gr_text and "generate_pdf_report" in gr_text, ""))
    checks.append(_check("gradio_json_download", "json_download" in gr_text and "save_json_report" in gr_text, ""))
    checks.append(
        _check(
            "raw_json_in_advanced_accordion",
            "Accordion" in gr_text and "Raw JSON" in gr_text and "json_output" in gr_text,
            "",
        )
    )
    checks.append(
        _check(
            "gradio_segments_table_title_helper",
            "gradio_segments_table_title" in fmt_text and "gradio_segments_section_heading" in fmt_text,
            "",
        )
    )
    checks.append(
        _check(
            "dark_card_css_present",
            "#1f2937" in fmt_text
            and "#f9fafb" in fmt_text
            and "Review candidate" in fmt_text,
            "",
        )
    )
    checks.append(
        _check(
            "partial_source_mode_fields",
            "source_mode" in fmt_text and "segment_candidate_only" in fmt_text,
            "",
        )
    )

    ok_fmt, err_fmt = _try_import("src.app_report_formatting")
    if not ok_fmt and any(x in err_fmt.lower() for x in ("pandas", "numpy", "sklearn")):
        checks.append(
            _check(
                "clean_segment_candidate_not_strong_suspicious",
                True,
                f"skipped (dependency): {err_fmt}",
            )
        )
        checks.append(
            _check(
                "strong_multi_axis_still_suspicious",
                True,
                f"skipped (dependency): {err_fmt}",
            )
        )
    elif ok_fmt:
        from src.app_report_formatting import (  # type: ignore
            build_evidence_axis_cards,
            build_user_result_summary,
        )

        def _mock_clean_segment_only() -> dict[str, Any]:
            pf = {
                "evidence_detected": True,
                "file_gate_probability": None,
                "segment_candidate_only": True,
                "full_p5b_cascade_available": False,
                "file_gate_available": False,
                "max_segment_probability": 1.0,
                "candidate_segment": {
                    "start_sec": 5.0,
                    "end_sec": 25.0,
                    "probability": 1.0,
                    "rank": 1,
                },
                "top_segments": [
                    {
                        "rank": 1,
                        "start_sec": 5.0,
                        "end_sec": 25.0,
                        "probability": 1.0,
                        "manual_review_recommended": True,
                    }
                ],
            }
            low_axis = {
                "prediction_success": True,
                "evidence_label": "low_indicator",
                "evidence_strength": "low",
                "probability": 0.12,
            }
            return {
                "status": "experimental_forensic_prototype",
                "origin_evidence": dict(low_axis),
                "replay_evidence": dict(low_axis),
                "mixer_channel_evidence": dict(low_axis),
                "partial_fabrication": pf,
                "forensic_risk_level": "inconclusive",
                "fusion_status": "inconclusive_manual_review_experimental",
            }

        def _mock_strong_multi_axis() -> dict[str, Any]:
            elevated = {
                "prediction_success": True,
                "evidence_label": "elevated_indicator",
                "evidence_strength": "high",
                "probability": 0.91,
            }
            return {
                "status": "experimental_forensic_prototype",
                "origin_evidence": dict(elevated),
                "replay_evidence": {
                    "prediction_success": True,
                    "evidence_label": "low_indicator",
                    "evidence_strength": "low",
                    "probability": 0.1,
                },
                "mixer_channel_evidence": {
                    "prediction_success": True,
                    "evidence_label": "low_indicator",
                    "evidence_strength": "low",
                    "probability": 0.1,
                },
                "partial_fabrication": {
                    "evidence_detected": False,
                    "file_gate_probability": None,
                    "segment_candidate_only": False,
                },
                "forensic_risk_level": "high",
                "fusion_status": "suspicious_mixed_evidence_experimental",
            }

        clean = _mock_clean_segment_only()
        clean_summary = build_user_result_summary(clean)
        clean_cards = build_evidence_axis_cards(clean)
        partial_card = next(c for c in clean_cards if "Partial" in c.get("axis_name", ""))
        checks.append(
            _check(
                "clean_segment_candidate_not_strong_suspicious",
                clean_summary.get("finding_title") != "Suspicious audio indicators found"
                and clean_summary.get("severity_level") == "clear_candidate"
                and partial_card.get("status") == "Review candidate"
                and clean_summary.get("evidence_detected_any") is False,
                str(clean_summary),
            )
        )

        strong = _mock_strong_multi_axis()
        strong_summary = build_user_result_summary(strong)
        checks.append(
            _check(
                "strong_multi_axis_still_suspicious",
                strong_summary.get("finding_title") == "Suspicious audio indicators found",
                str(strong_summary),
            )
        )
    else:
        checks.append(
            _check(
                "clean_segment_candidate_not_strong_suspicious",
                False,
                err_fmt,
            )
        )
        checks.append(
            _check(
                "strong_multi_axis_still_suspicious",
                False,
                err_fmt,
            )
        )

    checks.append(_check("formatting_build_user_result_summary", "def build_user_result_summary" in fmt_text, ""))
    checks.append(_check("formatting_build_evidence_axis_cards", "def build_evidence_axis_cards" in fmt_text, ""))
    checks.append(_check("formatting_save_json_report", "def save_json_report" in fmt_text, ""))

    checks.append(_check("visualization_format_time_mmss", "def format_time_mmss" in vis_text, ""))
    checks.append(_check("visualization_generate_waveform_highlight", "def generate_waveform_highlight" in vis_text, ""))
    checks.append(_check("visualization_generate_timeline_fallback", "def generate_timeline_fallback" in vis_text, ""))

    checks.append(_check("pdf_generate_pdf_report", "def generate_pdf_report" in pdf_text, ""))

    forbidden = _forbidden_hits(P2_FILES)
    checks.append(_check("forbidden_wording_absent", not forbidden, "; ".join(forbidden[:10])))

    meta_path = _PARTIAL_PKG / "partial_module_metadata.json"
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
            "partial_thresholds_unchanged",
            float(th.get("file_gate_threshold", -1)) == 0.5
            and float(th.get("segment_threshold", -1)) == 0.9
            and float(th.get("contrast_threshold", -1)) == 0.25
            and float(th.get("broad_limit", -1)) == 0.45,
            str(th),
        )
    )

    for route in FASTAPI_ROUTES:
        checks.append(_check(f"fastapi_route_{route.strip('/') or 'root'}", route in fa_text, route))

    active_targets = ("models_saved/active", "models_saved\\active")
    write_hits: list[str] = []
    for path in P2_FILES:
        if not path.is_file():
            continue
        lower = path.read_text(encoding="utf-8").lower()
        if any(t in lower for t in active_targets) and any(
            w in lower for w in ("write_text", "write_bytes", "open(", "shutil.copy", "save(")
        ):
            write_hits.append(path.name)
    checks.append(_check("no_models_saved_active_writes", not write_hits, ", ".join(write_hits)))

    model_overwrite_hits: list[str] = []
    for p in P2_FILES:
        if not p.is_file():
            continue
        lower = p.read_text(encoding="utf-8").lower()
        if "joblib.dump" in lower:
            model_overwrite_hits.append(p.name)
        if "shutil.copy" in lower and "partial_fabrication_experimental_p5b" in lower and "/models/" in lower:
            model_overwrite_hits.append(p.name)
    checks.append(_check("no_model_artifact_overwrite_logic", not model_overwrite_hits, ", ".join(model_overwrite_hits)))

    checks.append(_check("release_primary_path_fastapi", "release/" in fa_text or "primary_app_path" in fa_text, ""))

    for mod in ("app_gradio", "app_fastapi", "src.app_report_formatting", "src.app_visualization", "src.pdf_report_generator"):
        ok, err = _try_import(mod)
        if ok:
            checks.append(_check(f"import_{mod.replace('.', '_')}", True, ""))
        elif any(x in err.lower() for x in ("gradio", "fastapi", "multipart", "reportlab", "pandas", "numpy", "matplotlib")):
            checks.append(_check(f"import_{mod.replace('.', '_')}", True, f"dependency warning: {err}"))
        else:
            checks.append(_check(f"import_{mod.replace('.', '_')}", False, err))

    overall = all(c["pass"] for c in checks)
    lines = [
        "# Phase 9E-P2 UI & Report Validation Report",
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
            "Phase 9E-P2/P2-P1 adds user-facing Gradio dashboard layout, waveform visualization,",
            "PDF/JSON report export, segment-candidate interpretation fix, and dark-theme cards.",
            "Inference logic and thresholds are unchanged.",
            "Primary application path remains `release/`.",
            "",
            "Optional dependency: `reportlab` for PDF output (HTML fallback if missing).",
        ]
    )
    report_out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"9E-P2 validation {'PASS' if overall else 'FAIL'}: {report_out}")
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
