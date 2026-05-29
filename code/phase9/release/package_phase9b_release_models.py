#!/usr/bin/env python3
"""
Phase 9B: package accepted Phase 8 experimental evidence models into release/models/.

Manual-run only. Fits lightweight sklearn pipelines on full accepted datasets.
Does not write to models_saved/active/.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from phase9b_packaging_utils import (  # noqa: E402
    RELEASE_STATUS,
    ReleaseModelSpec,
    build_metadata,
    build_model_inventory,
    default_release_model_specs,
    fit_full_dataset_pipeline,
    join_partial_segment_datasets,
    load_csv_required,
    load_threshold_from_csv,
    now_iso,
    prepare_partial_training_rows,
    repo_root_from_here,
    resolve_path,
    save_joblib_artifact,
    select_file_level_features,
    select_partial_combined_features,
    write_json,
    write_model_card,
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Package Phase 9B experimental release models.")
    p.add_argument("--output_root", default="release/models")
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
        "--partial_segment_table",
        default="reports/phase8/models/phase8e2/phase8e2_partial_segment_localization_table.csv",
    )
    p.add_argument(
        "--partial_inside_outside_features",
        default="reports/phase8/models/phase8e2/phase8e2_inside_outside_delta_features.csv",
    )
    p.add_argument(
        "--partial_neighbor_features",
        default="reports/phase8/models/phase8e2/phase8e2_neighbor_transition_features.csv",
    )
    p.add_argument(
        "--segment_master",
        default="reports/phase8/models/phase8e0/phase8e0_segment_level_master_dataset.csv",
    )
    p.add_argument(
        "--phase8e1_metrics",
        default="reports/phase8/models/phase8e1/phase8e1_metrics_summary.csv",
    )
    p.add_argument(
        "--phase8e1a_thresholds",
        default="reports/phase8/models/phase8e1a/phase8e1a_threshold_recommendations.csv",
    )
    p.add_argument(
        "--phase8e3_metrics",
        default="reports/phase8/models/phase8e3/phase8e3_partial_segment_metrics_summary.csv",
    )
    p.add_argument(
        "--report",
        default="reports/phase9/release/phase9b_model_packaging_report.md",
    )
    p.add_argument("--random_seed", type=int, default=42)
    p.add_argument("--max_selected_features_file", type=int, default=50)
    p.add_argument("--max_selected_features_segment", type=int, default=75)
    p.add_argument("--force", action="store_true")
    p.add_argument("--no_progress", action="store_true")
    return p.parse_args()


def _apply_threshold_overrides(specs: list[ReleaseModelSpec], thresholds_csv: Path) -> list[ReleaseModelSpec]:
    updated: list[ReleaseModelSpec] = []
    for s in specs:
        th = load_threshold_from_csv(thresholds_csv, s.task_name, s.feature_set, s.threshold_candidate)
        updated.append(
            ReleaseModelSpec(
                **{**s.__dict__, "threshold_candidate": th}
            )
        )
    return updated


def _package_file_model(
    spec: ReleaseModelSpec,
    dataset_path: Path,
    output_root: Path,
    random_seed: int,
    max_features: int,
    force: bool,
) -> dict[str, Any]:
    df = load_csv_required(dataset_path)
    features = select_file_level_features(df, spec.feature_set)
    pipe, selected, summary = fit_full_dataset_pipeline(
        df, features, spec.target_column, max_features, random_seed
    )
    artifact_path = output_root / spec.artifact_rel
    metadata_path = output_root / spec.metadata_rel
    save_joblib_artifact(artifact_path, pipe, force=force)
    meta = build_metadata(
        spec=spec,
        source_dataset_paths=[str(dataset_path.as_posix())],
        feature_names=selected,
        excluded_summary={
            "all_missing": summary["excluded_all_missing"],
            "non_numeric": summary["excluded_non_numeric"],
            "input_feature_count": summary["input_feature_count"],
            "usable_feature_count": summary["usable_feature_count"],
        },
        target_mapping={"0": spec.negative_label, "1": spec.positive_label},
        random_seed=random_seed,
    )
    write_json(metadata_path, meta)
    card_path = metadata_path.with_name(metadata_path.stem.replace("_metadata", "_model_card") + ".md")
    write_model_card(card_path, spec, summary)
    return {
        "model_name": spec.model_name,
        "artifact_path": str(artifact_path.as_posix()),
        "metadata_path": str(metadata_path.as_posix()),
        "summary": summary,
    }


def _package_partial_model(
    spec: ReleaseModelSpec,
    seg_table: Path,
    inside: Path,
    neigh: Path,
    segment_master: Path,
    output_root: Path,
    random_seed: int,
    max_features: int,
    force: bool,
) -> dict[str, Any]:
    merged = join_partial_segment_datasets(
        load_csv_required(seg_table),
        load_csv_required(inside),
        load_csv_required(neigh),
        load_csv_required(segment_master),
    )
    train_df = prepare_partial_training_rows(merged)
    features, _forbidden_checked = select_partial_combined_features(train_df)
    pipe, selected, summary = fit_full_dataset_pipeline(
        train_df, features, spec.target_column, max_features, random_seed
    )
    artifact_path = output_root / spec.artifact_rel
    metadata_path = output_root / spec.metadata_rel
    save_joblib_artifact(artifact_path, pipe, force=force)
    meta = build_metadata(
        spec=spec,
        source_dataset_paths=[
            str(seg_table.as_posix()),
            str(inside.as_posix()),
            str(neigh.as_posix()),
            str(segment_master.as_posix()),
        ],
        feature_names=selected,
        excluded_summary={
            "all_missing": summary["excluded_all_missing"],
            "non_numeric": summary["excluded_non_numeric"],
            "forbidden_label_derived_excluded": True,
            "safe_localization_features_only": True,
        },
        target_mapping={
            "0": "outside_fabricated_region",
            "1": "fabricated_region",
        },
        random_seed=random_seed,
    )
    write_json(metadata_path, meta)
    card_path = metadata_path.with_name(metadata_path.stem.replace("_metadata", "_model_card") + ".md")
    write_model_card(card_path, spec, summary)
    return {
        "model_name": spec.model_name,
        "artifact_path": str(artifact_path.as_posix()),
        "metadata_path": str(metadata_path.as_posix()),
        "summary": summary,
    }


def write_packaging_report(path: Path, packaged: list[dict[str, Any]], warnings: list[str]) -> None:
    lines = [
        "# Phase 9B Model Packaging Report",
        "",
        f"**Generated:** {now_iso()}",
        "",
        f"- status: {RELEASE_STATUS}",
        "- models packaged: " + ", ".join(p["model_name"] for p in packaged),
        "- no production/active promotion",
        "- no models_saved/active writes",
        "- next step: Phase 9C live inference pipeline",
        "",
        "## Models",
        "",
    ]
    for p in packaged:
        s = p["summary"]
        lines.extend(
            [
                f"### {p['model_name']}",
                f"- rows: {s.get('row_count')}",
                f"- class_counts: {s.get('class_counts')}",
                f"- selected_features: {s.get('selected_feature_count')}",
                f"- artifact: `{p['artifact_path']}`",
                f"- metadata: `{p['metadata_path']}`",
                "",
            ]
        )
    if warnings:
        lines.extend(["## Warnings", ""])
        for w in warnings:
            lines.append(f"- {w}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    root = repo_root_from_here(Path(__file__))
    output_root = resolve_path(root, args.output_root)
    specs = _apply_threshold_overrides(
        default_release_model_specs(), resolve_path(root, args.phase8e1a_thresholds)
    )
    # Apply CLI max feature overrides.
    spec_by_name = {s.model_name: s for s in specs}
    warnings: list[str] = []
    packaged: list[dict[str, Any]] = []

    origin = spec_by_name["origin_file_model"]
    replay = spec_by_name["replay_file_model"]
    mixer = spec_by_name["mixer_file_model"]
    partial = spec_by_name["partial_fabrication_segment_model"]

    tasks = [
        ("origin_file_model", lambda: _package_file_model(
            origin, resolve_path(root, args.origin_dataset), output_root,
            args.random_seed, args.max_selected_features_file, args.force)),
        ("replay_file_model", lambda: _package_file_model(
            replay, resolve_path(root, args.replay_dataset), output_root,
            args.random_seed, args.max_selected_features_file, args.force)),
        ("mixer_file_model", lambda: _package_file_model(
            mixer, resolve_path(root, args.mixer_dataset), output_root,
            args.random_seed, args.max_selected_features_file, args.force)),
        ("partial_fabrication_segment_model", lambda: _package_partial_model(
            partial,
            resolve_path(root, args.partial_segment_table),
            resolve_path(root, args.partial_inside_outside_features),
            resolve_path(root, args.partial_neighbor_features),
            resolve_path(root, args.segment_master),
            output_root,
            args.random_seed,
            args.max_selected_features_segment,
            args.force,
        )),
    ]

    iterator = tasks if args.no_progress else tasks
    for name, fn in iterator:
        try:
            packaged.append(fn())
        except FileExistsError as exc:
            warnings.append(f"{name}: skipped existing artifact ({exc})")
        except Exception as exc:
            raise RuntimeError(f"Packaging failed for {name}: {exc}") from exc

    inventory_models = [
        {
            "model_name": p["model_name"],
            "artifact_path": p["artifact_path"],
            "metadata_path": p["metadata_path"],
            "status": RELEASE_STATUS,
        }
        for p in packaged
    ]
    inventory = build_model_inventory(inventory_models, warnings)
    write_json(output_root / "model_inventory.json", inventory)
    write_packaging_report(resolve_path(root, args.report), packaged, warnings)
    print(f"Packaged {len(packaged)} model(s) into {output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
