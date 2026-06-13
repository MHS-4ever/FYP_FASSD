"""Phase 4 — Two-stage manipulation v3 (experimental, no release overwrite).

Stage 1: clean/direct vs manipulated
Stage 2: replay | mixer_channel | partial_insert | edited_spliced |
         platform_compression | unknown_channel_artifact

Train-only synthetic edits + codec augmentation from existing 184 files.
Thresholds chosen on leakage-safe dev only. testing_audios is eval-only.

Stop rule: Stage-1 recall on manipulated testing_audios cases < 70% -> do not
keep retraining; document limitation and move to Phase 6 calibration wording.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / "release"
if str(RELEASE) not in sys.path:
    sys.path.insert(0, str(RELEASE))

from phase3_common import tqdm_iter  # noqa: E402
from phase4_synthetic_augmentation import (  # noqa: E402
    build_edited_splice_rows,
    build_mixer_codec_augmentation_rows,
    build_platform_compression_rows,
)
from train_two_stage_manipulation_prototype import (  # noqa: E402
    LEAKAGE_MANIFEST,
    TESTING_MANIFEST,
    acoustic_feature_columns,
    build_model,
    choose_stage1_threshold,
    clean_feature_matrix,
    extract_rows,
    phase7_stage_labels,
    predict_stage1,
    predict_stage2,
    stage1_metrics,
    stage2_accuracy,
    testing_stage_labels,
)
from train_two_stage_manipulation_v2 import (  # noqa: E402
    add_train_proxy_rows,
    apply_final_two_stage_labels,
    subtype_metrics,
)

DEFAULT_OUT = ROOT / "reports" / "release_audit" / "phase4_two_stage_manipulation_v3_2026-06-13"
STOP_RULE_MIN_STAGE1_RECALL = 0.70


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT))
    parser.add_argument("--max-selected-features", type=int, default=50)
    parser.add_argument("--random-seed", type=int, default=42)
    parser.add_argument("--stage1-min-dev-specificity", type=float, default=0.88)
    parser.add_argument("--max-synth-human-edited", type=int, default=46)
    parser.add_argument("--max-synth-ai-platform", type=int, default=46)
    parser.add_argument("--max-codec-aug-rows", type=int, default=120)
    parser.add_argument("--max-proxy-source-rows", type=int, default=80)
    parser.add_argument("--max-testing-duration-sec", type=float, default=45.0)
    parser.add_argument("--skip-feature-extract", action="store_true", help="Reuse cached feature CSVs in out-dir")
    return parser.parse_args()


def progress(msg: str) -> None:
    print(msg, flush=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def phase7_v3_labels(df: pd.DataFrame) -> pd.DataFrame:
    out = phase7_stage_labels(df)
    # Extend stage2 with synthetic labels when present.
    synth = out.get("stage2_target_type", pd.Series("", index=out.index)).astype(str)
    out.loc[synth.ne(""), "stage2_target_type"] = synth[synth.ne("")]
    return out


def choose_stage2_confidence(
    dev_pred: pd.DataFrame,
    *,
    expected_col: str = "stage2_target_type",
) -> tuple[float, pd.DataFrame]:
    ok = dev_pred[
        dev_pred["feature_status"].eq("ok")
        & dev_pred["stage1_manipulation_prediction"].fillna(0).astype(float).ge(1.0)
        & dev_pred[expected_col].astype(str).ne("")
    ].copy()
    rows: list[dict] = []
    if len(ok) == 0:
        return 0.55, pd.DataFrame()
    for conf in np.round(np.arange(0.35, 0.96, 0.05), 2):
        tmp = ok.copy()
        tmp["stage2_reported_type"] = [
            raw if float(c) >= conf else "unknown_channel_artifact"
            for raw, c in zip(tmp["stage2_raw_type"].astype(str), tmp["stage2_confidence"].astype(float))
        ]
        expected = tmp[expected_col].astype(str)
        pred = tmp["stage2_reported_type"].astype(str)
        rows.append(
            {
                "min_confidence": float(conf),
                "n": int(len(tmp)),
                "accuracy": float((expected == pred).mean()),
                "unknown_rate": float((pred == "unknown_channel_artifact").mean()),
            }
        )
    grid = pd.DataFrame(rows)
    grid = grid.sort_values(["accuracy", "unknown_rate", "min_confidence"], ascending=[False, True, False])
    return float(grid.iloc[0]["min_confidence"]), grid


def stage1_manipulated_testing_recall(testing_pred: pd.DataFrame) -> dict:
    ok = testing_pred[testing_pred["feature_status"].eq("ok")].copy()
    manip = ok[ok["stage1_target_manipulated"].astype(int).eq(1)]
    if len(manip) == 0:
        return {"n_manipulated": 0, "recall": float("nan"), "passes_stop_rule": False}
    pred = manip["stage1_manipulation_prediction"].fillna(0).astype(int)
    recall = float(pred.mean())
    return {
        "n_manipulated": int(len(manip)),
        "tp": int(pred.sum()),
        "recall": recall,
        "passes_stop_rule": bool(recall >= STOP_RULE_MIN_STAGE1_RECALL),
        "stop_rule_threshold": STOP_RULE_MIN_STAGE1_RECALL,
    }


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    started = utc_now()

    phase7_feat_path = out_dir / "phase7_features_base.csv"
    testing_feat_path = out_dir / "testing_audios_features_base.csv"

    manifest = pd.read_csv(LEAKAGE_MANIFEST, dtype=str, keep_default_na=False)
    eligible = manifest[
        manifest["ground_truth_origin"].isin(["human", "ai", "mixed"])
        & manifest["manipulation_type"].isin(
            ["clean_direct", "ai_replay", "human_replay", "mixer_processed", "partial_ai_insert"]
        )
    ].copy()

    if args.skip_feature_extract and phase7_feat_path.is_file() and testing_feat_path.is_file():
        progress("[phase4] loading cached base features")
        phase7 = phase7_v3_labels(pd.read_csv(phase7_feat_path))
    else:
        progress("[phase4] extracting Phase 7 base acoustic features (184 eligible files)")
        phase7 = phase7_v3_labels(
            extract_rows(
                eligible,
                testing=False,
                label="phase7",
                max_duration_sec=None,
                progress_every=1,
            )
        )
        phase7.to_csv(phase7_feat_path, index=False)

        testing_manifest = pd.read_csv(TESTING_MANIFEST, dtype=str, keep_default_na=False)
        progress(f"[phase4] extracting testing_audios features (max {args.max_testing_duration_sec}s)")
        testing_base = extract_rows(
            testing_manifest,
            testing=True,
            label="testing_audios",
            max_duration_sec=args.max_testing_duration_sec,
            progress_every=1,
        )
        testing_base.to_csv(testing_feat_path, index=False)

    train = phase7[phase7["eval_split"].eq("train")].copy()
    dev = phase7[phase7["eval_split"].eq("dev")].copy()
    test = phase7[phase7["eval_split"].eq("test")].copy()

    progress("[phase4] building train-only synthetic + augmentation rows")
    synth_parts = [
        build_edited_splice_rows(train, max_rows=args.max_synth_human_edited, seed=args.random_seed),
        build_platform_compression_rows(train, max_rows=args.max_synth_ai_platform),
        build_mixer_codec_augmentation_rows(
            train, max_rows=args.max_codec_aug_rows, policy="v3_targeted", progress_every=1
        ),
        add_train_proxy_rows(train, args.max_proxy_source_rows, progress_every=1),
    ]
    synth_frames = [df for df in synth_parts if len(df)]
    synth_all = pd.concat(synth_frames, ignore_index=True, sort=False) if synth_frames else pd.DataFrame()
    synth_all.to_csv(out_dir / "phase4_train_synthetic_rows.csv", index=False)
    progress(f"[phase4] synthetic/aug rows: {len(synth_all)}")

    fit_train = pd.concat([train, synth_all], ignore_index=True, sort=False) if len(synth_all) else train.copy()
    fit_train.to_csv(out_dir / "phase4_fit_train_manifest.csv", index=False)

    features = acoustic_feature_columns(fit_train)
    ok_fit = fit_train[fit_train["feature_status"].eq("ok")].copy()
    x_stage1, stage1_features = clean_feature_matrix(ok_fit, features)
    y_stage1 = ok_fit["stage1_target_manipulated"].astype(int).to_numpy()
    k1 = min(args.max_selected_features, len(stage1_features))
    stage1_model = build_model(k1, args.random_seed, multiclass=False)
    progress(f"[phase4] fitting Stage 1 on {len(ok_fit)} rows ({int(y_stage1.sum())} manipulated)")
    stage1_model.fit(x_stage1, y_stage1)

    stage2_train = ok_fit[ok_fit["stage2_target_type"].astype(str).ne("")].copy()
    x_stage2, stage2_features = clean_feature_matrix(stage2_train, features)
    encoder = LabelEncoder()
    y_stage2 = encoder.fit_transform(stage2_train["stage2_target_type"].astype(str))
    k2 = min(args.max_selected_features, len(stage2_features))
    stage2_model = build_model(k2, args.random_seed, multiclass=True)
    progress(f"[phase4] fitting Stage 2 on {len(stage2_train)} rows, classes={list(encoder.classes_)}")
    stage2_model.fit(x_stage2, y_stage2)

    dev_s1_probe = predict_stage1(stage1_model, dev, stage1_features, 0.5)
    stage1_threshold, stage1_grid = choose_stage1_threshold(
        dev_s1_probe, args.stage1_min_dev_specificity
    )
    progress(f"[phase4] Stage 1 dev threshold: {stage1_threshold}")

    dev_s1 = predict_stage1(stage1_model, dev, stage1_features, stage1_threshold)
    dev_s2_probe = predict_stage2(stage2_model, encoder, dev_s1, stage2_features, 0.0)
    stage2_confidence, stage2_grid = choose_stage2_confidence(dev_s2_probe)
    progress(f"[phase4] Stage 2 dev min-confidence: {stage2_confidence}")

    if not testing_feat_path.is_file():
        testing_manifest = pd.read_csv(TESTING_MANIFEST, dtype=str, keep_default_na=False)
        testing_base = extract_rows(
            testing_manifest,
            testing=True,
            label="testing_audios",
            max_duration_sec=args.max_testing_duration_sec,
            progress_every=1,
        )
        testing_base.to_csv(testing_feat_path, index=False)
    testing = testing_stage_labels(pd.read_csv(testing_feat_path))

    frames = []
    for scope, frame in {
        "train": train,
        "fit_train": fit_train,
        "dev": dev,
        "test": test,
    }.items():
        pred = predict_stage1(stage1_model, frame, stage1_features, stage1_threshold)
        pred = predict_stage2(stage2_model, encoder, pred, stage2_features, stage2_confidence)
        pred = apply_final_two_stage_labels(pred)
        pred["prediction_scope"] = scope
        frames.append(pred)

    testing_pred = predict_stage1(stage1_model, testing, stage1_features, stage1_threshold)
    testing_pred = predict_stage2(stage2_model, encoder, testing_pred, stage2_features, stage2_confidence)
    testing_pred = apply_final_two_stage_labels(testing_pred)
    testing_pred["prediction_scope"] = "testing_audios"
    frames.append(testing_pred)

    predictions = pd.concat(frames, ignore_index=True, sort=False)
    predictions.to_csv(out_dir / "two_stage_v3_predictions.csv", index=False)

    stage1_metrics_df = pd.DataFrame(
        [stage1_metrics(str(s), f) for s, f in predictions.groupby("prediction_scope", dropna=False)]
    )
    stage1_metrics_df.to_csv(out_dir / "two_stage_v3_stage1_metrics.csv", index=False)

    subtype_rows = [
        subtype_metrics("train", predictions[predictions["prediction_scope"].eq("train")], "stage2_target_type"),
        subtype_metrics("fit_train", predictions[predictions["prediction_scope"].eq("fit_train")], "stage2_target_type"),
        subtype_metrics("dev", predictions[predictions["prediction_scope"].eq("dev")], "stage2_target_type"),
        subtype_metrics("test", predictions[predictions["prediction_scope"].eq("test")], "stage2_target_type"),
        subtype_metrics(
            "testing_audios",
            predictions[predictions["prediction_scope"].eq("testing_audios")],
            "stage2_expected_type",
        ),
    ]
    subtype_metrics_df = pd.DataFrame(subtype_rows)
    subtype_metrics_df.to_csv(out_dir / "two_stage_v3_subtype_metrics.csv", index=False)

    stop = stage1_manipulated_testing_recall(testing_pred)
    (out_dir / "two_stage_v3_stop_rule.json").write_text(json.dumps(stop, indent=2), encoding="utf-8")

    focus_cols = [
        "test_id",
        "audio_path",
        "manipulation_type",
        "stage1_target_manipulated",
        "stage1_manipulation_probability",
        "stage1_manipulation_prediction",
        "stage2_expected_type",
        "stage2_raw_type",
        "stage2_confidence",
        "stage2_reported_type",
        "final_reported_type",
        "feature_status",
    ]
    testing_focus = testing_pred[[c for c in focus_cols if c in testing_pred.columns]].copy()
    testing_focus.to_csv(out_dir / "two_stage_v3_testing_focus.csv", index=False)

    if len(stage1_grid):
        stage1_grid.to_csv(out_dir / "two_stage_v3_stage1_threshold_grid.csv", index=False)
    if len(stage2_grid):
        stage2_grid.to_csv(out_dir / "two_stage_v3_stage2_confidence_grid.csv", index=False)

    joblib.dump(stage1_model, out_dir / "stage1_v3_manipulation_detector.joblib")
    joblib.dump(stage2_model, out_dir / "stage2_v3_subtype_classifier.joblib")
    metadata = {
        "created_at": utc_now(),
        "started_at": started,
        "status": "phase4_experimental",
        "active_production_model": False,
        "stage1_threshold": stage1_threshold,
        "stage1_threshold_source": "leakage_safe_dev_grid",
        "stage2_min_confidence": stage2_confidence,
        "stage2_confidence_source": "leakage_safe_dev_grid",
        "stage1_features": stage1_features,
        "stage2_features": stage2_features,
        "stage2_classes": list(encoder.classes_),
        "synthetic_rows": int(len(synth_all)),
        "stop_rule": stop,
        "training_source": str(LEAKAGE_MANIFEST),
        "testing_source": str(TESTING_MANIFEST),
    }
    (out_dir / "two_stage_v3_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    (out_dir / "stage2_v3_label_encoder_classes.json").write_text(
        json.dumps({"classes": list(encoder.classes_)}, indent=2), encoding="utf-8"
    )

    report = [
        "# Phase 4 — Two-Stage Manipulation v3",
        "",
        f"Generated: {utc_now()}",
        "",
        f"Stage 1 threshold (dev): `{stage1_threshold}`",
        f"Stage 2 min confidence (dev): `{stage2_confidence}`",
        f"Synthetic/aug train rows: `{len(synth_all)}`",
        f"Stage 2 classes: `{', '.join(encoder.classes_)}`",
        "",
        "## Stop rule (manipulated testing_audios Stage-1 recall >= 70%)",
        "",
        f"- n_manipulated: {stop['n_manipulated']}",
        f"- recall: {stop.get('recall', float('nan')):.4f}",
        f"- **{'PASS' if stop.get('passes_stop_rule') else 'FAIL'}**",
        "",
        "## Stage 1 metrics",
        "",
        stage1_metrics_df.round(4).to_string(index=False),
        "",
        "## Stage 2 subtype metrics",
        "",
        subtype_metrics_df.round(4).to_string(index=False),
        "",
        "## Testing audios focus",
        "",
        testing_focus.round(4).to_string(index=False),
    ]
    if not stop.get("passes_stop_rule"):
        report.extend(
            [
                "",
                "## Stop-rule guidance",
                "",
                "Stage-1 recall on manipulated `testing_audios` is below 70%. "
                "Do not keep retraining this axis in Phase 4; document the limitation "
                "and proceed to Phase 6 calibration / honest UI wording.",
            ]
        )
    (out_dir / "phase4_two_stage_v3_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    progress(f"[phase4] complete -> {out_dir}")
    progress(f"[phase4] stop rule: {stop}")
    return 0 if stop.get("passes_stop_rule", False) else 2


if __name__ == "__main__":
    raise SystemExit(main())
