#!/usr/bin/env python3
"""Validate Phase 8G freeze docs and manifest."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]

REQUIRED_DOCS = [
    "phase8g_phase8_final_summary.md",
    "phase8g_evidence_model_registry.md",
    "phase8g_fusion_summary.md",
    "phase8g_limitations_and_claims.md",
    "phase8g_phase9_handoff_plan.md",
    "phase8g_freeze_manifest.csv",
    "phase8g_freeze_report.md",
]
MANIFEST_REQUIRED_COLS = [
    "item_type",
    "phase",
    "file_path",
    "exists",
    "role",
    "freeze_status",
    "notes",
]
CORE_FILES = [
    "reports/phase8/fusion/phase8f/phase8f_file_fusion_records.csv",
    "reports/phase8/fusion/phase8f/phase8f_fusion_summary.csv",
    "reports/phase8/fusion/phase8f/phase8f_fusion_report.md",
    "reports/phase8/validation/phase8f_fusion_validation_report.md",
    "reports/phase8/models/phase8e1/phase8e1_metrics_summary.csv",
    "reports/phase8/models/phase8e1a/phase8e1a_threshold_recommendations.csv",
    "reports/phase8/models/phase8e3/phase8e3_partial_segment_metrics_summary.csv",
    "reports/phase8/validation/phase8e3_results_validation_report.md",
]
FORBIDDEN_WORDS = [
    "guaranteed fake",
    "guaranteed real",
    "court-proven",
    "perfect detector",
    "final production model",
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate Phase 8G freeze docs.")
    p.add_argument("--freeze_dir", default="reports/phase8/freeze")
    p.add_argument("--output_report", default="reports/phase8/validation/phase8g_freeze_validation_report.md")
    return p.parse_args()


def _resolve(path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else (REPO_ROOT / p).resolve()


def validate(args: argparse.Namespace) -> dict[str, object]:
    freeze_dir = _resolve(args.freeze_dir)
    blocking: list[str] = []
    warnings: list[str] = []

    for doc in REQUIRED_DOCS:
        if not (freeze_dir / doc).is_file():
            blocking.append(f"Missing required freeze document: {doc}")

    manifest_path = freeze_dir / "phase8g_freeze_manifest.csv"
    manifest = pd.DataFrame()
    if manifest_path.is_file():
        manifest = pd.read_csv(manifest_path, dtype=str, keep_default_na=False)
        missing_cols = [c for c in MANIFEST_REQUIRED_COLS if c not in manifest.columns]
        if missing_cols:
            blocking.append(f"Freeze manifest missing required columns: {missing_cols}")
    else:
        blocking.append("Freeze manifest file missing.")

    if len(manifest):
        for core in CORE_FILES:
            row = manifest[manifest["file_path"].astype(str).str.replace("\\", "/", regex=False) == core]
            if len(row) == 0:
                blocking.append(f"Core file not listed in freeze manifest: {core}")
                continue
            if str(row.iloc[0].get("exists", "")).lower() != "true":
                blocking.append(f"Core file listed but marked missing: {core}")

    reg_path = freeze_dir / "phase8g_evidence_model_registry.md"
    if reg_path.is_file():
        reg = reg_path.read_text(encoding="utf-8").lower()
        for model in [
            "origin_file_model",
            "replay_file_model",
            "mixer_file_model",
            "partial_fabrication_segment_model",
        ]:
            if model not in reg:
                blocking.append(f"Model registry missing model: {model}")
        if "experimental_forensic_evidence_model" not in reg:
            warnings.append("Model registry missing explicit experimental model status phrase.")
    else:
        blocking.append("Missing model registry document.")

    lim_path = freeze_dir / "phase8g_limitations_and_claims.md"
    if lim_path.is_file():
        lim = lim_path.read_text(encoding="utf-8").lower()
        for phrase in ["allowed claims", "not allowed claims"]:
            if phrase not in lim:
                blocking.append(f"Limitations doc missing section: {phrase}")
    else:
        blocking.append("Missing limitations and claims document.")

    handoff = freeze_dir / "phase8g_phase9_handoff_plan.md"
    if not handoff.is_file():
        blocking.append("Missing Phase 9 handoff plan document.")

    all_text = ""
    for doc in REQUIRED_DOCS:
        p = freeze_dir / doc
        if p.suffix.lower() == ".md" and p.is_file():
            all_text += "\n" + p.read_text(encoding="utf-8").lower()
    if "fake/real" not in all_text and "no single fake/real" not in all_text:
        warnings.append("Freeze docs should explicitly mention no final fake/real score.")
    if "experimental" not in all_text:
        blocking.append("Freeze docs missing experimental-status wording.")
    if "phase 9 status: **not started**" not in all_text and "phase 9 status: not started" not in all_text:
        warnings.append("Freeze docs should explicitly state Phase 9 not started.")
    for bad in FORBIDDEN_WORDS:
        if bad in all_text:
            blocking.append(f"Forbidden wording found in freeze docs: {bad}")

    return {
        "status": "FAIL" if blocking else "PASS",
        "blocking": blocking,
        "warnings": warnings,
    }


def write_report(path: Path, result: dict[str, object]) -> None:
    lines = [
        "# Phase 8G Freeze Validation Report",
        "",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"**Status:** **{result.get('status', 'FAIL')}**",
    ]
    if result.get("blocking"):
        lines.extend(["", "## Blocking Errors", ""])
        lines.extend(f"- {x}" for x in result["blocking"])  # type: ignore[index]
    if result.get("warnings"):
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {x}" for x in result["warnings"])  # type: ignore[index]
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Phase 8 freeze docs are documentation artifacts, not model retraining outputs.",
            "- Validation checks wording safety and freeze manifest completeness.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    result = validate(args)
    out = _resolve(args.output_report)
    write_report(out, result)
    print(f"Validation: {result['status']}")
    print(f"Report -> {out}")
    return 1 if result["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
