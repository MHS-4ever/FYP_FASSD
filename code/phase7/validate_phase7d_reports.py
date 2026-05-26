"""
Phase 7D1: Validate generated forensic JSON and Markdown reports.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "code"))

from phase7.phase7d_common import (  # noqa: E402
    MARKDOWN_REQUIRED_SECTIONS,
    REQUIRED_JSON_KEYS,
    lint_full_report,
    lint_report_text,
)
from phase7.phase7_paths import resolve_phase7_report_path  # noqa: E402

DEFAULT_JSON_DIR = "reports/phase7/phase7d_report_layer/outputs/json"
DEFAULT_MD_DIR = "reports/phase7/phase7d_report_layer/outputs/markdown"
DEFAULT_OUT_MD = "reports/phase7/phase7d_report_layer/outputs/phase7d_report_validation_report.md"
DEFAULT_OUT_CSV = "reports/phase7/phase7d_report_layer/outputs/phase7d_rejected_or_failed_reports.csv"


def validate_json_file(path: Path) -> list[str]:
    issues: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"invalid_json:{e}"]

    for key in REQUIRED_JSON_KEYS:
        if key not in data:
            issues.append(f"missing_key:{key}")

    issues.extend(lint_full_report(data))
    return issues


def validate_markdown_file(path: Path, json_data: dict | None) -> list[str]:
    issues: list[str] = []
    text = path.read_text(encoding="utf-8")
    for section in MARKDOWN_REQUIRED_SECTIONS:
        if section not in text:
            issues.append(f"missing_section:{section}")

    narrative_parts: list[str] = []
    for sec in ("## 3.", "## 4.", "## 5.", "## 6.", "## 7.", "## 8.", "## 9."):
        if sec in text:
            chunk = text.split(sec, 1)[1]
            for stop in ("## 10.", "## 11.", "## 12."):
                if stop in chunk:
                    chunk = chunk.split(stop, 1)[0]
            narrative_parts.append(chunk)
    issues.extend(lint_report_text("\n".join(narrative_parts)))

    if "decision-support prototype" not in text.lower():
        issues.append("markdown_missing_disclaimer_phrase")

    if json_data:
        risk = json_data.get("overall_risk_level")
        if risk in ("medium", "high", "inconclusive") and json_data.get("manual_review_required"):
            if not re.search(r"manual review required\s*\|\s*\*\*true\*\*", text, re.IGNORECASE):
                issues.append("markdown_manual_review_not_true")

        st = json_data.get("technical_traceability", {}).get("phase7c4_status", "")
        if st == "clean_human_borderline":
            exec_match = re.search(
                r"## 3\. Executive Summary\s*\n+(.*?)(?=\n## )",
                text,
                re.DOTALL | re.IGNORECASE,
            )
            if exec_match:
                exec_s = exec_match.group(1).lower()
                if re.search(r"\b(is|are)\s+fake\b", exec_s):
                    issues.append("borderline_markdown_described_as_fake")

        if st == "direct_ai_file_level_missed_but_segment_suspicious":
            if "file-level proof" in text.lower() or "proven at file level" in text.lower():
                issues.append("segment_markdown_claims_file_level_proof")

        if st == "human_replay_manipulation_detected":
            exec_match = re.search(
                r"## 3\. Executive Summary\s*\n+(.*?)(?=\n## )",
                text,
                re.DOTALL | re.IGNORECASE,
            )
            if exec_match:
                exec_s = exec_match.group(1).lower()
                if "ai-generated" in exec_s and "does not" not in exec_s and "not by itself" not in exec_s:
                    issues.append("human_replay_markdown_claims_ai")

        if st == "partial_fabrication_detected":
            if "## 7. Suspicious Segment Analysis" in text:
                body = text.split("## 7. Suspicious Segment Analysis", 1)[1].split("## 8.", 1)[0]
                if "labeled_partial_region" not in body and "high_spoof_chunk" not in body:
                    seg_ev = json_data.get("segment_level_evidence") or {}
                    if seg_ev.get("partial_region_detected") or seg_ev.get("labeled_suspicious_start_s"):
                        issues.append("partial_markdown_missing_segments")

    return issues


def main() -> int:
    p = argparse.ArgumentParser(description="Phase 7D1 — validate forensic reports")
    p.add_argument("--json_dir", type=str, default=DEFAULT_JSON_DIR)
    p.add_argument("--markdown_dir", type=str, default=DEFAULT_MD_DIR)
    p.add_argument("--output_md", type=str, default=DEFAULT_OUT_MD)
    p.add_argument("--output_csv", type=str, default=DEFAULT_OUT_CSV)
    p.add_argument("--strict", action="store_true")
    args = p.parse_args()

    json_dir = resolve_phase7_report_path(args.json_dir)
    md_dir = resolve_phase7_report_path(args.markdown_dir)
    out_md = resolve_phase7_report_path(args.output_md, for_write=True)
    out_csv = resolve_phase7_report_path(args.output_csv, for_write=True)

    json_files = sorted(json_dir.glob("*_forensic_report.json"))
    report_ids: list[str] = []
    failed_rows: list[dict] = []
    issue_counts: Counter = Counter()
    passed = 0

    for jpath in json_files:
        sample_id = jpath.name.replace("_forensic_report.json", "")
        mpath = md_dir / f"{sample_id}_forensic_report.md"
        issues: list[str] = []

        j_issues = validate_json_file(jpath)
        issues.extend(j_issues)

        json_data = None
        if not j_issues or "invalid_json" not in j_issues[0]:
            json_data = json.loads(jpath.read_text(encoding="utf-8"))
            rid = json_data.get("report_id")
            if rid:
                if rid in report_ids:
                    issues.append(f"duplicate_report_id:{rid}")
                report_ids.append(rid)

        if not mpath.is_file():
            issues.append("missing_markdown_pair")
        else:
            issues.extend(validate_markdown_file(mpath, json_data))

        if issues:
            failed_rows.append(
                {
                    "sample_id": sample_id,
                    "json_path": str(jpath),
                    "markdown_path": str(mpath) if mpath.is_file() else "",
                    "issues": "; ".join(issues),
                }
            )
            for iss in issues:
                issue_counts[iss.split(":")[0]] += 1
        else:
            passed += 1

    lines = [
        "# Phase 7D Report Validation",
        "",
        f"- JSON files checked: **{len(json_files)}**",
        f"- Passed: **{passed}**",
        f"- Failed: **{len(failed_rows)}**",
        "",
        "## Issue type counts",
        "",
    ]
    if issue_counts:
        for k, v in issue_counts.most_common():
            lines.append(f"- `{k}`: {v}")
    else:
        lines.append("_No issues._")
    lines.extend(["", "## Failed reports", ""])
    if failed_rows:
        lines.append("| sample_id | issues |")
        lines.append("|-----------|--------|")
        for row in failed_rows[:100]:
            lines.append(f"| {row['sample_id']} | {row['issues']} |")
        if len(failed_rows) > 100:
            lines.append(f"\n_... and {len(failed_rows) - 100} more._")
    else:
        lines.append("_All reports passed validation checks._")

    lines.extend(
        [
            "",
            "## Checks performed",
            "",
            "1. Required JSON keys",
            "2. Markdown pair exists",
            "3. Forbidden wording",
            "4. Mandatory disclaimer",
            "5. Manual review for elevated risk",
            "6. Status-specific narrative rules",
            "7. Unique report_id",
            "8. Required Markdown sections",
            "",
        ]
    )

    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines), encoding="utf-8")

    import pandas as pd

    if failed_rows:
        pd.DataFrame(failed_rows).to_csv(out_csv, index=False)
    elif out_csv.is_file():
        out_csv.unlink()

    print(f"[CHECK] {len(json_files)} JSON reports")
    print(f"[PASS] {passed}  [FAIL] {len(failed_rows)}")
    print(f"[SAVE] {out_md}")
    if failed_rows:
        print(f"[SAVE] {out_csv}")

    return 1 if args.strict and failed_rows else 0


if __name__ == "__main__":
    raise SystemExit(main())
