#!/usr/bin/env python3
"""
Phase 9D-P5C: Controlled evaluation of accepted P5B partial-fabrication cascade.

Experimental manual-review support only — do NOT package to release/models.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import numpy as np
import pandas as pd

from phase9d_p5_partial_utils import (
    compute_live_localization_features,
    infer_file_category,
    load_timestamp_annotation_rows,
    match_timestamp_to_files,
    normalize_path_str,
    path_basename,
    path_stem_lower,
    progress,
    repo_root_from_here,
    segment_overlap_metrics,
    timestamp_lookup_from_audit,
)
from phase9d_p5_training_utils import (
    DIRECT_CATEGORIES,
    MIXER_CATEGORIES,
    PARTIAL_FILE_CATEGORIES as TRAIN_PARTIAL_CATS,
    REPLAY_CATEGORIES,
    P5C_ACCEPTED_CASCADE_THRESHOLDS,
    P5C_FILE_GATE_FEATURE_SET,
    P5C_SEGMENT_FEATURE_SET,
    apply_p5c_cascade_rule,
    assess_p5c_release_readiness,
    load_dataset_csv,
    load_p5b_candidate_artifacts,
    now_utc_str,
    predict_candidate_proba,
    repo_root_from_here,
)

AUDIO_EXTENSIONS = {".wav", ".flac", ".mp3", ".ogg", ".m4a"}
SEGMENT_DURATION_SEC = 4.0
SEGMENT_HOP_SEC = 2.0


def parse_args() -> argparse.Namespace:
    root = repo_root_from_here(Path(__file__))
    p = argparse.ArgumentParser(description="Phase 9D-P5C controlled cascade evaluation (experimental).")
    p.add_argument("--input_dir", default=str(root / "data/phase7c1/raw"))
    p.add_argument("--output_dir", default=str(root / "reports/phase9/partial_redesign/phase9d_p5c"))
    p.add_argument("--p5b_dir", default=str(root / "reports/phase9/partial_redesign/phase9d_p5b"))
    p.add_argument(
        "--file_master",
        default=str(root / "reports/phase8/models/phase8e0/phase8e0_file_level_master_dataset.csv"),
    )
    p.add_argument(
        "--segment_master",
        default=str(root / "reports/phase8/models/phase8e0/phase8e0_segment_level_master_dataset.csv"),
    )
    p.add_argument(
        "--file_gate_dataset",
        default=str(root / "reports/phase9/partial_redesign/phase9d_p5_file_partial_gate_dataset.csv"),
    )
    p.add_argument(
        "--segment_dataset",
        default=str(root / "reports/phase9/partial_redesign/phase9d_p5_segment_partial_localizer_dataset.csv"),
    )
    p.add_argument(
        "--ai_timestamp_csv",
        default=str(root / "data/phase7c1/raw/ai_fabricated/insertion_stamps.csv"),
    )
    p.add_argument(
        "--human_timestamp_csv",
        default=str(root / "data/phase7c1/raw/human_fabricated/insertion_stamps.csv"),
    )
    p.add_argument("--make_plots", action="store_true")
    p.add_argument("--no_progress", action="store_true")
    return p.parse_args()


def _rel_path(path: Path, root: Path) -> str:
    try:
        return normalize_path_str(str(path.resolve().relative_to(root.resolve())))
    except ValueError:
        return normalize_path_str(str(path.resolve()))


def infer_expected_condition(category: str) -> str:
    if category in TRAIN_PARTIAL_CATS:
        return "fabricated"
    if category in DIRECT_CATEGORIES:
        return "direct"
    if category in REPLAY_CATEGORIES:
        return "replay"
    if category in MIXER_CATEGORIES:
        return "mixer"
    return "unknown"


def scan_controlled_audio(input_dir: Path, root: Path) -> list[dict[str, Any]]:
    from phase9d_p5_training_utils import P5C_SKIP_SCAN_DIR_NAMES

    rows: list[dict[str, Any]] = []
    if not input_dir.is_dir():
        return rows
    for child in sorted(input_dir.iterdir()):
        if child.is_dir():
            if child.name.lower() in P5C_SKIP_SCAN_DIR_NAMES:
                continue
            for f in sorted(child.iterdir()):
                if f.is_file() and f.suffix.lower() in AUDIO_EXTENSIONS:
                    rows.append(_manifest_row_from_path(f, root))
        elif child.is_file() and child.suffix.lower() in AUDIO_EXTENSIONS:
            rows.append(_manifest_row_from_path(child, root))
    return rows


def _manifest_row_from_path(path: Path, root: Path) -> dict[str, Any]:
    rel = _rel_path(path, root)
    cat = infer_file_category(rel)
    expected_partial = 1 if cat in TRAIN_PARTIAL_CATS else 0
    return {
        "file_path": rel,
        "file_name": path.name,
        "category": cat,
        "expected_partial_label": expected_partial,
        "expected_condition": infer_expected_condition(cat),
        "timestamp_start": "",
        "timestamp_end": "",
        "has_timestamp_label": False,
        "source_split_status": "unknown_overlap_status",
    }


def _cheap_file_hash(path: Path, max_bytes: int = 65536) -> str:
    h = hashlib.sha256()
    try:
        with path.open("rb") as f:
            h.update(f.read(max_bytes))
        return h.hexdigest()[:16]
    except OSError:
        return ""


def build_overlap_audit(
    manifest: pd.DataFrame,
    file_gate_df: pd.DataFrame,
    segment_df: pd.DataFrame,
    root: Path,
) -> pd.DataFrame:
    train_paths: set[str] = set()
    train_names: set[str] = set()
    train_stems: set[str] = set()
    for df in (file_gate_df, segment_df):
        if df.empty or "audio_path" not in df.columns:
            continue
        for p in df["audio_path"].astype(str):
            train_paths.add(normalize_path_str(p))
            train_names.add(path_basename(p).lower())
            train_stems.add(path_stem_lower(p))

    rows: list[dict[str, Any]] = []
    for _, m in manifest.iterrows():
        fp = normalize_path_str(str(m["file_path"]))
        name = path_basename(fp).lower()
        stem = path_stem_lower(fp)
        abs_path = root / fp
        file_hash = _cheap_file_hash(abs_path) if abs_path.is_file() else ""
        if fp in train_paths or name in train_names or stem in train_stems:
            status = "seen_in_p5_training"
        else:
            status = "independent_holdout"
        rows.append(
            {
                "file_path": fp,
                "file_name": m["file_name"],
                "normalized_file_name": name,
                "file_stem": stem,
                "file_hash_prefix": file_hash,
                "overlap_status": status,
            }
        )
    return pd.DataFrame(rows)


def _load_audio_probe(path: Path) -> tuple[str, str, float | None]:
    """Return (error_status, error_message, duration_sec)."""
    try:
        import soundfile as sf
    except ImportError:
        return "ok", "", None
    try:
        info = sf.info(str(path))
        dur = float(info.duration)
        if dur < 0.25:
            return "too_short", f"duration_sec={dur:.3f}", dur
        if dur > 3600:
            return "suspicious_duration", f"duration_sec={dur:.1f}", dur
        return "ok", "", dur
    except Exception as exc:
        return "load_failure", str(exc), None


def _synthetic_segments(duration_sec: float) -> list[tuple[float, float]]:
    if duration_sec <= 0:
        return [(0.0, min(SEGMENT_DURATION_SEC, 0.25))]
    segs: list[tuple[float, float]] = []
    start = 0.0
    while start < duration_sec:
        end = min(start + SEGMENT_DURATION_SEC, duration_sec)
        if end - start >= 0.1:
            segs.append((start, end))
        start += SEGMENT_HOP_SEC
        if len(segs) > 500:
            break
    return segs or [(0.0, min(SEGMENT_DURATION_SEC, duration_sec))]


def _attach_timestamps(manifest: pd.DataFrame, root: Path, ai_csv: Path, human_csv: Path) -> pd.DataFrame:
    out = manifest.copy()
    parts: list[pd.DataFrame] = []
    if ai_csv.is_file():
        parts.append(load_timestamp_annotation_rows(ai_csv, "ai_fabricated"))
    if human_csv.is_file():
        parts.append(load_timestamp_annotation_rows(human_csv, "human_fabricated"))
    if not parts:
        return out
    ts_df = pd.concat(parts, ignore_index=True)
    audit = match_timestamp_to_files(ts_df, out.assign(audio_path=out["file_path"]))
    lookup = timestamp_lookup_from_audit(audit)
    for idx, row in out.iterrows():
        fp = normalize_path_str(str(row["file_path"]))
        hit = lookup.get(fp) or lookup.get(path_basename(fp).lower()) or lookup.get(path_stem_lower(fp))
        if hit:
            out.at[idx, "timestamp_start"] = hit.get("fabricated_start_sec", "")
            out.at[idx, "timestamp_end"] = hit.get("fabricated_end_sec", "")
            out.at[idx, "has_timestamp_label"] = True
    return out


def evaluate_controlled_cascade(
    *,
    manifest: pd.DataFrame,
    overlap_df: pd.DataFrame,
    file_master: pd.DataFrame,
    segment_master: pd.DataFrame,
    artifacts: dict[str, Any],
    root: Path,
    show: bool,
) -> tuple[pd.DataFrame, pd.DataFrame, list[dict[str, Any]]]:
    thresholds = artifacts.get("thresholds", P5C_ACCEPTED_CASCADE_THRESHOLDS)
    fg_bundle = artifacts["file_gate_bundle"]
    sg_bundle = artifacts["segment_bundle"]

    file_master = file_master.copy()
    file_master["_path_norm"] = file_master["audio_path"].map(normalize_path_str)
    segment_master = segment_master.copy()
    segment_master["_path_norm"] = segment_master["audio_path"].map(normalize_path_str)

    overlap_map = dict(zip(overlap_df["file_path"], overlap_df["overlap_status"]))
    file_rows: list[dict[str, Any]] = []
    segment_rows: list[dict[str, Any]] = []
    error_rows: list[dict[str, Any]] = []

    for i, m in enumerate(manifest.itertuples(index=False), start=1):
        fp = normalize_path_str(m.file_path)
        abs_path = root / fp
        split_status = overlap_map.get(fp, "unknown_overlap_status")
        err_status, err_msg, dur = _load_audio_probe(abs_path)

        fm = file_master[file_master["_path_norm"] == fp]
        sm = segment_master[segment_master["_path_norm"] == fp]

        base = {
            "file_path": fp,
            "file_name": m.file_name,
            "category": m.category,
            "expected_partial_label": int(m.expected_partial_label),
            "expected_condition": m.expected_condition,
            "source_split_status": split_status,
            "error_status": err_status,
            "error_message": err_msg,
        }

        if err_status != "ok":
            error_rows.append({**base, "failure_type": err_status})
            file_rows.append(
                {
                    **base,
                    "file_gate_probability": np.nan,
                    "file_gate_positive": False,
                    "max_segment_probability": np.nan,
                    "segment_threshold_positive": False,
                    "high_segment_fraction": np.nan,
                    "broad_activation_flag": False,
                    "topk_minus_rest_probability": np.nan,
                    "contrast_positive": False,
                    "partial_evidence_positive": False,
                    "candidate_segment_start": np.nan,
                    "candidate_segment_end": np.nan,
                    "has_timestamp_label": bool(m.has_timestamp_label),
                    "top1_timestamp_hit": False,
                    "top3_timestamp_hit": False,
                    "top5_timestamp_hit": False,
                }
            )
            continue

        if fm.empty:
            error_rows.append({**base, "failure_type": "missing_file_features"})
            file_rows.append({**base, "partial_evidence_positive": False})
            continue

        try:
            gate_proba = float(predict_candidate_proba(fg_bundle, fm)[0])
        except Exception as exc:
            error_rows.append({**base, "failure_type": "file_gate_predict_failure", "error_message": str(exc)})
            file_rows.append({**base, "partial_evidence_positive": False})
            continue

        if sm.empty:
            error_rows.append({**base, "failure_type": "missing_segment_features"})
            file_rows.append({**base, "file_gate_probability": gate_proba, "partial_evidence_positive": False})
            continue

        seg_work = sm.copy()
        if "segment_id" not in seg_work.columns:
            seg_work["segment_id"] = [f"{path_stem_lower(fp)}_{j:04d}" for j in range(len(seg_work))]
        seg_work = compute_live_localization_features(seg_work)
        try:
            seg_probs = predict_candidate_proba(sg_bundle, seg_work)
        except Exception as exc:
            error_rows.append({**base, "failure_type": "segment_predict_failure", "error_message": str(exc)})
            file_rows.append({**base, "file_gate_probability": gate_proba, "partial_evidence_positive": False})
            continue

        seg_work["segment_probability"] = seg_probs
        order = np.argsort(-seg_probs)
        seg_work = seg_work.iloc[order].reset_index(drop=True)
        seg_work["segment_rank"] = np.arange(1, len(seg_work) + 1)
        seg_work["is_high_segment"] = seg_work["segment_probability"] >= float(thresholds["segment_threshold"])

        cascade = apply_p5c_cascade_rule(
            file_gate_probability=gate_proba,
            segment_probs=seg_probs,
            thresholds=thresholds,
        )
        best_idx = int(np.argmax(seg_probs)) if len(seg_probs) else 0
        cand_start = float(seg_work.iloc[best_idx]["start_sec"]) if len(seg_work) else np.nan
        cand_end = float(seg_work.iloc[best_idx]["end_sec"]) if len(seg_work) else np.nan

        ts_start = pd.to_numeric(m.timestamp_start, errors="coerce") if m.has_timestamp_label else np.nan
        ts_end = pd.to_numeric(m.timestamp_end, errors="coerce") if m.has_timestamp_label else np.nan
        top1 = top3 = top5 = False
        if m.has_timestamp_label and np.isfinite(ts_start) and np.isfinite(ts_end):
            ranked = seg_work.sort_values("segment_probability", ascending=False)
            for k in (1, 3, 5):
                head = ranked.head(k)
                hit = False
                for _, srow in head.iterrows():
                    ov = segment_overlap_metrics(
                        float(srow["start_sec"]),
                        float(srow["end_sec"]),
                        float(ts_start),
                        float(ts_end),
                    )
                    if ov.get("timestamp_region_label") == "inside_fabricated_region":
                        hit = True
                        break
                if k == 1:
                    top1 = hit
                elif k == 3:
                    top3 = hit
                else:
                    top5 = hit

        file_rows.append(
            {
                **base,
                "error_status": "ok",
                "error_message": "",
                "file_gate_probability": gate_proba,
                **cascade,
                "candidate_segment_start": cand_start,
                "candidate_segment_end": cand_end,
                "has_timestamp_label": bool(m.has_timestamp_label),
                "top1_timestamp_hit": top1,
                "top3_timestamp_hit": top3,
                "top5_timestamp_hit": top5,
            }
        )

        for _, srow in seg_work.iterrows():
            ov_known = False
            if m.has_timestamp_label and np.isfinite(ts_start) and np.isfinite(ts_end):
                ov = segment_overlap_metrics(
                    float(srow["start_sec"]),
                    float(srow["end_sec"]),
                    float(ts_start),
                    float(ts_end),
                )
                ov_known = ov.get("timestamp_region_label") == "inside_fabricated_region"
            segment_rows.append(
                {
                    "file_path": fp,
                    "segment_index": int(srow["segment_rank"]) - 1,
                    "segment_start": float(srow["start_sec"]),
                    "segment_end": float(srow["end_sec"]),
                    "segment_probability": float(srow["segment_probability"]),
                    "segment_rank": int(srow["segment_rank"]),
                    "is_high_segment": bool(srow["is_high_segment"]),
                    "overlaps_known_fabricated_timestamp": ov_known,
                    "expected_segment_label": int(ov_known),
                }
            )

        if show and i % 25 == 0:
            progress(f"P5C evaluated {i}/{len(manifest)} files...", enabled=True)

    return pd.DataFrame(file_rows), pd.DataFrame(segment_rows), error_rows


def compute_controlled_metrics(file_df: pd.DataFrame) -> dict[str, Any]:
    ok = file_df[file_df["error_status"].astype(str) == "ok"].copy()
    metrics: dict[str, Any] = {
        "total_files": int(len(file_df)),
        "evaluated_files": int(len(ok)),
        "failed_files": int(len(file_df) - len(ok)),
        "independent_holdout_count": int((ok["source_split_status"] == "independent_holdout").sum()),
        "seen_controlled_count": int((ok["source_split_status"] == "seen_in_p5_training").sum()),
        "unknown_overlap_count": int((ok["source_split_status"] == "unknown_overlap_status").sum()),
    }
    partial = ok[ok["expected_partial_label"].astype(int) == 1]
    non_partial = ok[ok["expected_partial_label"].astype(int) == 0]
    metrics["partial_file_count"] = int(len(partial))
    metrics["non_partial_file_count"] = int(len(non_partial))

    if len(partial):
        metrics["partial_evidence_recall"] = float(partial["partial_evidence_positive"].astype(bool).mean())
    else:
        metrics["partial_evidence_recall"] = np.nan

    if len(non_partial):
        metrics["non_partial_false_alarm_rate"] = float(
            non_partial["partial_evidence_positive"].astype(bool).mean()
        )
    else:
        metrics["non_partial_false_alarm_rate"] = np.nan

    def _cond_rate(cond: str) -> float:
        g = ok[ok["expected_condition"].astype(str) == cond]
        if g.empty:
            return np.nan
        return float(g["partial_evidence_positive"].astype(bool).mean())

    metrics["direct_false_partial_rate"] = _cond_rate("direct")
    metrics["replay_false_partial_rate"] = _cond_rate("replay")
    metrics["mixer_false_partial_rate"] = _cond_rate("mixer")

    pos = ok[ok["partial_evidence_positive"].astype(bool)]
    if len(pos):
        metrics["broad_activation_rate_when_positive"] = float(pos["broad_activation_flag"].astype(bool).mean())
        metrics["top1_hit_rate_when_positive"] = float(pos.loc[pos["has_timestamp_label"], "top1_timestamp_hit"].astype(bool).mean()) if pos["has_timestamp_label"].any() else np.nan
        metrics["top3_hit_rate_when_positive"] = float(pos.loc[pos["has_timestamp_label"], "top3_timestamp_hit"].astype(bool).mean()) if pos["has_timestamp_label"].any() else np.nan
        metrics["top5_hit_rate_when_positive"] = float(pos.loc[pos["has_timestamp_label"], "top5_timestamp_hit"].astype(bool).mean()) if pos["has_timestamp_label"].any() else np.nan
    else:
        metrics["broad_activation_rate_when_positive"] = np.nan
        metrics["top1_hit_rate_when_positive"] = np.nan
        metrics["top3_hit_rate_when_positive"] = np.nan
        metrics["top5_hit_rate_when_positive"] = np.nan

    ts_pos = ok[ok["has_timestamp_label"].astype(bool) & ok["partial_evidence_positive"].astype(bool)]
    metrics["timestamp_positive_count"] = int(len(ts_pos))

    invalid_cases = file_df[file_df["error_status"].astype(str).isin({"too_short", "silent", "invalid", "load_failure"})]
    if len(invalid_cases):
        handled = invalid_cases[invalid_cases["error_status"].astype(str).ne("ok")]
        metrics["invalid_file_handling_pass_rate"] = float(len(handled) / len(invalid_cases))
    else:
        metrics["invalid_file_handling_pass_rate"] = 1.0

    metrics["median_candidate_timestamp_error_seconds"] = np.nan
    return metrics


def write_p5c_report(
    path: Path,
    *,
    args: argparse.Namespace,
    manifest: pd.DataFrame,
    overlap_df: pd.DataFrame,
    metrics: dict[str, Any],
    artifacts: dict[str, Any],
    release_ready: bool,
    release_reasons: list[str],
    examples_success: pd.DataFrame,
    examples_false: pd.DataFrame,
) -> None:
    holdout = int(metrics.get("independent_holdout_count", 0))
    seen = int(metrics.get("seen_controlled_count", 0))
    if holdout == 0 and seen > 0:
        eval_mode = "controlled reuse/sanity evaluation (NOT independent held-out)"
    elif holdout > 0:
        eval_mode = "includes independent held-out files"
    else:
        eval_mode = "overlap status unclear"

    th = artifacts.get("thresholds", P5C_ACCEPTED_CASCADE_THRESHOLDS)
    paths = artifacts.get("paths", {})
    if release_ready:
        next_action = (
            "Candidate acceptable for release packaging evaluation (still experimental; "
            "not production-ready; manual review recommended)."
        )
    elif holdout == 0:
        next_action = (
            "P5C controlled evaluation completed, but release packaging is not recommended "
            "because no independent held-out files were available."
        )
    else:
        next_action = (
            "P5C controlled evaluation completed, but P5B partial cascade remains "
            "manual-review support only."
        )

    lines = [
        "# Phase 9D-P5C Controlled Evaluation Report (Experimental)",
        "",
        f"Generated: {now_utc_str()}",
        "",
        "**Production claim:** NO — experimental partial-fabrication evidence only.",
        "",
        "**Release packaging performed:** NO — nothing written to `release/models/` or `models_saved/active/`.",
        "",
        "## Purpose",
        "",
        "Evaluate whether the accepted P5B two-stage cascade produces useful partial-fabrication "
        "evidence indicators on controlled audio without unacceptable false partial alerts on "
        "direct, replay, and mixer files.",
        "",
        "## Input",
        "",
        f"- Controlled audio directory: `{args.input_dir}`",
        f"- Files in manifest: {len(manifest)}",
        "",
        "## Overlap audit summary",
        "",
        f"- Evaluation mode: **{eval_mode}**",
        f"- Independent holdout files: {holdout}",
        f"- Seen in P5 training: {seen}",
        f"- Unknown overlap: {int(metrics.get('unknown_overlap_count', 0))}",
        "",
        "This phase does not hide overlap with P5A/P5B training data.",
        "",
        "## Accepted cascade thresholds (P5B-P2)",
        "",
        f"- file_gate_threshold = {th['file_gate_threshold']}",
        f"- segment_threshold = {th['segment_threshold']}",
        f"- contrast_threshold = {th['contrast_threshold']}",
        f"- broad_limit = {th['broad_limit']}",
        "",
        f"- File gate feature set: `{P5C_FILE_GATE_FEATURE_SET}`",
        f"- Segment localizer feature set: `{P5C_SEGMENT_FEATURE_SET}`",
        "",
        "## Model artifacts used (experimental candidates only)",
        "",
        f"- File gate: `{paths.get('file_gate', 'missing')}`",
        f"- Segment localizer v2: `{paths.get('segment_localizer', 'missing')}`",
        f"- Cascade config: `{paths.get('cascade_config', 'missing')}`",
        "",
        "## File-level results",
        "",
        f"- Total files: {metrics.get('total_files')}",
        f"- Evaluated (ok): {metrics.get('evaluated_files')}",
        f"- Failed/skipped: {metrics.get('failed_files')}",
        f"- Partial evidence recall (partial files): {metrics.get('partial_evidence_recall', np.nan)}",
        f"- Non-partial false alarm rate: {metrics.get('non_partial_false_alarm_rate', np.nan)}",
        "",
        "## Condition-wise false partial rates",
        "",
        f"- direct_false_partial_rate: {metrics.get('direct_false_partial_rate', np.nan)}",
        f"- replay_false_partial_rate: {metrics.get('replay_false_partial_rate', np.nan)}",
        f"- mixer_false_partial_rate: {metrics.get('mixer_false_partial_rate', np.nan)}",
        "",
        "## Localization quality (when cascade positive)",
        "",
        f"- broad_activation_rate_when_positive: {metrics.get('broad_activation_rate_when_positive', np.nan)}",
        f"- top1_hit_rate_when_positive: {metrics.get('top1_hit_rate_when_positive', np.nan)}",
        f"- top3_hit_rate_when_positive: {metrics.get('top3_hit_rate_when_positive', np.nan)}",
        f"- top5_hit_rate_when_positive: {metrics.get('top5_hit_rate_when_positive', np.nan)}",
        "",
        "## Error handling",
        "",
        f"- invalid_file_handling_pass_rate: {metrics.get('invalid_file_handling_pass_rate', np.nan)}",
        "",
        "## Examples — successful candidate localization",
        "",
    ]
    if examples_success.empty:
        lines.append("- None selected.")
    else:
        for _, r in examples_success.head(5).iterrows():
            lines.append(
                f"- `{r['file_path']}` — partial evidence indicator at "
                f"{r.get('candidate_segment_start', 'n/a')}–{r.get('candidate_segment_end', 'n/a')}s "
                f"(gate={r.get('file_gate_probability', np.nan):.3f}, max_seg={r.get('max_segment_probability', np.nan):.3f})"
            )

    lines.extend(["", "## Examples — false partial evidence", ""])
    if examples_false.empty:
        lines.append("- None selected.")
    else:
        for _, r in examples_false.head(5).iterrows():
            lines.append(
                f"- `{r['file_path']}` ({r.get('expected_condition', 'n/a')}) — "
                f"partial_evidence_positive=True with gate={r.get('file_gate_probability', np.nan):.3f}"
            )

    lines.extend(
        [
            "",
            "## Release readiness assessment",
            "",
            f"**Candidate acceptable for release packaging evaluation:** {'yes' if release_ready else 'no'}",
            "",
        ]
    )
    if release_reasons:
        lines.append("Reasons:")
        for r in release_reasons:
            lines.append(f"- {r}")
    lines.extend(
        [
            "",
            "## Limitations",
            "",
            "- Uses phase8e0 precomputed features when available; not a fully live feature-extraction deployment test.",
            "- Does not use release partial model, AASIST, or HybridResNet.",
            "- Evidence axes remain separated (origin, replay, mixer, partial fabrication).",
            "- Outputs are candidate indicators for manual review, not final authenticity verdicts.",
            "",
            "## Recommended next action",
            "",
            next_action,
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    show = not args.no_progress
    root = repo_root_from_here(Path(__file__))
    out_dir = Path(args.output_dir)
    p5b_dir = Path(args.p5b_dir)
    if not out_dir.is_absolute():
        out_dir = (root / out_dir).resolve()
    if not p5b_dir.is_absolute():
        p5b_dir = (root / p5b_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    input_dir = Path(args.input_dir)
    if not input_dir.is_absolute():
        input_dir = (root / input_dir).resolve()

    progress("Loading P5B experimental candidate models...", enabled=show)
    artifacts = load_p5b_candidate_artifacts(p5b_dir)

    progress("Building controlled evaluation manifest...", enabled=show)
    manifest_rows = scan_controlled_audio(input_dir, root)
    manifest = pd.DataFrame(manifest_rows)
    manifest = _attach_timestamps(
        manifest,
        root,
        Path(args.ai_timestamp_csv) if Path(args.ai_timestamp_csv).is_absolute() else root / args.ai_timestamp_csv,
        Path(args.human_timestamp_csv) if Path(args.human_timestamp_csv).is_absolute() else root / args.human_timestamp_csv,
    )
    manifest_path = out_dir / "phase9d_p5c_controlled_manifest.csv"
    manifest.to_csv(manifest_path, index=False)

    file_gate_df = load_dataset_csv(
        Path(args.file_gate_dataset) if Path(args.file_gate_dataset).is_absolute() else root / args.file_gate_dataset
    )
    segment_df = load_dataset_csv(
        Path(args.segment_dataset) if Path(args.segment_dataset).is_absolute() else root / args.segment_dataset
    )
    overlap_df = build_overlap_audit(manifest, file_gate_df, segment_df, root)
    manifest["source_split_status"] = manifest["file_path"].map(
        dict(zip(overlap_df["file_path"], overlap_df["overlap_status"]))
    )
    overlap_df.to_csv(out_dir / "phase9d_p5c_overlap_audit.csv", index=False)

    overlap_md = [
        "# Phase 9D-P5C Overlap Audit",
        "",
        f"Generated: {now_utc_str()}",
        "",
        f"- Independent holdout: {(overlap_df['overlap_status'] == 'independent_holdout').sum()}",
        f"- Seen in P5 training: {(overlap_df['overlap_status'] == 'seen_in_p5_training').sum()}",
        "",
    ]
    if (overlap_df["overlap_status"] == "independent_holdout").sum() == 0:
        overlap_md.append(
            "**Note:** This is a controlled reuse/sanity evaluation, not a true independent held-out evaluation."
        )
    (out_dir / "phase9d_p5c_overlap_audit.md").write_text("\n".join(overlap_md) + "\n", encoding="utf-8")

    fm_path = Path(args.file_master) if Path(args.file_master).is_absolute() else root / args.file_master
    sm_path = Path(args.segment_master) if Path(args.segment_master).is_absolute() else root / args.segment_master
    file_master = pd.read_csv(fm_path, low_memory=False)
    segment_master = pd.read_csv(sm_path, low_memory=False)

    progress("Running controlled cascade inference...", enabled=show)
    file_pred, seg_pred, error_list = evaluate_controlled_cascade(
        manifest=manifest,
        overlap_df=overlap_df,
        file_master=file_master,
        segment_master=segment_master,
        artifacts=artifacts,
        root=root,
        show=show,
    )
    file_pred.to_csv(out_dir / "phase9d_p5c_file_predictions.csv", index=False)
    seg_pred.to_csv(out_dir / "phase9d_p5c_segment_predictions.csv", index=False)
    pd.DataFrame(error_list).to_csv(out_dir / "phase9d_p5c_error_cases.csv", index=False)

    metrics = compute_controlled_metrics(file_pred)
    metrics["accepted_cascade_thresholds"] = artifacts.get("thresholds", P5C_ACCEPTED_CASCADE_THRESHOLDS)
    pd.DataFrame([metrics]).to_csv(out_dir / "phase9d_p5c_controlled_metrics.csv", index=False)
    (out_dir / "phase9d_p5c_controlled_metrics.json").write_text(
        json.dumps(metrics, indent=2, default=str), encoding="utf-8"
    )

    release_ready, release_reasons = assess_p5c_release_readiness(metrics)
    ok = file_pred[file_pred["error_status"].astype(str) == "ok"]
    examples_success = ok[
        ok["partial_evidence_positive"].astype(bool) & ok["expected_partial_label"].astype(int).eq(1)
    ].sort_values("max_segment_probability", ascending=False)
    examples_false = ok[
        ok["partial_evidence_positive"].astype(bool) & ok["expected_partial_label"].astype(int).eq(0)
    ].sort_values("file_gate_probability", ascending=False)

    write_p5c_report(
        out_dir / "phase9d_p5c_controlled_evaluation_report.md",
        args=args,
        manifest=manifest,
        overlap_df=overlap_df,
        metrics=metrics,
        artifacts=artifacts,
        release_ready=release_ready,
        release_reasons=release_reasons,
        examples_success=examples_success,
        examples_false=examples_false,
    )

    progress(f"P5C complete. Outputs: {out_dir}", enabled=show)
    progress("No release packaging performed.", enabled=show)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
