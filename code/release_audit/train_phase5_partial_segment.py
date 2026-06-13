"""Phase 5 — retrain partial segment localizer without F9 features (experimental).

Uses leakage-safe train/dev/test splits. No augmentation. Does not overwrite
release/models/partial_segment/.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from phase5_partial_common import (
    DEFAULT_OUT,
    F9_FORBIDDEN_FEATURES,
    PARTIAL_FILE_CATEGORIES,
    P5_SEGMENT_DATASET,
    STOP_RULE_MIN_ORACLE_TOP5_RATE,
    attach_leakage_safe_split,
    build_phase5_model_features,
    progress,
    setup_import_paths,
    write_f9_audit,
)

ROOT = Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT))
    parser.add_argument("--segment-dataset", default=str(P5_SEGMENT_DATASET))
    parser.add_argument("--random-seed", type=int, default=42)
    parser.add_argument("--max-selected-features", type=int, default=75)
    parser.add_argument("--broad-limit", type=float, default=0.45)
    parser.add_argument("--max-scripted-insert-files", type=int, default=0, help="Optional 2-3 scripted inserts (0=off)")
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def choose_segment_threshold(
    dev_pred: pd.DataFrame,
    *,
    broad_limit: float,
) -> tuple[float, pd.DataFrame]:
    """Pick threshold maximizing partial-file top-5 hit with broad_activation control."""
    rows: list[dict[str, Any]] = []
    partial_files = dev_pred[dev_pred["file_category"].isin(PARTIAL_FILE_CATEGORIES)]
    if partial_files.empty:
        return 0.50, pd.DataFrame()

    for th in np.round(np.arange(0.20, 0.951, 0.05), 2):
        top5_hits = 0
        n_partial = 0
        broad_fail = 0
        for _, g in partial_files.groupby("file_id", sort=False):
            n_partial += 1
            g = g.sort_values("segment_probability", ascending=False)
            high_frac = float((g["segment_probability"] >= th).mean())
            inside = g[g["target_is_fabricated_segment"].astype(int).eq(1)]
            top5_inside = bool(g.head(5)["target_is_fabricated_segment"].astype(int).eq(1).any())
            if top5_inside:
                top5_hits += 1
            if high_frac >= broad_limit:
                broad_fail += 1
        rows.append(
            {
                "threshold": float(th),
                "n_partial_files": n_partial,
                "top5_hit_rate": float(top5_hits / max(n_partial, 1)),
                "broad_activation_files": broad_fail,
                "broad_activation_rate": float(broad_fail / max(n_partial, 1)),
            }
        )
    grid = pd.DataFrame(rows)
    candidates = grid[grid["broad_activation_rate"] <= 0.35].copy()
    if candidates.empty:
        candidates = grid.copy()
    candidates = candidates.sort_values(
        ["top5_hit_rate", "broad_activation_rate", "threshold"],
        ascending=[False, True, False],
    )
    best_th = float(candidates.iloc[0]["threshold"])
    return best_th, grid


def oracle_file_metrics(
    pred: pd.DataFrame,
    *,
    threshold: float,
    broad_limit: float,
    scope: str,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for file_id, g in pred.groupby("file_id", sort=False):
        g = g.sort_values("segment_probability", ascending=False)
        cat = str(g["file_category"].iloc[0]) if "file_category" in g.columns else ""
        is_partial = cat in PARTIAL_FILE_CATEGORIES
        high_frac = float((g["segment_probability"] >= threshold).mean())
        top5_hit = bool(g.head(5)["target_is_fabricated_segment"].astype(int).eq(1).any()) if is_partial else False
        localized = bool(is_partial and top5_hit and high_frac < broad_limit)
        rows.append(
            {
                "scope": scope,
                "file_id": file_id,
                "file_category": cat,
                "is_partial_file": is_partial,
                "segment_threshold": threshold,
                "high_segment_fraction": high_frac,
                "top5_inside_hit": top5_hit,
                "localized_oracle": localized,
                "broad_activation": bool(high_frac >= broad_limit),
            }
        )
    return pd.DataFrame(rows)


def summarize_oracle(metrics: pd.DataFrame) -> dict[str, Any]:
    partial = metrics[metrics["is_partial_file"].astype(bool)]
    clean = metrics[~metrics["is_partial_file"].astype(bool)]
    return {
        "n_partial_files": int(len(partial)),
        "n_clean_files": int(len(clean)),
        "top5_hit_rate": float(partial["top5_inside_hit"].mean()) if len(partial) else float("nan"),
        "localized_rate": float(partial["localized_oracle"].mean()) if len(partial) else float("nan"),
        "clean_broad_activation_rate": float(clean["broad_activation"].mean()) if len(clean) else float("nan"),
    }


def main() -> int:
    args = parse_args()
    setup_import_paths()
    from phase9d_p5_training_utils import (  # noqa: E402
        TASK_SEGMENT_LOCALIZER,
        build_pipeline,
        clean_feature_matrix,
        parse_binary_target,
    )

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    started = utc_now()

    seg_path = Path(args.segment_dataset)
    if not seg_path.is_file():
        raise FileNotFoundError(f"Segment dataset missing: {seg_path}. Run prepare_phase5_partial_dataset.py first.")

    progress("[phase5] loading segment dataset (large CSV — please wait)")
    df = pd.read_csv(seg_path, low_memory=False)
    df = attach_leakage_safe_split(df)
    if "allowed_use" in df.columns:
        df = df[df["allowed_use"].astype(str) != "exclude_missing_features"].copy()

    header_cols = list(df.columns)
    model_features = build_phase5_model_features(header_cols)
    write_f9_audit(out_dir, model_features)
    removed_in_model = [c for c in F9_FORBIDDEN_FEATURES if c in header_cols]
    progress(f"[phase5] model features: {len(model_features)} (F9 removed: {removed_in_model})")

    train = df[df["leakage_safe_split"].eq("train")].copy()
    dev = df[df["leakage_safe_split"].eq("dev")].copy()
    test = df[df["leakage_safe_split"].eq("test")].copy()
    progress(f"[phase5] rows train/dev/test: {len(train)}/{len(dev)}/{len(test)}")

    if args.max_scripted_insert_files > 0:
        progress(
            f"[phase5] note: --max-scripted-insert-files={args.max_scripted_insert_files} "
            "reserved for future scripted inserts; not applied in v1 (no new audio)."
        )

    x_train, usable, _, _ = clean_feature_matrix(train, model_features)
    y_train = parse_binary_target(train["target_is_fabricated_segment"], "target_is_fabricated_segment")
    k = min(args.max_selected_features, len(usable))
    model = build_pipeline(k, args.random_seed)
    progress(f"[phase5] fitting segment localizer on {len(train)} rows, {int(y_train.sum())} positives, k={k}")
    model.fit(x_train, y_train)

    def predict_frame(frame: pd.DataFrame) -> pd.DataFrame:
        out = frame.copy()
        x, cols, _, _ = clean_feature_matrix(out, usable)
        out["segment_probability"] = model.predict_proba(x)[:, 1]
        out["model_features_used"] = len(cols)
        return out

    dev_pred = predict_frame(dev)
    threshold, threshold_grid = choose_segment_threshold(dev_pred, broad_limit=args.broad_limit)
    progress(f"[phase5] dev-selected segment threshold: {threshold}")

    scopes = {"train": train, "dev": dev, "test": test}
    pred_frames = []
    oracle_frames = []
    for scope, frame in scopes.items():
        pred = predict_frame(frame)
        pred["prediction_scope"] = scope
        pred["segment_threshold"] = threshold
        pred_frames.append(pred)
        oracle_frames.append(
            oracle_file_metrics(pred, threshold=threshold, broad_limit=args.broad_limit, scope=scope)
        )

    predictions = pd.concat(pred_frames, ignore_index=True, sort=False)
    predictions.to_csv(out_dir / "phase5_segment_predictions.csv", index=False)

    oracle_metrics = pd.concat(oracle_frames, ignore_index=True)
    oracle_metrics.to_csv(out_dir / "phase5_oracle_file_metrics.csv", index=False)
    if len(threshold_grid):
        threshold_grid.to_csv(out_dir / "phase5_dev_threshold_grid.csv", index=False)

    test_summary = summarize_oracle(oracle_metrics[oracle_metrics["scope"].eq("test")])
    dev_summary = summarize_oracle(oracle_metrics[oracle_metrics["scope"].eq("dev")])
    stop = {
        "oracle_test_top5_hit_rate": test_summary["top5_hit_rate"],
        "oracle_test_localized_rate": test_summary["localized_rate"],
        "min_required_top5_hit_rate": STOP_RULE_MIN_ORACLE_TOP5_RATE,
        "passes_stop_rule": bool(
            test_summary.get("top5_hit_rate", 0.0) >= STOP_RULE_MIN_ORACLE_TOP5_RATE
        ),
        "n_partial_test_files": test_summary["n_partial_files"],
    }
    (out_dir / "phase5_stop_rule.json").write_text(json.dumps(stop, indent=2), encoding="utf-8")

    metadata = {
        "created_at": utc_now(),
        "started_at": started,
        "status": "phase5_experimental",
        "active_production_model": False,
        "task": TASK_SEGMENT_LOCALIZER,
        "f9_features_removed": sorted(F9_FORBIDDEN_FEATURES),
        "model_features": usable,
        "segment_threshold": threshold,
        "segment_threshold_source": "leakage_safe_dev_oracle_grid",
        "broad_limit": args.broad_limit,
        "training_rows": int(len(train)),
        "positive_training_segments": int(y_train.sum()),
        "dev_oracle_summary": dev_summary,
        "test_oracle_summary": test_summary,
        "stop_rule": stop,
        "segment_dataset": str(seg_path),
        "no_augmentation": True,
    }
    (out_dir / "phase5_partial_segment_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    joblib.dump(
        {
            "model": model,
            "features": usable,
            "task_name": TASK_SEGMENT_LOCALIZER,
            "feature_set": "phase5_combined_no_f9",
            "segment_threshold": threshold,
            "experimental": True,
        },
        out_dir / "phase5_partial_segment_localizer.joblib",
    )

    report = [
        "# Phase 5 — Partial segment localizer (no F9)",
        "",
        f"Generated: {utc_now()}",
        "",
        f"Segment threshold (dev oracle grid): `{threshold}`",
        f"Model features: `{len(usable)}` (F9 removed)",
        f"Training segments: `{len(train)}` ({int(y_train.sum())} positive)",
        "",
        "## Oracle summary (leakage-safe test)",
        "",
        f"- partial files: {test_summary['n_partial_files']}",
        f"- top-5 hit rate: {test_summary.get('top5_hit_rate', float('nan')):.4f}",
        f"- localized rate (top5 + not broad): {test_summary.get('localized_rate', float('nan')):.4f}",
        f"- clean broad-activation rate: {test_summary.get('clean_broad_activation_rate', float('nan')):.4f}",
        "",
        "## Stop rule (test top-5 hit >= 50%)",
        "",
        f"- **{'PASS' if stop['passes_stop_rule'] else 'FAIL'}**",
        "",
        "## Dev oracle",
        "",
        f"- top-5 hit: {dev_summary.get('top5_hit_rate', float('nan')):.4f}",
        f"- localized: {dev_summary.get('localized_rate', float('nan')):.4f}",
    ]
    if not stop["passes_stop_rule"]:
        report.extend(
            [
                "",
                "## Guidance",
                "",
                "Oracle localization on leakage-safe test is below 50% top-5 hit. "
                "Do not reconnect cascade gating to release; proceed to Phase 6 honest wording.",
            ]
        )
    (out_dir / "phase5_partial_train_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    progress(f"[phase5] complete -> {out_dir}")
    progress(f"[phase5] stop rule: {stop}")
    return 0 if stop["passes_stop_rule"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
