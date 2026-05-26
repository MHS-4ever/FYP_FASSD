"""
Phase 7C4: Compare Phase 7A holdout product_status across baseline vs R2 checkpoints.

Analysis only — does not train or modify checkpoints.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "code"))

from phase7.phase7c4_common import md_table, status_counts  # noqa: E402
from phase7.phase7_paths import (  # noqa: E402
    HOLDOUT_PRODUCT,
    P7,
    R2_HOLDOUT_LOSS,
    R2_HOLDOUT_PRODUCT,
    resolve_phase7_report_path,
)

P7A_STATUS_GROUPS = {
    "clean_human": [
        "clean_human_accepted",
        "clean_human_borderline",
        "clean_human_false_alarm",
    ],
    "direct_ai": [
        "direct_ai_detected",
        "direct_ai_missed",
        "direct_ai_file_level_missed_but_segment_suspicious",
        "direct_ai_borderline",
    ],
    "processed_human": [
        "processed_human_manipulation_detected",
        "processed_human_missed",
    ],
    "ai_replay_or_processed": [
        "ai_replay_or_processed_detected",
        "ai_replay_or_processed_missed",
        "ai_replay_file_level_missed_but_segment_suspicious",
        "processed_ai_file_level_missed_but_segment_suspicious",
    ],
    "partial_fabrication": [
        "partial_fabrication_detected",
        "partial_fabrication_missed",
        "partial_not_evaluated_missing_timestamp",
        "partial_fabrication_not_evaluable",
    ],
}


def load_product_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(resolve_phase7_report_path(path), low_memory=False)
    id_col = "test_id" if "test_id" in df.columns else "sample_id"
    df[id_col] = df[id_col].astype(str)
    return df


def count_group(df: pd.DataFrame, statuses: list[str], col: str = "product_status") -> dict[str, int]:
    c = status_counts(df, col)
    return {s: c.get(s, 0) for s in statuses}


def summarize_source(df: pd.DataFrame, label: str) -> dict:
    ch = df[
        (df["manipulation_type"].astype(str).str.lower() == "clean_direct")
        & (df["ground_truth_origin"].astype(str).str.lower() == "human")
    ]
    return {
        "source": label,
        "n": len(df),
        "clean_human": count_group(ch, P7A_STATUS_GROUPS["clean_human"]),
        "direct_ai": count_group(
            df[
                (df["manipulation_type"].astype(str).str.lower() == "clean_direct")
                & (df["ground_truth_origin"].astype(str).str.lower() == "ai")
            ],
            P7A_STATUS_GROUPS["direct_ai"],
        ),
        "processed_human": count_group(df, P7A_STATUS_GROUPS["processed_human"]),
        "ai_replay_or_processed": count_group(df, P7A_STATUS_GROUPS["ai_replay_or_processed"]),
        "partial_fabrication": count_group(
            df[df["manipulation_type"].astype(str).str.lower() == "partial_ai_insert"],
            P7A_STATUS_GROUPS["partial_fabrication"],
        ),
    }


def flatten_summary(s: dict) -> dict:
    row = {"source": s["source"], "n_samples": s["n"]}
    for group, counts in s.items():
        if group in ("source", "n"):
            continue
        for status, n in counts.items():
            row[f"{group}__{status}"] = n
    return row


def write_holdout_md(
    path: Path,
    baseline: dict,
    r2_product: dict,
    r2_loss: dict,
) -> None:
    lines = [
        "# Phase 7C4 — Phase 7A Holdout Impact",
        "",
        "Compares `product_status` on the **controlled holdout** (T1–T5) across:",
        "- Original baseline model",
        "- R2 `best_product`",
        "- R2 `best_loss`",
        "",
        "**Note:** The calibrated decision layer (`apply_phase7c4_decision_layer.py`) is evaluated on Phase 7C1 in this phase. "
        "This report compares checkpoint outputs on holdout only. "
        "**A decision-layer prototype is not fully accepted until holdout impact is reviewed.**",
        "",
        "> Borderline is not accepted as clean; it means manual review.",
        "",
        "## Clean human (holdout)",
        "",
    ]

    def fmt_ch(s: dict) -> str:
        c = s["clean_human"]
        return (
            f"accepted={c.get('clean_human_accepted', 0)}, "
            f"borderline={c.get('clean_human_borderline', 0)}, "
            f"false_alarm={c.get('clean_human_false_alarm', 0)}"
        )

    lines.append(
        md_table(
            ["Source", "Counts"],
            [
                ["Baseline", fmt_ch(baseline)],
                ["R2 best_product", fmt_ch(r2_product)],
                ["R2 best_loss", fmt_ch(r2_loss)],
            ],
        )
    )

    def fmt_group(s: dict, key: str, labels: list[str]) -> list:
        c = s[key]
        return [key, *[str(c.get(l, 0)) for l in labels]]

    for title, key, labels in [
        ("Direct AI", "direct_ai", P7A_STATUS_GROUPS["direct_ai"]),
        (
            "Processed human manipulation",
            "processed_human",
            P7A_STATUS_GROUPS["processed_human"],
        ),
        (
            "AI replay / processed AI",
            "ai_replay_or_processed",
            P7A_STATUS_GROUPS["ai_replay_or_processed"],
        ),
        (
            "Partial fabrication",
            "partial_fabrication",
            P7A_STATUS_GROUPS["partial_fabrication"],
        ),
    ]:
        lines += [f"## {title}", ""]
        headers = ["Group"] + [l.replace("_", " ")[:24] for l in labels]
        rows = [
            ["Baseline", *[str(baseline[key].get(l, 0)) for l in labels]],
            ["R2 product", *[str(r2_product[key].get(l, 0)) for l in labels]],
            ["R2 loss", *[str(r2_loss[key].get(l, 0)) for l in labels]],
        ]
        lines.append(md_table(headers[: len(rows[0])], rows))

    lines += [
        "",
        "## Acceptance note",
        "",
        "- Do **not** treat R2 holdout numbers as product sign-off without comparing to baseline segment-suspicious counts.",
        "- If R2 collapses direct-AI segment-suspicious or processed-human detection vs baseline, keep baseline segment rules in the decision layer.",
        "- More external audio beyond T1–T5 is required before market-level claims.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    p = argparse.ArgumentParser(description="Phase 7C4 Phase 7A holdout impact")
    p.add_argument("--baseline_csv", type=str, default=HOLDOUT_PRODUCT)
    p.add_argument("--r2_product_csv", type=str, default=R2_HOLDOUT_PRODUCT)
    p.add_argument("--r2_loss_csv", type=str, default=R2_HOLDOUT_LOSS)
    p.add_argument(
        "--output_csv",
        type=str,
        default=f"{P7}/phase7c4_calibration/calibration_outputs/phase7c4_phase7a_holdout_impact.csv",
    )
    p.add_argument(
        "--output_md",
        type=str,
        default=f"{P7}/phase7c4_calibration/phase7c4_phase7a_holdout_impact.md",
    )
    args = p.parse_args()

    out_csv = resolve_phase7_report_path(args.output_csv, for_write=True)
    out_md = resolve_phase7_report_path(args.output_md, for_write=True)

    baseline_df = load_product_csv(Path(args.baseline_csv))
    r2p_df = load_product_csv(Path(args.r2_product_csv))
    r2l_df = load_product_csv(Path(args.r2_loss_csv))

    baseline_s = summarize_source(baseline_df, "baseline")
    r2p_s = summarize_source(r2p_df, "r2_product")
    r2l_s = summarize_source(r2l_df, "r2_loss")

    rows = [flatten_summary(baseline_s), flatten_summary(r2p_s), flatten_summary(r2l_s)]
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out_csv, index=False)
    print(f"[SAVE] {out_csv}")

    write_holdout_md(out_md, baseline_s, r2p_s, r2l_s)
    print(f"[SAVE] {out_md}")


if __name__ == "__main__":
    main()
