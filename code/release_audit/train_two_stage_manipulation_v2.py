"""Train two-stage manipulation prototype v2 with unknown-artifact proxies.

This experiment keeps testing_audios as evaluation-only. It adds train-only
proxy examples for broad channel/edit/platform artifacts so Stage 1 can learn
higher recall and Stage 2 can fall back to unknown_channel_artifact.
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
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / "release"
if str(RELEASE) not in sys.path:
    sys.path.insert(0, str(RELEASE))

from src.audio_io import load_audio  # noqa: E402
from src.feature_extraction import extract_file_acoustic_features  # noqa: E402

from train_two_stage_manipulation_prototype import (  # noqa: E402
    LEAKAGE_MANIFEST,
    SUPPORTED_EXTENSIONS,
    TESTING_MANIFEST,
    acoustic_feature_columns,
    clean_feature_matrix,
    extract_rows,
    predict_stage1,
    predict_stage2,
    stage1_metrics,
    stage2_accuracy,
    testing_stage_labels,
)
from retrain_mixer_channel_experimental import channel_degrade  # noqa: E402

DEFAULT_OUT = ROOT / "reports" / "release_audit" / "two_stage_manipulation_v2_2026-06-13"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT))
    parser.add_argument("--max-selected-features", type=int, default=50)
    parser.add_argument("--random-seed", type=int, default=42)
    parser.add_argument("--stage1-threshold", type=float, default=0.45)
    parser.add_argument("--stage2-min-confidence", type=float, default=0.7)
    parser.add_argument("--max-proxy-source-rows", type=int, default=80)
    parser.add_argument("--max-testing-duration-sec", type=float, default=30.0)
    parser.add_argument("--progress-every", type=int, default=5)
    return parser.parse_args()


def progress(message: str) -> None:
    print(message, flush=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def resolve_audio(path_str: str) -> Path | None:
    path = Path(path_str)
    if path.is_file():
        return path.resolve()
    path = (ROOT / path).resolve()
    return path if path.is_file() else None


def build_model(k: int, seed: int, *, multiclass: bool) -> Pipeline:
    solver = "lbfgs" if multiclass else "liblinear"
    return Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("select", SelectKBest(score_func=f_classif, k=k)),
            (
                "clf",
                LogisticRegression(
                    penalty="l2",
                    class_weight="balanced",
                    max_iter=3000,
                    solver=solver,
                    random_state=seed,
                ),
            ),
        ]
    )


def phase7_v2_labels(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    manipulation = out["manipulation_type"].astype(str)
    out["stage1_target_manipulated"] = manipulation.ne("clean_direct").astype(int)
    out["stage2_target_type"] = manipulation.map(
        {
            "ai_replay": "replay",
            "human_replay": "replay",
            "mixer_processed": "mixer_channel",
            "partial_ai_insert": "partial_insert",
        }
    ).fillna("")
    out["eval_split"] = out["leakage_safe_split"]
    return out


def proxy_modes_for_row(row: pd.Series) -> list[tuple[str, str]]:
    manipulation = str(row.get("manipulation_type", ""))
    if manipulation == "clean_direct":
        return [
            ("gain_noise", "unknown_channel_artifact"),
            ("codec_12k_light", "unknown_channel_artifact"),
            ("whatsapp_8k", "unknown_channel_artifact"),
            ("dynamic_compress_noise", "unknown_channel_artifact"),
        ]
    if manipulation in {"ai_replay", "human_replay"}:
        return [
            ("codec_12k_light", "replay"),
            ("gain_noise", "replay"),
            ("mixer_eq_mobile", "unknown_channel_artifact"),
        ]
    if manipulation == "mixer_processed":
        return [
            ("bandpass_mobile", "mixer_channel"),
            ("low_mid_rebalance", "mixer_channel"),
            ("clip_boost", "mixer_channel"),
        ]
    return []


def add_train_proxy_rows(train_df: pd.DataFrame, max_rows: int, progress_every: int) -> pd.DataFrame:
    sources = train_df[train_df["feature_status"].eq("ok")].head(max_rows).copy()
    rows: list[dict] = []
    total = len(sources)
    for idx, (_, row) in enumerate(sources.iterrows(), start=1):
        row_id = row.get("sample_id") or f"row_{idx}"
        plan = proxy_modes_for_row(row)
        if not plan:
            continue
        if idx == 1 or idx % max(progress_every, 1) == 0:
            progress(f"[proxy] {idx}/{total} start {row_id} plan={len(plan)}")
        audio = resolve_audio(str(row["audio_path"]))
        if audio is None or audio.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        try:
            y, sr = load_audio(str(audio), target_sample_rate=16000)
        except Exception:
            continue
        for mode, subtype in plan:
            start = time.time()
            out = row.to_dict()
            z = channel_degrade(y, sr, mode)
            out.update(extract_file_acoustic_features(z, sr))
            out["sample_id"] = f"{row_id}__proxy_{mode}"
            out["feature_status"] = "ok"
            out["eval_split"] = "train"
            out["stage1_target_manipulated"] = 1
            out["stage2_target_type"] = subtype
            out["proxy_mode"] = mode
            rows.append(out)
            progress(
                f"[proxy] {idx}/{total} done {row_id} {mode}->{subtype}: "
                f"elapsed={round(time.time() - start, 3)}s"
            )
    return pd.DataFrame(rows)


def subtype_metrics(scope: str, df: pd.DataFrame, expected_col: str) -> dict:
    ok = df[
        df["feature_status"].eq("ok")
        & df[expected_col].astype(str).ne("")
        & df[expected_col].astype(str).ne("clean")
    ].copy()
    if len(ok) == 0:
        return {"scope": scope, "n": 0}
    pred = ok["final_reported_type"].astype(str)
    expected = ok[expected_col].astype(str)
    return {
        "scope": scope,
        "n": int(len(ok)),
        "accuracy_exact": float((pred == expected).mean()),
        "unknown_rate": float((pred == "unknown_channel_artifact").mean()),
        "safe_non_clean_rate": float(pred.ne("clean").mean()),
    }


def apply_final_two_stage_labels(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["final_reported_type"] = "clean"
    active = out["stage1_manipulation_prediction"].fillna(0).astype(float) >= 1.0
    out.loc[active, "final_reported_type"] = out.loc[active, "stage2_reported_type"].replace(
        {"": "unknown_channel_artifact"}
    )
    return out


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = pd.read_csv(LEAKAGE_MANIFEST, dtype=str, keep_default_na=False)
    eligible = manifest[
        manifest["ground_truth_origin"].isin(["human", "ai", "mixed"])
        & manifest["manipulation_type"].isin(
            ["clean_direct", "ai_replay", "human_replay", "mixer_processed", "partial_ai_insert"]
        )
    ].copy()

    progress("[phase7] extracting v2 train/dev/test features")
    phase7 = phase7_v2_labels(
        extract_rows(
            eligible,
            testing=False,
            label="phase7",
            max_duration_sec=None,
            progress_every=args.progress_every,
        )
    )
    train = phase7[phase7["eval_split"].eq("train")].copy()
    dev = phase7[phase7["eval_split"].eq("dev")].copy()
    test = phase7[phase7["eval_split"].eq("test")].copy()

    progress("[proxy] generating train-only unknown/channel proxy rows")
    proxies = add_train_proxy_rows(train, args.max_proxy_source_rows, args.progress_every)
    fit_train = pd.concat([train, proxies], ignore_index=True, sort=False) if len(proxies) else train.copy()

    features = acoustic_feature_columns(fit_train)
    ok_train = fit_train[fit_train["feature_status"].eq("ok")].copy()

    x_stage1, stage1_features = clean_feature_matrix(ok_train, features)
    y_stage1 = ok_train["stage1_target_manipulated"].astype(int).to_numpy()
    stage1 = build_model(min(args.max_selected_features, len(stage1_features)), args.random_seed, multiclass=False)
    stage1.fit(x_stage1, y_stage1)

    stage2_train = ok_train[ok_train["stage2_target_type"].astype(str).ne("")].copy()
    x_stage2, stage2_features = clean_feature_matrix(stage2_train, features)
    encoder = LabelEncoder()
    y_stage2 = encoder.fit_transform(stage2_train["stage2_target_type"].astype(str))
    stage2 = build_model(min(args.max_selected_features, len(stage2_features)), args.random_seed, multiclass=True)
    stage2.fit(x_stage2, y_stage2)

    frames = []
    for scope, frame in {"train": train, "fit_train": fit_train, "dev": dev, "test": test}.items():
        pred = predict_stage1(stage1, frame, stage1_features, args.stage1_threshold)
        pred = predict_stage2(stage2, encoder, pred, stage2_features, args.stage2_min_confidence)
        pred = apply_final_two_stage_labels(pred)
        pred["prediction_scope"] = scope
        frames.append(pred)

    testing_manifest = pd.read_csv(TESTING_MANIFEST, dtype=str, keep_default_na=False)
    progress(
        "[testing_audios] extracting v2 evaluation features "
        f"(max_duration_sec={args.max_testing_duration_sec})"
    )
    testing = testing_stage_labels(
        extract_rows(
            testing_manifest,
            testing=True,
            label="testing_audios",
            max_duration_sec=args.max_testing_duration_sec,
            progress_every=1,
        )
    )
    testing_pred = predict_stage1(stage1, testing, stage1_features, args.stage1_threshold)
    testing_pred = predict_stage2(stage2, encoder, testing_pred, stage2_features, args.stage2_min_confidence)
    testing_pred = apply_final_two_stage_labels(testing_pred)
    testing_pred["prediction_scope"] = "testing_audios"
    frames.append(testing_pred)

    predictions = pd.concat(frames, ignore_index=True, sort=False)
    predictions.to_csv(out_dir / "two_stage_v2_predictions.csv", index=False)

    stage1_metrics_df = pd.DataFrame(
        [stage1_metrics(str(scope), frame) for scope, frame in predictions.groupby("prediction_scope", dropna=False)]
    )
    stage1_metrics_df.to_csv(out_dir / "two_stage_v2_stage1_metrics.csv", index=False)

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
    subtype_metrics_df.to_csv(out_dir / "two_stage_v2_subtype_metrics.csv", index=False)

    focus_cols = [
        "test_id",
        "audio_path",
        "ground_truth_origin",
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
    testing_focus.to_csv(out_dir / "two_stage_v2_testing_focus.csv", index=False)

    joblib.dump(stage1, out_dir / "stage1_v2_manipulation_detector.joblib")
    joblib.dump(stage2, out_dir / "stage2_v2_subtype_classifier.joblib")
    metadata = {
        "created_at": utc_now(),
        "status": "experimental_forensic_prototype",
        "active_production_model": False,
        "not_final_forensic_decision": True,
        "stage1_threshold": args.stage1_threshold,
        "stage2_min_confidence": args.stage2_min_confidence,
        "stage2_classes": list(encoder.classes_),
        "proxy_rows": int(len(proxies)),
        "training_source": str(LEAKAGE_MANIFEST),
        "testing_source": str(TESTING_MANIFEST),
        "notes": [
            "Experimental two-stage v2 only.",
            "testing_audios is evaluation-only.",
            "unknown_channel_artifact proxy rows are generated from Phase 7 train files only.",
        ],
    }
    (out_dir / "two_stage_v2_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    report = [
        "# Two-Stage Manipulation Prototype V2",
        "",
        f"Generated: {utc_now()}",
        "",
        f"Stage 1 threshold: `{args.stage1_threshold}`",
        f"Stage 2 min confidence: `{args.stage2_min_confidence}`",
        f"Proxy rows: `{len(proxies)}`",
        f"Stage 2 classes: `{', '.join(encoder.classes_)}`",
        "",
        "## Stage 1 Metrics",
        "",
        stage1_metrics_df.round(4).to_string(index=False),
        "",
        "## Subtype Metrics",
        "",
        subtype_metrics_df.round(4).to_string(index=False),
        "",
        "## Testing Focus",
        "",
        testing_focus.round(4).to_string(index=False),
        "",
        "## Testing Classification Report",
        "",
    ]
    eval_stage2 = testing_focus[
        testing_focus["stage2_expected_type"].astype(str).ne("clean")
        & testing_focus["feature_status"].eq("ok")
    ].copy()
    if len(eval_stage2):
        report.append(
            classification_report(
                eval_stage2["stage2_expected_type"].astype(str),
                eval_stage2["final_reported_type"].astype(str),
                zero_division=0,
            )
        )
    else:
        report.append("(none)")
    report.extend(
        [
            "",
            "## Outputs",
            "",
            f"- `{out_dir / 'two_stage_v2_predictions.csv'}`",
            f"- `{out_dir / 'two_stage_v2_stage1_metrics.csv'}`",
            f"- `{out_dir / 'two_stage_v2_subtype_metrics.csv'}`",
            f"- `{out_dir / 'two_stage_v2_testing_focus.csv'}`",
            f"- `{out_dir / 'two_stage_v2_metadata.json'}`",
        ]
    )
    (out_dir / "two_stage_v2_report.md").write_text("\n".join(report), encoding="utf-8")

    print(f"Wrote two-stage v2 outputs to {out_dir}")
    print("Stage 1 metrics:")
    print(stage1_metrics_df.round(4).to_string(index=False))
    print("Subtype metrics:")
    print(subtype_metrics_df.round(4).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
