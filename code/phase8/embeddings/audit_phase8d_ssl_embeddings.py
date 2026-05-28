#!/usr/bin/env python3
"""
Phase 8D-A1 — Descriptive SSL embedding sanity audit (no ML, no predictions).
"""

from __future__ import annotations

import argparse
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

_EMB_DIR = Path(__file__).resolve().parent
_COMMON_DIR = Path(__file__).resolve().parents[1] / "common"
for _p in (_EMB_DIR, _COMMON_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from progress_utils import iter_with_progress, progress_method  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[3]

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
    ("clean_vs_partial_combo", "clean", "partial_combo", None, None, "manip_bool", "manip_bool"),
    ("human_vs_ai_synthetic", "human", "ai_synthetic", None, None, "origin", "origin"),
    ("clean_vs_non_clean", "clean", "non_clean", None, None, "manip_bool", "manip_bool"),
    ("mixed_vs_clean_human", "mixed", "human", None, "clean", "origin", "origin_clean_human"),
]

SEGMENT_COMPARISONS = [
    ("seg_clean_vs_replay_inherited", "clean", "replay", "manip_bool", "manip_bool"),
    ("seg_clean_vs_mixer_inherited", "clean", "mixer", "manip_bool", "manip_bool"),
    ("seg_clean_vs_partial_inherited", "clean", "partial_combo", "manip_bool", "manip_bool"),
    ("seg_human_vs_ai_inherited", "human", "ai_synthetic", "origin", "origin"),
    ("seg_mixed_vs_clean_human_inherited", "mixed", "human", "origin", "origin_clean_human"),
]

