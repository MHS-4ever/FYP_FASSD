"""Retrain an experimental replay axis with mixer hard negatives.

This script does not overwrite release models. It trains an acoustic-only
file-level replay classifier from the leakage-safe Phase 7 manifest and
evaluates on testing_audios. testing_audios is evaluation-only.
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
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

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
DEFAULT_OUT = ROOT / "reports" / "release_audit" / "replay_retrain_experimental_2026-06-13"
SUPPORTED_EXTENSIONS = {".wav", ".flac", ".mp3", ".ogg", ".m4a", ".aac"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT))
    parser.add_argument("--max-selected-features", type=int, default=50)
    parser.add_argument("--random-seed", type=int, default=42)
    parser.add_argument("--min-dev-specificity", type=float, default=0.9)
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
            duration = len(y) / float(sr)
            out["loaded_duration_sec"] = round(duration, 4)
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

    df = pd.DataFrame(rows)
    if testing:
        df["target_is_replay"] = df["manipulation_type"].isin(["human_replay", "ai_replay"]).astype(int)
        df["eval_split"] = "testing_audios"
    else:
        df["target_is_replay"] = pd.to_numeric(df["audit_replay_gt"], errors="coerce").fillna(0).astype(int)
        df["eval_split"] = df["leakage_safe_split"]
    return df


def feature_columns(df: pd.DataFrame) -> list[str]:
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


def build_model(k: int, seed: int) -> Pipeline:
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
                    max_iter=2000,
                    solver="liblinear",
                    random_state=seed,
                ),
            ),
        ]
    )


def predict_frame(model: Pipeline, df: pd.DataFrame, cols: list[str], threshold: float) -> pd.DataFrame:
    out = df.copy()
    ok = out["feature_status"].eq("ok")
    out["replay_probability"] = np.nan
    out["replay_prediction"] = np.nan
    if ok.any():
        x = out.loc[ok, cols].apply(pd.to_numeric, errors="coerce")
        probs = model.predict_proba(x)[:, 1]
        out.loc[ok, "replay_probability"] = probs
        out.loc[ok, "replay_prediction"] = (probs >= threshold).astype(int)
    return out


def metric_row(name: str, df: pd.DataFrame) -> dict:
    ok = df[df["feature_status"].eq("ok") & df["replay_prediction"].notna()].copy()
    if len(ok) == 0:
        return {"scope": name, "n": 0}
    y = ok["target_is_replay"].astype(int).to_numpy()
    pred = ok["replay_prediction"].astype(int).to_numpy()
    prob = ok["replay_probability"].astype(float).to_numpy()
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {
        "scope": name,
        "n": int(len(ok)),
        "tp": int(tp),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "accuracy": float(accuracy_score(y, pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y, pred)) if len(set(y)) > 1 else np.nan,
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "specificity": float(tn / max(tn + fp, 1)),
        "fpr": float(fp / max(tn + fp, 1)),
        "fnr": float(fn / max(tp + fn, 1)),
        "f1": float(f1_score(y, pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y, prob)) if len(set(y)) > 1 else np.nan,
        "pr_auc": float(average_precision_score(y, prob)) if len(set(y)) > 1 else np.nan,
    }


def choose_threshold(dev_pred: pd.DataFrame, min_specificity: float) -> tuple[float, pd.DataFrame]:
    ok = dev_pred[dev_pred["feature_status"].eq("ok")].copy()
    if len(ok) == 0 or ok["target_is_replay"].nunique() < 2:
        return 0.5, pd.DataFrame()
    rows = []
    for th in np.round(np.arange(0.05, 0.951, 0.01), 2):
        tmp = ok.copy()
        tmp["replay_prediction"] = (tmp["replay_probability"].astype(float) >= th).astype(int)
        row = metric_row("dev", tmp)
        row["threshold"] = float(th)
        rows.append(row)
    grid = pd.DataFrame(rows)
    candidates = grid[grid["specificity"] >= float(min_specificity)].copy()
    if len(candidates) == 0:
        candidates = grid.copy()
    candidates = candidates.sort_values(
        ["recall", "specificity", "balanced_accuracy", "f1", "threshold"],
        ascending=[False, False, False, False, False],
    )
    return float(candidates.iloc[0]["threshold"]), grid


def selected_features(model: Pipeline, cols: list[str]) -> list[str]:
    mask = model.named_steps["select"].get_support()
    return [c for c, keep in zip(cols, mask) if bool(keep)]


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = pd.read_csv(LEAKAGE_MANIFEST, dtype=str, keep_default_na=False)
    eligible = manifest[
        manifest["ground_truth_origin"].isin(["human", "ai"])
        & manifest["partial_fabrication_binary"].astype(str).isin(["0", "false", "False", ""])
        & manifest["manipulation_type"].isin(["clean_direct", "ai_replay", "human_replay", "mixer_processed"])
    ].copy()

    progress("[phase7] extracting replay train/dev/test acoustic features")
    phase7 = extract_rows(
        eligible,
        testing=False,
        label="phase7",
        max_duration_sec=None,
        progress_every=args.progress_every,
    )

    train = phase7[phase7["eval_split"].eq("train")].copy()
    dev = phase7[phase7["eval_split"].eq("dev")].copy()
    test = phase7[phase7["eval_split"].eq("test")].copy()
    fit_train = train[train["feature_status"].eq("ok")].copy()

    raw_features = feature_columns(fit_train)
    x_train, fit_features = clean_feature_matrix(fit_train, raw_features)
    y_train = fit_train["target_is_replay"].astype(int).to_numpy()
    if len(set(y_train)) < 2:
        raise ValueError("Training data must contain both replay positives and negatives.")

    k = min(args.max_selected_features, len(fit_features))
    model = build_model(k=k, seed=args.random_seed)
    model.fit(x_train, y_train)

    dev_pred_050 = predict_frame(model, dev, fit_features, threshold=0.5)
    threshold, grid = choose_threshold(dev_pred_050, args.min_dev_specificity)

    frames = []
    for scope, frame in {
        "fit_train": fit_train,
        "train_original": train,
        "dev": dev,
        "test": test,
    }.items():
        pred = predict_frame(model, frame, fit_features, threshold)
        pred["prediction_scope"] = scope
        frames.append(pred)

    testing_manifest = pd.read_csv(TESTING_MANIFEST, dtype=str, keep_default_na=False)
    progress(
        "[testing_audios] extracting replay evaluation acoustic features "
        f"(max_duration_sec={args.max_testing_duration_sec})"
    )
    testing = extract_rows(
        testing_manifest,
        testing=True,
        label="testing_audios",
        max_duration_sec=args.max_testing_duration_sec,
        progress_every=1,
    )
    testing_pred = predict_frame(model, testing, fit_features, threshold)
    testing_pred["prediction_scope"] = "testing_audios"
    frames.append(testing_pred)

    all_pred = pd.concat(frames, ignore_index=True, sort=False)
    all_pred.to_csv(out_dir / "replay_experimental_predictions.csv", index=False)

    metrics_df = pd.DataFrame(
        [metric_row(str(scope), frame) for scope, frame in all_pred.groupby("prediction_scope", dropna=False)]
    )
    metrics_df.to_csv(out_dir / "replay_experimental_metrics.csv", index=False)

    valid = all_pred[
        all_pred["feature_status"].eq("ok")
        & all_pred["replay_prediction"].notna()
        & all_pred["target_is_replay"].notna()
    ].copy()
    valid["target_int"] = pd.to_numeric(valid["target_is_replay"], errors="coerce").fillna(-1).astype(int)
    valid["prediction_int"] = pd.to_numeric(valid["replay_prediction"], errors="coerce").fillna(-2).astype(int)
    errors = valid[valid["target_int"] != valid["prediction_int"]].copy()
    error_cols = [
        c
        for c in [
            "prediction_scope",
            "sample_id",
            "test_id",
            "audio_path",
            "ground_truth_origin",
            "manipulation_type",
            "language",
            "target_is_replay",
            "replay_probability",
            "replay_prediction",
            "feature_status",
        ]
        if c in errors.columns
    ]
    errors[error_cols].to_csv(out_dir / "replay_experimental_errors.csv", index=False)
    if len(grid):
        grid.to_csv(out_dir / "replay_experimental_dev_threshold_grid.csv", index=False)

    sel = selected_features(model, fit_features)
    pd.DataFrame({"selected_feature": sel}).to_csv(
        out_dir / "replay_experimental_selected_features.csv", index=False
    )

    artifact = out_dir / "replay_experimental_acoustic_logistic_regression.joblib"
    joblib.dump(model, artifact)
    metadata = {
        "model_name": "replay_experimental_acoustic_logistic_regression",
        "created_at": utc_now(),
        "status": "experimental_forensic_prototype",
        "active_production_model": False,
        "not_final_forensic_decision": True,
        "task_name": "replay_file_model",
        "feature_set": "acoustic",
        "threshold_candidate": threshold,
        "input_feature_names": fit_features,
        "feature_names": sel,
        "model_artifact": str(artifact),
        "training_source": str(LEAKAGE_MANIFEST),
        "testing_source": str(TESTING_MANIFEST),
        "train_rows_fit": int(len(fit_train)),
        "dev_rows": int(len(dev)),
        "test_rows": int(len(test)),
        "hard_negative_policy": "clean_direct and mixer_processed are replay negatives",
        "notes": [
            "Experimental replay retrain only.",
            "testing_audios is evaluation-only and is not used for fitting.",
            "Does not overwrite release packaged model.",
        ],
    }
    (out_dir / "replay_experimental_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )

    report = [
        "# Experimental Replay Retrain",
        "",
        f"Generated: {utc_now()}",
        "",
        f"Threshold selected on dev: `{threshold}`",
        "Hard negatives: `clean_direct`, `mixer_processed`",
        "",
        "## Metrics",
        "",
        metrics_df.round(4).to_string(index=False),
        "",
        "## Testing Audios Errors",
        "",
    ]
    testing_errors = errors[errors["prediction_scope"].eq("testing_audios")]
    report.append(testing_errors[error_cols].round(4).to_string(index=False) if len(testing_errors) else "(none)")
    report.extend(
        [
            "",
            "## Outputs",
            "",
            f"- `{artifact}`",
            f"- `{out_dir / 'replay_experimental_metadata.json'}`",
            f"- `{out_dir / 'replay_experimental_predictions.csv'}`",
            f"- `{out_dir / 'replay_experimental_metrics.csv'}`",
            f"- `{out_dir / 'replay_experimental_errors.csv'}`",
            f"- `{out_dir / 'replay_experimental_selected_features.csv'}`",
        ]
    )
    (out_dir / "replay_experimental_retrain_report.md").write_text(
        "\n".join(report), encoding="utf-8"
    )

    print(f"Wrote experimental replay retrain outputs to {out_dir}")
    print(metrics_df.round(4).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
