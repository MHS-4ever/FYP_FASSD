"""
Phase 7E1: Inspect expected AASIST I/O from source files (no training).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from _common import (
    CONFIG_EXTENSIONS,
    discover_model_candidates,
    extract_io_hints_from_text,
    list_files_by_extensions,
    list_python_files,
    read_text_snippet,
    resolve_path,
    utc_now_iso,
    write_json,
    write_markdown,
)

DATASET_KEYWORDS = ("dataset", "dataloader", "data_loader", "collate", "load_data")


def inspect_io(aasist_src: Path | None, *, allow_missing: bool) -> dict[str, Any]:
    result: dict[str, Any] = {
        "timestamp_utc": utc_now_iso(),
        "aasist_src": str(aasist_src) if aasist_src else None,
        "verdict": "SOURCE_REQUIRED",
        "config_inspections": [],
        "dataset_file_inspections": [],
        "aggregated_hints": {
            "sample_rate": [],
            "input_length": [],
            "n_fft": [],
            "labels": [],
            "checkpoint_keys": [],
        },
        "unknowns": [
            "Exact tensor layout (waveform vs spectrogram) without running upstream code",
            "Official checkpoint key names without loading a real checkpoint",
            "Training label CSV format for FASSD until Phase 7E2 adapter",
        ],
        "phase7e2_notes": [],
    }

    if not aasist_src or not aasist_src.is_dir():
        result["user_actions"] = [
            "Provide AASIST source at code/phase7/aasist/vendor/AASIST or external/AASIST",
            "Re-run after source is available",
        ]
        return result

    root = aasist_src
    configs = list_files_by_extensions(root, CONFIG_EXTENSIONS)
    for cfg in configs[:25]:
        text = read_text_snippet(cfg, 12000)
        hints = extract_io_hints_from_text(text)
        result["config_inspections"].append(
            {
                "file": str(cfg.relative_to(root)).replace("\\", "/"),
                "hints": hints,
            }
        )
        for k, vals in hints.items():
            result["aggregated_hints"][k].extend(vals)

    py_files = list_python_files(root)
    for py in py_files:
        rel = str(py.relative_to(root)).replace("\\", "/").lower()
        if not any(k in rel for k in DATASET_KEYWORDS):
            continue
        text = read_text_snippet(py, 12000)
        hints = extract_io_hints_from_text(text)
        result["dataset_file_inspections"].append(
            {
                "file": str(py.relative_to(root)).replace("\\", "/"),
                "hints": hints,
            }
        )
        for k, vals in hints.items():
            result["aggregated_hints"][k].extend(vals)

    # Dedupe hints
    for k in result["aggregated_hints"]:
        seen = set()
        uniq = []
        for v in result["aggregated_hints"][k]:
            if v not in seen:
                seen.add(v)
                uniq.append(v)
        result["aggregated_hints"][k] = uniq[:20]

    result["model_candidates"] = discover_model_candidates(root)

    if result["config_inspections"] or result["dataset_file_inspections"]:
        result["verdict"] = "PASS"
        result["phase7e2_notes"] = [
            "Build adapter to emit audio paths + binary risk_target per PHASE7E0_AASIST_LABEL_STRATEGY.md",
            "Map FASSD manifests using phase7e0_selected_paths.json canonical paths",
            "Align sample rate / clip length with values found in config (if any)",
            "Support partial-fabrication suspicious windows from 7C1 manifest",
            "Never include Phase 7A holdout in train/val",
        ]
        if not result["aggregated_hints"]["sample_rate"]:
            result["unknowns"].append("sample_rate not found in configs — confirm from upstream README (often 16 kHz)")
    else:
        result["verdict"] = "PASS_WITH_WARNINGS"
        result["notes"] = "Source present but few config/dataset hints detected"

    return result


def _md(data: dict[str, Any]) -> list[str]:
    lines = [
        "# Phase 7E1 — AASIST Expected I/O Inspection",
        "",
        f"**Generated:** {data['timestamp_utc']}  ",
        f"**Verdict:** `{data['verdict']}`  ",
        f"**Source:** `{data.get('aasist_src') or '(missing)'}`  ",
        "",
        "## Aggregated hints (heuristic)",
        "",
    ]
    for k, vals in data.get("aggregated_hints", {}).items():
        lines.append(f"### {k}")
        if vals:
            for v in vals[:15]:
                lines.append(f"- `{v}`")
        else:
            lines.append("- _(none detected)_")
        lines.append("")

    lines.append("## Unknowns / manual confirmation")
    lines.append("")
    for u in data.get("unknowns", []):
        lines.append(f"- {u}")
    lines.append("")

    if data.get("phase7e2_notes"):
        lines.append("## Notes for Phase 7E2")
        lines.append("")
        for n in data["phase7e2_notes"]:
            lines.append(f"- {n}")
        lines.append("")

    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 7E1 AASIST expected I/O inspection")
    parser.add_argument("--aasist_src", type=str, default="code/phase7/aasist/vendor/AASIST")
    parser.add_argument(
        "--output_dir",
        type=str,
        default="reports/phase7/phase7e_aasist_experiment/audit",
    )
    parser.add_argument("--allow_missing_source", action="store_true")
    args = parser.parse_args()

    src = resolve_path(args.aasist_src)
    data = inspect_io(src if src.is_dir() else None, allow_missing=args.allow_missing_source)
    out = resolve_path(args.output_dir)
    write_json(out / "phase7e1_expected_io_report.json", data)
    write_markdown(out / "phase7e1_expected_io_report.md", _md(data))

    print(f"Phase 7E1 expected IO verdict: {data['verdict']}")
    if data["verdict"] == "SOURCE_REQUIRED" and not args.allow_missing_source:
        return 1
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    raise SystemExit(main())