_MANIP_BOOL_COL_MAP = {
    "clean": "is_clean",
    "replay": "is_replay_rerecorded",
    "mixer": "is_mixer_channel_processed",
    "partial_combo": "is_partial_combo",
    "non_clean": "is_non_clean",
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Phase 8D-A1 SSL embedding descriptive audit.")
    p.add_argument(
        "--file_embeddings",
        default="reports/phase8/embeddings/phase8d_file_ssl_embeddings.csv",
    )
    p.add_argument(
        "--segment_embeddings",
        default="reports/phase8/embeddings/phase8d_segment_ssl_embeddings.csv",
    )
    p.add_argument(
        "--file_table",
        default="reports/phase8/evidence_table/phase8b_file_evidence_table.csv",
    )
    p.add_argument(
        "--segment_table",
        default="reports/phase8/evidence_table/phase8b_segment_evidence_table.csv",
    )
    p.add_argument("--output_dir", default="reports/phase8/embeddings/audit")
    p.add_argument("--top_k", type=int, default=25)
    p.add_argument("--max_dims_for_correlation", type=int, default=100)
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


def _embedding_cols(df: pd.DataFrame) -> list[str]:
    cols = [c for c in df.columns if c.startswith("ssl_emb_") and c not in FORBIDDEN_COLUMNS]
    return sorted(cols)


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


def _row_norm_metrics(df: pd.DataFrame, emb_cols: list[str]) -> pd.DataFrame:
    emb = df[emb_cols].apply(_to_numeric_series)
    arr = emb.to_numpy(dtype=np.float64)
    is_finite = np.isfinite(arr)
    valid_mask = np.all(is_finite | np.isnan(arr), axis=1)
    arr = np.where(np.isnan(arr), 0.0, arr)
    l2 = np.linalg.norm(arr, axis=1)
    mean_abs = np.mean(np.abs(arr), axis=1)
    max_abs = np.max(np.abs(arr), axis=1)
    out = pd.DataFrame(
        {
            "l2_norm": l2,
            "mean_abs_value": mean_abs,
            "max_abs_value": max_abs,
            "finite_row": valid_mask,
        }
    )
    return out


def _summary_stats(df: pd.DataFrame, emb_cols: list[str], level: str, group_col: str | None) -> pd.DataFrame:
    rows: list[dict] = []

    def _summarize(sub: pd.DataFrame, label: str) -> None:
        for d in emb_cols:
            s = _to_numeric_series(sub[d])
            n = int(s.notna().sum())
            miss = 100.0 * (1.0 - n / max(len(sub), 1))
            rows.append(
                {
                    "level": level,
                    "group_dimension": group_col or "all",
                    "group_value": label,
                    "embedding_dim_name": d,
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


def _missingness_report(df: pd.DataFrame, emb_cols: list[str], level: str) -> pd.DataFrame:
    rows = []
    n = max(len(df), 1)
    for d in emb_cols:
        s = _to_numeric_series(df[d])
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
        elif not np.isnan(var) and var == 0.0:
            usability = "exclude_for_now"
            note = "zero variance"
        rows.append(
            {
                "level": level,
                "embedding_dim_name": d,
                "missing_percent": round(miss_pct, 4),
                "non_null_count": int(s.notna().sum()),
                "row_count": n,
                "variance": var,
                "usability": usability,
                "note": note,
            }
        )
    return pd.DataFrame(rows)


def _mask_for_comparison(df: pd.DataFrame, comp: tuple, level: str) -> tuple[pd.Series, pd.Series, str, str]:
    a, b = comp[1], comp[2]
    if len(comp) >= 7:
        manip_a, manip_b, dim_a, dim_b = comp[3], comp[4], comp[5], comp[6]
    else:
        manip_a, manip_b, dim_a, dim_b = None, None, comp[3], comp[4]

    if dim_a == "origin":
        mask_a = df["known_origin_label"].astype(str).eq(a)
        mask_b = df["known_origin_label"].astype(str).eq(b)
        if manip_a:
            mask_a &= df["known_manipulation_labels"].astype(str).eq(manip_a)
            mask_b &= df["known_manipulation_labels"].astype(str).eq(manip_b)
        return mask_a, mask_b, str(a), str(b)

    if dim_a == "origin_clean_human":
        mask_a = df["known_origin_label"].astype(str).eq(a)
        mask_b = df["known_origin_label"].astype(str).eq(b) & df["known_manipulation_labels"].astype(str).eq(manip_b)
        return mask_a, mask_b, str(a), f"{b}_clean"

    mask_a = df[_MANIP_BOOL_COL_MAP[a]]
    mask_b = df[_MANIP_BOOL_COL_MAP[b]]
    return mask_a, mask_b, str(a), str(b)


def _interpretation(effect: float, miss: float) -> str:
    if miss > MISSING_LIMITED_PCT:
        return "limited missingness — not a standalone detector; requires validation in Phase 8E"
    if np.isnan(effect):
        return "insufficient data — possible candidate for later modeling; requires validation in Phase 8E"
    if effect >= 0.8:
        return "embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector"
    if effect >= 0.5:
        return "possible candidate for later modeling; descriptive only; requires validation in Phase 8E"
    return "weak descriptive separation; not a standalone detector; requires validation in Phase 8E"


def _group_differences(
    df: pd.DataFrame,
    emb_cols: list[str],
    comparisons: list[tuple],
    level: str,
    *,
    progress_on: bool,
    progress_every: int,
) -> pd.DataFrame:
    rows: list[dict] = []
    for comp in iter_with_progress(
        comparisons,
        total=len(comparisons),
        desc=f"{level}_comparisons",
        enabled=progress_on,
        progress_every=progress_every,
    ):
        cname = comp[0]
        mask_a, mask_b, la, lb = _mask_for_comparison(df, comp, level)
        a_df = df[mask_a]
        b_df = df[mask_b]
        ca, cb = len(a_df), len(b_df)

        for d in emb_cols:
            sa = _to_numeric_series(a_df[d])
            sb = _to_numeric_series(b_df[d])
            miss_pct = 100.0 * (1.0 - (sa.notna().sum() + sb.notna().sum()) / max(ca + cb, 1))
            if miss_pct > MISSING_LIMITED_PCT:
                effect = np.nan
            else:
                ma = float(sa.mean()) if sa.notna().sum() else np.nan
                mb = float(sb.mean()) if sb.notna().sum() else np.nan
                va = float(sa.var()) if sa.notna().sum() > 1 else 0.0
                vb = float(sb.var()) if sb.notna().sum() > 1 else 0.0
                pooled = math.sqrt((va + vb) / 2.0) if (va + vb) > 0 else 0.0
                effect = abs(ma - mb) / pooled if pooled > 0 and not np.isnan(ma) and not np.isnan(mb) else np.nan

            ma = float(sa.mean()) if sa.notna().sum() else np.nan
            mb = float(sb.mean()) if sb.notna().sum() else np.nan
            md_a = float(sa.median()) if sa.notna().sum() else np.nan
            md_b = float(sb.median()) if sb.notna().sum() else np.nan
            abs_diff = abs(ma - mb) if not np.isnan(ma) and not np.isnan(mb) else np.nan
            direction = "insufficient_data"
            if ca >= MIN_GROUP_SIZE and cb >= MIN_GROUP_SIZE and not np.isnan(ma) and not np.isnan(mb):
                if ma > mb:
                    direction = "higher_in_group_a"
                elif mb > ma:
                    direction = "higher_in_group_b"
                else:
                    direction = "no_clear_direction"

            rows.append(
                {
                    "level": level,
                    "comparison_name": cname,
                    "level_a": la,
                    "level_b": lb,
                    "embedding_dim_name": d,
                    "group_a_count": ca,
                    "group_b_count": cb,
                    "group_a_mean": ma,
                    "group_b_mean": mb,
                    "group_a_median": md_a,
                    "group_b_median": md_b,
                    "abs_mean_difference": abs_diff,
                    "effect_size": effect,
                    "missing_percent": round(miss_pct, 4),
                    "direction": direction,
                    "interpretation_note": _interpretation(effect, miss_pct),
                }
            )
    return pd.DataFrame(rows)


def _top_candidates(diff_df: pd.DataFrame, top_k: int) -> pd.DataFrame:
    if diff_df.empty:
        return diff_df
    x = diff_df.copy()
    x["effect_size_sort"] = pd.to_numeric(x["effect_size"], errors="coerce").fillna(-1)
    out = (
        x.sort_values(["comparison_name", "effect_size_sort"], ascending=[True, False])
        .groupby("comparison_name", group_keys=False)
        .head(top_k)
        .drop(columns=["effect_size_sort"])
    )
    return out


def _corr_summary(df: pd.DataFrame, emb_cols: list[str], max_dims: int) -> pd.DataFrame:
    emb = pd.DataFrame({c: _to_numeric_series(df[c]) for c in emb_cols}).dropna(axis=1, how="all")
    if emb.shape[1] < 2:
        return pd.DataFrame(columns=["embedding_dim_a", "embedding_dim_b", "correlation", "abs_correlation"])
    if emb.shape[1] > max_dims:
        keep = list(emb.var().sort_values(ascending=False).head(max_dims).index)
        emb = emb[keep]
    corr = emb.corr()
    rows = []
    cols = list(corr.columns)
    for i, a in enumerate(cols):
        for j, b in enumerate(cols):
            if j <= i:
                continue
            v = float(corr.loc[a, b])
            rows.append({"embedding_dim_a": a, "embedding_dim_b": b, "correlation": v, "abs_correlation": abs(v)})
    out = pd.DataFrame(rows)
    if len(out):
        out = out.sort_values("abs_correlation", ascending=False)
    return out


def _plot_outputs(
    out_dir: Path,
    file_df: pd.DataFrame,
    emb_cols: list[str],
    top_dims: pd.DataFrame,
    miss_df: pd.DataFrame,
    max_dims: int,
) -> list[str]:
    warnings: list[str] = []
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return ["matplotlib not available — plots skipped"]

    fig_dir = out_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    # missingness
    sub = miss_df[miss_df["level"] == "file"].sort_values("missing_percent", ascending=False).head(max_dims)
    if len(sub):
        fig, ax = plt.subplots(figsize=(10, max(4, len(sub) * 0.22)))
        ax.barh(sub["embedding_dim_name"], sub["missing_percent"])
        ax.set_title("Embedding missingness (file)")
        ax.set_xlabel("missing %")
        fig.tight_layout()
        fig.savefig(fig_dir / "missingness_file_embeddings.png", dpi=120)
        plt.close(fig)

    # norm by manipulation
    if "known_manipulation_labels" in file_df.columns and "l2_norm" in file_df.columns:
        groups, ticks = [], []
        for lbl, g in file_df.groupby("known_manipulation_labels"):
            vals = _to_numeric_series(g["l2_norm"]).dropna()
            if len(vals):
                groups.append(vals)
                ticks.append(str(lbl)[:30])
        if groups:
            fig, ax = plt.subplots(figsize=(8, 4))
            try:
                ax.boxplot(groups, tick_labels=ticks)
            except TypeError:
                ax.boxplot(groups, labels=ticks)
            ax.set_title("Embedding L2 norm by manipulation")
            ax.tick_params(axis="x", rotation=25)
            fig.tight_layout()
            fig.savefig(fig_dir / "embedding_norm_by_manip.png", dpi=120)
            plt.close(fig)

    # top dims boxplots
    dims = top_dims.head(min(6, max_dims))["embedding_dim_name"].tolist() if len(top_dims) else []
    for d in dims:
        if d not in file_df.columns:
            continue
        groups, ticks = [], []
        for lbl, g in file_df.groupby("known_origin_label"):
            vals = _to_numeric_series(g[d]).dropna()
            if len(vals):
                groups.append(vals)
                ticks.append(str(lbl))
        if groups:
            fig, ax = plt.subplots(figsize=(8, 4))
            try:
                ax.boxplot(groups, tick_labels=ticks)
            except TypeError:
                ax.boxplot(groups, labels=ticks)
            ax.set_title(f"{d} by origin (descriptive)")
            fig.tight_layout()
            fig.savefig(fig_dir / f"boxplot_origin_{d}.png", dpi=120)
            plt.close(fig)

    # correlation heatmap
    sel = [d for d in dims if d in emb_cols]
    if len(sel) >= 2:
        c = pd.DataFrame({d: _to_numeric_series(file_df[d]) for d in sel}).corr()
        fig, ax = plt.subplots(figsize=(6, 5))
        im = ax.imshow(c.values, vmin=-1, vmax=1, aspect="auto")
        ax.set_xticks(range(len(sel)), sel, rotation=90, fontsize=7)
        ax.set_yticks(range(len(sel)), sel, fontsize=7)
        fig.colorbar(im, ax=ax)
        ax.set_title("Top embedding dims correlation")
        fig.tight_layout()
        fig.savefig(fig_dir / "embedding_correlation_heatmap.png", dpi=120)
        plt.close(fig)

    return warnings


def _write_report(
    path: Path,
    args: argparse.Namespace,
    runtime_sec: float,
    id_notes: list[str],
    top_dims: pd.DataFrame,
    miss_df: pd.DataFrame,
    plot_warnings: list[str],
) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        "# Phase 8D-A1 SSL Embedding Audit Report",
        "",
        f"**Generated:** {now}",
        f"**Runtime:** {runtime_sec:.2f}s",
        "",
        "> **Descriptive analysis only** — no training, no predictions, no model performance claims.",
        "",
        "## 1. Consistency checks",
        "",
    ]
    if id_notes:
        for n in id_notes:
            lines.append(f"- {n}")
    else:
        lines.append("- Embedding rows and IDs align with Phase 8B tables.")

    lines.extend(
        [
            "",
            "## 2. Segment label inheritance",
            "",
            "Segment group analysis is based on file-level known labels unless true segment annotations are available.",
            "",
            "## 3. Missingness and limitations",
            "",
        ]
    )
    excl = miss_df[miss_df["usability"] == "exclude_for_now"]
    lim = miss_df[miss_df["usability"] == "limited"]
    lines.append(f"- exclude_for_now: {len(excl)} entries")
    lines.append(f"- limited: {len(lim)} entries")

    lines.extend(["", "## 4. Top candidate embedding dimensions (descriptive)", ""])
    for cname in top_dims["comparison_name"].unique()[:8]:
        lines.append(f"### {cname}")
        sub = top_dims[top_dims["comparison_name"] == cname].head(8)
        for _, r in sub.iterrows():
            lines.append(
                f"- `{r['embedding_dim_name']}` effect_size={r['effect_size']} direction={r['direction']} — {r['interpretation_note']}"
            )
        lines.append("")

    lines.extend(
        [
            "## 5. Notes for Phase 8E",
            "",
            "- Candidate dimensions are only descriptive indicators.",
            "- Embedding dimensions are less interpretable than handcrafted acoustic features.",
            "- Calibration and model validation are still required in Phase 8E.",
            "",
            "## 6. Outputs",
            "",
            f"- `{args.output_dir}`",
        ]
    )
    if plot_warnings:
        lines.extend(["", "## Plot warnings", ""])
        lines.extend(f"- {w}" for w in plot_warnings)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_audit(args: argparse.Namespace) -> dict[str, Any]:
    t0 = time.perf_counter()
    progress_on = not args.no_progress
    out_dir = _resolve(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    femb = pd.read_csv(_resolve(args.file_embeddings), dtype=str, keep_default_na=False)
    semb = pd.read_csv(_resolve(args.segment_embeddings), dtype=str, keep_default_na=False)
    ftab = pd.read_csv(_resolve(args.file_table), dtype=str, keep_default_na=False)
    stab = pd.read_csv(_resolve(args.segment_table), dtype=str, keep_default_na=False)

    # consistency
    id_notes: list[str] = []
    if len(femb) != len(ftab):
        id_notes.append(f"file row count mismatch: emb={len(femb)} table={len(ftab)}")
    if len(semb) != len(stab):
        id_notes.append(f"segment row count mismatch: emb={len(semb)} table={len(stab)}")
    if not set(femb["file_id"]).issubset(set(ftab["file_id"])):
        id_notes.append("file_id mismatch between embeddings and phase8b file table")
    if not set(semb["segment_id"]).issubset(set(stab["segment_id"])):
        id_notes.append("segment_id mismatch between embeddings and phase8b segment table")
    if femb.duplicated(subset=["file_id"]).any():
        id_notes.append("duplicate file_id rows found in file embeddings")
    if semb.duplicated(subset=["segment_id"]).any():
        id_notes.append("duplicate segment_id rows found in segment embeddings")

    femb = _add_manipulation_bools(femb)
    semb = semb.merge(
        femb[
            [
                "file_id",
                "known_origin_label",
                "known_manipulation_labels",
                "is_clean",
                "is_replay_rerecorded",
                "is_mixer_channel_processed",
                "is_partial_combo",
                "is_non_clean",
            ]
        ],
        on="file_id",
        how="left",
    )

    emb_cols_file = _embedding_cols(femb)
    emb_cols_seg = _embedding_cols(semb)

    # finite/nonblank checks
    finite_issues = 0
    for d in iter_with_progress(
        emb_cols_file,
        total=len(emb_cols_file),
        desc="finite_check_file_dims",
        enabled=progress_on,
        progress_every=args.progress_every,
    ):
        s = _to_numeric_series(femb[d])
        finite_issues += int((~np.isfinite(s.dropna())).sum())
    if finite_issues > 0:
        id_notes.append(f"non-finite values detected in file embeddings: {finite_issues}")

    # summaries
    file_sum = pd.concat(
        [
            _summary_stats(femb, emb_cols_file, "file", None),
            _summary_stats(femb, emb_cols_file, "file", "known_origin_label"),
            _summary_stats(femb, emb_cols_file, "file", "known_manipulation_labels"),
        ],
        ignore_index=True,
    )
    seg_sum = pd.concat(
        [
            _summary_stats(semb, emb_cols_seg, "segment", None),
            _summary_stats(semb, emb_cols_seg, "segment", "known_origin_label"),
            _summary_stats(semb, emb_cols_seg, "segment", "known_manipulation_labels"),
        ],
        ignore_index=True,
    )

    file_norms = _row_norm_metrics(femb, emb_cols_file)
    seg_norms = _row_norm_metrics(semb, emb_cols_seg)
    file_norm_out = pd.concat([femb[["file_id", "known_origin_label", "known_manipulation_labels"]], file_norms], axis=1)
    seg_norm_out = pd.concat([semb[["file_id", "segment_id", "known_origin_label", "known_manipulation_labels"]], seg_norms], axis=1)
    norm_summary = pd.concat(
        [
            file_norm_out.assign(level="file"),
            seg_norm_out.assign(level="segment"),
        ],
        ignore_index=True,
    )

    miss = pd.concat(
        [
            _missingness_report(femb, emb_cols_file, "file"),
            _missingness_report(semb, emb_cols_seg, "segment"),
        ],
        ignore_index=True,
    )

    file_diff = _group_differences(
        femb,
        emb_cols_file,
        FILE_COMPARISONS,
        "file",
        progress_on=progress_on,
        progress_every=args.progress_every,
    )
    seg_diff = _group_differences(
        semb,
        emb_cols_seg,
        SEGMENT_COMPARISONS,
        "segment",
        progress_on=progress_on,
        progress_every=args.progress_every,
    )
    top = _top_candidates(pd.concat([file_diff, seg_diff], ignore_index=True), args.top_k)
    corr = _corr_summary(femb, emb_cols_file, args.max_dims_for_correlation)

    # save outputs
    file_sum.to_csv(out_dir / "phase8d_a1_file_embedding_summary.csv", index=False)
    seg_sum.to_csv(out_dir / "phase8d_a1_segment_embedding_summary.csv", index=False)
    miss.to_csv(out_dir / "phase8d_a1_missingness_report.csv", index=False)
    file_diff.to_csv(out_dir / "phase8d_a1_group_difference_file_embeddings.csv", index=False)
    seg_diff.to_csv(out_dir / "phase8d_a1_group_difference_segment_embeddings.csv", index=False)
    top.to_csv(out_dir / "phase8d_a1_top_candidate_embedding_dims.csv", index=False)
    corr.to_csv(out_dir / "phase8d_a1_embedding_correlation_summary.csv", index=False)
    norm_summary.to_csv(out_dir / "phase8d_a1_embedding_norm_summary.csv", index=False)

    plot_warnings: list[str] = []
    if args.make_plots:
        plot_warnings = _plot_outputs(out_dir, femb.join(file_norms), emb_cols_file, top, miss, args.max_dims_for_correlation)

    runtime = time.perf_counter() - t0
    _write_report(
        out_dir / "phase8d_a1_ssl_embedding_audit_report.md",
        args,
        runtime,
        id_notes,
        top,
        miss,
        plot_warnings,
    )

    return {
        "runtime_sec": runtime,
        "id_notes": id_notes,
        "candidate_rows": len(top),
        "missingness_rows": len(miss),
        "progress_method": progress_method(),
        "plot_warnings": plot_warnings,
    }


def main() -> int:
    args = parse_args()
    result = run_audit(args)
    print("--- Phase 8D-A1 audit summary ---")
    print(f"Runtime: {result['runtime_sec']:.2f}s")
    print(f"Progress method: {result['progress_method']}")
    print(f"Candidate rows: {result['candidate_rows']}")
    print(f"Missingness rows: {result['missingness_rows']}")
    print(f"Output dir: {_resolve(args.output_dir)}")
    if result["id_notes"]:
        print("Notes:", "; ".join(result["id_notes"]))
    if result["plot_warnings"]:
        print("Plot warnings:", result["plot_warnings"])
    print("Descriptive embedding audit only — no training/predictions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

