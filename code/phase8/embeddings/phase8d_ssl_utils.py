"""
Phase 8D SSL embedding extraction helpers.

Frozen embeddings only: no training, no fine-tuning, no predictions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_VERSION = "phase8d_v1"

EXTRACTION_STATUSES = frozenset(
    {
        "ok",
        "missing_audio",
        "unreadable_audio",
        "too_short",
        "silent_or_invalid",
        "model_error",
        "error",
    }
)

FILE_IDENTITY_COLUMNS = [
    "schema_version",
    "file_id",
    "audio_path",
    "source_dataset",
    "split",
    "known_origin_label",
    "known_manipulation_labels",
]

SEGMENT_IDENTITY_COLUMNS = [
    "schema_version",
    "file_id",
    "segment_id",
    "audio_path",
    "start_sec",
    "end_sec",
    "segment_duration_sec",
]

EMBEDDING_PROVENANCE_COLUMNS = [
    "embedding_model_name",
    "embedding_layer",
    "pooling",
    "target_sample_rate",
    "embedding_dim",
    "extraction_status",
    "warning_message",
]

FILE_EMBEDDING_BASE_COLUMNS = FILE_IDENTITY_COLUMNS + EMBEDDING_PROVENANCE_COLUMNS
SEGMENT_EMBEDDING_BASE_COLUMNS = SEGMENT_IDENTITY_COLUMNS + EMBEDDING_PROVENANCE_COLUMNS

FILE_METADATA_COLUMNS = [
    "file_id",
    "audio_path",
    "known_origin_label",
    "known_manipulation_labels",
    "duration_sec",
    "sample_rate",
    "embedding_model_name",
    "pooling",
    "extraction_status",
    "warning_message",
]

SEGMENT_METADATA_COLUMNS = [
    "file_id",
    "segment_id",
    "audio_path",
    "start_sec",
    "end_sec",
    "segment_duration_sec",
    "embedding_model_name",
    "pooling",
    "extraction_status",
    "warning_message",
]

MIN_DURATION_SEC = 0.03


def _lazy_torch():
    try:
        import torch  # type: ignore

        return torch
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "PyTorch is required for Phase 8D embeddings. "
            "Install with pip install torch."
        ) from exc


def _lazy_transformers():
    try:
        from transformers import AutoFeatureExtractor, AutoModel  # type: ignore

        return AutoModel, AutoFeatureExtractor
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "transformers is required for Phase 8D embeddings. "
            "Install with: python -m pip install transformers"
        ) from exc


def get_device(device_arg: str) -> Any:
    torch = _lazy_torch()
    arg = device_arg.lower().strip()
    if arg == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if arg == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("Requested --device cuda but CUDA is not available.")
        return torch.device("cuda")
    if arg == "cpu":
        return torch.device("cpu")
    raise ValueError(f"Unsupported device: {device_arg}")


def freeze_model(model: Any) -> Any:
    model.eval()
    for p in model.parameters():
        p.requires_grad_(False)
    return model


def load_ssl_model_and_processor(
    model_name: str,
    device: Any,
    use_safetensors: bool = True,
) -> tuple[Any, Any]:
    AutoModel, AutoFeatureExtractor = _lazy_transformers()
    try:
        # For embedding extraction we only need audio front-end, not tokenizer/ASR processor.
        processor = AutoFeatureExtractor.from_pretrained(model_name)
        model = AutoModel.from_pretrained(model_name, use_safetensors=use_safetensors)
    except Exception as exc:
        if use_safetensors:
            raise RuntimeError(
                f"Phase 8D tried loading '{model_name}' with use_safetensors=True and failed. "
                "If this model has no safetensors weights, use another SSL model with safetensors "
                "or upgrade torch carefully (consider CUDA compatibility). "
                f"Original error: {exc}"
            ) from exc
        raise RuntimeError(
            f"Failed to load frozen SSL extractor/model for '{model_name}' with use_safetensors=False. "
            "This path allows .bin weights and may depend on torch version/security policy. "
            "Possible causes: cache/network/model compatibility issues. "
            f"Original error: {exc}"
        ) from exc
    model = freeze_model(model)
    model.to(device)
    return model, processor


def _resolve_audio_path(audio_path: str | None) -> Path | None:
    if not audio_path or not str(audio_path).strip():
        return None
    p = Path(str(audio_path).strip())
    if p.is_file():
        return p.resolve()
    q = (REPO_ROOT / p).resolve()
    if q.is_file():
        return q
    return None


def _to_mono(y: np.ndarray) -> np.ndarray:
    y = np.asarray(y, dtype=np.float32)
    if y.ndim == 1:
        return y
    if y.ndim == 2:
        if y.shape[0] <= 8 and y.shape[1] > y.shape[0]:
            y = y.T
        return np.mean(y, axis=1, dtype=np.float32)
    return y.reshape(-1)


def _resample(y: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    if orig_sr == target_sr:
        return y
    try:
        import librosa  # type: ignore

        return librosa.resample(y, orig_sr=orig_sr, target_sr=target_sr).astype(np.float32)
    except Exception:
        dur = len(y) / float(orig_sr)
        n = max(int(dur * target_sr), 1)
        x_old = np.linspace(0, 1, num=len(y), endpoint=False)
        x_new = np.linspace(0, 1, num=n, endpoint=False)
        return np.interp(x_new, x_old, y).astype(np.float32)


def load_audio_mono(audio_path: str | None, target_sample_rate: int) -> tuple[np.ndarray | None, int | None, str]:
    resolved = _resolve_audio_path(audio_path)
    if resolved is None:
        return None, None, "missing_audio"

    y = None
    sr = None
    try:
        import soundfile as sf  # type: ignore

        data, sr = sf.read(str(resolved), always_2d=False)
        y = _to_mono(np.asarray(data, dtype=np.float32))
    except Exception:
        pass

    if y is None:
        try:
            import librosa  # type: ignore

            y, sr = librosa.load(str(resolved), sr=None, mono=True)
            y = np.asarray(y, dtype=np.float32)
        except Exception:
            return None, None, "unreadable_audio"

    if sr is None or sr <= 0:
        return None, None, "unreadable_audio"

    if int(sr) != int(target_sample_rate):
        y = _resample(y, int(sr), int(target_sample_rate))
        sr = target_sample_rate

    if len(y) < max(int(MIN_DURATION_SEC * sr), 8):
        return y, int(sr), "too_short"
    if np.max(np.abs(y)) < 1e-8:
        return y, int(sr), "silent_or_invalid"
    return y, int(sr), ""


def slice_audio(y: np.ndarray, sr: int, start_sec: float, end_sec: float) -> tuple[np.ndarray | None, str]:
    if y is None or sr <= 0 or len(y) == 0:
        return None, "silent_or_invalid"
    start = max(int(float(start_sec) * sr), 0)
    end = min(int(float(end_sec) * sr), len(y))
    if end <= start:
        return None, "too_short"
    seg = y[start:end]
    if len(seg) < max(int(MIN_DURATION_SEC * sr), 8):
        return None, "too_short"
    if np.max(np.abs(seg)) < 1e-8:
        return None, "silent_or_invalid"
    return seg.astype(np.float32), ""


def prepare_model_inputs(processor: Any, y: np.ndarray, sr: int, device: Any) -> dict[str, Any]:
    torch = _lazy_torch()
    inputs = processor(
        y,
        sampling_rate=sr,
        return_tensors="pt",
        padding=False,
    )
    out = {}
    for k, v in inputs.items():
        if isinstance(v, torch.Tensor):
            out[k] = v.to(device)
    return out


def mean_pool_hidden_state(last_hidden_state: Any, attention_mask: Any = None) -> Any:
    if attention_mask is None:
        return last_hidden_state.mean(dim=1)
    if attention_mask.ndim > 2:
        attention_mask = attention_mask.squeeze()
    # WavLM/wav2vec2 attention_mask may be at raw sample length; do not apply directly to hidden frames.
    if attention_mask.shape[-1] != last_hidden_state.shape[1]:
        return last_hidden_state.mean(dim=1)
    mask = attention_mask.unsqueeze(-1).type_as(last_hidden_state)
    summed = (last_hidden_state * mask).sum(dim=1)
    counts = mask.sum(dim=1).clamp(min=1e-9)
    return summed / counts


def mean_std_pool_hidden_state(last_hidden_state: Any, attention_mask: Any = None) -> Any:
    mean_vec = mean_pool_hidden_state(last_hidden_state, attention_mask)
    use_mask = attention_mask is not None and attention_mask.shape[-1] == last_hidden_state.shape[1]
    if not use_mask:
        std_vec = last_hidden_state.std(dim=1, unbiased=False)
    else:
        mask = attention_mask.unsqueeze(-1).type_as(last_hidden_state)
        centered = (last_hidden_state - mean_vec.unsqueeze(1)) * mask
        denom = mask.sum(dim=1).clamp(min=1e-9)
        var = (centered.pow(2).sum(dim=1)) / denom
        std_vec = torch.sqrt(var.clamp(min=1e-12))
    return torch.cat([mean_vec, std_vec], dim=-1)


def extract_ssl_embedding(
    y: np.ndarray,
    sr: int,
    processor: Any,
    model: Any,
    device: Any,
    pooling: str,
) -> np.ndarray:
    torch = _lazy_torch()
    inputs = prepare_model_inputs(processor, y, sr, device)
    with torch.no_grad():
        outputs = model(**inputs)
        last_hidden_state = outputs.last_hidden_state  # [B, T, H]
        attn = inputs.get("attention_mask")
        if pooling == "mean_std":
            pooled = mean_std_pool_hidden_state(last_hidden_state, attn)
        else:
            pooled = mean_pool_hidden_state(last_hidden_state, attn)
    emb = pooled[0].detach().float().cpu().numpy().reshape(-1)
    if emb.ndim != 1:
        raise RuntimeError(f"embedding is not 1D (ndim={emb.ndim})")
    if not np.isfinite(emb).all():
        raise RuntimeError("embedding contains non-finite values")
    return emb


def make_embedding_columns(embedding: np.ndarray) -> list[str]:
    n = int(len(embedding))
    return [f"ssl_emb_{i:03d}" for i in range(n)]


def empty_embedding_row(expected_dim: int) -> dict[str, str]:
    return {f"ssl_emb_{i:03d}": "" for i in range(expected_dim)}


def write_rows_append_safe(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    header = not path.is_file() or path.stat().st_size == 0
    df = pd.DataFrame(rows)
    for c in columns:
        if c not in df.columns:
            df[c] = ""
    df = df[columns]
    df.to_csv(path, mode="a", header=header, index=False)


def read_existing_ids_for_resume(path: Path, id_column: str) -> set[str]:
    if not path.is_file() or path.stat().st_size == 0:
        return set()
    try:
        df = pd.read_csv(path, usecols=[id_column], dtype=str, keep_default_na=False)
        return set(df[id_column].astype(str))
    except Exception:
        return set()

