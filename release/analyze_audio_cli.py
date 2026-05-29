#!/usr/bin/env python3
"""Phase 9C CLI: live single-audio inference (experimental forensic prototype)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure release/ is on path for `src` package imports.
_RELEASE_DIR = Path(__file__).resolve().parent
if str(_RELEASE_DIR) not in sys.path:
    sys.path.insert(0, str(_RELEASE_DIR))

from src.inference_pipeline import analyze_audio_file  # noqa: E402
from src.utils import write_json, write_markdown  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Analyze one audio file (Phase 9C experimental prototype).")
    p.add_argument("--audio", required=True, help="Path to input audio file")
    p.add_argument("--case_id", default=None)
    p.add_argument("--output_dir", default="release/sample_outputs")
    p.add_argument("--device", default="auto")
    p.add_argument("--debug", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    root = _RELEASE_DIR.parent
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = (root / output_dir).resolve()

    result = analyze_audio_file(
        audio_path=args.audio,
        case_id=args.case_id,
        output_dir=output_dir,
        device=args.device,
        return_debug=args.debug,
    )

    case_id = result.get("case_id", "CASE-UNKNOWN")
    json_path = output_dir / f"{case_id}_analysis.json"
    md_path = output_dir / f"{case_id}_report.md"
    write_json(json_path, result)
    write_markdown(md_path, result.get("report_markdown", ""))

    print(f"Case: {case_id}")
    print(f"Status: {result.get('status')}")
    print(f"Fusion: {result.get('fusion_status')}")
    print(f"Manual review: {result.get('manual_review_required')}")
    print(result.get("forensic_summary", ""))
    print(f"JSON: {json_path}")
    print(f"Markdown: {md_path}")
    return 0 if result.get("status") != "error" else 1


if __name__ == "__main__":
    raise SystemExit(main())
