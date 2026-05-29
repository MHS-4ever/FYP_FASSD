#!/usr/bin/env python3
"""Validate Phase 9D end-to-end testing artifacts (structure and safety checks)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path as _Path

_HERE = _Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import json
from pathlib import Path

from phase9d_common import repo_root, resolve_path

REQUIRED_SCRIPTS = [
    "code/phase9/testing/build_phase9d_test_manifest.py",
    "code/phase9/testing/run_phase9d_batch_inference.py",
    "code/phase9/testing/summarize_phase9d_results.py",
    "code/phase9/testing/validate_phase9d_end_to_end_tests.py",
]

REQUIRED_DOCS = [
    "reports/phase9/testing/phase9d_testing_design.md",
    "reports/phase9/roadmap/phase9d_status.md",
]

def _forbidden_output_tokens() -> tuple[str, ...]:
    """Tokens that must not appear in generated forensic outputs (built without literals in other scripts)."""
    return ("fake" + "_score", "real" + "_score", "final_fake_real")


# Validator may reference forbidden field names for checks only.
FORBIDDEN_TOKENS = list(_forbidden_output_tokens())

SCRIPT_SOURCE_CHECK_EXEMPT = frozenset(
    {
        "validate_phase9d_end_to_end_tests.py",
    }
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate Phase 9D end-to-end testing outputs.")
    p.add_argument("--testing_dir", default="reports/phase9/testing")
    p.add_argument(
        "--output_report",
        default="reports/phase9/validation/phase9d_end_to_end_testing_validation_report.md",
    )
    return p.parse_args()


def _artifact_contains_forbidden_token(blob_lower: str) -> list[str]:
    hits: list[str] = []
    for tok in FORBIDDEN_TOKENS:
        if tok in blob_lower:
            hits.append(tok)
    return hits


def _check_json_outputs(outputs_dir: Path, failures: list[str], warnings: list[str]) -> int:
    ok_count = 0
    if not outputs_dir.is_dir():
        warnings.append(f"outputs dir missing (batch may not have run): {outputs_dir}")
        return 0
    for json_path in sorted(outputs_dir.glob("*_analysis.json")):
        try:
            payload = json.loads(json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            failures.append(f"invalid JSON: {json_path}")
            continue
        ok_count += 1
        blob = json.dumps(payload).lower()
        for tok in _artifact_contains_forbidden_token(blob):
            failures.append(f"forbidden token '{tok}' in {json_path.name}")
        if payload.get("status") != "experimental_forensic_prototype" and payload.get("status") != "error":
            warnings.append(f"non-standard status in {json_path.name}: {payload.get('status')}")
        for axis in (
            "origin_evidence",
            "replay_evidence",
            "mixer_channel_evidence",
            "partial_fabrication_evidence",
        ):
            if axis not in payload and payload.get("status") != "error":
                failures.append(f"missing axis {axis} in {json_path.name}")
        partial = payload.get("partial_fabrication_evidence", {})
        if partial.get("prediction_success") and partial.get("partial_fusion_eligible") is None:
            failures.append(f"partial_fusion_eligible missing in {json_path.name}")
    return ok_count


def _check_markdown_outputs(outputs_dir: Path, failures: list[str]) -> None:
    if not outputs_dir.is_dir():
        return
    for md_path in sorted(outputs_dir.glob("*_report.md")):
        blob = md_path.read_text(encoding="utf-8").lower()
        for tok in _artifact_contains_forbidden_token(blob):
            failures.append(f"forbidden token '{tok}' in {md_path.name}")


def validate(args: argparse.Namespace) -> tuple[bool, list[str], list[str]]:
    root = repo_root()
    testing_dir = resolve_path(args.testing_dir, root)
    failures: list[str] = []
    warnings: list[str] = []

    for rel in REQUIRED_SCRIPTS:
        if not (root / rel).is_file():
            failures.append(f"missing script: {rel}")

    for rel in REQUIRED_DOCS:
        if not (root / rel).is_file():
            failures.append(f"missing doc: {rel}")

    design = testing_dir / "phase9d_testing_design.md"
    if design.is_file():
        text = design.read_text(encoding="utf-8").lower()
        if "experimental" not in text or "architecture verification" not in text:
            warnings.append("design doc should mention experimental architecture verification")
        if "court" not in text and "production" not in text:
            warnings.append("design doc should mention non-production / non-court-ready limitations")

    manifest = testing_dir / "phase9d_test_manifest.csv"
    batch_csv = testing_dir / "phase9d_batch_results.csv"
    summary_csv = testing_dir / "phase9d_test_summary.csv"
    partial_csv = testing_dir / "phase9d_partial_behavior_review.csv"
    report_md = testing_dir / "phase9d_end_to_end_test_report.md"
    outputs_dir = testing_dir / "phase9d_outputs"

    if not manifest.is_file():
        failures.append("phase9d_test_manifest.csv missing (run build_phase9d_test_manifest.py)")
    if not batch_csv.is_file():
        failures.append("phase9d_batch_results.csv missing (run run_phase9d_batch_inference.py)")
    if not summary_csv.is_file():
        failures.append("phase9d_test_summary.csv missing (run summarize_phase9d_results.py)")
    if not partial_csv.is_file():
        failures.append("phase9d_partial_behavior_review.csv missing")
    if not report_md.is_file():
        failures.append("phase9d_end_to_end_test_report.md missing")

    for rel in REQUIRED_SCRIPTS:
        src = root / rel
        script_name = Path(rel).name
        if script_name in SCRIPT_SOURCE_CHECK_EXEMPT:
            continue
        if src.is_file():
            lower = src.read_text(encoding="utf-8").lower()
            if any(tok in lower for tok in FORBIDDEN_TOKENS):
                failures.append(f"forbidden token in script source: {rel}")
            if "aasist" in lower or "hybrid" in lower:
                if "inactive" not in lower and "reference" not in lower:
                    warnings.append(f"script mentions reference models — verify inactive: {rel}")

    release_plan = root / "release/docs/PHASE9_RELEASE_PLAN.md"
    if release_plan.is_file():
        plan = release_plan.read_text(encoding="utf-8").lower()
        if "phase 9d" not in plan:
            warnings.append("PHASE9_RELEASE_PLAN.md should mention Phase 9D")

    ok_json = _check_json_outputs(outputs_dir, failures, warnings)
    _check_markdown_outputs(outputs_dir, failures)
    if report_md.is_file():
        report_blob = report_md.read_text(encoding="utf-8").lower()
        for tok in _artifact_contains_forbidden_token(report_blob):
            failures.append(f"forbidden token '{tok}' in phase9d_end_to_end_test_report.md")
    if batch_csv.is_file() and ok_json == 0:
        failures.append("no successful JSON outputs found under phase9d_outputs")
    elif ok_json > 0:
        warnings.append(f"validated {ok_json} JSON output(s)")

    if batch_csv.is_file():
        text = batch_csv.read_text(encoding="utf-8").lower()
        for tok in FORBIDDEN_TOKENS:
            if tok in text:
                failures.append(f"forbidden token in batch results: {tok}")

    return len(failures) == 0, failures, warnings


def write_report(path: Path, ok: bool, failures: list[str], warnings: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Phase 9D End-to-End Testing Validation Report",
        "",
        f"- Status: **{'PASS' if ok else 'FAIL'}**",
        "- Scope: experimental architecture verification (not production-ready)",
        "",
    ]
    if failures:
        lines.append("## Failures")
        for item in failures:
            lines.append(f"- {item}")
        lines.append("")
    if warnings:
        lines.append("## Warnings")
        for item in warnings:
            lines.append(f"- {item}")
        lines.append("")
    if ok and not failures:
        lines.append("All required Phase 9D structure checks passed.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    root = repo_root()
    ok, failures, warnings = validate(args)
    report_path = resolve_path(args.output_report, root)
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
