"""
Phase 7C2: Summarize training prep manifests (balance, weights, readiness).

Does not train models.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "code"))


def _md_table(headers: list[str], rows: list[list]) -> str:
    if not rows:
        return "_No data._\n"
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for r in rows:
        lines.append("| " + " | ".join(str(x) for x in r) + " |")
    return "\n".join(lines) + "\n"


def summarize(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame) -> tuple[str, pd.DataFrame]:
    all_df = pd.concat(
        [
            train.assign(_split="train"),
            val.assign(_split="val"),
            test.assign(_split="test"),
        ],
        ignore_index=True,
    )

    summary_rows = []
    for split_name in ("train", "val", "test"):
        sub = all_df[all_df["_split"] == split_name]
        summary_rows.append(
            {
                "split": split_name,
                "total_rows": len(sub),
                "old_rows": int((sub["data_source"] == "old").sum()),
                "phase7c1_rows": int((sub["data_source"] == "phase7c1").sum()),
                "avg_sample_weight": float(pd.to_numeric(sub["sample_weight"], errors="coerce").mean())
                if len(sub)
                else 0,
                "partial_fabrication_rows": int(
                    pd.to_numeric(sub["partial_fabrication_binary"], errors="coerce").fillna(0).eq(1).sum()
                ),
                "use_origin_loss_false": int(
                    (sub["use_origin_loss"].astype(str).str.lower() == "false").sum()
                ),
            }
        )
    summary_df = pd.DataFrame(summary_rows)

    lines = [
        "# Phase 7C2 Dataset Balance Report",
        "",
        "Fine-tuning preparation manifests — **no training performed**.",
        "",
        "## Totals by split",
        "",
        _md_table(
            list(summary_df.columns),
            summary_df.values.tolist(),
        ),
        "",
        "## Rows by data_source",
        "",
        _md_table(
            ["split", "data_source", "count"],
            [
                [k, ds, v]
                for (k, ds), v in all_df.groupby(["_split", "data_source"]).size().items()
            ],
        ),
        "",
        "## Rows by origin_label",
        "",
        _md_table(
            ["split", "origin_label", "count"],
            [
                [k, lab, v]
                for (k, lab), v in all_df.groupby(["_split", "origin_label"]).size().items()
            ],
        ),
        "",
        "## Rows by manipulation_label",
        "",
        _md_table(
            ["split", "manipulation_label", "count"],
            [
                [k, lab, v]
                for (k, lab), v in all_df.groupby(["_split", "manipulation_label"]).size().items()
            ],
        ),
        "",
        "## Rows by attack_hint",
        "",
        _md_table(
            ["split", "attack_hint", "count"],
            [
                [k, ah, v]
                for (k, ah), v in all_df.groupby(["_split", "attack_hint"]).size().items()
            ],
        ),
        "",
        "## Partial fabrication (binary=1)",
        "",
        _md_table(
            ["split", "count"],
            [
                [s, int(v)]
                for s, v in all_df.groupby("_split")["partial_fabrication_binary"]
                .apply(lambda x: pd.to_numeric(x, errors="coerce").fillna(0).eq(1).sum())
                .items()
            ],
        ),
        "",
        "## Average sample_weight by data_source",
        "",
        _md_table(
            ["split", "data_source", "mean_weight"],
            [
                [
                    k,
                    ds,
                    round(
                        float(
                            pd.to_numeric(
                                all_df[(all_df["_split"] == k) & (all_df["data_source"] == ds)][
                                    "sample_weight"
                                ],
                                errors="coerce",
                            ).mean()
                        ),
                        4,
                    ),
                ]
                for k in ("train", "val", "test")
                for ds in sorted(all_df["data_source"].unique())
                if len(all_df[(all_df["_split"] == k) & (all_df["data_source"] == ds)])
            ],
        ),
        "",
        "## Loss mask counts (train)",
        "",
    ]

    train_only = all_df[all_df["_split"] == "train"]
    for col in ("use_origin_loss", "use_manipulation_loss", "use_attack_loss", "use_partial_loss"):
        true_n = int((train_only[col].astype(str).str.lower() == "true").sum())
        false_n = int((train_only[col].astype(str).str.lower() == "false").sum())
        lines.append(f"- `{col}` true: {true_n}, false: {false_n}")

    train_n = len(train)
    p7_train = int((train["data_source"] == "phase7c1").sum())
    old_train = int((train["data_source"] == "old").sum())
    expected_p7 = 128

    lines.extend(
        [
            "",
            "## Phase 7C1 contribution",
            "",
            f"- Train: **{p7_train}** / expected ~{expected_p7}",
            f"- Val: **{int((val['data_source'] == 'phase7c1').sum())}** / expected ~24",
            f"- Test: **{int((test['data_source'] == 'phase7c1').sum())}** / expected ~32",
            "",
            "## Old balanced subset contribution",
            "",
            f"- Train: **{old_train}** (max ~4000 = 4×1000 per attack group)",
            f"- Val: **{int((val['data_source'] == 'old').sum())}** (max ~800)",
            f"- Test: **{int((test['data_source'] == 'old').sum())}** (max ~800)",
            "",
            "## Readiness verdict",
            "",
        ]
    )

    ready = train_n > 0 and p7_train >= 100 and old_train >= 500
    if ready:
        lines.append(
            "**READY FOR REVIEW** — Manifests combine balanced old subset + weighted Phase 7C1. "
            "Run validation, review holdout report, then sign off before Phase 7C3 fine-tuning script work."
        )
    else:
        lines.append(
            "**NEEDS ATTENTION** — Row counts below expected targets. Re-run builder or check inputs."
        )

    lines.append("")
    return "\n".join(lines), summary_df


def main():
    p = argparse.ArgumentParser(description="Phase 7C2 — summarize training prep manifests")
    p.add_argument("--train", type=str, required=True)
    p.add_argument("--val", type=str, required=True)
    p.add_argument("--test", type=str, required=True)
    p.add_argument("--output_md", type=str, default="reports/phase7/phase7c2_training_prep/phase7c2_dataset_balance_report.md")
    p.add_argument("--output_csv", type=str, default="reports/phase7/phase7c2_training_prep/phase7c2_manifest_summary.csv")
    args = p.parse_args()

    train = pd.read_csv(args.train, low_memory=False)
    val = pd.read_csv(args.val, low_memory=False)
    test = pd.read_csv(args.test, low_memory=False)

    md, summary_df = summarize(train, val, test)

    out_md = Path(args.output_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(md, encoding="utf-8")
    print(f"[SAVE] {out_md}")

    out_csv = Path(args.output_csv)
    summary_df.to_csv(out_csv, index=False)
    print(f"[SAVE] {out_csv}")


if __name__ == "__main__":
    main()
