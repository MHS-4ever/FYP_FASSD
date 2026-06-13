"""Run Phase 3 controlled experiments in order: 3A -> 3B -> 3C.

Writes a combined decision report under reports/release_audit/.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PHASE3_OUT = ROOT / "reports" / "release_audit" / "phase3_controlled_experiments_2026-06-13"
SCRIPTS = ROOT / "code" / "release_audit"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--skip-3a", action="store_true")
    parser.add_argument("--skip-3b", action="store_true")
    parser.add_argument("--skip-3c", action="store_true")
    return parser.parse_args()


def run_script(name: str, extra: list[str] | None = None) -> None:
    cmd = [sys.executable, str(SCRIPTS / name)] + (extra or [])
    print(f"RUN: {' '.join(cmd)}", flush=True)
    subprocess.run(cmd, check=True, cwd=str(SCRIPTS))


def read_decision(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else "(not run)"


def main() -> None:
    args = parse_args()
    PHASE3_OUT.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()

    if not args.skip_3a:
        run_script("experiment_3a_resampling_ablation.py", ["--device", args.device])
    if not args.skip_3b:
        run_script("experiment_3b_window_origin.py")
    if not args.skip_3c:
        run_script("experiment_3c_dual_resolution_replay_mixer.py")

    finished = datetime.now(timezone.utc).isoformat()

    summaries = []
    for tag, sub, key in [
        ("3A", "experiment_3a_resampling_ablation", "variant"),
        ("3B", "experiment_3b_window_origin", "aggregator"),
        ("3C", "experiment_3c_dual_resolution_replay_mixer", "feature_mode"),
    ]:
        summary_path = PHASE3_OUT / sub / f"experiment_{tag.lower()}_summary.csv"
        if tag == "3C":
            summary_path = PHASE3_OUT / sub / "experiment_3c_summary.csv"
        if summary_path.is_file():
            df = pd.read_csv(summary_path)
            df.insert(0, "experiment", tag)
            summaries.append(df)

    combined = pd.concat(summaries, ignore_index=True) if summaries else pd.DataFrame()
    if not combined.empty:
        combined.to_csv(PHASE3_OUT / "phase3_all_summaries.csv", index=False)

    report_parts = [
        "# Phase 3 — Controlled experiments (combined decision)",
        "",
        f"- Started: {started}",
        f"- Finished: {finished}",
        "- Order: 3A (resampling) → 3B (window origin) → 3C (dual-resolution replay/mixer)",
        "- New audio collected: **No**",
        "",
        "## Experiment decisions",
        "",
    ]
    for name, sub, fname in [
        ("3A Resampling ablation", "experiment_3a_resampling_ablation", "experiment_3a_decision.md"),
        ("3B Window-level origin", "experiment_3b_window_origin", "experiment_3b_decision.md"),
        ("3C Dual-resolution replay/mixer", "experiment_3c_dual_resolution_replay_mixer", "experiment_3c_decision.md"),
    ]:
        report_parts.append(f"### {name}")
        report_parts.append("")
        report_parts.append(read_decision(PHASE3_OUT / sub / fname))
        report_parts.append("")

    (PHASE3_OUT / "phase3_controlled_experiments_decision.md").write_text(
        "\n".join(report_parts),
        encoding="utf-8",
    )
    print(f"Phase 3 complete -> {PHASE3_OUT}", flush=True)


if __name__ == "__main__":
    main()
