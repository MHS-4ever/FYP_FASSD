"""Phase 5 — validate P5 segment dataset and write F9-stripped feature manifest."""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from phase5_partial_common import (
    DEFAULT_OUT,
    F9_FORBIDDEN_FEATURES,
    P5_SEGMENT_DATASET,
    attach_leakage_safe_split,
    build_phase5_model_features,
    progress,
    write_f9_audit,
)

ROOT = Path(__file__).resolve().parents[2]
ASSEMBLE_SCRIPT = ROOT / "code" / "phase9" / "partial_redesign" / "assemble_phase9d_p5_partial_datasets.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT))
    parser.add_argument("--segment-dataset", default=str(P5_SEGMENT_DATASET))
    parser.add_argument("--assemble-if-missing", action="store_true")
    parser.add_argument("--sample-rows", type=int, default=0, help="If >0, write a small sample CSV for smoke tests")
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_segment_dataset(path: Path, assemble: bool) -> None:
    if path.is_file():
        return
    if not assemble:
        raise FileNotFoundError(
            f"Segment dataset missing: {path}\n"
            "Run with --assemble-if-missing or assemble Phase 9D-P5 datasets first."
        )
    progress("[phase5] assembling Phase 9D-P5 datasets (long — segment master is large)")
    subprocess.run([sys.executable, str(ASSEMBLE_SCRIPT)], check=True)
    if not path.is_file():
        raise FileNotFoundError(f"Assembly finished but segment dataset still missing: {path}")


def summarize_split(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for split, g in df.groupby("leakage_safe_split", dropna=False):
        pos = int(pd.to_numeric(g["target_is_fabricated_segment"], errors="coerce").fillna(0).sum())
        rows.append(
            {
                "leakage_safe_split": split,
                "segment_rows": int(len(g)),
                "positive_segments": pos,
                "partial_files": int(g[g["file_category"].isin(["ai_fabricated", "human_fabricated"])]["file_id"].nunique()),
            }
        )
    return pd.DataFrame(rows)


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    seg_path = Path(args.segment_dataset)

    ensure_segment_dataset(seg_path, args.assemble_if_missing)
    progress(f"[phase5] reading segment dataset columns from {seg_path}")
    header = pd.read_csv(seg_path, nrows=0)
    model_features = build_phase5_model_features(list(header.columns))
    write_f9_audit(out_dir, model_features)

    # Lightweight split summary — read only required columns.
    usecols = [
        c
        for c in [
            "audio_path",
            "file_id",
            "file_category",
            "target_is_fabricated_segment",
            "leakage_safe_split",
            "allowed_use",
        ]
        if c in header.columns
    ]
    progress("[phase5] loading segment rows for split summary (may take ~1 min)")
    df = pd.read_csv(seg_path, usecols=usecols, low_memory=False)
    df = attach_leakage_safe_split(df)
    split_summary = summarize_split(df)
    split_summary.to_csv(out_dir / "phase5_segment_split_summary.csv", index=False)

    # Map file_id -> split for train script fast join
    file_split = (
        df.groupby("file_id", dropna=False)["leakage_safe_split"]
        .agg(lambda s: s.dropna().astype(str).mode().iloc[0] if len(s.dropna()) else "")
        .reset_index()
    )
    file_split.to_csv(out_dir / "phase5_file_leakage_split_map.csv", index=False)

    if args.sample_rows > 0:
        sample = df.head(args.sample_rows)
        sample.to_csv(out_dir / "phase5_segment_dataset_sample.csv", index=False)

    report = [
        "# Phase 5 — dataset preparation",
        "",
        f"Generated: {utc_now()}",
        "",
        f"Source segment dataset: `{seg_path}`",
        f"Model features (F9 removed): **{len(model_features)}**",
        f"F9 features removed from inputs: **{len(F9_FORBIDDEN_FEATURES)}**",
        "",
        "## Split summary",
        "",
        split_summary.to_string(index=False),
        "",
        "Training uses existing Phase 7 segment labels. No augmentation.",
    ]
    (out_dir / "phase5_dataset_prepare_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    progress(f"[phase5] prepare complete -> {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
