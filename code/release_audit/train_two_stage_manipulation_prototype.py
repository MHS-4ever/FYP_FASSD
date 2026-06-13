"""Train an experimental two-stage manipulation evidence prototype.

Stage 1: clean/direct vs manipulated/channel-artifact evidence.
Stage 2: manipulation subtype among replay, mixer/channel, and partial-insert
         classes available in Phase 7.

This does not overwrite release models. testing_audios is evaluation-only.
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

LEAKAGE_MANIFEST = (
    ROOT
    / "reports"
    / "release_audit"
    / "leakage_safe_eval_2026-06-13"
    / "leakage_safe_file_manifest.csv"
)
TESTING_MANIFEST = (
    ROOT
    / "reports"
    / "phase7"
    / "phase7_forensic_tests"
    / "forensic_test_manifest_backup_before_T4_3_timestamp.csv"
)
DEFAULT_OUT = ROOT / "reports" / "release_audit" / "two_stage_manipulation_prototype_2026-06-13"
SUPPORTED_EXTENSIONS = {".wav", ".flac", ".mp3", ".ogg", ".m4a", ".aac"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT))
    parser.add_argument("--max-selected-features", type=int, default=50)
    parser.add_argument("--random-seed", type=int, default=42)
    parser.add_argument("--stage1-min-dev-specificity", type=float, default=0.9)
    parser.add_argument("--stage2-min-confidence", type=float, default=0.55)
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


def extract_rows(
    manifest: pd.DataFrame,
    *,
    testing: bool,
    label: str,
    max_duration_sec: float | None,
    progress_every: int,
) -> pd.DataFrame:
    rows: list[dict] = []
    total = len(manifest)
    for idx, (_, row) in enumerate(manifest.iterrows(), start=1):
        row_id = row.get("sample_id") or row.get("test_id") or f"row_{idx}"
        audio = resolve_audio(row["audio_path"])
        out = row.to_dict()
        out["resolved_audio_path"] = str(audio) if audio else ""
        out["feature_status"] = "ok"
        if idx == 1 or idx % max(progress_every, 1) == 0 or testing:
            progress(f"[{label}] {idx}/{total} start {row_id}: {row['audio_path']}")
        if audio is None:
            out["feature_status"] = "missing_audio"
            rows.append(out)
            progress(f"[{label}] {idx}/{total} skip {row_id}: missing_audio")
            continue
        if audio.suffix.lower() not in SUPPORTED_EXTENSIONS:
            out["feature_status"] = "unsupported_audio_extension"
            rows.append(out)
            progress(f"[{label}] {idx}/{total} skip {row_id}: unsupported {audio.suffix}")
            continue
        try:
            start = time.time()
            y, sr = load_audio(str(audio), target_sample_rate=16000)
            if testing and max_duration_sec and max_duration_sec > 0:
                max_samples = int(max_duration_sec * sr)
                if len(y) > max_samples:
                    y = y[:max_samples]
                    out["feature_trimmed_for_speed"] = True
                else:
                    out["feature_trimmed_for_speed"] = False
            out["feature_duration_sec"] = round(len(y) / float(sr), 4)
            out.update(extract_file_acoustic_features(y, sr))
            out["feature_elapsed_sec"] = round(time.time() - start, 3)
            progress(
                f"[{label}] {idx}/{total} done {row_id}: "
                f"duration={out['feature_duration_sec']}s elapsed={out['feature_elapsed_sec']}s"
            )
        except Exception as exc:
            out["feature_status"] = f"error: {exc}"
            progress(f"[{label}] {idx}/{total} error {row_id}: {exc}")
        rows.append(out)
    return pd.DataFrame(rows)


def phase7_stage_labels(df: pd.DataFrame) -> pd.DataFrame:
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


def testing_stage_labels(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    manipulation = out["manipulation_type"].astype(str)
    out["stage1_target_manipulated"] = manipulation.ne("clean_direct").astype(int)
    out["stage2_expected_type"] = manipulation.map(
        {
            "ai_replay": "replay",
            "human_replay": "replay",
            "mixer_processed": "mixer_channel",
            "whatsapp_compressed": "platform_compression",
            "edited_spliced": "edited_spliced",
            "partial_ai_insert": "partial_insert",
        }
    ).fillna("clean")
    out["eval_split"] = "testing_audios"
    return out


def acoustic_feature_columns(df: pd.DataFrame) -> list[str]:
    prefixes = ("rms_", "spectral_", "mfcc_")
    exact = {
        "peak_amplitude",
        "mean_amplitude",
        "std_amplitude",
        "dc_offset",
        "zero_crossing_rate_mean",
        "zero_crossing_rate_std",
        "clipping_ratio",
        "silence_ratio",
        "active_audio_ratio",
        "low_band_energy_ratio",
        "mid_band_energy_ratio",
        "high_band_energy_ratio",
        "noise_floor_proxy",
        "snr_proxy",
        "dynamic_range_proxy",
        "high_freq_rolloff_ratio",
        "bandwidth_occupied_95",
    }
    return [c for c in df.columns if c.startswith(prefixes) or c in exact]


def clean_feature_matrix(df: pd.DataFrame, cols: list[str]) -> tuple[pd.DataFrame, list[str]]:
    x = df[cols].apply(pd.to_numeric, errors="coerce")
    usable = [c for c in x.columns if x[c].notna().any()]
    x = x[usable]
    med = x.median(numeric_only=True)
    filled = x.fillna(med).fillna(0.0)
    varied = [c for c in filled.columns if float(filled[c].var()) > 1e-12]
    return x[varied], varied


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


def predict_stage1(model: Pipeline, df: pd.DataFrame, cols: list[str], threshold: float) -> pd.DataFrame:
    out = df.copy()
    ok = out["feature_status"].eq("ok")
    out["stage1_manipulation_probability"] = np.nan
    out["stage1_manipulation_prediction"] = np.nan
    if ok.any():
        x = out.loc[ok, cols].apply(pd.to_numeric, errors="coerce")
        probs = model.predict_proba(x)[:, 1]
        out.loc[ok, "stage1_manipulation_probability"] = probs
        out.loc[ok, "stage1_manipulation_prediction"] = (probs >= threshold).astype(int)
    return out


def predict_stage2(
    model: Pipeline,
    encoder: LabelEncoder,
    df: pd.DataFrame,
    cols: list[str],
    min_confidence: float,
) -> pd.DataFrame:
    out = df.copy()
    ok = out["feature_status"].eq("ok")
    out["stage2_raw_type"] = ""
    out["stage2_confidence"] = np.nan
    out["stage2_reported_type"] = ""
    if ok.any():
        x = out.loc[ok, cols].apply(pd.to_numeric, errors="coerce")
        probs = model.predict_proba(x)
        best = np.argmax(probs, axis=1)
        conf = np.max(probs, axis=1)
        labels = encoder.inverse_transform(best)
        out.loc[ok, "stage2_raw_type"] = labels
        out.loc[ok, "stage2_confidence"] = conf
        out.loc[ok, "stage2_reported_type"] = [
            label if c >= min_confidence else "unknown_channel_artifact"
            for label, c in zip(labels, conf)
        ]
    return out


def choose_stage1_threshold(dev_pred: pd.DataFrame, min_specificity: float) -> tuple[float, pd.DataFrame]:
    ok = dev_pred[dev_pred["feature_status"].eq("ok")].copy()
    if ok["stage1_target_manipulated"].nunique() < 2:
        return 0.5, pd.DataFrame()
    rows = []
    for th in np.round(np.arange(0.05, 0.951, 0.01), 2):
        tmp = ok.copy()
        tmp["stage1_manipulation_prediction"] = (
            tmp["stage1_manipulation_probability"].astype(float) >= th
        ).astype(int)
        rows.append(stage1_metrics("dev", tmp) | {"threshold": float(th)})
    grid = pd.DataFrame(rows)
    candidates = grid[grid["specificity"] >= float(min_specificity)].copy()
    if len(candidates) == 0:
        candidates = grid.copy()
    candidates = candidates.sort_values(
        ["recall", "specificity", "balanced_accuracy", "f1", "threshold"],
        ascending=[False, False, False, False, False],
    )
    return float(candidates.iloc[0]["threshold"]), grid


def stage1_metrics(scope: str, df: pd.DataFrame) -> dict:
    ok = df[df["feature_status"].eq("ok") & df["stage1_manipulation_prediction"].notna()].copy()
    if len(ok) == 0:
        return {"scope": scope, "n": 0}
    y = ok["stage1_target_manipulated"].astype(int).to_numpy()
    pred = ok["stage1_manipulation_prediction"].astype(int).to_numpy()
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {
        "scope": scope,
        "n": int(len(ok)),
        "tp": int(tp),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "accuracy": float(accuracy_score(y, pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y, pred)),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "specificity": float(tn / max(tn + fp, 1)),
        "fpr": float(fp / max(tn + fp, 1)),
        "fnr": float(fn / max(tp + fn, 1)),
        "f1": float(f1_score(y, pred, zero_division=0)),
    }


def stage2_accuracy(scope: str, df: pd.DataFrame, expected_col: str) -> dict:
    ok = df[
        df["feature_status"].eq("ok")
        & df[expected_col].astype(str).ne("")
        & df["stage2_reported_type"].astype(str).ne("")
    ].copy()
    ok = ok[ok[expected_col].astype(str).ne("clean")]
    if len(ok) == 0:
        return {"scope": scope, "n": 0}
    expected = ok[expected_col].astype(str)
    pred = ok["stage2_reported_type"].astype(str)
    return {
        "scope": scope,
        "n": int(len(ok)),
        "accuracy": float((expected == pred).mean()),
        "unknown_rate": float((pred == "unknown_channel_artifact").mean()),
    }


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
    progress("[phase7] extracting two-stage train/dev/test features")
    phase7 = phase7_stage_labels(
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

    features = acoustic_feature_columns(train)
    x_stage1, stage1_features = clean_feature_matrix(train[train["feature_status"].eq("ok")], features)
    y_stage1 = train[train["feature_status"].eq("ok")]["stage1_target_manipulated"].astype(int).to_numpy()
    k1 = min(args.max_selected_features, len(stage1_features))
    stage1 = build_model(k1, args.random_seed, multiclass=False)
    stage1.fit(x_stage1, y_stage1)

    stage2_train = train[
        train["feature_status"].eq("ok") & train["stage2_target_type"].astype(str).ne("")
    ].copy()
    x_stage2, stage2_features = clean_feature_matrix(stage2_train, features)
    encoder = LabelEncoder()
    y_stage2 = encoder.fit_transform(stage2_train["stage2_target_type"].astype(str))
    k2 = min(args.max_selected_features, len(stage2_features))
    stage2 = build_model(k2, args.random_seed, multiclass=True)
    stage2.fit(x_stage2, y_stage2)

    dev_stage1_050 = predict_stage1(stage1, dev, stage1_features, 0.5)
    stage1_threshold, threshold_grid = choose_stage1_threshold(
        dev_stage1_050, args.stage1_min_dev_specificity
    )

    frames = []
    for scope, frame in {
        "train": train,
        "dev": dev,
        "test": test,
    }.items():
        pred = predict_stage1(stage1, frame, stage1_features, stage1_threshold)
        pred = predict_stage2(stage2, encoder, pred, stage2_features, args.stage2_min_confidence)
        pred["prediction_scope"] = scope
        frames.append(pred)

    testing_manifest = pd.read_csv(TESTING_MANIFEST, dtype=str, keep_default_na=False)
    progress(
        "[testing_audios] extracting two-stage evaluation features "
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
    testing_pred = predict_stage1(stage1, testing, stage1_features, stage1_threshold)
    testing_pred = predict_stage2(stage2, encoder, testing_pred, stage2_features, args.stage2_min_confidence)
    testing_pred["prediction_scope"] = "testing_audios"
    frames.append(testing_pred)

    predictions = pd.concat(frames, ignore_index=True, sort=False)
    predictions.to_csv(out_dir / "two_stage_predictions.csv", index=False)

    stage1_metrics_df = pd.DataFrame(
        [
            stage1_metrics(str(scope), frame)
            for scope, frame in predictions.groupby("prediction_scope", dropna=False)
        ]
    )
    stage1_metrics_df.to_csv(out_dir / "two_stage_stage1_metrics.csv", index=False)

    stage2_rows = [
        stage2_accuracy("train", predictions[predictions["prediction_scope"].eq("train")], "stage2_target_type"),
        stage2_accuracy("dev", predictions[predictions["prediction_scope"].eq("dev")], "stage2_target_type"),
        stage2_accuracy("test", predictions[predictions["prediction_scope"].eq("test")], "stage2_target_type"),
        stage2_accuracy(
            "testing_audios",
            predictions[predictions["prediction_scope"].eq("testing_audios")],
            "stage2_expected_type",
        ),
    ]
    stage2_metrics_df = pd.DataFrame(stage2_rows)
    stage2_metrics_df.to_csv(out_dir / "two_stage_stage2_metrics.csv", index=False)

    testing_focus_cols = [
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
        "feature_status",
    ]
    testing_focus = testing_pred[[c for c in testing_focus_cols if c in testing_pred.columns]].copy()
    testing_focus.to_csv(out_dir / "two_stage_testing_audios_focus.csv", index=False)

    if len(threshold_grid):
        threshold_grid.to_csv(out_dir / "two_stage_stage1_threshold_grid.csv", index=False)

    joblib.dump(stage1, out_dir / "stage1_manipulation_detector.joblib")
    joblib.dump(stage2, out_dir / "stage2_manipulation_type_classifier.joblib")
    (out_dir / "stage2_label_encoder_classes.json").write_text(
        json.dumps({"classes": list(encoder.classes_)}, indent=2), encoding="utf-8"
    )
    metadata = {
        "created_at": utc_now(),
        "status": "experimental_forensic_prototype",
        "active_production_model": False,
        "not_final_forensic_decision": True,
        "stage1_threshold": stage1_threshold,
        "stage2_min_confidence": args.stage2_min_confidence,
        "stage1_features": stage1_features,
        "stage2_features": stage2_features,
        "stage2_classes": list(encoder.classes_),
        "training_source": str(LEAKAGE_MANIFEST),
        "testing_source": str(TESTING_MANIFEST),
        "notes": [
            "Experimental two-stage manipulation prototype only.",
            "testing_audios is evaluation-only.",
            "No release models are overwritten.",
        ],
    }
    (out_dir / "two_stage_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    report = [
        "# Two-Stage Manipulation Prototype",
        "",
        f"Generated: {utc_now()}",
        "",
        f"Stage 1 threshold: `{stage1_threshold}`",
        f"Stage 2 min confidence: `{args.stage2_min_confidence}`",
        f"Stage 2 trained classes: `{', '.join(encoder.classes_)}`",
        "",
        "## Stage 1 Metrics",
        "",
        stage1_metrics_df.round(4).to_string(index=False),
        "",
        "## Stage 2 Metrics",
        "",
        stage2_metrics_df.round(4).to_string(index=False),
        "",
        "## Testing Audios Focus",
        "",
        testing_focus.round(4).to_string(index=False),
        "",
        "## Classification Report: Testing Stage 2 Known/Expected Types",
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
                eval_stage2["stage2_reported_type"].astype(str),
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
            f"- `{out_dir / 'two_stage_predictions.csv'}`",
            f"- `{out_dir / 'two_stage_stage1_metrics.csv'}`",
            f"- `{out_dir / 'two_stage_stage2_metrics.csv'}`",
            f"- `{out_dir / 'two_stage_testing_audios_focus.csv'}`",
            f"- `{out_dir / 'two_stage_metadata.json'}`",
        ]
    )
    (out_dir / "two_stage_manipulation_prototype_report.md").write_text(
        "\n".join(report), encoding="utf-8"
    )

    print(f"Wrote two-stage manipulation prototype outputs to {out_dir}")
    print("Stage 1 metrics:")
    print(stage1_metrics_df.round(4).to_string(index=False))
    print("Stage 2 metrics:")
    print(stage2_metrics_df.round(4).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
