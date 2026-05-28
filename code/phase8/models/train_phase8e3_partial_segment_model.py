#!/usr/bin/env python3
"""
Phase 8E-3: train/evaluate partial fabrication segment logic (manual-run script).

Important: experimental timestamp-aligned segment model only.
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
from phase8e3_segment_model_utils import (  # noqa: E402
    ALLOWED_FEATURE_SETS,
    SCHEMA_VERSION,
    TASK_NAME,
    file_level_localization_summary,
    load_csv_required,
    now_utc_str,
    run_cv,
    threshold_grid,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Train Phase 8E-3 partial segment model (experimental).")
    p.add_argument(
        "--segment_table",
        default="reports/phase8/models/phase8e2/phase8e2_partial_segment_localization_table.csv",
    )
    p.add_argument(
        "--inside_outside_features",
        default="reports/phase8/models/phase8e2/phase8e2_inside_outside_delta_features.csv",
    )
    p.add_argument(
        "--neighbor_features",
        default="reports/phase8/models/phase8e2/phase8e2_neighbor_transition_features.csv",
    )
    p.add_argument(
        "--segment_master",
        default="reports/phase8/models/phase8e0/phase8e0_segment_level_master_dataset.csv",
    )
    p.add_argument(
        "--segment_acoustic_features",
        default="reports/phase8/features/phase8c_segment_acoustic_features.csv",
    )
    p.add_argument(
        "--segment_ssl_embeddings",
        default="reports/phase8/embeddings/phase8d_segment_ssl_embeddings.csv",
    )
    p.add_argument("--output_dir", default="reports/phase8/models/phase8e3")
    p.add_argument("--random_seed", type=int, default=42)
    p.add_argument("--cv_folds", type=int, default=5)
    p.add_argument("--feature_sets", default="localization,acoustic,ssl,combined")
    p.add_argument("--model_type", default="logistic_regression_l2", choices=["logistic_regression_l2"])
    p.add_argument("--max_selected_features", type=int, default=75)
    p.add_argument("--make_plots", action="store_true")
    p.add_argument("--save_artifacts", action="store_true")
    p.add_argument("--no_progress", action="store_true")
    return p.parse_args()


def _resolve(path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else (_ROOT / p).resolve()


def _join_inputs(
    seg_table: pd.DataFrame,
    inside: pd.DataFrame,
    neigh: pd.DataFrame,
    segment_master: pd.DataFrame,
    segment_acoustic_features: pd.DataFrame,
    segment_ssl_embeddings: pd.DataFrame,
) -> pd.DataFrame:
    left = seg_table.copy()
    inside_cols = [c for c in inside.columns if c not in {"start_sec", "end_sec"}]
    merged = left.merge(
        inside[inside_cols],
        on=["file_id", "segment_id"],
        how="left",
        suffixes=("", "_io"),
    )
    merged = merged.merge(
        neigh,
        on=["file_id", "segment_id"],
        how="left",
        suffixes=("", "_ng"),
    )
    # Prefer Phase 8E-0 segment master for raw acoustic+ssl feature availability.
    master_payload = segment_master.copy()
    drop_from_master = {
        "schema_version",
        "audio_path",
        "start_sec",
        "end_sec",
        "segment_duration_sec",
        "known_origin_label",
        "known_manipulation_labels",
        "segment_label_source",
        "inherited_target_origin_multiclass",
        "inherited_target_is_replay",
        "inherited_target_is_mixer_channel",
        "inherited_target_is_partial_fabrication_file",
        "inherited_target_is_clean",
        "eligible_segment_origin_context",
        "eligible_segment_replay_context",
        "eligible_segment_mixer_context",
        "eligible_partial_segment_training",
    }
    master_payload = master_payload[[c for c in master_payload.columns if c not in drop_from_master]]
    merged = merged.merge(master_payload, on=["file_id", "segment_id"], how="left", suffixes=("", "_sm"))

    # Optional fallback joins from direct feature files (do not overwrite existing values).
    for extra_df in (segment_acoustic_features, segment_ssl_embeddings):
        if len(extra_df) == 0:
            continue
        payload = extra_df.copy()
        payload = payload[[c for c in payload.columns if c not in {"schema_version", "audio_path", "start_sec", "end_sec", "segment_duration_sec"}]]
        merged = merged.merge(payload, on=["file_id", "segment_id"], how="left", suffixes=("", "_extra"))
        extra_cols = [c for c in merged.columns if c.endswith("_extra")]
        for c in extra_cols:
            base = c[:-6]
            if base not in merged.columns:
                merged.rename(columns={c: base}, inplace=True)
            else:
                merged[base] = merged[base].mask(merged[base].astype(str).str.strip().eq(""), merged[c])
                merged.drop(columns=[c], inplace=True)
    # drop duplicate merge artifacts
    dup_cols = [c for c in merged.columns if c.endswith("_sm") and c[:-3] in merged.columns]
    for c in dup_cols:
        base = c[:-3]
        merged[base] = merged[base].mask(merged[base].astype(str).str.strip().eq(""), merged[c])
        merged.drop(columns=[c], inplace=True)
    return merged


def _prepare_training_rows(df: pd.DataFrame) -> pd.DataFrame:
    ok = df[
        (df["training_label_available"].astype(str).str.lower() == "true")
        & (df["timestamp_segment_label"].isin(["fabricated_region", "outside_fabricated_region"]))
    ].copy()
    if len(ok) == 0:
        raise ValueError("No timestamp-aligned trainable rows found for Phase 8E-3.")
    ok["target_partial_fabricated"] = np.where(ok["timestamp_segment_label"] == "fabricated_region", "1", "0")
    ok["split_group_id"] = ok["source_group_id"].astype(str) if "source_group_id" in ok.columns else ok["file_id"].astype(str)
    return ok


def _write_report(path: Path, metrics_df: pd.DataFrame, conf_df: pd.DataFrame, thresh_df: pd.DataFrame, file_summary_df: pd.DataFrame, train_df: pd.DataFrame, feature_sets: list[str], split_methods: list[str]) -> None:
    lines = [
        "# Phase 8E-3 Training Report",
        "",
        f"**Generated:** {now_utc_str()}",
        "",
        "Experimental timestamp-aligned segment modeling only.",
        "No final forensic decisions are produced.",
        "Timestamp labels are used only as y_true targets, not as model input features.",
        "Label-aware inside/outside baseline and overlap fields are analysis-only and excluded from Phase 8E-3 model features.",
        "Expected performance may be lower than leakage-prone setups but is more scientifically valid.",
        "",
        "## Dataset Counts",
        "",
        f"- trainable segments: {len(train_df)}",
        f"- fabricated_region segments: {int((train_df['target_partial_fabricated'] == '1').sum())}",
        f"- outside_fabricated_region segments: {int((train_df['target_partial_fabricated'] == '0').sum())}",
        "",
        "## Feature Sets",
        "",
        f"- {feature_sets}",
        "",
        "## Split Method",
        "",
        f"- {sorted(set(split_methods))}",
        "",
        "## Metrics (experimental means)",
        "",
    ]
    for _, r in metrics_df.iterrows():
        lines.append(
            f"- {r['feature_set']}: bal_acc={round(float(r['balanced_accuracy']),4)}, f1={round(float(r['f1']),4)}, outside_false_fabricated_rate={round(float(r['outside_false_fabricated_rate']),4)}"
        )
    lines.extend(
        [
            "",
            "## Threshold Grid Summary",
            "",
            f"- threshold rows: {len(thresh_df)}",
            "",
            "## File-Level Localization Behavior",
            "",
            f"- file summary rows: {len(file_summary_df)}",
            "",
            "## Limitations",
            "",
            "- timestamp-aligned labels are preparation labels, not final forensic proof.",
            "- timestamp labels define target classes only (y_true) and are not feature inputs.",
            "- label-derived inside/outside baseline fields are excluded from model feature sets.",
            "- small/controlled data may overestimate generalization.",
            "- outputs must be reviewed with manual/fusion context.",
            "",
            "## Safety Statements",
            "",
            "- experimental only",
            "- no final forensic decision",
            "- timestamp labels are target-only",
            "- not proof of fabrication",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_model_card(path: Path, segment_table_path: Path, feature_sets: list[str]) -> None:
    lines = [
        "# Phase 8E-3 Model Card",
        "",
        "- Purpose: experimental timestamp-aligned partial-fabrication segment localization support.",
        "- Allowed use: research/evaluation and fusion-candidate analysis.",
        "- Not allowed use: final forensic decision or fabrication proof claim.",
        f"- Training data: `{segment_table_path}` with timestamp-aligned labels only.",
        "- Timestamp labels define target classes only (y_true).",
        "- Label-derived baseline/overlap features are excluded from model inputs.",
        f"- Feature sets: {feature_sets}",
        "- Evaluation method: cross-validation with group-aware splitting by file/source group.",
        "- Limitations: dataset scope, annotation noise, and domain shift risk.",
        "- Safety note: outputs are experimental and not final suspicious-segment decisions.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    show_progress = not args.no_progress

    output_dir = _resolve(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    seg = load_csv_required(_resolve(args.segment_table))
    inside = load_csv_required(_resolve(args.inside_outside_features))
    neigh = load_csv_required(_resolve(args.neighbor_features))
    seg_master = load_csv_required(_resolve(args.segment_master))
    seg_acoustic = load_csv_required(_resolve(args.segment_acoustic_features))
    seg_ssl = load_csv_required(_resolve(args.segment_ssl_embeddings))
    merged = _join_inputs(seg, inside, neigh, seg_master, seg_acoustic, seg_ssl)
    train_df = _prepare_training_rows(merged)
    train_df["schema_version"] = SCHEMA_VERSION

    feature_sets = [x.strip() for x in str(args.feature_sets).split(",") if x.strip()]
    bad = [x for x in feature_sets if x not in ALLOWED_FEATURE_SETS]
    if bad:
        raise ValueError(f"Unsupported feature_sets: {bad}")

    all_metrics = []
    all_fold_metrics = []
    all_oof = []
    all_conf = []
    all_manifest = []
    split_methods = []

    for fs in iter_with_progress(
        feature_sets,
        total=len(feature_sets),
        desc="phase8e3 feature sets",
        enabled=show_progress,
        progress_every=1,
        unit="feature_set",
    ):
        out = run_cv(
            df=train_df,
            feature_set=fs,
            cv_folds=args.cv_folds,
            random_seed=args.random_seed,
            max_selected_features=args.max_selected_features,
            model_type=args.model_type,
        )
        all_metrics.append(out["metrics_mean"])
        all_fold_metrics.append(out["metrics_fold"])
        all_oof.append(out["oof"])
        all_conf.append(out["confusion"])
        all_manifest.append(out["manifest"])
        split_methods.append(str(out["split_method"]))
        print(
            f"[feature_debug] set={fs} raw={out['raw_feature_count']} usable={out['usable_feature_count']} "
            f"excluded_all_missing={out['excluded_all_missing_count']} excluded_non_numeric={out['excluded_non_numeric_count']} "
            f"excluded_forbidden_label_derived={out['excluded_forbidden_label_derived_count']} "
            f"leakage_check={out['feature_leakage_check_status']}"
        )

    metrics_df = pd.concat(all_metrics, ignore_index=True)
    fold_metrics_df = pd.concat(all_fold_metrics, ignore_index=True)
    oof_df = pd.concat(all_oof, ignore_index=True)
    conf_df = pd.concat(all_conf, ignore_index=True)
    manifest_df = pd.concat(all_manifest, ignore_index=True)
    thresh_df = threshold_grid(oof_df)
    file_summary_df = file_level_localization_summary(oof_df, top_k=5)

    metrics_df.to_csv(output_dir / "phase8e3_partial_segment_metrics_summary.csv", index=False)
    fold_metrics_df.to_csv(output_dir / "phase8e3_feature_set_metrics.csv", index=False)
    oof_df.to_csv(output_dir / "phase8e3_out_of_fold_segment_predictions.csv", index=False)
    conf_df.to_csv(output_dir / "phase8e3_confusion_matrices.csv", index=False)
    file_summary_df.to_csv(output_dir / "phase8e3_file_level_localization_summary.csv", index=False)
    thresh_df.to_csv(output_dir / "phase8e3_threshold_grid.csv", index=False)
    manifest_df.to_csv(output_dir / "phase8e3_training_manifest.csv", index=False)

    _write_model_card(output_dir / "phase8e3_model_card.md", _resolve(args.segment_table), feature_sets)
    _write_report(
        output_dir / "phase8e3_training_report.md",
        metrics_df=metrics_df,
        conf_df=conf_df,
        thresh_df=thresh_df,
        file_summary_df=file_summary_df,
        train_df=train_df,
        feature_sets=feature_sets,
        split_methods=split_methods,
    )

    if args.make_plots:
        try:
            import matplotlib.pyplot as plt

            fig_dir = output_dir / "figures"
            fig_dir.mkdir(parents=True, exist_ok=True)
            for (feature_set,), g in thresh_df.groupby(["feature_set"], dropna=False):
                plt.figure(figsize=(7, 4))
                plt.plot(g["threshold"], g["outside_false_fabricated_rate"], label="outside_false_fabricated_rate")
                plt.plot(g["threshold"], g["fabricated_detected_rate"], label="fabricated_detected_rate")
                plt.plot(g["threshold"], g["balanced_accuracy"], label="balanced_accuracy")
                plt.xlabel("threshold")
                plt.ylabel("metric")
                plt.title(f"{feature_set} threshold tradeoff")
                plt.legend()
                plt.tight_layout()
                plt.savefig(fig_dir / f"{feature_set}__threshold_tradeoff.png", dpi=120)
                plt.close()
        except Exception:
            pass

    if args.save_artifacts:
        art_dir = output_dir / "artifacts"
        art_dir.mkdir(parents=True, exist_ok=True)
        (art_dir / "README.txt").write_text(
            "Experimental artifacts only. status=experimental_not_active\n",
            encoding="utf-8",
        )

    print("Phase 8E-3 experimental training script completed.")
    print(f"Output dir: {output_dir}")
    print("Task: partial_fabrication_segment_model")
    print("No final forensic decisions produced.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
