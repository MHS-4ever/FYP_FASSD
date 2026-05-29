#!/usr/bin/env python3
"""
Phase 9D-P5B: Train/evaluate redesigned partial file gate + segment localizer v2.

Experimental only — do NOT package to release/models or models_saved/active.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import pandas as pd

from phase9d_p5_partial_utils import infer_file_category
from phase9d_p5_training_utils import (
    FILE_GATE_FEATURE_SETS,
    SEGMENT_FEATURE_SETS,
    TASK_FILE_GATE,
    TASK_SEGMENT_LOCALIZER,
    compute_segment_file_localization,
    fit_p5b_experimental_candidate_models,
    load_dataset_csv,
    load_json_columns,
    maybe_save_artifacts,
    maybe_save_plots,
    progress,
    recompute_p5b_derived_outputs,
    repo_root_from_here,
    resolve_group_column,
    run_task_cv,
)


def parse_args() -> argparse.Namespace:
    root = repo_root_from_here(Path(__file__))
    p = argparse.ArgumentParser(description="Phase 9D-P5B partial model training (experimental, manual run).")
    p.add_argument(
        "--file_gate_dataset",
        default=str(root / "reports/phase9/partial_redesign/phase9d_p5_file_partial_gate_dataset.csv"),
    )
    p.add_argument(
        "--segment_dataset",
        default=str(root / "reports/phase9/partial_redesign/phase9d_p5_segment_partial_localizer_dataset.csv"),
    )
    p.add_argument(
        "--file_feature_columns",
        default=str(root / "reports/phase9/partial_redesign/phase9d_p5_file_gate_feature_columns.json"),
    )
    p.add_argument(
        "--segment_feature_columns",
        default=str(root / "reports/phase9/partial_redesign/phase9d_p5_segment_localizer_feature_columns.json"),
    )
    p.add_argument(
        "--output_dir",
        default=str(root / "reports/phase9/partial_redesign/phase9d_p5b"),
    )
    p.add_argument("--cv_folds", type=int, default=5)
    p.add_argument("--random_seed", type=int, default=42)
    p.add_argument("--file_feature_sets", default="acoustic,ssl,combined")
    p.add_argument("--segment_feature_sets", default="acoustic,ssl,localization,combined")
    p.add_argument("--model_type", default="logistic_regression_l2", choices=["logistic_regression_l2"])
    p.add_argument("--max_selected_features_file", type=int, default=75)
    p.add_argument("--max_selected_features_segment", type=int, default=100)
    p.add_argument("--selected_segment_feature_set", default="combined")
    p.add_argument("--selected_segment_threshold", type=float, default=0.50)
    p.add_argument("--reuse_existing_predictions", action="store_true")
    p.add_argument("--fit_final_candidate_models", action="store_true")
    p.add_argument("--force_candidate_models", action="store_true")
    p.add_argument("--make_plots", action="store_true")
    p.add_argument("--save_artifacts", action="store_true")
    p.add_argument("--no_progress", action="store_true")
    return p.parse_args()


def _parse_feature_sets(raw: str, allowed: tuple[str, ...]) -> list[str]:
    out = [s.strip() for s in raw.split(",") if s.strip()]
    bad = [s for s in out if s not in allowed]
    if bad:
        raise ValueError(f"Unsupported feature sets: {bad}; allowed={allowed}")
    return out


def _prepare_file_gate_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "file_category" not in out.columns or out["file_category"].astype(str).str.strip().eq("").all():
        out["file_category"] = out["audio_path"].map(infer_file_category)
    if "allowed_use" in out.columns:
        out = out[out["allowed_use"].astype(str) != "exclude_missing_features"].copy()
    return out


def _prepare_segment_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "file_category" not in out.columns or out["file_category"].astype(str).str.strip().eq("").all():
        out["file_category"] = out["audio_path"].map(infer_file_category)
    return out


def _load_metrics_summary(out_dir: Path, prefix: str, feature_sets: list[str]) -> dict[str, pd.DataFrame]:
    path = out_dir / f"phase9d_p5b_{prefix}_metrics.csv"
    if not path.is_file():
        return {fs: pd.DataFrame() for fs in feature_sets}
    df = pd.read_csv(path, low_memory=False)
    out: dict[str, pd.DataFrame] = {}
    for fs in feature_sets:
        g = df[(df["feature_set"].astype(str) == fs) & (df.get("metric_scope", pd.Series("")) == "cross_validated_experimental_mean")]
        if g.empty:
            g = df[df["feature_set"].astype(str) == fs].tail(1)
        out[fs] = g
    return out


def main() -> int:
    args = parse_args()
    show = not args.no_progress
    root = repo_root_from_here(Path(__file__))
    out_dir = Path(args.output_dir)
    if not out_dir.is_absolute():
        out_dir = (root / out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    file_sets = _parse_feature_sets(args.file_feature_sets, FILE_GATE_FEATURE_SETS)
    segment_sets = _parse_feature_sets(args.segment_feature_sets, SEGMENT_FEATURE_SETS)

    if args.fit_final_candidate_models:
        progress("Fitting P5B experimental candidate models (candidate_models/ only)...", enabled=show)
        file_df = _prepare_file_gate_df(load_dataset_csv(Path(args.file_gate_dataset)))
        segment_df = _prepare_segment_df(load_dataset_csv(Path(args.segment_dataset)))
        file_feature_cols = load_json_columns(Path(args.file_feature_columns))
        segment_feature_cols = load_json_columns(Path(args.segment_feature_columns))
        paths = fit_p5b_experimental_candidate_models(
            file_gate_df=file_df,
            segment_df=segment_df,
            file_feature_columns=file_feature_cols,
            segment_feature_columns=segment_feature_cols,
            out_dir=out_dir,
            random_seed=args.random_seed,
            max_selected_features_file=args.max_selected_features_file,
            max_selected_features_segment=args.max_selected_features_segment,
            force=args.force_candidate_models,
        )
        progress(f"Candidate models ready under {out_dir / 'candidate_models'}", enabled=show)
        progress("No release packaging performed.", enabled=show)
        return 0

    if args.reuse_existing_predictions:
        progress("Reusing existing OOF predictions — skipping training...", enabled=show)
        file_oof_path = out_dir / "phase9d_p5b_file_gate_oof_predictions.csv"
        segment_oof_path = out_dir / "phase9d_p5b_segment_oof_predictions.csv"
        if not file_oof_path.is_file() or not segment_oof_path.is_file():
            raise FileNotFoundError("reuse_existing_predictions requires existing OOF CSV files in output_dir")
        file_oof_df = pd.read_csv(file_oof_path, low_memory=False)
        segment_oof_df = pd.read_csv(segment_oof_path, low_memory=False)
        file_results_summary = _load_metrics_summary(out_dir, "file_gate", file_sets)
        segment_results_summary = _load_metrics_summary(out_dir, "segment_localizer", segment_sets)
        recompute_p5b_derived_outputs(
            file_oof_df=file_oof_df,
            segment_oof_df=segment_oof_df,
            file_results_summary=file_results_summary,
            segment_results_summary=segment_results_summary,
            out_dir=out_dir,
            args=args,
            selected_segment_feature_set=args.selected_segment_feature_set,
            selected_segment_threshold=args.selected_segment_threshold,
            training_performed=False,
        )
        progress("P5B-P1 recompute complete (no retraining).", enabled=show)
        return 0

    progress("Loading P5A datasets and feature lists...", enabled=show)
    file_df = _prepare_file_gate_df(load_dataset_csv(Path(args.file_gate_dataset)))
    segment_df = _prepare_segment_df(load_dataset_csv(Path(args.segment_dataset)))
    file_feature_cols = load_json_columns(Path(args.file_feature_columns))
    segment_feature_cols = load_json_columns(Path(args.segment_feature_columns))

    file_group_col = resolve_group_column(file_df, ("leakage_group_id", "split_group_id", "file_id"))
    segment_group_col = resolve_group_column(segment_df, ("file_id", "leakage_group_id", "split_group_id"))

    file_metrics_parts: list[pd.DataFrame] = []
    file_oof_parts: list[pd.DataFrame] = []
    file_thresh_parts: list[pd.DataFrame] = []
    file_audit_parts: list[dict] = []
    file_results_summary: dict[str, pd.DataFrame] = {}

    for fs in file_sets:
        progress(f"Training file gate CV — feature_set={fs}", enabled=show)
        result = run_task_cv(
            file_df,
            task_name=TASK_FILE_GATE,
            target_col="target_is_partial_fabrication_file",
            feature_set=fs,
            feature_columns=file_feature_cols,
            group_col=file_group_col,
            cv_folds=args.cv_folds,
            random_seed=args.random_seed,
            max_selected_features=args.max_selected_features_file,
            model_type=args.model_type,
        )
        file_metrics_parts.append(result["metrics_fold"])
        file_metrics_parts.append(result["metrics_mean"])
        file_oof_parts.append(result["oof"])
        file_thresh_parts.append(result["threshold_grid"])
        file_audit_parts.append(result["feature_audit"])
        file_results_summary[fs] = result["metrics_mean"]

        if args.save_artifacts:
            maybe_save_artifacts(
                out_dir / "artifacts",
                file_df,
                task_name=TASK_FILE_GATE,
                feature_set=fs,
                target_col="target_is_partial_fabrication_file",
                feature_columns=file_feature_cols,
                group_col=file_group_col,
                random_seed=args.random_seed,
                max_selected_features=args.max_selected_features_file,
            )

    segment_metrics_parts: list[pd.DataFrame] = []
    segment_oof_parts: list[pd.DataFrame] = []
    segment_thresh_parts: list[pd.DataFrame] = []
    segment_audit_parts: list[dict] = []
    segment_results_summary: dict[str, pd.DataFrame] = {}

    for fs in segment_sets:
        progress(f"Training segment localizer v2 CV — feature_set={fs}", enabled=show)
        result = run_task_cv(
            segment_df,
            task_name=TASK_SEGMENT_LOCALIZER,
            target_col="target_is_fabricated_segment",
            feature_set=fs,
            feature_columns=segment_feature_cols,
            group_col=segment_group_col,
            cv_folds=args.cv_folds,
            random_seed=args.random_seed,
            max_selected_features=args.max_selected_features_segment,
            model_type=args.model_type,
        )
        segment_metrics_parts.append(result["metrics_fold"])
        segment_metrics_parts.append(result["metrics_mean"])
        segment_oof_parts.append(result["oof"])
        segment_thresh_parts.append(result["threshold_grid"])
        segment_audit_parts.append(result["feature_audit"])
        segment_results_summary[fs] = result["metrics_mean"]

        if args.save_artifacts:
            maybe_save_artifacts(
                out_dir / "artifacts",
                segment_df,
                task_name=TASK_SEGMENT_LOCALIZER,
                feature_set=fs,
                target_col="target_is_fabricated_segment",
                feature_columns=segment_feature_cols,
                group_col=segment_group_col,
                random_seed=args.random_seed,
                max_selected_features=args.max_selected_features_segment,
            )

    file_metrics_df = pd.concat(file_metrics_parts, ignore_index=True)
    file_oof_df = pd.concat(file_oof_parts, ignore_index=True)
    file_thresh_df = pd.concat(file_thresh_parts, ignore_index=True)
    segment_metrics_df = pd.concat(segment_metrics_parts, ignore_index=True)
    segment_oof_df = pd.concat(segment_oof_parts, ignore_index=True)
    segment_thresh_df = pd.concat(segment_thresh_parts, ignore_index=True)
    feature_audit_df = pd.DataFrame(file_audit_parts + segment_audit_parts)

    progress("Writing metrics/OOF/threshold outputs...", enabled=show)
    file_metrics_df.to_csv(out_dir / "phase9d_p5b_file_gate_metrics.csv", index=False)
    file_oof_df.to_csv(out_dir / "phase9d_p5b_file_gate_oof_predictions.csv", index=False)
    file_thresh_df.to_csv(out_dir / "phase9d_p5b_file_gate_threshold_grid.csv", index=False)
    segment_metrics_df.to_csv(out_dir / "phase9d_p5b_segment_localizer_metrics.csv", index=False)
    segment_oof_df.to_csv(out_dir / "phase9d_p5b_segment_oof_predictions.csv", index=False)
    segment_thresh_df.to_csv(out_dir / "phase9d_p5b_segment_threshold_grid.csv", index=False)
    feature_audit_df.to_csv(out_dir / "phase9d_p5b_feature_audit.csv", index=False)

    recompute_p5b_derived_outputs(
        file_oof_df=file_oof_df,
        segment_oof_df=segment_oof_df,
        file_results_summary=file_results_summary,
        segment_results_summary=segment_results_summary,
        out_dir=out_dir,
        args=args,
        selected_segment_feature_set=args.selected_segment_feature_set,
        selected_segment_threshold=args.selected_segment_threshold,
        training_performed=True,
    )

    if args.make_plots:
        maybe_save_plots(out_dir, file_oof_df, segment_oof_df)

    progress(f"P5B training complete (experimental). Outputs: {out_dir}", enabled=show)
    progress("No release packaging performed.", enabled=show)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
