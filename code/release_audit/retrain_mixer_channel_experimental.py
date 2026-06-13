"""Retrain an experimental mixer/channel model with leakage-safe splits.

This script does not overwrite release models. It trains a new acoustic-only
file-level mixer/channel classifier from the leakage-safe Phase 7 manifest,
selects a threshold on dev, and evaluates on test plus testing_audios.
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
DEFAULT_OUT = ROOT / "reports" / "release_audit" / "mixer_retrain_experimental_v3_2026-06-13"
SUPPORTED_EXTENSIONS = {".wav", ".flac", ".mp3", ".ogg", ".m4a", ".aac"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT))
    parser.add_argument("--max-selected-features", type=int, default=50)
    parser.add_argument("--random-seed", type=int, default=42)
    parser.add_argument(
        "--add-compression-aug",
        action="store_true",
        help="Add train-only codec/downsample/gain channel positives.",
    )
    parser.add_argument(
        "--augmentation-policy",
        default="v3_targeted",
        choices=["v3_targeted", "v2_balanced", "legacy_all_positive"],
        help=(
            "v3_targeted creates stronger mobile/mixer/platform positives from train audio; "
            "v2_balanced keeps clean/replay mild transforms as negative hard examples "
            "and uses stronger channel transforms as positives; legacy_all_positive "
            "matches the first failed attempt."
        ),
    )
    parser.add_argument(
        "--min-dev-specificity",
        type=float,
        default=0.9,
        help="Prefer thresholds with at least this dev specificity before maximizing recall.",
    )
    parser.add_argument(
        "--targeted-positive-limit",
        type=int,
        default=120,
        help="Maximum number of train rows used for v3 targeted positive augmentation.",
    )
    parser.add_argument(
        "--max-aug-source-rows",
        type=int,
        default=80,
        help="Limit train rows used for compression augmentation.",
    )
    parser.add_argument(
        "--max-testing-duration-sec",
        type=float,
        default=45.0,
        help="Trim each testing_audios file to this many seconds for fast acoustic evaluation. Use 0 to disable.",
    )
    parser.add_argument(
        "--progress-every",
        type=int,
        default=1,
        help="Print progress every N files.",
    )
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def resolve_audio(path_str: str) -> Path | None:
    path = Path(path_str)
    if path.is_file():
        return path.resolve()
    path = (ROOT / path).resolve()
    return path if path.is_file() else None


def progress(message: str) -> None:
    print(message, flush=True)


def channel_degrade(y: np.ndarray, sr: int, mode: str) -> np.ndarray:
    """In-memory channel/codec style degradation for train-only positives."""
    y = np.asarray(y, dtype=np.float64)
    try:
        import librosa

        if mode == "codec_8k":
            z = librosa.resample(y, orig_sr=sr, target_sr=8000)
            z = librosa.resample(z, orig_sr=8000, target_sr=sr)
        elif mode == "codec_12k":
            z = librosa.resample(y, orig_sr=sr, target_sr=12000)
            z = librosa.resample(z, orig_sr=12000, target_sr=sr)
        elif mode == "codec_12k_light":
            z = librosa.resample(y, orig_sr=sr, target_sr=12000)
            z = librosa.resample(z, orig_sr=12000, target_sr=sr)
            z = 0.95 * z + 0.05 * y[: len(z)]
        elif mode == "whatsapp_8k":
            z = librosa.resample(y, orig_sr=sr, target_sr=8000)
            z = librosa.resample(z, orig_sr=8000, target_sr=sr)
            z = np.round(z * 512.0) / 512.0
        elif mode == "mobile_11k":
            z = librosa.resample(y, orig_sr=sr, target_sr=11025)
            z = librosa.resample(z, orig_sr=11025, target_sr=sr)
        else:
            z = y.copy()
    except Exception:
        step = 2 if mode == "codec_8k" else 1
        z = np.repeat(y[::step], step)[: len(y)] if step > 1 else y.copy()
    if mode == "gain_noise":
        rng = np.random.default_rng(42)
        z = y * 0.82 + rng.normal(0.0, 0.0025, size=len(y))
    elif mode == "bandpass_mobile":
        try:
            from scipy.signal import butter, sosfilt

            sos = butter(6, [300, 3400], btype="bandpass", fs=sr, output="sos")
            z = sosfilt(sos, y)
            z = 0.9 * z
        except Exception:
            z = y.copy()
    elif mode == "clip_boost":
        z = np.tanh(y * 2.4) * 0.85
    elif mode == "mixer_eq_mobile":
        try:
            from scipy.signal import butter, sosfilt

            low = butter(3, 220, btype="highpass", fs=sr, output="sos")
            high = butter(3, 4300, btype="lowpass", fs=sr, output="sos")
            z = sosfilt(high, sosfilt(low, y))
            z = np.tanh((z * 1.8) + 0.003) * 0.8
        except Exception:
            z = np.tanh(y * 1.8) * 0.8
    elif mode == "dynamic_compress_noise":
        rng = np.random.default_rng(123)
        z = np.sign(y) * (np.abs(y) ** 0.65)
        z = z * 0.72 + rng.normal(0.0, 0.0035, size=len(y))
    elif mode == "low_mid_rebalance":
        try:
            from scipy.signal import butter, sosfilt

            low = sosfilt(butter(3, 650, btype="lowpass", fs=sr, output="sos"), y)
            mid = sosfilt(butter(3, [650, 3400], btype="bandpass", fs=sr, output="sos"), y)
            high = sosfilt(butter(3, 3400, btype="highpass", fs=sr, output="sos"), y)
            z = 0.35 * low + 1.45 * mid + 0.2 * high
        except Exception:
            z = y.copy()
    peak = float(np.max(np.abs(z))) if len(z) else 0.0
    if peak > 0.99:
        z = z / peak * 0.99
    return z.astype(np.float64)


def extract_rows(
    manifest: pd.DataFrame,
    *,
    testing: bool,
    label: str,
    max_duration_sec: float | None = None,
    progress_every: int = 1,
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
            original_duration = len(y) / float(sr)
            out["loaded_duration_sec"] = round(original_duration, 4)
            if max_duration_sec and max_duration_sec > 0:
                max_samples = int(max_duration_sec * sr)
                if len(y) > max_samples:
                    y = y[:max_samples]
                    out["feature_trimmed_for_speed"] = True
                    out["feature_duration_sec"] = round(len(y) / float(sr), 4)
                else:
                    out["feature_trimmed_for_speed"] = False
                    out["feature_duration_sec"] = round(original_duration, 4)
            out.update(extract_file_acoustic_features(y, sr))
            out["feature_elapsed_sec"] = round(time.time() - start, 3)
            progress(
                f"[{label}] {idx}/{total} done {row_id}: "
                f"duration={out.get('feature_duration_sec', out.get('loaded_duration_sec'))}s "
                f"elapsed={out['feature_elapsed_sec']}s"
            )
        except Exception as exc:
            out["feature_status"] = f"error: {exc}"
            progress(f"[{label}] {idx}/{total} error {row_id}: {exc}")
        rows.append(out)
    df = pd.DataFrame(rows)
    if testing:
        df["target_is_mixer_channel"] = df["manipulation_type"].isin(
            ["mixer_processed", "whatsapp_compressed"]
        ).astype(int)
        df["eval_split"] = "testing_audios"
    else:
        df["target_is_mixer_channel"] = pd.to_numeric(
            df["audit_mixer_gt"], errors="coerce"
        ).fillna(0).astype(int)
        df["eval_split"] = df["leakage_safe_split"]
    return df


def _augmentation_plan(row: pd.Series, policy: str) -> list[tuple[str, int]]:
    manipulation = str(row.get("manipulation_type", ""))
    origin = str(row.get("ground_truth_origin", row.get("source_origin", "")))
    if policy == "legacy_all_positive":
        return [(mode, 1) for mode in ["codec_8k", "codec_12k", "gain_noise"]]

    if policy == "v3_targeted":
        manipulation = str(row.get("manipulation_type", ""))
        origin = str(row.get("ground_truth_origin", row.get("source_origin", "")))
        hard_negative_plan = [
            ("gain_noise", 0),
            ("codec_12k_light", 0),
        ]
        targeted_positive_plan = [
            ("mixer_eq_mobile", 1),
            ("dynamic_compress_noise", 1),
            ("low_mid_rebalance", 1),
            ("whatsapp_8k", 1),
            ("mobile_11k", 1),
            ("clip_boost", 1),
            ("bandpass_mobile", 1),
        ]
        if manipulation == "mixer_processed":
            return targeted_positive_plan
        if manipulation in {"clean_direct", "ai_replay", "human_replay"}:
            plan = list(hard_negative_plan)
            # Create targeted positives from both human and AI train audio,
            # but keep mild replay/clean degradations as negative controls.
            if origin in {"human", "ai"}:
                plan.extend(targeted_positive_plan)
            return plan
        return []

    if manipulation == "mixer_processed":
        return [
            ("codec_8k", 1),
            ("codec_12k", 1),
            ("bandpass_mobile", 1),
            ("clip_boost", 1),
            ("gain_noise", 1),
        ]
    if manipulation == "clean_direct":
        plan = [
            ("gain_noise", 0),
            ("codec_12k_light", 0),
        ]
        # Platform-compressed AI is a positive channel condition, but keep it
        # narrower than the failed v1 policy so clean humans do not dominate.
        if origin == "ai":
            plan.extend([("codec_8k", 1), ("bandpass_mobile", 1)])
        return plan
    if manipulation in {"ai_replay", "human_replay"}:
        return [
            ("gain_noise", 0),
            ("codec_12k_light", 0),
        ]
    return []


def augmentation_rows(
    train_df: pd.DataFrame,
    max_rows: int,
    progress_every: int = 1,
    policy: str = "v2_balanced",
) -> pd.DataFrame:
    sources = train_df[train_df["feature_status"].eq("ok")].copy()
    sources = sources[
        sources["manipulation_type"].isin(["clean_direct", "ai_replay", "human_replay", "mixer_processed"])
    ].head(max_rows)
    rows: list[dict] = []
    total = len(sources)
    for idx, (_, row) in enumerate(sources.iterrows(), start=1):
        row_id = row.get("sample_id") or row.get("test_id") or f"row_{idx}"
        plan = _augmentation_plan(row, policy)
        if not plan:
            continue
        if idx == 1 or idx % max(progress_every, 1) == 0:
            progress(f"[augmentation] {idx}/{total} start {row_id} plan={len(plan)} policy={policy}")
        audio = Path(str(row["resolved_audio_path"]))
        if not audio.is_file():
            progress(f"[augmentation] {idx}/{total} skip {row_id}: missing_audio")
            continue
        try:
            y, sr = load_audio(str(audio), target_sample_rate=16000)
        except Exception:
            progress(f"[augmentation] {idx}/{total} skip {row_id}: load_error")
            continue
        for mode, target in plan:
            start = time.time()
            out = row.to_dict()
            z = channel_degrade(y, sr, mode)
            out.update(extract_file_acoustic_features(z, sr))
            out["sample_id"] = f"{row.get('sample_id', row.get('test_id', 'row'))}__aug_{mode}"
            out["feature_status"] = "ok"
            out["eval_split"] = "train"
            out["leakage_safe_split"] = "train"
            out["augmentation_mode"] = mode
            out["target_is_mixer_channel"] = int(target)
            rows.append(out)
            progress(
                f"[augmentation] {idx}/{total} done {row_id} {mode}: "
                f"target={target} elapsed={round(time.time() - start, 3)}s"
            )
    return pd.DataFrame(rows)


def feature_columns(df: pd.DataFrame) -> list[str]:
    identity = {
        "sample_id",
        "test_id",
        "audio_path",
        "resolved_audio_path",
        "feature_status",
        "eval_split",
        "leakage_safe_split",
        "target_is_mixer_channel",
    }
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
    cols = []
    for col in df.columns:
        if col in identity:
            continue
        if col.startswith(prefixes) or col in exact:
            cols.append(col)
    return cols


def clean_feature_matrix(df: pd.DataFrame, cols: list[str]) -> tuple[pd.DataFrame, list[str]]:
    x = df[cols].apply(pd.to_numeric, errors="coerce")
    usable = [c for c in x.columns if x[c].notna().any()]
    x = x[usable]
    med = x.median(numeric_only=True)
    tmp = x.fillna(med).fillna(0.0)
    varied = [c for c in tmp.columns if float(tmp[c].var()) > 1e-12]
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
    out["mixer_probability"] = np.nan
    out["mixer_prediction"] = np.nan
    if ok.any():
        x = out.loc[ok, cols].apply(pd.to_numeric, errors="coerce")
        probs = model.predict_proba(x)[:, 1]
        out.loc[ok, "mixer_probability"] = probs
        out.loc[ok, "mixer_prediction"] = (probs >= threshold).astype(int)
    return out


def metric_row(name: str, df: pd.DataFrame) -> dict:
    ok = df[df["feature_status"].eq("ok") & df["mixer_prediction"].notna()].copy()
    if len(ok) == 0:
        return {"scope": name, "n": 0}
    y = ok["target_is_mixer_channel"].astype(int).to_numpy()
    pred = ok["mixer_prediction"].astype(int).to_numpy()
    prob = ok["mixer_probability"].astype(float).to_numpy()
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
    if len(ok) == 0 or ok["target_is_mixer_channel"].nunique() < 2:
        return 0.5, pd.DataFrame()
    rows = []
    for th in np.round(np.arange(0.05, 0.951, 0.01), 2):
        tmp = ok.copy()
        tmp["mixer_prediction"] = (tmp["mixer_probability"].astype(float) >= th).astype(int)
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
    return [col for col, keep in zip(cols, mask) if bool(keep)]


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
    progress("[phase7] extracting leakage-safe train/dev/test acoustic features")
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
    if args.add_compression_aug:
        progress("[augmentation] building train-only channel/compression positives")
        aug = augmentation_rows(
            fit_train,
            args.max_aug_source_rows,
            progress_every=args.progress_every,
            policy=args.augmentation_policy,
        )
        if len(aug):
            fit_train = pd.concat([fit_train, aug], ignore_index=True, sort=False)

    raw_features = feature_columns(fit_train)
    x_train_raw, fit_features = clean_feature_matrix(fit_train, raw_features)
    y_train = fit_train["target_is_mixer_channel"].astype(int).to_numpy()
    if len(set(y_train)) < 2:
        raise ValueError("Training data must contain both mixer/channel positives and negatives.")

    k = min(args.max_selected_features, len(fit_features))
    model = build_model(k=k, seed=args.random_seed)
    model.fit(x_train_raw, y_train)

    train_pred_050 = predict_frame(model, fit_train, fit_features, threshold=0.5)
    dev_pred_050 = predict_frame(model, dev, fit_features, threshold=0.5)
    threshold, grid = choose_threshold(dev_pred_050, min_specificity=args.min_dev_specificity)

    splits = {
        "fit_train": fit_train,
        "train_original": train,
        "dev": dev,
        "test": test,
    }
    pred_frames = []
    for split_name, frame in splits.items():
        pred = predict_frame(model, frame, fit_features, threshold=threshold)
        pred["prediction_scope"] = split_name
        pred_frames.append(pred)

    testing_manifest = pd.read_csv(TESTING_MANIFEST, dtype=str, keep_default_na=False)
    progress(
        "[testing_audios] extracting evaluation acoustic features "
        f"(max_duration_sec={args.max_testing_duration_sec})"
    )
    testing = extract_rows(
        testing_manifest,
        testing=True,
        label="testing_audios",
        max_duration_sec=args.max_testing_duration_sec,
        progress_every=1,
    )
    testing_pred = predict_frame(model, testing, fit_features, threshold=threshold)
    testing_pred["prediction_scope"] = "testing_audios"
    pred_frames.append(testing_pred)

    all_pred = pd.concat(pred_frames, ignore_index=True, sort=False)
    all_pred.to_csv(out_dir / "mixer_experimental_predictions.csv", index=False)

    metrics = []
    for scope, frame in all_pred.groupby("prediction_scope", dropna=False):
        metrics.append(metric_row(str(scope), frame))
    metrics_df = pd.DataFrame(metrics)
    metrics_df.to_csv(out_dir / "mixer_experimental_metrics.csv", index=False)

    valid_for_error_table = all_pred[
        all_pred["feature_status"].eq("ok")
        & all_pred["mixer_prediction"].notna()
        & all_pred["target_is_mixer_channel"].notna()
    ].copy()
    valid_for_error_table["target_int"] = (
        pd.to_numeric(valid_for_error_table["target_is_mixer_channel"], errors="coerce")
        .fillna(-1)
        .astype(int)
    )
    valid_for_error_table["prediction_int"] = (
        pd.to_numeric(valid_for_error_table["mixer_prediction"], errors="coerce")
        .fillna(-2)
        .astype(int)
    )
    errors = valid_for_error_table[
        valid_for_error_table["target_int"] != valid_for_error_table["prediction_int"]
    ].copy()
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
            "target_is_mixer_channel",
            "mixer_probability",
            "mixer_prediction",
            "feature_status",
        ]
        if c in errors.columns
    ]
    errors[error_cols].to_csv(out_dir / "mixer_experimental_errors.csv", index=False)
    if len(grid):
        grid.to_csv(out_dir / "mixer_experimental_dev_threshold_grid.csv", index=False)

    sel = selected_features(model, fit_features)
    pd.DataFrame({"selected_feature": sel}).to_csv(
        out_dir / "mixer_experimental_selected_features.csv", index=False
    )

    artifact = out_dir / "mixer_channel_experimental_acoustic_logistic_regression.joblib"
    joblib.dump(model, artifact)
    metadata = {
        "model_name": "mixer_channel_experimental_acoustic_logistic_regression",
        "created_at": utc_now(),
        "status": "experimental_forensic_prototype",
        "active_production_model": False,
        "not_final_forensic_decision": True,
        "task_name": "mixer_file_model",
        "feature_set": "acoustic",
        "threshold_candidate": threshold,
        "input_feature_names": fit_features,
        "feature_names": sel,
        "model_artifact": str(artifact),
        "training_source": str(LEAKAGE_MANIFEST),
        "testing_source": str(TESTING_MANIFEST),
        "train_rows_original": int(len(train)),
        "train_rows_fit": int(len(fit_train)),
        "dev_rows": int(len(dev)),
        "test_rows": int(len(test)),
        "compression_augmentation_enabled": bool(args.add_compression_aug),
        "augmentation_policy": str(args.augmentation_policy),
        "min_dev_specificity": float(args.min_dev_specificity),
        "notes": [
            "Experimental mixer/channel retrain only.",
            "testing_audios is evaluation-only and is not used for fitting.",
            "Does not overwrite release packaged model.",
        ],
    }
    (out_dir / "mixer_channel_experimental_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )

    report = [
        "# Experimental Mixer/Channel Retrain",
        "",
        f"Generated: {utc_now()}",
        "",
        f"Threshold selected on dev: `{threshold}`",
        f"Compression augmentation enabled: `{bool(args.add_compression_aug)}`",
        f"Augmentation policy: `{args.augmentation_policy}`",
        f"Minimum dev specificity preference: `{args.min_dev_specificity}`",
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
            f"- `{out_dir / 'mixer_channel_experimental_metadata.json'}`",
            f"- `{out_dir / 'mixer_experimental_predictions.csv'}`",
            f"- `{out_dir / 'mixer_experimental_metrics.csv'}`",
            f"- `{out_dir / 'mixer_experimental_errors.csv'}`",
            f"- `{out_dir / 'mixer_experimental_selected_features.csv'}`",
        ]
    )
    (out_dir / "mixer_experimental_retrain_report.md").write_text(
        "\n".join(report), encoding="utf-8"
    )

    print(f"Wrote experimental mixer retrain outputs to {out_dir}")
    print(metrics_df.round(4).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
