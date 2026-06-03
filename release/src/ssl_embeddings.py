"""Frozen WavLM SSL embeddings for Phase 9C live inference."""

from __future__ import annotations

import sys
from functools import lru_cache
from typing import Any

import numpy as np
import pandas as pd

from .utils import repo_root

DEFAULT_MODEL_NAME = "microsoft/wavlm-base-plus"
EMBEDDING_DIM = 768


def _import_phase8d():
    root = repo_root()
    emb_dir = root / "code" / "phase8" / "embeddings"
    if str(emb_dir) not in sys.path:
        sys.path.insert(0, str(emb_dir))
    try:
        import phase8d_ssl_utils as p8d  # type: ignore

        return p8d
    except Exception as exc:
        raise RuntimeError(
            "Phase 9C requires code.phase8.embeddings.phase8d_ssl_utils. "
            f"Import failed: {exc}"
        ) from exc


@lru_cache(maxsize=2)
def load_ssl_extractor(model_name: str = DEFAULT_MODEL_NAME, device: str = "auto"):
    """Load WavLM once per process (model_name, device) — avoids repeated weight loading."""
    p8d = _import_phase8d()
    dev = p8d.get_device(device)
    model, processor = p8d.load_ssl_model_and_processor(model_name, dev, use_safetensors=True)
    return model, processor, dev


def clear_ssl_extractor_cache() -> None:
    load_ssl_extractor.cache_clear()


def _embedding_to_dict(emb: np.ndarray) -> dict[str, float]:
    emb = np.asarray(emb, dtype=np.float64).reshape(-1)
    if len(emb) != EMBEDDING_DIM:
        # Pad/truncate to expected 768 for column naming consistency.
        fixed = np.full(EMBEDDING_DIM, np.nan, dtype=np.float64)
        n = min(len(emb), EMBEDDING_DIM)
        fixed[:n] = emb[:n]
        emb = fixed
    return {f"ssl_emb_{i:03d}": float(emb[i]) for i in range(EMBEDDING_DIM)}


def extract_file_ssl_embedding(
    y: np.ndarray,
    sr: int,
    model: Any,
    feature_extractor: Any,
    device: Any,
) -> dict[str, float]:
    p8d = _import_phase8d()
    emb = p8d.extract_ssl_embedding(y, sr, feature_extractor, model, device, pooling="mean")
    return _embedding_to_dict(emb)


def extract_segment_ssl_embeddings(
    segments: pd.DataFrame,
    y: np.ndarray,
    sr: int,
    model: Any,
    feature_extractor: Any,
    device: Any,
) -> pd.DataFrame:
    p8d = _import_phase8d()
    rows: list[dict[str, Any]] = []
    for _, seg in segments.iterrows():
        base = seg.to_dict()
        seg_y, err = p8d.slice_audio(y, sr, float(seg["start_sec"]), float(seg["end_sec"]))
        if seg_y is None:
            base.update({f"ssl_emb_{i:03d}": np.nan for i in range(EMBEDDING_DIM)})
            base["ssl_extraction_status"] = err
        else:
            emb = p8d.extract_ssl_embedding(
                seg_y, sr, feature_extractor, model, device, pooling="mean"
            )
            base.update(_embedding_to_dict(emb))
            base["ssl_extraction_status"] = "ok"
        rows.append(base)
    return pd.DataFrame(rows)
