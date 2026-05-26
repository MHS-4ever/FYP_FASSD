"""
Phase 7E3B: Validate AASIST fine-tuning manifests before training (hardened checks).
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd

from _common import ensure_dir, resolve_path, utc_now_iso, write_markdown
from aasist_eval_common import resolve_audio_path

REQUIRED_COLUMNS = [
    "finetune_row_id",
    "audio_path",
    "split",
    "risk_target",
    "aasist_label",
    "sample_weight",
    "window_strategy",
    "window_start_time",
    "window_end_time",
    "use_for_aasist_training",
    "split_group_id",
    "source_branch_role",
]

HOLDOUT_PATTERNS = (
    "testing_audios/",
    "forensic_test",
    "phase7a",
    "controlled_holdout",
)

WEIGHTED_RATIO_WARN = 3.0


def _is_holdout_row(row: pd.Series) -> bool:
    import re

    blob = " ".join(
        str(row.get(c, "")) for c in ("audio_path", "data_source", "sample_id", "notes", "source_subset")
    ).lower()
    sid = str(row.get("sample_id", ""))
    if any(p in blob for p in HOLDOUT_PATTERNS):
        return True
    return bool(re.match(r"^T\d", sid))


def _expected_aasist_label(risk_target: int) -> int:
    return 1 if risk_target == 0 else 0


def compute_weighted_balance(df: pd.DataFrame) -> dict:
    if df.empty or "risk_target" not in df.columns:
        return {"w0": 0.0, "w1": 0.0, "ratio_pos_to_neg": None, "ratio_neg_to_pos": None}
    w0 = float(df.loc[df["risk_target"] == 0, "sample_weight"].sum())
    w1 = float(df.loc[df["risk_target"] == 1, "sample_weight"].sum())
    ratio_pos_to_neg = (w1 / w0) if w0 > 0 else None
    ratio_neg_to_pos = (w0 / w1) if w1 > 0 else None
    return {
        "w0": w0,
        "w1": w1,
        "ratio_pos_to_neg": ratio_pos_to_neg,
        "ratio_neg_to_pos": ratio_neg_to_pos,
    }


def clean_human_stats(df: pd.DataFrame, split_name: str) -> dict:
    if df.empty or "source_branch_role" not in df.columns:
        return {"split": split_name, "window_count": 0, "total_sample_weight": 0.0}
    mask = df["source_branch_role"].astype(str).str.contains("clean_human", case=False, na=False)
    ch = df[mask]
    return {
        "split": split_name,
        "window_count": len(ch),
        "total_sample_weight": float(ch["sample_weight"].sum()) if len(ch) else 0.0,
    }


def validate_manifest(path: Path, split_name: str) -> tuple[list[dict], list[dict], pd.DataFrame]:
    issues: list[dict] = []
    warnings: list[dict] = []
    df = pd.read_csv(path)

    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            issues.append({"split": split_name, "check": "required_columns", "detail": f"missing {col}"})

    if df.empty:
        issues.append({"split": split_name, "check": "empty_manifest", "detail": "no rows"})
        return issues, warnings, df

    for idx, row in df.iterrows():
        rid = row.get("finetune_row_id", idx)
        if _is_holdout_row(row):
            issues.append({"split": split_name, "finetune_row_id": rid, "check": "holdout_leak", "detail": "7A/holdout pattern"})

        ap = str(row.get("audio_path", "")).strip()
        if not ap:
            issues.append({"split": split_name, "finetune_row_id": rid, "check": "audio_path", "detail": "blank"})
        elif resolve_audio_path(ap) is None:
            warnings.append({"split": split_name, "finetune_row_id": rid, "check": "audio_missing", "detail": ap})

        try:
            rt_i = int(row["risk_target"])
            if rt_i not in (0, 1):
                issues.append({"split": split_name, "finetune_row_id": rid, "check": "risk_target", "detail": rt_i})
            else:
                expected_al = _expected_aasist_label(rt_i)
                try:
                    al_i = int(row["aasist_label"])
                    if al_i != expected_al:
                        issues.append(
                            {
                                "split": split_name,
                                "finetune_row_id": rid,
                                "check": "aasist_label_mapping",
                                "detail": f"risk_target={rt_i} aasist_label={al_i} expected={expected_al}",
                            }
                        )
                except (TypeError, ValueError):
                    issues.append(
                        {
                            "split": split_name,
                            "finetune_row_id": rid,
                            "check": "aasist_label_mapping",
                            "detail": f"invalid aasist_label={row.get('aasist_label')}",
                        }
                    )
        except (TypeError, ValueError, KeyError):
            issues.append({"split": split_name, "finetune_row_id": rid, "check": "risk_target", "detail": row.get("risk_target")})

        sw = float(row.get("sample_weight", 0))
        if sw < 0.1 or sw > 4.0:
            issues.append({"split": split_name, "finetune_row_id": rid, "check": "sample_weight", "detail": sw})

        partial = str(row.get("manipulation_type", "")).lower() == "partial_ai_insert" or str(
            row.get("partial_fabrication_binary", "")
        ).strip() in ("1", "True", "true")
        if partial:
            s = row.get("suspicious_start_time")
            e = row.get("suspicious_end_time")
            try:
                if pd.isna(s) or pd.isna(e) or float(e) <= float(s):
                    issues.append(
                        {"split": split_name, "finetune_row_id": rid, "check": "partial_timestamps", "detail": f"{s},{e}"}
                    )
            except (TypeError, ValueError):
                issues.append(
                    {"split": split_name, "finetune_row_id": rid, "check": "partial_timestamps", "detail": f"{s},{e}"}
                )

    if all(c in df.columns for c in ("audio_path", "window_start_time", "window_end_time")):
        dup = df.duplicated(subset=["audio_path", "window_start_time", "window_end_time"], keep=False)
        for idx in df[dup].index[:50]:
            warnings.append(
                {
                    "split": split_name,
                    "finetune_row_id": df.at[idx, "finetune_row_id"],
                    "check": "duplicate_window",
                    "detail": "same audio_path+window times",
                }
            )

    return issues, warnings, df


def check_split_leakage(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame) -> list[dict]:
    issues = []
    if "split_group_id" not in train.columns:
        return issues
    train_g = set(train["split_group_id"].astype(str))
    val_g = set(val["split_group_id"].astype(str)) if not val.empty else set()
    test_g = set(test["split_group_id"].astype(str)) if not test.empty else set()
    if train_g & val_g:
        issues.append({"check": "split_leakage", "detail": f"train/val shared split_group_id: {len(train_g & val_g)}"})
    if train_g & test_g:
        issues.append({"check": "split_leakage", "detail": f"train/test shared split_group_id: {len(train_g & test_g)}"})
    if val_g & test_g:
        issues.append({"check": "split_leakage", "detail": f"val/test shared split_group_id: {len(val_g & test_g)}"})
    return issues


def check_weighted_balance(
    df: pd.DataFrame, split_name: str, warnings: list[dict]
) -> dict:
    bal = compute_weighted_balance(df)
    if bal["ratio_pos_to_neg"] is not None and bal["ratio_pos_to_neg"] > WEIGHTED_RATIO_WARN:
        warnings.append(
            {
                "check": "weighted_balance",
                "split": split_name,
                "detail": f"weighted risk_target=1:0 ratio={bal['ratio_pos_to_neg']:.2f} > {WEIGHTED_RATIO_WARN}",
            }
        )
    if bal["ratio_neg_to_pos"] is not None and bal["ratio_neg_to_pos"] > WEIGHTED_RATIO_WARN:
        warnings.append(
            {
                "check": "weighted_balance",
                "split": split_name,
                "detail": f"weighted risk_target=0:1 ratio={bal['ratio_neg_to_pos']:.2f} > {WEIGHTED_RATIO_WARN}",
            }
        )
    return bal


def _md_table(headers: list[str], rows: list[list]) -> str:
    if not rows:
        return "_No rows._\n"
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for r in rows:
        lines.append("| " + " | ".join(str(x) for x in r) + " |")
    return "\n".join(lines) + "\n"


def write_validation_report(
    out_dir: Path,
    verdict: str,
    all_issues: list[dict],
    all_warnings: list[dict],
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    balance: dict[str, dict],
    ch_stats: list[dict],
) -> None:
    lines = [
        "# Phase 7E3B — AASIST Fine-Tune Manifest Validation (hardened)",
        "",
        f"**Generated:** {utc_now_iso()}",
        f"**Verdict:** **{verdict}**",
        "",
        f"- Issues: **{len(all_issues)}**",
        f"- Warnings: **{len(all_warnings)}**",
        "",
        "## Row counts",
        "",
        _md_table(
            ["split", "rows"],
            [
                ["train", len(train_df)],
                ["val", len(val_df)],
                ["test", len(test_df)],
                ["total", len(train_df) + len(val_df) + len(test_df)],
            ],
        ),
        "",
        "## risk_target counts (unweighted)",
        "",
    ]

    for name, sdf in ("train", train_df), ("val", val_df), ("test", test_df):
        if sdf.empty:
            continue
        lines.append(f"### {name}")
        lines.append(
            _md_table(
                ["risk_target", "count"],
                [[rt, cnt] for rt, cnt in sorted(Counter(sdf["risk_target"]).items())],
            )
        )
        lines.append("")

    lines.extend(["## Weighted risk balance (sum of sample_weight)", ""])
    bal_rows = []
    for name in ("train", "val", "test"):
        b = balance.get(name, {})
        bal_rows.append(
            [
                name,
                f"{b.get('w0', 0):.1f}",
                f"{b.get('w1', 0):.1f}",
                f"{b.get('ratio_pos_to_neg', 0) or 0:.2f}" if b.get("ratio_pos_to_neg") else "n/a",
                f"{b.get('ratio_neg_to_pos', 0) or 0:.2f}" if b.get("ratio_neg_to_pos") else "n/a",
            ]
        )
    lines.append(
        _md_table(
            ["split", "weighted_risk_0", "weighted_risk_1", "ratio_1_to_0", "ratio_0_to_1"],
            bal_rows,
        )
    )
    lines.extend(
        [
            "",
            f"Warn if either weighted ratio exceeds **{WEIGHTED_RATIO_WARN}** (class imbalance after weighting).",
            "",
            "## Role distribution (train)",
            "",
        ]
    )
    if not train_df.empty and "source_branch_role" in train_df.columns:
        role_rows = [[role, cnt] for role, cnt in Counter(train_df["source_branch_role"]).most_common()]
        lines.append(_md_table(["source_branch_role", "count"], role_rows))
    else:
        lines.append("_No train role data._\n")

    lines.extend(["", "## Clean-human window summary", ""])
    lines.append(
        _md_table(
            ["split", "window_count", "total_sample_weight"],
            [[s["split"], s["window_count"], f"{s['total_sample_weight']:.1f}"] for s in ch_stats],
        )
    )

    lines.extend(
        [
            "",
            "## Training readiness note",
            "",
            "Manifest validation PASS does **not** mean training is ready. Review `AASIST_L_FINETUNE_TRAINING_PLAN.md`: "
            "**do not use plain weighted CE only** — require balanced sampler and/or class-balanced loss.",
            "",
            "## Checks performed",
            "",
            "1. Required columns",
            "2. `aasist_label` vs `risk_target` (0→1 bonafide, 1→0 spoof)",
            "3. Weighted class balance per split",
            "4. Clean-human count and weight per split",
            "5. Holdout leak, audio paths, partial timestamps, split leakage",
            "",
        ]
    )

    if all_issues:
        lines.extend(["## Issues", ""])
        for it in all_issues[:50]:
            lines.append(f"- `{it}`")
        lines.append("")
    if all_warnings:
        lines.extend(["## Warnings", ""])
        for w in all_warnings[:50]:
            lines.append(f"- `{w}`")
        lines.append("")

    write_markdown(out_dir / "aasist_finetune_manifest_validation_report.md", lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate AASIST fine-tune manifests (hardened)")
    parser.add_argument("--train", type=str, required=True)
    parser.add_argument("--val", type=str, required=True)
    parser.add_argument("--test", type=str, required=True)
    parser.add_argument("--output_dir", type=str, required=True)
    parser.add_argument("--rejected_csv", type=str, default="", help="Optional path to aasist_finetune_rejected_rows.csv")
    parser.add_argument("--allow_warnings", action="store_true")
    args = parser.parse_args()

    out_dir = ensure_dir(resolve_path(args.output_dir))
    train_p, val_p, test_p = resolve_path(args.train), resolve_path(args.val), resolve_path(args.test)

    all_issues: list[dict] = []
    all_warnings: list[dict] = []

    ti, tw, train_df = validate_manifest(train_p, "train")
    vi, vw, val_df = validate_manifest(val_p, "val")
    tei, tew, test_df = validate_manifest(test_p, "test")
    all_issues.extend(ti + vi + tei)
    all_warnings.extend(tw + vw + tew)
    all_issues.extend(check_split_leakage(train_df, val_df, test_df))

    balance = {
        "train": check_weighted_balance(train_df, "train", all_warnings),
        "val": check_weighted_balance(val_df, "val", all_warnings),
        "test": check_weighted_balance(test_df, "test", all_warnings),
    }

    ch_stats = [clean_human_stats(train_df, "train"), clean_human_stats(val_df, "val"), clean_human_stats(test_df, "test")]

    if not train_df.empty:
        ch_train = clean_human_stats(train_df, "train")
        if ch_train["window_count"] < 20:
            all_warnings.append({"check": "clean_human_count", "split": "train", "detail": f"windows={ch_train['window_count']}"})

    dist_rows = []
    for name, sdf in ("train", train_df), ("val", val_df), ("test", test_df):
        if sdf.empty:
            continue
        for rt, cnt in Counter(sdf["risk_target"]).items():
            dist_rows.append({"split": name, "risk_target": rt, "count": cnt})
    pd.DataFrame(dist_rows).to_csv(out_dir / "aasist_finetune_split_distribution.csv", index=False)
    pd.DataFrame(dist_rows).to_csv(out_dir / "aasist_finetune_label_distribution.csv", index=False)

    warn_df = pd.DataFrame(all_warnings) if all_warnings else pd.DataFrame(columns=["check", "split", "detail"])
    warn_df.to_csv(out_dir / "aasist_finetune_warning_rows.csv", index=False)

    rejected_cols = ["row_id", "sample_id", "audio_path", "reason"]
    rejected_path = resolve_path(args.rejected_csv) if args.rejected_csv else train_p.parent / "aasist_finetune_rejected_rows.csv"
    if rejected_path.is_file() and rejected_path.stat().st_size > 0:
        try:
            rej = pd.read_csv(rejected_path)
        except pd.errors.EmptyDataError:
            rej = pd.DataFrame(columns=rejected_cols)
    else:
        rej = pd.DataFrame(columns=rejected_cols)
    if rej.empty:
        pd.DataFrame(columns=rejected_cols).to_csv(rejected_path, index=False)

    verdict = "PASS" if not all_issues else "FAIL"
    if all_warnings and verdict == "PASS":
        verdict = "PASS_WITH_WARNINGS" if args.allow_warnings else "FAIL"

    write_validation_report(out_dir, verdict, all_issues, all_warnings, train_df, val_df, test_df, balance, ch_stats)

    print(f"Verdict: {verdict}")
    print(f"Report: {out_dir / 'aasist_finetune_manifest_validation_report.md'}")
    return 0 if verdict != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
