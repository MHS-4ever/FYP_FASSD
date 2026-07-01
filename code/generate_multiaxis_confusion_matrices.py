"""
Generate confusion-matrix figures for the four packaged multi-axis release models.

Source metrics (default):
  reports/release_audit/phase7_final_release_2026-06-13/phase7_final_testing_audios_metrics.csv

Outputs (default: submissions/thesis_preparation/figures/multiaxis/):
  multiaxis_origin_confusion_matrix.png
  multiaxis_replay_confusion_matrix.png
  multiaxis_mixer_confusion_matrix.png
  multiaxis_partial_confusion_matrix.png
  multiaxis_all_axes_confusion_matrices.png  (4-panel summary)
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

AXIS_CONFIG = {
    "origin": {
        "title": "Origin SSL axis (AI-origin evidence)",
        "neg_label": "Human-origin",
        "pos_label": "AI-origin",
        "model_note": "Logistic regression on frozen WavLM SSL features",
    },
    "replay": {
        "title": "Replay axis (replay / rerecording evidence)",
        "neg_label": "No replay",
        "pos_label": "Replay",
        "model_note": "Logistic regression on acoustic features",
    },
    "mixer": {
        "title": "Mixer / channel axis",
        "neg_label": "No mixer/channel",
        "pos_label": "Mixer/channel",
        "model_note": "Logistic regression on acoustic features",
    },
    "partial": {
        "title": "Partial fabrication axis",
        "neg_label": "No partial",
        "pos_label": "Partial fabrication",
        "model_note": "Segment logistic regression (fusion-gated)",
    },
}


def _cm_from_counts(tp: int, tn: int, fp: int, fn: int) -> np.ndarray:
    # Rows = true label (0 negative, 1 positive); cols = predicted.
    return np.array([[tn, fp], [fn, tp]], dtype=int)


def _draw_panel(
    ax: plt.Axes,
    cm: np.ndarray,
    neg_label: str,
    pos_label: str,
    title: str,
    metrics: dict[str, float],
    n: int,
) -> None:
    labels = [neg_label, pos_label]
    im = ax.imshow(cm, interpolation="nearest", cmap="Blues")
    ax.set_title(title, fontsize=11, fontweight="bold", pad=8)
    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels([f"Pred: {neg_label}", f"Pred: {pos_label}"], fontsize=8)
    ax.set_yticklabels([f"True: {neg_label}", f"True: {pos_label}"], fontsize=8)
    ax.set_xlabel("Predicted", fontsize=9)
    ax.set_ylabel("True", fontsize=9)

    cell_names = [["TN", "FP"], ["FN", "TP"]]
    thresh = cm.max() * 0.5 if cm.size else 0
    for i in range(2):
        for j in range(2):
            val = int(cm[i, j])
            ax.text(
                j,
                i,
                f"{cell_names[i][j]}\n{val}",
                ha="center",
                va="center",
                color="white" if cm[i, j] > thresh else "black",
                fontsize=10,
                fontweight="bold",
            )

    metric_line = f"n = {n}  |  Accuracy: {metrics['accuracy'] * 100:.2f}%"
    ax.text(
        0.5,
        -0.18,
        metric_line,
        transform=ax.transAxes,
        va="top",
        ha="center",
        fontsize=10,
        fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#fff8e1", edgecolor="#c9a227", linewidth=1.2),
    )
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)


def _metrics_dict(metrics_row: pd.Series) -> dict[str, float]:
    return {"accuracy": float(metrics_row["accuracy"])}


def _save_single(cm: np.ndarray, cfg: dict, metrics_row: pd.Series, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.5, 5.4))
    metrics = _metrics_dict(metrics_row)
    _draw_panel(
        ax,
        cm,
        cfg["neg_label"],
        cfg["pos_label"],
        cfg["title"],
        metrics,
        int(metrics_row["n"]),
    )
    fig.suptitle(
        f"testing_audios evaluation — {cfg['model_note']}",
        fontsize=9,
        y=0.98,
        color="#444444",
    )
    fig.subplots_adjust(bottom=0.16)
    fig.tight_layout(rect=[0, 0.06, 1, 0.93])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[SAVE] {out_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate multi-axis confusion matrix figures.")
    parser.add_argument(
        "--metrics-csv",
        default=str(
            ROOT
            / "reports"
            / "release_audit"
            / "phase7_final_release_2026-06-13"
            / "phase7_final_testing_audios_metrics.csv"
        ),
    )
    parser.add_argument(
        "--output-dir",
        default=str(ROOT / "submissions" / "thesis_preparation" / "figures" / "multiaxis"),
    )
    args = parser.parse_args()

    metrics_path = Path(args.metrics_csv)
    out_dir = Path(args.output_dir)
    df = pd.read_csv(metrics_path)

    panels: list[tuple[str, np.ndarray, dict, pd.Series]] = []
    for axis in ["origin", "replay", "mixer", "partial"]:
        row = df.loc[df["axis"] == axis].iloc[0]
        cm = _cm_from_counts(int(row["tp"]), int(row["tn"]), int(row["fp"]), int(row["fn"]))
        cfg = AXIS_CONFIG[axis]
        panels.append((axis, cm, cfg, row))
        _save_single(cm, cfg, row, out_dir / f"multiaxis_{axis}_confusion_matrix.png")

    fig, axes = plt.subplots(2, 2, figsize=(15, 13))
    for ax, (axis, cm, cfg, row) in zip(axes.ravel(), panels):
        metrics = _metrics_dict(row)
        _draw_panel(
            ax,
            cm,
            cfg["neg_label"],
            cfg["pos_label"],
            cfg["title"],
            metrics,
            int(row["n"]),
        )

    fig.suptitle(
        "FASSD multi-axis release models — confusion matrices (testing_audios, evaluation-only)",
        fontsize=13,
        fontweight="bold",
        y=0.98,
    )
    fig.text(
        0.5,
        0.94,
        "Experimental forensic prototype. Small external eval set; manual review required.",
        ha="center",
        fontsize=9,
        color="#555555",
    )
    fig.subplots_adjust(hspace=0.55, wspace=0.35)
    fig.tight_layout(rect=[0, 0.02, 1, 0.91])
    combined = out_dir / "multiaxis_all_axes_confusion_matrices.png"
    fig.savefig(combined, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[SAVE] {combined}")

    summary_md = out_dir / "README.md"
    lines = [
        "# Multi-axis confusion matrices",
        "",
        "Generated from official release-audit metrics on **testing_audios** (evaluation-only).",
        "",
        f"Source: `{metrics_path.relative_to(ROOT).as_posix()}`",
        "",
        "| Figure | Axis | n | TP | TN | FP | FN |",
        "|--------|------|---|----|----|----|-----|",
    ]
    for axis, cm, _cfg, row in panels:
        lines.append(
            f"| `multiaxis_{axis}_confusion_matrix.png` | {axis} | {int(row['n'])} | "
            f"{int(row['tp'])} | {int(row['tn'])} | {int(row['fp'])} | {int(row['fn'])} |"
        )
    lines.extend(
        [
            "",
            "Combined 4-panel: `multiaxis_all_axes_confusion_matrices.png`",
            "",
            "Regenerate:",
            "```bash",
            "python code/generate_multiaxis_confusion_matrices.py",
            "```",
        ]
    )
    summary_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[SAVE] {summary_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
