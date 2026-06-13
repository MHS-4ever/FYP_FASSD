"""Shared helpers for Phase 3 controlled experiments (3A/3B/3C)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
    roc_auc_score,
)

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / "release"
LEAKAGE_MANIFEST = (
    ROOT
    / "reports"
    / "release_audit"
    / "leakage_safe_eval_2026-06-13"
    / "leakage_safe_file_manifest.csv"
)
PHASE8_MASTER = (
    ROOT
    / "reports"
    / "phase8"
    / "models"
    / "phase8e0"
    / "phase8e0_file_level_master_dataset.csv"
)
PHASE8_FILE_SSL = ROOT / "reports" / "phase8" / "embeddings" / "phase8d_file_ssl_embeddings.csv"
PHASE8_SEGMENT_SSL = ROOT / "reports" / "phase8" / "embeddings" / "phase8d_segment_ssl_embeddings.csv"
TESTING_MANIFEST = (
    ROOT
    / "reports"
    / "phase7"
    / "phase7_forensic_tests"
    / "forensic_test_manifest_backup_before_T4_3_timestamp.csv"
)
PHASE3_OUT = ROOT / "reports" / "release_audit" / "phase3_controlled_experiments_2026-06-13"
SSL_DIM = 768
ORIGIN_THRESHOLD = 0.92

if str(RELEASE) not in sys.path:
    sys.path.insert(0, str(RELEASE))

from src.feature_extraction import align_features_to_metadata  # noqa: E402
from src.model_loader import (  # noqa: E402
    clear_active_model_cache,
    get_model_input_feature_names,
    get_threshold,
    load_all_active_models,
)


def normalized_path(path: Any) -> str:
    return str(path).replace("\\", "/").lower()


def resolve_audio(path_str: str) -> Path | None:
    p = Path(path_str)
    if p.is_file():
        return p.resolve()
    q = (ROOT / p).resolve()
    return q if q.is_file() else None


def ssl_columns() -> list[str]:
    return [f"ssl_emb_{i:03d}" for i in range(SSL_DIM)]


def load_origin_model() -> tuple[Any, dict[str, Any]]:
    clear_active_model_cache()
    models = load_all_active_models()
    return models["origin"]["model"], models["origin"]["metadata"]


def predict_origin_probability(
    model: Any,
    metadata: dict[str, Any],
    features: dict[str, float],
) -> float:
    names = get_model_input_feature_names(model, metadata)
    x = align_features_to_metadata(features, names)
    return float(model.predict_proba(x)[0, 1])


def metric_row(
    scope: str,
    df: pd.DataFrame,
    *,
    target_col: str = "target",
    pred_col: str = "pred",
    prob_col: str = "probability",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    sub = df.dropna(subset=[target_col, pred_col]).copy()
    if sub.empty:
        row = {"scope": scope, "n": 0}
        if extra:
            row.update(extra)
        return row
    y = sub[target_col].astype(int).to_numpy()
    yp = sub[pred_col].astype(int).to_numpy()
    prb = pd.to_numeric(sub[prob_col], errors="coerce").to_numpy(dtype=float)
    tn, fp, fn, tp = confusion_matrix(y, yp, labels=[0, 1]).ravel()
    precision, recall, f1, _ = precision_recall_fscore_support(
        y, yp, average="binary", zero_division=0
    )
    roc = pr = float("nan")
    if len(set(y)) > 1 and np.isfinite(prb).all():
        roc = float(roc_auc_score(y, prb))
        pr = float(average_precision_score(y, prb))
    row = {
        "scope": scope,
        "n": int(len(sub)),
        "tp": int(tp),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "accuracy": float(accuracy_score(y, yp)),
        "balanced_accuracy": float(balanced_accuracy_score(y, yp)) if len(set(y)) > 1 else float("nan"),
        "precision": float(precision),
        "recall": float(recall),
        "specificity": float(tn / max(tn + fp, 1)),
        "fpr": float(fp / max(tn + fp, 1)),
        "fnr": float(fn / max(tp + fn, 1)),
        "f1": float(f1),
        "roc_auc": roc,
        "pr_auc": pr,
    }
    if extra:
        row.update(extra)
    return row


def _to_mono(y: np.ndarray) -> np.ndarray:
    y = np.asarray(y, dtype=np.float32)
    if y.ndim == 1:
        return y
    if y.ndim == 2:
        if y.shape[0] <= 8 and y.shape[1] > y.shape[0]:
            y = y.T
        return np.mean(y, axis=1, dtype=np.float32)
    return y.reshape(-1)


def resample_audio(y: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    if int(orig_sr) == int(target_sr):
        return np.asarray(y, dtype=np.float32)
    try:
        import librosa

        return librosa.resample(y, orig_sr=int(orig_sr), target_sr=int(target_sr)).astype(np.float32)
    except Exception:
        dur = len(y) / float(orig_sr)
        n = max(int(dur * target_sr), 1)
        x_old = np.linspace(0, 1, num=len(y), endpoint=False)
        x_new = np.linspace(0, 1, num=n, endpoint=False)
        return np.interp(x_new, x_old, y).astype(np.float32)


def load_native_audio_mono(audio_path: Path) -> tuple[np.ndarray, int]:
    y = None
    sr = None
    try:
        import soundfile as sf

        data, sr = sf.read(str(audio_path), always_2d=False)
        y = _to_mono(np.asarray(data, dtype=np.float32))
    except Exception:
        pass
    if y is None:
        import librosa

        y, sr = librosa.load(str(audio_path), sr=None, mono=True)
        y = np.asarray(y, dtype=np.float32)
    if sr is None or sr <= 0:
        raise ValueError(f"invalid sample rate for {audio_path}")
    return y, int(sr)


def apply_resample_chain(y: np.ndarray, native_sr: int, chain_hz: list[int]) -> tuple[np.ndarray, int]:
    sr = int(native_sr)
    out = np.asarray(y, dtype=np.float32)
    for target in chain_hz:
        out = resample_audio(out, sr, int(target))
        sr = int(target)
    return out, sr


# Front-end chains before WavLM (always ends at 16 kHz).
RESAMPLE_VARIANTS: dict[str, list[int]] = {
    "ssl_16k_direct": [16000],
    "ssl_chain_8k_16k": [8000, 16000],
    "ssl_chain_12k_16k": [12000, 16000],
    "ssl_chain_22_05k_16k": [22050, 16000],
    "ssl_chain_24k_16k": [24000, 16000],
    "ssl_roundtrip_16_8_16": [16000, 8000, 16000],
}


def phase7_origin_eval_frame() -> pd.DataFrame:
    manifest = pd.read_csv(LEAKAGE_MANIFEST)
    manifest["_join_audio_path"] = manifest["audio_path"].map(normalized_path)
    manifest["target"] = pd.to_numeric(manifest["audit_origin_expected_ai"], errors="coerce")
    manifest["origin_training_scope"] = manifest["audit_condition"].isin(
        {
            "ai_clean_direct",
            "ai_mixer_processed",
            "ai_replayed",
            "human_clean",
            "human_mixer_processed",
            "human_replayed",
        }
    )
    return manifest


def testing_origin_eval_frame() -> pd.DataFrame:
    manifest = pd.read_csv(TESTING_MANIFEST, dtype=str, keep_default_na=False)
    manifest["target"] = manifest["ground_truth_origin"].eq("ai").astype(int)
    return manifest


def tqdm_iter(items, *, desc: str, unit: str = "item"):
    """Progress bar wrapper; falls back to plain iteration if tqdm is missing."""
    try:
        from tqdm import tqdm

        return tqdm(items, desc=desc, unit=unit, dynamic_ncols=True, mininterval=0.5)
    except Exception:
        return items


def variant_outputs_complete(out_dir: Path, variant: str) -> bool:
    p7 = out_dir / f"predictions_phase7_{variant}.csv"
    ta = out_dir / f"predictions_testing_audios_{variant}.csv"
    return p7.is_file() and ta.is_file()


def beats_baseline(
    candidate: dict[str, float],
    baseline: dict[str, float],
    *,
    min_delta: float = 0.0,
) -> bool:
    """True when candidate strictly improves both leakage-safe test bal-acc and testing_audios bal-acc."""
    return (
        candidate.get("phase7_test_balanced_accuracy", float("-inf"))
        > baseline.get("phase7_test_balanced_accuracy", float("-inf")) + min_delta
        and candidate.get("testing_audios_balanced_accuracy", float("-inf"))
        > baseline.get("testing_audios_balanced_accuracy", float("-inf")) + min_delta
    )
