#!/usr/bin/env python3
"""Validate Phase 9D-P4 partial timestamp diagnostic outputs."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path as _Path

_HERE = _Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from phase9d_common import repo_root, resolve_path


REQUIRED_FILES = [
    "phase9d_p4_partial_segment_diagnostics.csv",
    "phase9d_p4_partial_file_diagnostics.csv",
    "phase9d_p4_boundary_diagnostics.csv",
    "phase9d_p4_partial_summary.csv",
    "phase9d_p4_partial_diagnostic_report.md",
]

REQUIRED_SCRIPTS = [
    "code/phase9/testing/run_phase9d_p4_partial_timestamp_diagnostics.py",
    "code/phase9/testing/summarize_phase9d_p4_partial_diagnostics.py",
    "code/phase9/testing/validate_phase9d_p4_partial_diagnostics.py",
]

DESIGN_DOC = "reports/phase9/testing/phase9d_p4_partial_diagnostic_design.md"


def _forbidden_tokens() -> tuple[str, ...]:
    return ("fake" + "_score", "real" + "_score", "final_fake_real")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate Phase 9D-P4 partial diagnostics.")
    p.add_argument(
        "--diagnostics_dir",
        default="reports/phase9/testing/phase9d_p4_partial_diagnostics",
    )
    p.add_argument(
        "--output_report",
        default="reports/phase9/validation/phase9d_p4_partial_diagnostics_validation_report.md",
    )
    p.add_argument("--ai_timestamp_csv", default="data/phase7c1/raw/ai_fabricated/insertion_stamps.csv")
    p.add_argument("--human_timestamp_csv", default="data/phase7c1/raw/human_fabricated/insertion_stamps.csv")
    return p.parse_args()


def _read_csv(path: _Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def validate(args: argparse.Namespace) -> tuple[bool, list[str], list[str]]:
    root = repo_root()
    diag_dir = resolve_path(args.diagnostics_dir, root)
    failures: list[str] = []
    warnings: list[str] = []

    for rel in REQUIRED_SCRIPTS:
        if not (root / rel).is_file():
            failures.append(f"missing script: {rel}")

    design = root / DESIGN_DOC
    if not design.is_file():
        failures.append(f"missing design doc: {DESIGN_DOC}")
    else:
        text = design.read_text(encoding="utf-8").lower()
        if "evaluation only" not in text and "evaluation-only" not in text:
            failures.append("design doc must state timestamps are evaluation-only")
        if "recommendation" not in text:
            warnings.append("design doc should mention recommendation outputs")

    for name in REQUIRED_FILES:
        if not (diag_dir / name).is_file():
            failures.append(f"missing diagnostic artifact: {name}")

    seg_rows = _read_csv(diag_dir / "phase9d_p4_partial_segment_diagnostics.csv")
    file_rows = _read_csv(diag_dir / "phase9d_p4_partial_file_diagnostics.csv")
    report_path = diag_dir / "phase9d_p4_partial_diagnostic_report.md"

    if seg_rows and "true_region_label" not in seg_rows[0]:
        failures.append("segment diagnostics missing true_region_label column")

    if file_rows:
        for col in ("top5_any_inside_true_region", "top1_inside_true_region", "localization_diagnostic_label"):
            if col not in file_rows[0]:
                failures.append(f"file diagnostics missing column: {col}")

    ai_ts = resolve_path(args.ai_timestamp_csv, root)
    human_ts = resolve_path(args.human_timestamp_csv, root)
    if ai_ts.is_file() and file_rows:
        if not any(r.get("fabrication_direction") == "ai_fabricated" for r in file_rows):
            warnings.append("no ai_fabricated rows in file diagnostics despite ai timestamp CSV")
    if human_ts.is_file() and file_rows:
        if not any(r.get("fabrication_direction") == "human_fabricated" for r in file_rows):
            warnings.append("no human_fabricated rows in file diagnostics despite human timestamp CSV")

    if report_path.is_file():
        report = report_path.read_text(encoding="utf-8").lower()
        if "recommendation" not in report:
            failures.append("diagnostic report missing recommendation section")
        if "evaluation" not in report:
            failures.append("diagnostic report must document evaluation-only timestamp use")
        for tok in _forbidden_tokens():
            if tok in report:
                failures.append(f"forbidden token in report: {tok}")
    else:
        failures.append("phase9d_p4_partial_diagnostic_report.md missing")

    for csv_name in (
        "phase9d_p4_partial_segment_diagnostics.csv",
        "phase9d_p4_partial_file_diagnostics.csv",
        "phase9d_p4_boundary_diagnostics.csv",
    ):
        path = diag_dir / csv_name
        if path.is_file():
            blob = path.read_text(encoding="utf-8").lower()
            for tok in _forbidden_tokens():
                if tok in blob:
                    failures.append(f"forbidden token '{tok}' in {csv_name}")

    run_script = root / "code/phase9/testing/run_phase9d_p4_partial_timestamp_diagnostics.py"
    if run_script.is_file():
        src = run_script.read_text(encoding="utf-8").lower()
        if "insert_start_sec" in src and "model input" in src:
            failures.append("timestamp fields must not be described as model inputs")
        if "never used as model" not in src and "never model input" not in src and "evaluation-only" not in src:
            warnings.append("run script should document evaluation-only timestamp use")

    if file_rows and not any(r.get("localization_diagnostic_label") not in ("", "inference_error") for r in file_rows):
        warnings.append("all file diagnostics are inference_error or empty")

    return len(failures) == 0, failures, warnings


def write_report(path: _Path, ok: bool, failures: list[str], warnings: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Phase 9D-P4 Partial Diagnostics Validation Report",
        "",
        f"- Status: **{'PASS' if ok else 'FAIL'}**",
        "- Scope: timestamp-based partial localization diagnostic (evaluation only)",
        "",
    ]
    if failures:
        lines.append("## Failures")
        for f in failures:
            lines.append(f"- {f}")
        lines.append("")
    if warnings:
        lines.append("## Warnings")
        for w in warnings:
            lines.append(f"- {w}")
        lines.append("")
    if ok:
        lines.append("Phase 9D-P4 diagnostic structure checks passed.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    ok, failures, warnings = validate(args)
    report_path = resolve_path(args.output_report, repo_root())
    write_report(report_path, ok, failures, warnings)
    print(f"Validation: {'PASS' if ok else 'FAIL'}")
    print(f"Report: {report_path}")
    for w in warnings:
        print(f"WARNING: {w}")
    for f in failures:
        print(f"FAIL: {f}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
