#!/usr/bin/env python3
"""
Phase 8E-1: train lightweight file-level experimental evidence models.

Supported tasks:
- origin_file_model (clean human vs clean ai_synthetic)
- replay_file_model (clean vs replay_rerecorded)
- mixer_file_model (clean vs mixer_channel_processed)

No segment model, no partial fabrication model, no fake/real model.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[3]
_COMMON_DIR = Path(__file__).resolve().parents[1] / "common"
if str(_COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(_COMMON_DIR))

from progress_utils import iter_with_progress  # noqa: E402
from phase8e1_model_utils import (  # noqa: E402
    ALLOWED_FEATURE_SETS,
    ALLOWED_TASKS,
    FORBIDDEN_COLUMNS,
    TASK_CONFIGS,
    get_feature_columns,
    load_csv_required,
    now_utc_str,
    run_cv_for_task,
    write_json,
    write_model_card_section,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Train Phase 8E-1 file-level lightweight experimental models.")
    p.add_argument(
        "--origin_dataset",
        default="reports/phase8/models/phase8e0/phase8e0_origin_file_dataset.csv",
    )
    p.add_argument(
        "--replay_dataset",
        default="reports/phase8/models/phase8e0/phase8e0_replay_file_dataset.csv",
    )
    p.add_argument(
        "--mixer_dataset",
        default="reports/phase8/models/phase8e0/phase8e0_mixer_file_dataset.csv",
    )
    p.add_argument(
        "--leakage_audit",
        default="reports/phase8/models/phase8e0/phase8e0_leakage_audit.csv",
    )
    p.add_argument(
        "--phase8e0_validation_report",
        default="reports/phase8/validation/phase8e0_dataset_validation_report.md",
    )
    p.add_argument("--output_dir", default="reports/phase8/models/phase8e1")
    p.add_argument("--random_seed", type=int, default=42)
    p.add_argument("--cv_folds", type=int, default=5)
    p.add_argument("--feature_sets", default="acoustic,ssl,combined")
    p.add_argument("--model_type", default="logistic_regression_l2", choices=["logistic_regression_l2"])
    p.add_argument("--max_selected_features", type=int, default=50)
    p.add_argument("--save_artifacts", action="store_true")
    p.add_argument("--make_plots", action="store_true")
    p.add_argument("--no_progress", action="store_true")
    return p.parse_args()


def _resolve(path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else (_ROOT / p).resolve()


def _validate_dataset_for_task(df: pd.DataFrame, task_name: str) -> None:
    if "file_id" not in df.columns:
        raise ValueError(f"{task_name}: missing file_id")
    if "source_group_id" not in df.columns:
        raise ValueError(f"{task_name}: missing source_group_id")
    if task_name == "origin_file_model":
        bad = df[
            ~df["known_origin_label"].isin(["human", "ai_synthetic"])
            | (df["known_manipulation_labels"].astype(str).str.strip().str.lower() != "clean")
        ]
        if len(bad):
            raise ValueError(f"{task_name}: dataset contains non-clean or invalid origin rows")
    elif task_name == "replay_file_model":
        allowed = {"clean", "replay_rerecorded"}
        bad = df[~df["known_manipulation_labels"].astype(str).str.strip().str.lower().isin(allowed)]
        if len(bad):
            raise ValueError(f"{task_name}: dataset contains labels outside clean/replay_rerecorded")
    elif task_name == "mixer_file_model":
        allowed = {"clean", "mixer_channel_processed"}
        bad = df[~df["known_manipulation_labels"].astype(str).str.strip().str.lower().isin(allowed)]
        if len(bad):
            raise ValueError(f"{task_name}: dataset contains labels outside clean/mixer_channel_processed")

    found_forbidden = sorted(FORBIDDEN_COLUMNS.intersection(set(df.columns)))
    if found_forbidden:
        raise ValueError(f"{task_name}: forbidden columns present: {found_forbidden}")


def _write_training_report(
    path: Path,
    metrics_df: pd.DataFrame,
    feature_metrics_df: pd.DataFrame,
    confusion_df: pd.DataFrame,
    dataset_counts: dict[str, int],
    class_counts: dict[str, dict[str, int]],
) -> None:
    lines = [
        "# Phase 8E-1 Training Report",
        "",
        f"**Generated:** {now_utc_str()}",
        "",
        "> Experimental cross-validated evidence modeling only. No final forensic decisions.",
        "",
        "## Dataset Counts",
        "",
    ]
    for k, v in dataset_counts.items():
        lines.append(f"- {k}: {v}")
    lines.extend(["", "## Class Counts", ""])
    for task_name, dist in class_counts.items():
        lines.append(f"- {task_name}: {dist}")

    lines.extend(["", "## Feature Set Sizes", ""])
    for _, r in feature_metrics_df.groupby(["task_name", "feature_set"], as_index=False).agg({"input_feature_count": "max", "selected_feature_count": "mean"}).iterrows():
        lines.append(
            f"- {r['task_name']} / {r['feature_set']}: input={int(r['input_feature_count'])}, mean_selected={round(float(r['selected_feature_count']), 2)}"
        )

    lines.extend(["", "## Cross-Validated Experimental Metrics", ""])
    for _, r in metrics_df.iterrows():
        lines.append(
            f"- {r['task_name']} / {r['feature_set']} | split={r['split_method']} | acc={round(float(r['accuracy']),4)} | bal_acc={round(float(r['balanced_accuracy']),4)} | f1={round(float(r['f1']),4)}"
        )

    lines.extend(["", "## Confusion Matrices (OOF Aggregated)", ""])
    if len(confusion_df):
        cmg = confusion_df.groupby(["task_name", "feature_set"], as_index=False)[["tn", "fp", "fn", "tp"]].sum()
        for _, r in cmg.iterrows():
            lines.append(
                f"- {r['task_name']} / {r['feature_set']}: tn={int(r['tn'])}, fp={int(r['fp'])}, fn={int(r['fn'])}, tp={int(r['tp'])}"
            )

    lines.extend(
        [
            "",
            "## Known Limitations",
            "",
            "- Small dataset sizes; metrics are unstable across folds.",
            "- Group-aware splitting may reduce effective training data.",
            "- No segment-level modeling in this phase.",
            "- No partial fabrication training in this phase.",
            "- No final forensic decisions are produced.",
            "",
            "## Recommendation",
            "",
            "- Review experimental metrics and failure patterns before Phase 8E-2 or Phase 8F planning.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    show_progress = not args.no_progress

    out_dir = _resolve(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir = out_dir / "artifacts"

    feature_sets = [x.strip() for x in str(args.feature_sets).split(",") if x.strip()]
    invalid = [x for x in feature_sets if x not in ALLOWED_FEATURE_SETS]
    if invalid:
        raise ValueError(f"Unsupported feature sets: {invalid}. Allowed={ALLOWED_FEATURE_SETS}")
    if not feature_sets:
        raise ValueError("No feature sets selected.")

    datasets = {
        "origin_file_model": load_csv_required(_resolve(args.origin_dataset)),
        "replay_file_model": load_csv_required(_resolve(args.replay_dataset)),
        "mixer_file_model": load_csv_required(_resolve(args.mixer_dataset)),
    }
    leakage_audit = load_csv_required(_resolve(args.leakage_audit))
    if "audit_item" in leakage_audit.columns:
        if not (leakage_audit["audit_item"] == "partial_inherited_label_risk").any():
            print("[warn] leakage audit does not include partial_inherited_label_risk")

    validation_report_path = _resolve(args.phase8e0_validation_report)
    if not validation_report_path.is_file():
        print(f"[warn] phase8e0 validation report not found: {validation_report_path}")

    for task_name, df in datasets.items():
        _validate_dataset_for_task(df, task_name)

    metrics_rows = []
    feature_rows = []
    oof_rows = []
    conf_rows = []
    manifest_rows = []
    model_card_sections: list[str] = []
    dataset_counts = {k: len(v) for k, v in datasets.items()}
    class_counts: dict[str, dict[str, int]] = {}

    total_runs = len(ALLOWED_TASKS) * len(feature_sets)
    run_items = [(t, fs) for t in ALLOWED_TASKS for fs in feature_sets]
    for task_name, feature_set in iter_with_progress(
        run_items,
        total=total_runs,
        desc="phase8e1 cv runs",
        enabled=show_progress,
        progress_every=1,
        unit="run",
    ):
        df = datasets[task_name]
        task = TASK_CONFIGS[task_name]
        class_counts[f"{task_name}__{feature_set}"] = (
            df[task.target_col].astype(str).value_counts().to_dict()
        )
        result = run_cv_for_task(
            df=df,
            task=task,
            feature_set=feature_set,
            max_selected_features=args.max_selected_features,
            cv_folds=args.cv_folds,
            random_seed=args.random_seed,
            model_type=args.model_type,
        )
        metrics_rows.append(result["metrics_mean"])
        feat_df = result["feature_selection"].copy()
        feat_df["dropped_all_missing_features"] = result.get("dropped_all_missing_features", "")
        feature_rows.append(feat_df)
        oof_rows.append(result["oof"])
        conf_rows.append(result["confusion"])
        manifest_rows.append(result["manifest"])
        if result.get("dropped_all_missing_features"):
            print(
                f"[warn] {task_name}/{feature_set}: dropped all-missing features: {result['dropped_all_missing_features']}"
            )

        model_card_sections.append(
            write_model_card_section(
                task_name=task_name,
                feature_set=feature_set,
                dataset_path=str(_resolve(getattr(args, task.dataset_arg_name))),
                split_method=result["split_method"],
                used_folds=result["used_folds"],
            )
        )

        if args.save_artifacts:
            # Train single experimental model on full task dataset (for experimentation only).
            from sklearn.pipeline import Pipeline
            from phase8e1_model_utils import build_pipeline, parse_binary_target
            import joblib

            feats = get_feature_columns(df, feature_set)
            x_all = df[feats].replace("", np.nan)
            y_all = parse_binary_target(df[task.target_col], task.target_col)
            model: Pipeline = build_pipeline(
                max_selected_features=min(args.max_selected_features, len(feats)),
                random_seed=args.random_seed,
            )
            model.fit(x_all, y_all)
            artifacts_dir.mkdir(parents=True, exist_ok=True)
            model_name = f"{task_name}__{feature_set}__experimental.joblib"
            model_path = artifacts_dir / model_name
            joblib.dump(model, model_path)
            write_json(
                model_path.with_suffix(".json"),
                {
                    "task": task_name,
                    "feature_set": feature_set,
                    "model_type": args.model_type,
                    "training_dataset_path": str(_resolve(getattr(args, task.dataset_arg_name))),
                    "created_at": now_utc_str(),
                    "status": "experimental_not_active",
                    "warning": "not final forensic decision model",
                },
            )

    metrics_df = pd.concat(metrics_rows, ignore_index=True)
    feature_df = pd.concat(feature_rows, ignore_index=True)
    oof_df = pd.concat(oof_rows, ignore_index=True)
    conf_df = pd.concat(conf_rows, ignore_index=True)
    manifest_df = pd.concat(manifest_rows, ignore_index=True)

    metrics_df.to_csv(out_dir / "phase8e1_metrics_summary.csv", index=False)
    feature_df.to_csv(out_dir / "phase8e1_feature_selection_summary.csv", index=False)
    oof_df.to_csv(out_dir / "phase8e1_out_of_fold_predictions.csv", index=False)
    conf_df.to_csv(out_dir / "phase8e1_confusion_matrices.csv", index=False)
    manifest_df.to_csv(out_dir / "phase8e1_training_manifest.csv", index=False)

    # Per-task feature-set metric table.
    metrics_df.to_csv(out_dir / "phase8e1_task_feature_set_metrics.csv", index=False)

    model_cards_path = out_dir / "phase8e1_model_cards.md"
    model_cards_path.write_text(
        "\n".join(
            [
                "# Phase 8E-1 Model Cards",
                "",
                "> Experimental evidence models only. Not active and not final forensic decision models.",
                "",
            ]
            + model_card_sections
        )
        + "\n",
        encoding="utf-8",
    )

    _write_training_report(
        path=out_dir / "phase8e1_training_report.md",
        metrics_df=metrics_df,
        feature_metrics_df=feature_df,
        confusion_df=conf_df,
        dataset_counts=dataset_counts,
        class_counts=class_counts,
    )

    print("Phase 8E-1 experimental training/evaluation complete.")
    print(f"Output dir: {out_dir}")
    print(f"Supported tasks: {list(ALLOWED_TASKS)}")
    print(f"Feature sets: {feature_sets}")
    print("No partial-fabrication model trained. No segment model trained.")
    print("No fake/real classifier trained. No final forensic decisions produced.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
