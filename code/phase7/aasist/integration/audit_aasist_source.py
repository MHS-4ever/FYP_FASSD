"""
Phase 7E1: Audit local or importable AASIST source tree.

Does not train, download, or implement AASIST architecture.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from _common import (
    REPO_ROOT,
    CHECKPOINT_EXTENSIONS,
    CONFIG_EXTENSIONS,
    discover_model_candidates,
    grep_symbols_in_file,
    list_files_by_extensions,
    list_python_files,
    resolve_path,
    try_import_installed_aasist,
    utc_now_iso,
    write_json,
    write_markdown,
)


def audit_source(aasist_src: Path | None, *, allow_missing: bool) -> dict[str, Any]:
    result: dict[str, Any] = {
        "timestamp_utc": utc_now_iso(),
        "aasist_src": str(aasist_src) if aasist_src else None,
        "aasist_src_exists": bool(aasist_src and aasist_src.is_dir()),
        "verdict": "SOURCE_REQUIRED",
        "mode_b_installed": try_import_installed_aasist(),
        "python_files": [],
        "config_files": [],
        "checkpoint_files": [],
        "model_candidates": [],
        "symbol_scan": [],
        "readme_files": [],
        "license_files": [],
        "user_actions": [],
    }

    if not result["aasist_src_exists"]:
        result["user_actions"] = [
            "Clone or copy a verified AASIST repository into code/phase7/aasist/vendor/AASIST/",
            "OR place source at external/AASIST/ and pass --aasist_src external/AASIST",
            "OR install an importable AASIST package in the (fassd) environment (Mode B)",
            "Re-run audit without --allow_missing_source once source is present",
            "Do not approximate AASIST with a custom architecture in this project",
        ]
        if result["mode_b_installed"].get("found"):
            result["verdict"] = "PASS_IMPORT_ONLY"
            result["notes"] = "No local folder; installed module may be usable (verify license and version)"
        elif not allow_missing:
            result["error"] = "AASIST source directory not found"
        return result

    root = aasist_src  # type: ignore[assignment]
    py_files = list_python_files(root)
    result["python_files"] = [str(p.relative_to(root)).replace("\\", "/") for p in py_files[:100]]
    result["python_file_count"] = len(py_files)

    configs = list_files_by_extensions(root, CONFIG_EXTENSIONS)
    result["config_files"] = [str(p.relative_to(root)).replace("\\", "/") for p in configs[:50]]

    checkpoints = list_files_by_extensions(root, CHECKPOINT_EXTENSIONS)
    result["checkpoint_files"] = [str(p.relative_to(root)).replace("\\", "/") for p in checkpoints[:30]]

    for name in ("README.md", "README.rst", "readme.md"):
        for p in root.rglob(name):
            result["readme_files"].append(str(p.relative_to(root)).replace("\\", "/"))
    for p in root.rglob("LICENSE*"):
        if p.is_file():
            result["license_files"].append(str(p.relative_to(root)).replace("\\", "/"))

    result["model_candidates"] = discover_model_candidates(root)

    for py in py_files[:80]:
        hits = grep_symbols_in_file(py)
        if hits:
            result["symbol_scan"].append(
                {
                    "file": str(py.relative_to(root)).replace("\\", "/"),
                    "symbols": hits,
                }
            )

    if result["model_candidates"] or result["symbol_scan"]:
        result["verdict"] = "PASS"
    else:
        result["verdict"] = "PASS_WITH_WARNINGS"
        result["notes"] = "Source tree exists but no AASIST-like model classes detected by AST scan"

    return result


def _md_report(data: dict[str, Any]) -> list[str]:
    lines = [
        "# Phase 7E1 — AASIST Source Audit",
        "",
        f"**Generated:** {data['timestamp_utc']}  ",
        f"**Verdict:** `{data['verdict']}`  ",
        f"**Source path:** `{data.get('aasist_src') or '(missing)'}`  ",
        f"**Exists:** {data['aasist_src_exists']}  ",
        "",
    ]
    if data.get("user_actions"):
        lines.append("## User actions required")
        lines.append("")
        for a in data["user_actions"]:
            lines.append(f"- {a}")
        lines.append("")

    lines.extend(
        [
            "## Mode B — installed import check",
            "",
            f"- Found importable AASIST-like module: `{data.get('mode_b_installed', {}).get('found')}`",
            "",
            "## Summary counts",
            "",
            f"- Python files scanned: {data.get('python_file_count', 0)}",
            f"- Config files: {len(data.get('config_files', []))}",
            f"- Checkpoint files in tree: {len(data.get('checkpoint_files', []))}",
            f"- Model candidates (AST): {len(data.get('model_candidates', []))}",
            "",
        ]
    )

    if data.get("model_candidates"):
        lines.append("## Model candidates")
        lines.append("")
        for c in data["model_candidates"][:15]:
            lines.append(
                f"- `{c['file']}` module=`{c['module']}` classes={c.get('matched_classes') or c.get('classes')[:5]}"
            )
        lines.append("")

    if data.get("readme_files"):
        lines.append("## README files")
        for r in data["readme_files"][:10]:
            lines.append(f"- `{r}`")
        lines.append("")

    lines.append("## Full JSON")
    lines.append("")
    lines.append("See `phase7e1_aasist_source_audit.json`.")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 7E1 AASIST source audit")
    parser.add_argument(
        "--aasist_src",
        type=str,
        default="code/phase7/aasist/vendor/AASIST",
        help="Local AASIST source directory",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="reports/phase7/phase7e_aasist_experiment/audit",
    )
    parser.add_argument(
        "--allow_missing_source",
        action="store_true",
        help="Do not exit non-zero when source is missing",
    )
    args = parser.parse_args()

    src = resolve_path(args.aasist_src)
    out_dir = resolve_path(args.output_dir)
    data = audit_source(src if src.is_dir() else None, allow_missing=args.allow_missing_source)

    write_json(out_dir / "phase7e1_aasist_source_audit.json", data)
    write_markdown(out_dir / "phase7e1_aasist_source_audit.md", _md_report(data))

    print(f"Phase 7E1 source audit verdict: {data['verdict']}")
    print(f"Wrote: {out_dir / 'phase7e1_aasist_source_audit.json'}")

    if data["verdict"] == "SOURCE_REQUIRED" and not args.allow_missing_source:
        return 1
    return 0


if __name__ == "__main__":
    # Allow running as script: python code/phase7/aasist/integration/audit_aasist_source.py
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    raise SystemExit(main())
