#!/usr/bin/env python3
"""
Phase 8C-A1 — Descriptive acoustic feature sanity audit (no ML, no predictions).
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

_FEATURES_DIR = Path(__file__).resolve().parent
_COMMON_DIR = Path(__file__).resolve().parents[1] / "common"
for _p in (_FEATURES_DIR, _COMMON_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from phase8c_feature_utils import (  # noqa: E402
    FILE_FEATURE_NAMES,
    FILE_IDENTITY_COLUMNS,
    REPO_ROOT,
    SEGMENT_FEATURE_NAMES,
    SEGMENT_FAST_BLANK_FEATURES,
    SEGMENT_IDENTITY_COLUMNS,
)
from progress_utils import iter_with_progress, progress_method  # noqa: E402

FORBIDDEN_COLUMNS = frozenset(
    {
        "fake_score",
        "real_score",
        "ai_score",
        "replay_decision",
        "mixer_decision",
        "final_forensic_status",
        "suspicious_segment_flag",
        "evidence_origin_score",
        "origin_score",
    }
)

MIN_GROUP_SIZE = 5
MISSING_LIMITED_PCT = 50.0

FILE_COMPARISONS = [
    ("clean_human_vs_clean_ai_synthetic", "human", "ai_synthetic", "clean", "clean", "origin", "origin"),
    ("clean_vs_replay_rerecorded", "clean", "replay", None, None, "manip_bool", "manip_bool"),
    ("clean_vs_mixer_channel_processed", "clean", "mixer", None, None, "manip_bool", "manip_bool"),
    ("clean_vs_partial_fabrication_combo", "clean", "partial_combo", None, None, "manip_bool", "manip_bool"),
    ("human_vs_ai_synthetic", "human", "ai_synthetic", None, None, "origin", "origin"),
    ("clean_vs_non_clean", "clean", "non_clean", None, None, "manip_bool", "manip_bool"),
]

SEGMENT_COMPARISONS = [
    ("seg_clean_vs_replay_inherited", "clean", "replay", "manip_bool", "manip_bool"),
    ("seg_clean_vs_mixer_inherited", "clean", "mixer", "manip_bool", "manip_bool"),
    ("seg_clean_vs_partial_inherited", "clean", "partial_combo", "manip_bool", "manip_bool"),
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Phase 8C-A1 acoustic feature audit.")
    p.add_argument(
        "--file_features",
        default="reports/phase8/features/phase8c_file_acoustic_features.csv",
    )
    p.add_argument(
        "--segment_features",
        default="reports/phase8/features/phase8c_segment_acoustic_features.csv",
    )
    p.add_argument(
        "--file_table",
        default="reports/phase8/evidence_table/phase8b_file_evidence_table.csv",
    )
    p.add_argument(
        "--segment_table",
        default="reports/phase8/evidence_table/phase8b_segment_evidence_table.csv",
    )
    p.add_argument("--output_dir", default="reports/phase8/features/audit")
    p.add_argument("--max_features_for_plots", type=int, default=20)
    p.add_argument("--top_k", type=int, default=25)
    p.add_argument("--make_plots", action="store_true")
    p.add_argument("--no_progress", action="store_true")
    p.add_argument("--progress_every", type=int, default=100)
    return p.parse_args()


def _resolve(path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else (REPO_ROOT / p).resolve()


def _to_numeric_series(s: pd.Series) -> pd.Series:
    blank = s.astype(str).str.strip().isin(("", "nan", "NaN", "None"))
    return pd.to_numeric(s.mask(blank), errors="coerce")


def _add_manipulation_bools(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    manip = out.get("known_manipulation_labels", pd.Series("", index=out.index)).astype(str)

    def _has(token: str) -> pd.Series:
        return manip.str.contains(token, regex=False, na=False)

    out["is_clean"] = manip.eq("clean")
    out["is_replay_rerecorded"] = _has("replay_rerecorded")
    out["is_mixer_channel_processed"] = _has("mixer_channel_processed")
    out["is_partial_fabrication"] = _has("partial_fabrication")
    out["is_edited_spliced"] = _has("edited_spliced")
    out["is_partial_combo"] = _has("partial_fabrication") | _has("edited_spliced")
    out["is_non_clean"] = ~out["is_clean"]
    return out


def _feature_summary(df: pd.DataFrame, feature_cols: list[str], group_col: str | None) -> pd.DataFrame:
    rows: list[dict] = []

    def _summarize(sub: pd.DataFrame, label: str) -> None:
        for feat in feature_cols:
            s = _to_numeric_series(sub[feat])
            n = int(s.notna().sum())
            miss = 100.0 * (1.0 - n / max(len(sub), 1))
            rows.append(
                {
                    "group_dimension": group_col or "all",
                    "group_value": label,
                    "feature": feat,
                    "count": n,
                    "row_count": len(sub),
                    "missing_percent": round(miss, 4),
                    "mean": float(s.mean()) if n else np.nan,
                    "std": float(s.std()) if n > 1 else np.nan,
                    "min": float(s.min()) if n else np.nan,
                    "median": float(s.median()) if n else np.nan,
                    "max": float(s.max()) if n else np.nan,
                }
            )

    if group_col is None:
        _summarize(df, "all")
    else:
        for val, sub in df.groupby(group_col, dropna=False):
            _summarize(sub, str(val))
    return pd.DataFrame(rows)


def _missingness_report(df: pd.DataFrame, feature_cols: list[str], level: str) -> pd.DataFrame:
    rows = []
    n = max(len(df), 1)
    for feat in feature_cols:
        s = _to_numeric_series(df[feat])
        miss_pct = 100.0 * float(s.isna().mean())
        var = float(s.var()) if s.notna().sum() > 1 else np.nan
        usability = "usable"
        note = ""
        if miss_pct >= 100.0:
            usability = "exclude_for_now"
            note = "100% missing"
        elif miss_pct > MISSING_LIMITED_PCT:
            usability = "limited"
            note = f">{MISSING_LIMITED_PCT}% missing"
        elif feat in SEGMENT_FAST_BLANK_FEATURES and level == "segment":
            usability = "limited"
            note = "often blank in fast segment mode (expected)"
        elif feat == "very_high_band_energy_ratio":
            usability = "limited"
            note = "may be blank at 16 kHz (Nyquist 8 kHz band edge)"
        elif not np.isnan(var) and var == 0.0:
            usability = "exclude_for_now"
            note = "zero variance"
        rows.append(
            {
                "level": level,
                "feature": feat,
                "missing_percent": round(miss_pct, 4),
                "non_null_count": int(s.notna().sum()),
                "row_count": n,
                "variance": var,
                "usability": usability,
                "note": note,
            }
        )
    return pd.DataFrame(rows)


_MANIP_BOOL_COL_MAP = {
    "clean": "is_clean",
    "replay": "is_replay_rerecorded",
    "mixer": "is_mixer_channel_processed",
    "partial_combo": "is_partial_combo",
    "non_clean": "is_non_clean",
}


def _mask_for_comparison(df: pd.DataFrame, comp: tuple, level: str) -> tuple[pd.Series, pd.Series, str, str]:
    a, b = comp[1], comp[2]

    if level == "file" and len(comp) >= 7:
        manip_a, manip_b, dim_a, _dim_b = comp[3], comp[4], comp[5], comp[6]
        if dim_a == "origin":
            mask_a = df["known_origin_label"].astype(str).eq(a)
            mask_b = df["known_origin_label"].astype(str).eq(b)
            if manip_a:
                mask_a &= df["known_manipulation_labels"].astype(str).eq(manip_a)
                mask_b &= df["known_manipulation_labels"].astype(str).eq(manip_b)
            return mask_a, mask_b, str(a), str(b)

    mask_a = df[_MANIP_BOOL_COL_MAP[a]]
    mask_b = df[_MANIP_BOOL_COL_MAP[b]]
    return mask_a, mask_b, str(a), str(b)


def _interpretation_note(effect: float, miss_pct: float) -> str:
    if miss_pct > MISSING_LIMITED_PCT:
        return "limited missingness — not a standalone detector; requires validation in later phases"
    if np.isnan(effect):
        return "insufficient data for effect size — descriptive only; requires validation in later phases"
    if effect >= 0.8:
        return "feature shows descriptive separation — possible candidate for later modeling; not a standalone detector"
    if effect >= 0.5:
        return "moderate descriptive separation — possible candidate for later modeling; requires validation in later phases"
    return "weak descriptive separation — treat carefully; requires validation in later phases"


def _compare_groups(
    df: pd.DataFrame,
    feature_cols: list[str],
    comparisons: list,
    level: str,
    *,
    progress_on: bool,
    progress_every: int,
) -> pd.DataFrame:
    rows: list[dict] = []
    comp_list = list(comparisons)

    for comp in iter_with_progress(
        comp_list,
        total=len(comp_list),
        desc=f"{level}_comparisons",
        enabled=progress_on,
        progress_every=progress_every,
    ):
        name = comp[0]
        mask_a, mask_b, la, lb = _mask_for_comparison(df, comp, level)
        sub_a = df[mask_a]
        sub_b = df[mask_b]
        ca, cb = len(sub_a), len(sub_b)

        for feat in feature_cols:
            sa = _to_numeric_series(sub_a[feat])
            sb = _to_numeric_series(sub_b[feat])
            miss_pct = 100.0 * (1.0 - (sa.notna().sum() + sb.notna().sum()) / max(ca + cb, 1))
            mean_a = float(sa.mean()) if sa.notna().sum() else np.nan
            mean_b = float(sb.mean()) if sb.notna().sum() else np.nan
            med_a = float(sa.median()) if sa.notna().sum() else np.nan
            med_b = float(sb.median()) if sb.notna().sum() else np.nan
            abs_diff = abs(mean_a - mean_b) if not (np.isnan(mean_a) or np.isnan(mean_b)) else np.nan

            effect = np.nan
            direction = "insufficient_data"
            if ca >= MIN_GROUP_SIZE and cb >= MIN_GROUP_SIZE:
                va = float(sa.var()) if sa.notna().sum() > 1 else 0.0
                vb = float(sb.var()) if sb.notna().sum() > 1 else 0.0
                pooled = np.sqrt((va + vb) / 2.0) if (va + vb) > 0 else 0.0
                if pooled > 0 and not (np.isnan(mean_a) or np.isnan(mean_b)):
                    effect = abs(mean_a - mean_b) / pooled
                    if mean_a > mean_b:
                        direction = "higher_in_group_a"
                    elif mean_b > mean_a:
                        direction = "higher_in_group_b"
                    else:
                        direction = "no_clear_direction"
                elif not (np.isnan(mean_a) or np.isnan(mean_b)):
                    direction = "no_clear_direction"

            rows.append(
                {
                    "level": level,
                    "comparison_name": name,
                    "level_a": la,
                    "level_b": lb,
                    "feature": feat,
                    "group_a_count": ca,
                    "group_b_count": cb,
                    "group_a_mean": mean_a,
                    "group_b_mean": mean_b,
                    "group_a_median": med_a,
                    "group_b_median": med_b,
                    "abs_mean_difference": abs_diff,
                    "effect_size": effect,
                    "missing_percent": round(miss_pct, 4),
                    "direction": direction,
                    "interpretation_note": _interpretation_note(effect, miss_pct),
                }
            )
    return pd.DataFrame(rows)


def _top_candidates(diff_df: pd.DataFrame, top_k: int) -> pd.DataFrame:
    if diff_df.empty:
        return diff_df
    out = diff_df.copy()
    out["effect_size_sort"] = pd.to_numeric(out["effect_size"], errors="coerce").fillna(-1)
    ranked = (
        out.sort_values(["comparison_name", "effect_size_sort"], ascending=[True, False])
        .groupby("comparison_name", group_keys=False)
        .head(top_k)
        .drop(columns=["effect_size_sort"])
    )
    return ranked


def _correlation_summary(df: pd.DataFrame, feature_cols: list[str], max_features: int) -> pd.DataFrame:
    numeric = pd.DataFrame({c: _to_numeric_series(df[c]) for c in feature_cols})
    numeric = numeric.dropna(axis=1, how="all")
    if numeric.shape[1] < 2:
        return pd.DataFrame(columns=["feature_a", "feature_b", "correlation"])
    if numeric.shape[1] > max_features:
        variances = numeric.var().sort_values(ascending=False)
        keep = list(variances.head(max_features).index)
        numeric = numeric[keep]
    corr = numeric.corr()
    rows = []
    cols = list(corr.columns)
    for i, a in enumerate(cols):
        for j, b in enumerate(cols):
            if j <= i:
                continue
            rows.append({"feature_a": a, "feature_b": b, "correlation": float(corr.loc[a, b])})
    out = pd.DataFrame(rows)
    if len(out):
        out["abs_correlation"] = out["correlation"].abs()
        out = out.sort_values("abs_correlation", ascending=False)
    return out


def _id_consistency(file_feat: pd.DataFrame, file_8b: pd.DataFrame, seg_feat: pd.DataFrame, seg_8b: pd.DataFrame) -> list[str]:
    notes = []
    ff_ids = set(file_feat["file_id"].astype(str))
    b_ids = set(file_8b["file_id"].astype(str))
    if ff_ids != b_ids:
        notes.append(f"file_id mismatch: features={len(ff_ids)} 8b={len(b_ids)} extra_in_feat={len(ff_ids-b_ids)} missing={len(b_ids-ff_ids)}")
    sf_ids = set(seg_feat["segment_id"].astype(str))
    sb_ids = set(seg_8b["segment_id"].astype(str))
    if sf_ids != sb_ids:
        notes.append(f"segment_id mismatch: features={len(sf_ids)} 8b={len(sb_ids)}")
    if len(file_feat) != len(file_8b):
        notes.append(f"file row count features={len(file_feat)} 8b={len(file_8b)}")
    if len(seg_feat) != len(seg_8b):
        notes.append(f"segment row count features={len(seg_feat)} 8b={len(seg_8b)}")
    return notes


def _make_plots(
    out_dir: Path,
    file_df: pd.DataFrame,
    file_feats: list[str],
    top_cand: pd.DataFrame,
    miss_df: pd.DataFrame,
    max_plots: int,
) -> list[str]:
    warnings: list[str] = []
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return ["matplotlib not available — plots skipped"]

    fig_dir = out_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    # Missingness bar (file level)
    sub = miss_df[miss_df["level"] == "file"].sort_values("missing_percent", ascending=False).head(max_plots)
    if len(sub):
        fig, ax = plt.subplots(figsize=(10, max(4, len(sub) * 0.25)))
        ax.barh(sub["feature"], sub["missing_percent"])
        ax.set_xlabel("missing %")
        ax.set_title("File feature missingness (top)")
        fig.tight_layout()
        p = fig_dir / "missingness_file.png"
        fig.savefig(p, dpi=120)
        plt.close(fig)

    # Top candidate boxplots by manipulation
    plot_feats = (
        top_cand[top_cand["comparison_name"] == "clean_vs_replay_rerecorded"]
        .head(min(6, max_plots))["feature"]
        .tolist()
    )
    for feat in plot_feats:
        if feat not in file_df.columns:
            continue
        fig, ax = plt.subplots(figsize=(8, 4))
        groups = []
        tick_labels = []
        for label, sub in file_df.groupby("known_manipulation_labels"):
            vals = _to_numeric_series(sub[feat]).dropna()
            if len(vals):
                groups.append(vals)
                tick_labels.append(str(label)[:30])
        if groups:
            ax.boxplot(groups, tick_labels=tick_labels)
            ax.set_title(f"{feat} by manipulation (descriptive)")
            ax.tick_params(axis="x", rotation=25)
            fig.tight_layout()
            fp = fig_dir / f"boxplot_manip_{feat[:40]}.png"
            fig.savefig(fp, dpi=120)
            plt.close(fig)

    # Correlation heatmap for top variance features
    numeric = pd.DataFrame({c: _to_numeric_series(file_df[c]) for c in file_feats}).dropna(axis=1, how="all")
    if numeric.shape[1] >= 2:
        keep = list(numeric.var().sort_values(ascending=False).head(min(15, max_plots)).index)
        c = numeric[keep].corr()
        fig, ax = plt.subplots(figsize=(8, 7))
        im = ax.imshow(c.values, aspect="auto", vmin=-1, vmax=1)
        ax.set_xticks(range(len(keep)), keep, rotation=90, fontsize=7)
        ax.set_yticks(range(len(keep)), keep, fontsize=7)
        ax.set_title("Feature correlation (descriptive)")
        fig.colorbar(im, ax=ax)
        fig.tight_layout()
        fig.savefig(fig_dir / "correlation_heatmap.png", dpi=120)
        plt.close(fig)

    return warnings


def _write_audit_report(
    path: Path,
    *,
    id_notes: list[str],
    miss_df: pd.DataFrame,
    top_cand: pd.DataFrame,
    file_diff: pd.DataFrame,
    seg_diff: pd.DataFrame,
    plot_warnings: list[str],
    runtime_sec: float,
    args: argparse.Namespace,
) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        "# Phase 8C-A1 Acoustic Feature Audit Report",
        "",
        f"**Generated:** {now}",
        f"**Runtime:** {runtime_sec:.1f}s",
        "",
        "> **Descriptive analysis only** — not model performance, not fake/real detection, not forensic proof.",
        "",
        "## 1. Purpose",
        "",
        "Sanity-check Phase 8C acoustic/channel features for internal consistency, missingness, and",
        "descriptive differences across **known** origin/manipulation labels on Phase 7C1.",
        "",
        "## 2. Data consistency",
        "",
    ]
    if id_notes:
        for n in id_notes:
            lines.append(f"- {n}")
    else:
        lines.append("- File/segment IDs and row counts match Phase 8B tables.")

    lines.extend(
        [
            "",
            "## 3. Segment label inheritance (important)",
            "",
            "Segment group analysis uses **file-level** `known_manipulation_labels` and `known_origin_label`",
            "joined by `file_id` unless true per-segment ground truth exists in Phase 8B.",
            "Do not interpret segment group shifts as localized segment truth.",
            "",
            "## 4. Fast segment mode limitations",
            "",
            "- Segment MFCC columns may be 100% blank (expected).",
            "- `spectral_contrast_mean` often blank at segment level.",
            "- `very_high_band_energy_ratio` may be blank at 16 kHz (Nyquist 8 kHz).",
            "",
            "## 5. Missingness highlights",
            "",
        ]
    )
    excl = miss_df[miss_df["usability"] == "exclude_for_now"]
    lim = miss_df[miss_df["usability"] == "limited"]
    lines.append(f"- exclude_for_now: {len(excl)} feature-level entries")
    lines.append(f"- limited: {len(lim)} feature-level entries")
    for _, r in excl.head(15).iterrows():
        lines.append(f"- `{r['level']}` `{r['feature']}`: {r['note']}")

    lines.extend(["", "## 6. Top descriptive candidates (file-level, by comparison)", ""])
    for comp in top_cand["comparison_name"].unique()[:8]:
        lines.append(f"### {comp}")
        sub = top_cand[top_cand["comparison_name"] == comp].head(8)
        for _, r in sub.iterrows():
            es = r.get("effect_size", "")
            lines.append(
                f"- `{r['feature']}` effect_size={es} direction={r['direction']} — {r['interpretation_note']}"
            )
        lines.append("")

    lines.extend(
        [
            "## 7. Safe use for Phase 8E (indicators only)",
            "",
            "- Prefer features marked **usable** with effect_size ≥ 0.5 on replay/mixer/partial comparisons.",
            "- Exclude 100% missing or zero-variance features.",
            "- Do not use a single feature as spoof/AI proof.",
            "",
            "## 8. Outputs",
            "",
            f"- Directory: `{args.output_dir}`",
            "",
            "## 9. What this audit did NOT do",
            "",
            "- No classifier training or inference",
            "- No predictions or forensic decisions",
            "- No modification of Phase 8B/8C CSVs",
            "",
        ]
    )
    if plot_warnings:
        lines.extend(["## Plot warnings", ""])
        for w in plot_warnings:
            lines.append(f"- {w}")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_audit(args: argparse.Namespace) -> dict[str, Any]:
    t0 = time.perf_counter()
    progress_on = not args.no_progress

    file_feat = pd.read_csv(_resolve(args.file_features), dtype=str, keep_default_na=False)
    seg_feat = pd.read_csv(_resolve(args.segment_features), dtype=str, keep_default_na=False)
    file_8b = pd.read_csv(_resolve(args.file_table), dtype=str, keep_default_na=False)
    seg_8b = pd.read_csv(_resolve(args.segment_table), dtype=str, keep_default_na=False)

    id_notes = _id_consistency(file_feat, file_8b, seg_feat, seg_8b)

    file_feats = [c for c in FILE_FEATURE_NAMES if c in file_feat.columns]
    seg_feats = [c for c in SEGMENT_FEATURE_NAMES if c in seg_feat.columns]

    file_df = _add_manipulation_bools(file_feat)
    seg_df = seg_feat.merge(
        file_df[["file_id", "known_origin_label", "known_manipulation_labels", "is_clean", "is_replay_rerecorded", "is_mixer_channel_processed", "is_partial_combo", "is_non_clean"]],
        on="file_id",
        how="left",
        suffixes=("", "_file"),
    )

    out_dir = _resolve(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    miss_file = _missingness_report(file_df, file_feats, "file")
    miss_seg = _missingness_report(seg_df, seg_feats, "segment")
    miss_all = pd.concat([miss_file, miss_seg], ignore_index=True)
    miss_all.to_csv(out_dir / "phase8c_a1_missingness_report.csv", index=False)

    file_summary_all = _feature_summary(file_df, file_feats, None)
    file_summary_origin = _feature_summary(file_df, file_feats, "known_origin_label")
    file_summary_manip = _feature_summary(file_df, file_feats, "known_manipulation_labels")
    file_summary = pd.concat([file_summary_all, file_summary_origin, file_summary_manip], ignore_index=True)
    file_summary.to_csv(out_dir / "phase8c_a1_file_feature_summary.csv", index=False)

    seg_summary_all = _feature_summary(seg_df, seg_feats, None)
    seg_summary_manip = _feature_summary(seg_df, seg_feats, "known_manipulation_labels")
    seg_summary = pd.concat([seg_summary_all, seg_summary_manip], ignore_index=True)
    seg_summary.to_csv(out_dir / "phase8c_a1_segment_feature_summary.csv", index=False)

    file_diff = _compare_groups(file_df, file_feats, FILE_COMPARISONS, "file", progress_on=progress_on, progress_every=args.progress_every)
    file_diff.to_csv(out_dir / "phase8c_a1_group_difference_file_features.csv", index=False)

    seg_diff = _compare_groups(seg_df, seg_feats, SEGMENT_COMPARISONS, "segment", progress_on=progress_on, progress_every=args.progress_every)
    seg_diff.to_csv(out_dir / "phase8c_a1_group_difference_segment_features.csv", index=False)

    all_diff = pd.concat([file_diff, seg_diff], ignore_index=True)
    top_cand = _top_candidates(all_diff, args.top_k)
    top_cand.to_csv(out_dir / "phase8c_a1_top_candidate_features.csv", index=False)

    corr = _correlation_summary(file_df, file_feats, args.max_features_for_plots)
    corr.to_csv(out_dir / "phase8c_a1_feature_correlation_summary.csv", index=False)

    plot_warnings: list[str] = []
    if args.make_plots:
        plot_warnings = _make_plots(out_dir, file_df, file_feats, top_cand, miss_all, args.max_features_for_plots)

    runtime = time.perf_counter() - t0
    _write_audit_report(
        out_dir / "phase8c_a1_acoustic_feature_audit_report.md",
        id_notes=id_notes,
        miss_df=miss_all,
        top_cand=top_cand,
        file_diff=file_diff,
        seg_diff=seg_diff,
        plot_warnings=plot_warnings,
        runtime_sec=runtime,
        args=args,
    )

    return {
        "runtime_sec": runtime,
        "id_notes": id_notes,
        "top_cand_rows": len(top_cand),
        "miss_rows": len(miss_all),
        "plot_warnings": plot_warnings,
    }


def main() -> int:
    args = parse_args()
    result = run_audit(args)
    print("--- Phase 8C-A1 audit summary ---")
    print(f"Runtime: {result['runtime_sec']:.1f}s")
    print(f"Progress method: {progress_method()}")
    print(f"Top candidate rows: {result['top_cand_rows']}")
    print(f"Missingness rows: {result['miss_rows']}")
    print(f"Output dir: {_resolve(args.output_dir)}")
    if result["id_notes"]:
        print("ID notes:", "; ".join(result["id_notes"]))
    if result["plot_warnings"]:
        print("Plot warnings:", result["plot_warnings"])
    print("Descriptive audit only — no training/predictions.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
