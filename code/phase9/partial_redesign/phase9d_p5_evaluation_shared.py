"""Shared helpers for Phase 9D-P5C/P5D cascade evaluation (experimental only)."""

from __future__ import annotations

import hashlib
import json
import gc
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from phase9d_p5_partial_utils import (
    compute_live_localization_features,
    normalize_path_str,
    path_basename,
    path_stem_lower,
    segment_overlap_metrics,
)
from phase9d_p5_training_utils import (
    P5C_ACCEPTED_CASCADE_THRESHOLDS,
    P5D_RUN_STATUS_FILENAME,
    P5D_TIMESTAMP_OVERLAP_THRESHOLD,
    apply_p5c_cascade_rule,
    now_utc_str,
    predict_candidate_proba,
)

AUDIO_EXTENSIONS = {".wav", ".flac", ".mp3", ".ogg", ".m4a", ".mp4"}
SEGMENT_DURATION_SEC = 4.0
SEGMENT_HOP_SEC = 2.0
TARGET_SR = 16000
CPU_SSL_FALLBACK_MAX_SEC = 45.0

_CODE_ROOT = Path(__file__).resolve().parents[2]


def compute_candidate_timestamp_error_seconds(
    timestamp_start: float,
    timestamp_end: float,
    candidate_segment_start: float,
    candidate_segment_end: float,
) -> float | None:
    """Center-to-center absolute error in seconds; None if boundaries are not finite."""
    bounds = (timestamp_start, timestamp_end, candidate_segment_start, candidate_segment_end)
    if not all(np.isfinite(float(b)) for b in bounds):
        return None
    known_center = (float(timestamp_start) + float(timestamp_end)) / 2.0
    candidate_center = (float(candidate_segment_start) + float(candidate_segment_end)) / 2.0
    return abs(candidate_center - known_center)
_PHASE8_FEATURES = _CODE_ROOT / "phase8" / "features"
_PHASE8_EMB = _CODE_ROOT / "phase8" / "embeddings"
for _p in (_PHASE8_FEATURES, _PHASE8_EMB):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))


def rel_path(path: Path, root: Path) -> str:
    try:
        return normalize_path_str(str(path.resolve().relative_to(root.resolve())))
    except ValueError:
        return normalize_path_str(str(path.resolve()))


def cheap_file_hash(path: Path, max_bytes: int = 65536) -> str:
    h = hashlib.sha256()
    try:
        with path.open("rb") as f:
            h.update(f.read(max_bytes))
        return h.hexdigest()[:16]
    except OSError:
        return ""


def _classify_audio_load_failure(path: Path, err: str) -> tuple[str, str]:
    low = str(err or "").lower()
    ext = path.suffix.lower()
    if "no audio" in low or "audio stream" in low:
        return "no_audio_stream", "no_audio_stream"
    if ext in {".mp4", ".m4a"} and any(
        k in low for k in ("format not recognised", "unsupported", "decoder", "audioread", "ffmpeg")
    ):
        return "unsupported_container_or_decoder_missing", "unsupported_container_or_decoder_missing"
    if "silent" in low:
        return "silent_or_invalid", "silent_or_invalid"
    return "load_failure", "load_failure"


def load_audio_probe(path: Path) -> tuple[str, str, float | None]:
    try:
        import soundfile as sf
    except ImportError:
        return "ok", "", None
    try:
        info = sf.info(str(path))
        dur = float(info.duration)
        if dur < 0.25:
            return "too_short", f"duration_sec={dur:.3f}", dur
        return "ok", "", dur
    except Exception as exc:
        # Probe fallback: attempt lightweight duration lookup via librosa/torchaudio.
        try:
            import librosa  # type: ignore

            dur = float(librosa.get_duration(path=str(path)))
            if dur < 0.25:
                return "too_short", f"duration_sec={dur:.3f}", dur
            return "ok", "", dur
        except Exception:
            pass
        try:
            import torchaudio  # type: ignore

            info = torchaudio.info(str(path))
            sr = float(getattr(info, "sample_rate", 0) or 0)
            nf = float(getattr(info, "num_frames", 0) or 0)
            if sr > 0 and nf > 0:
                dur = nf / sr
                if dur < 0.25:
                    return "too_short", f"duration_sec={dur:.3f}", dur
                return "ok", "", dur
        except Exception:
            pass
        st, _ = _classify_audio_load_failure(path, str(exc))
        return st, str(exc), None


def synthetic_segments(duration_sec: float, max_segments_per_file: int = 500) -> list[tuple[float, float]]:
    if duration_sec <= 0:
        return [(0.0, min(SEGMENT_DURATION_SEC, 0.25))]
    segs: list[tuple[float, float]] = []
    start = 0.0
    while start < duration_sec:
        end = min(start + SEGMENT_DURATION_SEC, duration_sec)
        if end - start >= 0.1:
            segs.append((start, end))
        start += SEGMENT_HOP_SEC
        if len(segs) >= max_segments_per_file:
            break
    return segs or [(0.0, min(SEGMENT_DURATION_SEC, duration_sec))]


_SSL_CTX: dict[str, dict[str, Any]] = {}


def _get_ssl_context(device_pref: str = "auto") -> dict[str, Any] | None:
    global _SSL_CTX
    if device_pref in _SSL_CTX:
        return _SSL_CTX[device_pref]
    try:
        from phase8d_ssl_utils import (
            extract_ssl_embedding,
            get_device,
            load_ssl_model_and_processor,
            make_embedding_columns,
        )

        model_name = "microsoft/wavlm-base-plus"
        pooling = "mean"
        device = get_device(device_pref)
        model, processor = load_ssl_model_and_processor(model_name, device)
        _SSL_CTX[device_pref] = {
            "model": model,
            "processor": processor,
            "device": device,
            "meta": {"pooling": pooling, "model_name": model_name},
            "extract": extract_ssl_embedding,
            "columns": make_embedding_columns,
        }
        return _SSL_CTX[device_pref]
    except Exception:
        return None


def _is_cuda_oom(exc: Exception) -> bool:
    msg = str(exc).lower()
    return "out of memory" in msg and "cuda" in msg


def _cleanup_torch_memory() -> None:
    try:
        import torch  # type: ignore

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass
    gc.collect()


def _inc_stat(stats: dict[str, int], key: str, amount: int = 1) -> None:
    stats[key] = int(stats.get(key, 0)) + int(amount)


def _ssl_chunk_starts(total_samples: int, chunk_samples: int, hop_samples: int, max_chunks: int) -> list[int]:
    if total_samples <= 0 or chunk_samples < 1 or hop_samples < 1:
        return []
    starts: list[int] = []
    pos = 0
    while pos < total_samples and len(starts) < max_chunks:
        starts.append(pos)
        pos += hop_samples
    return starts


def extract_ssl_embedding_chunked_robust(
    y: np.ndarray,
    sr: int,
    *,
    ssl_device: str,
    disable_ssl_cpu_fallback: bool,
    robustness_stats: dict[str, int],
    chunk_sec: float = 30.0,
    hop_sec: float | None = None,
    max_chunks: int = 200,
    prefer_cpu: bool = False,
) -> tuple[np.ndarray | None, str, str]:
    """Duration-weighted mean of per-chunk SSL embeddings (no temp files)."""
    if len(y) == 0:
        return None, "ssl_embedding_failure", "empty audio"
    if sr <= 0:
        return None, "ssl_embedding_failure", f"invalid sample rate {sr}"

    if hop_sec is None or hop_sec <= 0:
        hop_sec = chunk_sec
    chunk_samples = max(1, int(round(chunk_sec * sr)))
    hop_samples = max(1, int(round(hop_sec * sr)))
    min_chunk_samples = max(1, int(0.5 * sr))
    starts = _ssl_chunk_starts(len(y), chunk_samples, hop_samples, max_chunks)
    if not starts:
        return None, "ssl_embedding_failure", "no SSL chunks scheduled"

    devices: list[str] = []
    if prefer_cpu:
        devices.append("cpu")
    else:
        devices.append(ssl_device)
        if not disable_ssl_cpu_fallback and ssl_device != "cpu":
            devices.append("cpu")

    last_err = "no valid SSL chunks extracted"
    for device_name in devices:
        if disable_ssl_cpu_fallback and device_name == "cpu":
            continue
        ctx = _get_ssl_context(device_name)
        if ctx is None:
            last_err = f"SSL model unavailable on {device_name}"
            continue
        emb_chunks: list[np.ndarray] = []
        weights: list[float] = []
        def _run_chunks() -> None:
            for start in starts:
                end = min(start + chunk_samples, len(y))
                chunk = y[start:end]
                if len(chunk) < min_chunk_samples:
                    continue
                emb = ctx["extract"](
                    chunk,
                    sr,
                    ctx["processor"],
                    ctx["model"],
                    ctx["device"],
                    ctx["meta"]["pooling"],
                )
                emb_chunks.append(np.asarray(emb, dtype=np.float32))
                weights.append(float(len(chunk) / sr))
                _cleanup_torch_memory()

        try:
            try:
                import torch  # type: ignore

                with torch.inference_mode():
                    _run_chunks()
            except Exception:
                _run_chunks()
            if emb_chunks:
                _inc_stat(robustness_stats, "ssl_chunked_embedding_max_chunks_observed", len(emb_chunks))
                stacked = np.stack(emb_chunks, axis=0)
                w = np.asarray(weights, dtype=np.float32)
                if float(w.sum()) <= 0:
                    last_err = "zero total weight in chunk aggregation"
                    continue
                emb = np.average(stacked, axis=0, weights=w)
                _inc_stat(robustness_stats, "ssl_chunked_embedding_used_count")
                return emb.astype(np.float32), "", ""
        except Exception as exc:
            last_err = str(exc)
            _cleanup_torch_memory()
            continue

    return None, "ssl_embedding_failure", last_err


def _try_chunked_ssl_fallback(
    y: np.ndarray,
    sr: int,
    *,
    ssl_device: str,
    disable_ssl_cpu_fallback: bool,
    disable_ssl_chunked_fallback: bool,
    robustness_stats: dict[str, int],
    chunk_sec: float,
    hop_sec: float | None,
    max_chunks: int,
    prefer_cpu: bool,
    after_cuda_oom: bool,
    long_audio_sec: float = 60.0,
) -> tuple[np.ndarray | None, str, str, str]:
    """Return (emb, extraction_mode, failure_type, message)."""
    if disable_ssl_chunked_fallback:
        return None, "", "ssl_chunked_fallback_failed", "chunked SSL fallback disabled"

    _inc_stat(robustness_stats, "ssl_chunked_fallback_attempt_count")
    duration_sec = len(y) / float(max(sr, 1))
    if duration_sec >= long_audio_sec:
        _inc_stat(robustness_stats, "ssl_long_audio_file_count")

    modes_to_try: list[tuple[str, bool]] = []
    if prefer_cpu or after_cuda_oom:
        modes_to_try.append(("chunked_cpu_fallback", True))
        if not prefer_cpu and ssl_device != "cpu":
            modes_to_try.append(("chunked_cuda_fallback", False))
    else:
        modes_to_try.append(("chunked_cuda_fallback", False))
        if not disable_ssl_cpu_fallback:
            modes_to_try.append(("chunked_cpu_fallback", True))

    last_msg = "chunked SSL fallback failed"
    for mode_name, use_cpu in modes_to_try:
        if use_cpu:
            _inc_stat(robustness_stats, "ssl_chunked_cpu_fallback_attempt_count")
        emb, _ft, msg = extract_ssl_embedding_chunked_robust(
            y,
            sr,
            ssl_device="cpu" if use_cpu else ssl_device,
            disable_ssl_cpu_fallback=disable_ssl_cpu_fallback,
            robustness_stats=robustness_stats,
            chunk_sec=chunk_sec,
            hop_sec=hop_sec,
            max_chunks=max_chunks,
            prefer_cpu=use_cpu,
        )
        if emb is not None:
            _inc_stat(robustness_stats, "ssl_chunked_fallback_success_count")
            if use_cpu:
                _inc_stat(robustness_stats, "ssl_chunked_cpu_fallback_success_count")
            if after_cuda_oom and duration_sec >= long_audio_sec:
                _inc_stat(robustness_stats, "ssl_long_audio_recovered_count")
            return emb, mode_name, "", ""
        last_msg = msg or last_msg
        if use_cpu:
            _inc_stat(robustness_stats, "ssl_chunked_cpu_fallback_failure_count")

    _inc_stat(robustness_stats, "ssl_chunked_fallback_failure_count")
    if duration_sec >= long_audio_sec:
        _inc_stat(robustness_stats, "ssl_long_audio_failed_count")
    return None, "", "ssl_chunked_fallback_failed", last_msg


def _extract_ssl_embedding_robust(
    y: np.ndarray,
    sr: int,
    *,
    ssl_device: str,
    disable_ssl_cpu_fallback: bool,
    disable_ssl_chunked_fallback: bool = False,
    robustness_stats: dict[str, int],
    chunk_sec: float = 30.0,
    hop_sec: float | None = None,
    max_chunks: int = 200,
    prefer_cpu: bool = False,
    long_audio_sec: float = 60.0,
    prefer_cpu_for_long_audio: bool = False,
) -> tuple[np.ndarray | None, str, str, str]:
    """Return (embedding, extraction_mode, failure_type, message). failure_type empty on success."""
    duration_sec = len(y) / float(max(sr, 1))
    cuda_oom_seen = False

    if prefer_cpu_for_long_audio and duration_sec >= long_audio_sec and not disable_ssl_chunked_fallback:
        emb, mode, fail_type, fail_msg = _try_chunked_ssl_fallback(
            y,
            sr,
            ssl_device=ssl_device,
            disable_ssl_cpu_fallback=disable_ssl_cpu_fallback,
            disable_ssl_chunked_fallback=disable_ssl_chunked_fallback,
            robustness_stats=robustness_stats,
            chunk_sec=chunk_sec,
            hop_sec=hop_sec,
            max_chunks=max_chunks,
            prefer_cpu=True,
            after_cuda_oom=False,
            long_audio_sec=long_audio_sec,
        )
        if emb is not None:
            return emb, mode or "chunked_cpu_fallback", "", ""

    primary = _get_ssl_context(ssl_device)
    if primary is None:
        return None, "", "ssl_embedding_failure", "SSL model unavailable"
    try:
        emb = primary["extract"](
            y, sr, primary["processor"], primary["model"], primary["device"], primary["meta"]["pooling"]
        )
        return emb, "normal", "", ""
    except Exception as exc:
        if not _is_cuda_oom(exc):
            return None, "", "ssl_embedding_failure", str(exc)

        cuda_oom_seen = True
        _inc_stat(robustness_stats, "ssl_cuda_oom_count")
        _cleanup_torch_memory()

        if disable_ssl_cpu_fallback and disable_ssl_chunked_fallback:
            return None, "", "ssl_cuda_oom", str(exc)

        if not disable_ssl_cpu_fallback and ssl_device != "cpu" and duration_sec <= CPU_SSL_FALLBACK_MAX_SEC:
            _inc_stat(robustness_stats, "ssl_cpu_fallback_attempt_count")
            cpu_ctx = _get_ssl_context("cpu")
            if cpu_ctx is None:
                _inc_stat(robustness_stats, "ssl_cpu_fallback_failure_count")
            else:
                try:
                    if "cpu" not in str(cpu_ctx.get("device", "")).lower():
                        raise RuntimeError(f"CPU fallback context device is not CPU: {cpu_ctx.get('device')}")
                    emb = cpu_ctx["extract"](
                        y,
                        sr,
                        cpu_ctx["processor"],
                        cpu_ctx["model"],
                        cpu_ctx["device"],
                        cpu_ctx["meta"]["pooling"],
                    )
                    _inc_stat(robustness_stats, "ssl_cpu_fallback_success_count")
                    return emb, "cpu_fallback", "", ""
                except Exception as cpu_exc:
                    _inc_stat(robustness_stats, "ssl_cpu_fallback_failure_count")
                    if not _is_cuda_oom(cpu_exc):
                        last_cpu_msg = str(cpu_exc)
                    else:
                        last_cpu_msg = str(cpu_exc)
                    _cleanup_torch_memory()
                    emb, mode, fail_type, fail_msg = _try_chunked_ssl_fallback(
                        y,
                        sr,
                        ssl_device=ssl_device,
                        disable_ssl_cpu_fallback=disable_ssl_cpu_fallback,
                        disable_ssl_chunked_fallback=disable_ssl_chunked_fallback,
                        robustness_stats=robustness_stats,
                        chunk_sec=chunk_sec,
                        hop_sec=hop_sec,
                        max_chunks=max_chunks,
                        prefer_cpu=True,
                        after_cuda_oom=True,
                        long_audio_sec=long_audio_sec,
                    )
                    if emb is not None:
                        return emb, mode, "", ""
                    return None, "", fail_type or "ssl_chunked_fallback_failed", fail_msg or last_cpu_msg

        if duration_sec > CPU_SSL_FALLBACK_MAX_SEC:
            _inc_stat(robustness_stats, "ssl_cpu_fallback_skipped_long_audio_count")

        emb, mode, fail_type, fail_msg = _try_chunked_ssl_fallback(
            y,
            sr,
            ssl_device=ssl_device,
            disable_ssl_cpu_fallback=disable_ssl_cpu_fallback,
            disable_ssl_chunked_fallback=disable_ssl_chunked_fallback,
            robustness_stats=robustness_stats,
            chunk_sec=chunk_sec,
            hop_sec=hop_sec,
            max_chunks=max_chunks,
            prefer_cpu=cuda_oom_seen,
            after_cuda_oom=True,
            long_audio_sec=long_audio_sec,
        )
        if emb is not None:
            return emb, mode, "", ""
        return None, "", fail_type or "ssl_chunked_fallback_failed", fail_msg or str(exc)


def extract_live_feature_tables(
    abs_path: Path,
    *,
    segment_mode: str = "fast",
    ssl_device: str = "auto",
    disable_ssl_cpu_fallback: bool = False,
    disable_ssl_chunked_fallback: bool = False,
    ssl_chunk_sec: float = 30.0,
    ssl_chunk_hop_sec: float | None = None,
    ssl_chunk_max_chunks: int = 200,
    prefer_cpu_for_long_audio: bool = False,
    long_audio_sec: float = 60.0,
    max_audio_duration_sec: float | None = None,
    max_segments_per_file: int = 500,
    robustness_stats: dict[str, int] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, str, str, dict[str, Any]]:
    """Return (file_one_row_df, segment_df, error_status, error_message, ssl_meta)."""
    from phase8c_feature_utils import (
        empty_feature_dict,
        extract_file_feature_dict,
        extract_segment_feature_dict,
        load_audio_mono,
        safe_audio_slice,
    )

    if robustness_stats is None:
        robustness_stats = {}
    ssl_meta: dict[str, Any] = {
        "ssl_extraction_mode": "",
        "ssl_chunked_fallback_used": False,
        "ssl_cpu_fallback_used": False,
        "ssl_cuda_oom_recovered": False,
        "audio_duration_sec": np.nan,
    }
    try:
        y, sr, _feature_source, load_err = load_audio_mono(str(abs_path), TARGET_SR)
    except Exception as exc:
        st, _ = _classify_audio_load_failure(abs_path, str(exc))
        return pd.DataFrame(), pd.DataFrame(), st, str(exc), ssl_meta

    if y is None or sr is None:
        st, _ = _classify_audio_load_failure(abs_path, load_err or "missing_audio")
        return pd.DataFrame(), pd.DataFrame(), st, load_err or "missing_audio", ssl_meta

    duration = len(y) / float(sr)
    ssl_meta["audio_duration_sec"] = float(duration)
    if max_audio_duration_sec is not None and np.isfinite(max_audio_duration_sec) and duration > max_audio_duration_sec:
        y = y[: int(max_audio_duration_sec * sr)]
        duration = len(y) / float(sr)
        ssl_meta["audio_duration_sec"] = float(duration)
    if duration < 0.25:
        return pd.DataFrame(), pd.DataFrame(), "too_short", f"duration_sec={duration:.3f}", ssl_meta

    try:
        file_acoustic = extract_file_feature_dict(y, sr)
    except Exception as exc:
        return pd.DataFrame(), pd.DataFrame(), "feature_extraction_failure", f"acoustic_file: {exc}", ssl_meta

    oom_before = int(robustness_stats.get("ssl_cuda_oom_count", 0))
    file_ssl: dict[str, float] = {}
    emb, extraction_mode, fail_type, fail_msg = _extract_ssl_embedding_robust(
        y,
        sr,
        ssl_device=ssl_device,
        disable_ssl_cpu_fallback=disable_ssl_cpu_fallback,
        disable_ssl_chunked_fallback=disable_ssl_chunked_fallback,
        robustness_stats=robustness_stats,
        chunk_sec=ssl_chunk_sec,
        hop_sec=ssl_chunk_hop_sec,
        max_chunks=ssl_chunk_max_chunks,
        prefer_cpu_for_long_audio=prefer_cpu_for_long_audio,
        long_audio_sec=long_audio_sec,
    )
    if emb is None:
        return pd.DataFrame(), pd.DataFrame(), fail_type or "ssl_embedding_failure", fail_msg or "SSL failure", ssl_meta
    ssl_meta["ssl_extraction_mode"] = extraction_mode or "normal"
    ssl_meta["ssl_chunked_fallback_used"] = extraction_mode.startswith("chunked_")
    ssl_meta["ssl_cpu_fallback_used"] = extraction_mode in ("cpu_fallback", "chunked_cpu_fallback")
    ssl_meta["ssl_cuda_oom_recovered"] = int(robustness_stats.get("ssl_cuda_oom_count", 0)) > oom_before and (
        extraction_mode in ("cpu_fallback", "chunked_cpu_fallback", "chunked_cuda_fallback")
    )
    cols = [f"ssl_emb_{i:03d}" for i in range(len(emb))]
    for i, col in enumerate(cols):
        file_ssl[col] = float(emb[i])

    file_row = {**file_acoustic, **file_ssl}
    file_df = pd.DataFrame([file_row])

    seg_defs = synthetic_segments(duration, max_segments_per_file=max_segments_per_file)
    seg_rows: list[dict[str, Any]] = []
    for idx, (start, end) in enumerate(seg_defs):
        seg_audio, slice_err = safe_audio_slice(y, sr, start, end)
        if seg_audio is None:
            continue
        try:
            seg_ac = extract_segment_feature_dict(seg_audio, sr, mode=segment_mode)
        except Exception as exc:
            return file_df, pd.DataFrame(), "feature_extraction_failure", f"segment_acoustic: {exc}", ssl_meta
        seg_emb, _seg_mode, seg_fail_type, seg_fail_msg = _extract_ssl_embedding_robust(
            seg_audio,
            sr,
            ssl_device=ssl_device,
            disable_ssl_cpu_fallback=disable_ssl_cpu_fallback,
            disable_ssl_chunked_fallback=disable_ssl_chunked_fallback,
            robustness_stats=robustness_stats,
            chunk_sec=ssl_chunk_sec,
            hop_sec=ssl_chunk_hop_sec,
            max_chunks=ssl_chunk_max_chunks,
            long_audio_sec=long_audio_sec,
        )
        if seg_emb is None:
            return (
                file_df,
                pd.DataFrame(),
                seg_fail_type or "ssl_embedding_failure",
                f"segment_ssl: {seg_fail_msg}",
                ssl_meta,
            )
        seg_ssl = {f"ssl_emb_{i:03d}": float(seg_emb[i]) for i in range(len(seg_emb))}
        seg_rows.append(
            {
                "segment_id": f"live_{idx:04d}",
                "start_sec": start,
                "end_sec": end,
                "segment_duration_sec": end - start,
                **seg_ac,
                **seg_ssl,
            }
        )

    if not seg_rows:
        return file_df, pd.DataFrame(), "too_short", "no segments after slicing", ssl_meta

    seg_df = pd.DataFrame(seg_rows)
    seg_df = compute_live_localization_features(seg_df)
    return file_df, seg_df, "ok", "", ssl_meta


def evaluate_manifest_cascade(
    manifest: pd.DataFrame,
    overlap_df: pd.DataFrame,
    *,
    file_master: pd.DataFrame,
    segment_master: pd.DataFrame,
    artifacts: dict[str, Any],
    root: Path,
    show: bool,
    progress_fn: Any,
    use_live_extraction: bool = True,
    segment_mode: str = "fast",
    ssl_device: str = "auto",
    disable_ssl_cpu_fallback: bool = False,
    disable_ssl_chunked_fallback: bool = False,
    ssl_chunk_sec: float = 30.0,
    ssl_chunk_hop_sec: float | None = None,
    ssl_chunk_max_chunks: int = 200,
    prefer_cpu_for_long_audio: bool = False,
    long_audio_sec: float = 60.0,
    max_audio_duration_sec: float | None = None,
    max_segments_per_file: int = 500,
) -> tuple[pd.DataFrame, pd.DataFrame, list[dict[str, Any]], dict[str, int]]:
    thresholds = artifacts.get("thresholds", P5C_ACCEPTED_CASCADE_THRESHOLDS)
    fg_bundle = artifacts["file_gate_bundle"]
    sg_bundle = artifacts["segment_bundle"]

    if not file_master.empty:
        file_master = file_master.copy()
        file_master["_path_norm"] = file_master["audio_path"].map(normalize_path_str)
    if not segment_master.empty:
        segment_master = segment_master.copy()
        segment_master["_path_norm"] = segment_master["audio_path"].map(normalize_path_str)

    overlap_map = dict(zip(overlap_df["file_path"], overlap_df["overlap_status"]))
    file_rows: list[dict[str, Any]] = []
    segment_rows: list[dict[str, Any]] = []
    error_rows: list[dict[str, Any]] = []

    robustness_stats: dict[str, int] = {}
    for i, m in enumerate(manifest.itertuples(index=False), start=1):
        fp = normalize_path_str(m.file_path)
        abs_path = root / fp
        split_status = overlap_map.get(fp, getattr(m, "source_split_status", "unknown_overlap_status"))
        err_status, err_msg, dur = load_audio_probe(abs_path)

        mdict = m._asdict() if hasattr(m, "_asdict") else {c: getattr(m, c, "") for c in manifest.columns}
        base = {**mdict}
        base["file_path"] = fp
        base["source_split_status"] = split_status
        base["error_status"] = err_status
        base["error_message"] = err_msg
        if dur is not None and np.isfinite(dur):
            base["audio_duration_sec"] = float(dur)

        live_ssl_fields: dict[str, Any] = {}

        if err_status != "ok":
            error_rows.append({**base, "failure_type": err_status})
            file_rows.append({**base, "partial_evidence_positive": False, "file_gate_positive": False})
            continue

        fm = file_master[file_master["_path_norm"] == fp] if not file_master.empty else pd.DataFrame()
        sm = segment_master[segment_master["_path_norm"] == fp] if not segment_master.empty else pd.DataFrame()

        if fm.empty and sm.empty and use_live_extraction:
            try:
                fm, sm, live_st, live_msg, ssl_meta = extract_live_feature_tables(
                    abs_path,
                    segment_mode=segment_mode,
                    ssl_device=ssl_device,
                    disable_ssl_cpu_fallback=disable_ssl_cpu_fallback,
                    disable_ssl_chunked_fallback=disable_ssl_chunked_fallback,
                    ssl_chunk_sec=ssl_chunk_sec,
                    ssl_chunk_hop_sec=ssl_chunk_hop_sec,
                    ssl_chunk_max_chunks=ssl_chunk_max_chunks,
                    prefer_cpu_for_long_audio=prefer_cpu_for_long_audio,
                    long_audio_sec=long_audio_sec,
                    max_audio_duration_sec=max_audio_duration_sec,
                    max_segments_per_file=max_segments_per_file,
                    robustness_stats=robustness_stats,
                )
                live_ssl_fields = {
                    "ssl_extraction_mode": ssl_meta.get("ssl_extraction_mode", ""),
                    "ssl_chunked_fallback_used": bool(ssl_meta.get("ssl_chunked_fallback_used", False)),
                    "ssl_cpu_fallback_used": bool(ssl_meta.get("ssl_cpu_fallback_used", False)),
                    "ssl_cuda_oom_recovered": bool(ssl_meta.get("ssl_cuda_oom_recovered", False)),
                    "audio_duration_sec": ssl_meta.get("audio_duration_sec", np.nan),
                }
                if live_st != "ok":
                    error_rows.append({**base, "failure_type": live_st, "error_message": live_msg})
                    file_rows.append(
                        {
                            **base,
                            **live_ssl_fields,
                            "error_status": live_st,
                            "error_message": live_msg,
                            "partial_evidence_positive": False,
                            "file_gate_positive": False,
                        }
                    )
                    continue
            except Exception as exc:
                error_rows.append({**base, "failure_type": "feature_extraction_failure", "error_message": str(exc)})
                file_rows.append({**base, "partial_evidence_positive": False})
                continue
        elif fm.empty:
            error_rows.append({**base, "failure_type": "missing_file_features"})
            file_rows.append({**base, "partial_evidence_positive": False})
            continue

        if sm.empty:
            error_rows.append({**base, "failure_type": "missing_segment_features"})
            file_rows.append({**base, "file_gate_probability": np.nan, "partial_evidence_positive": False})
            continue

        try:
            gate_proba = float(predict_candidate_proba(fg_bundle, fm)[0])
        except Exception as exc:
            error_rows.append({**base, "failure_type": "file_gate_predict_failure", "error_message": str(exc)})
            file_rows.append({**base, "partial_evidence_positive": False})
            continue

        seg_work = sm.copy()
        if "segment_id" not in seg_work.columns:
            seg_work["segment_id"] = [f"{path_stem_lower(fp)}_{j:04d}" for j in range(len(seg_work))]
        if "start_sec" not in seg_work.columns:
            error_rows.append({**base, "failure_type": "missing_segment_times"})
            file_rows.append({**base, "partial_evidence_positive": False})
            continue

        if "acoustic_distance_from_file_median" not in seg_work.columns:
            seg_work = compute_live_localization_features(seg_work)

        try:
            seg_probs = predict_candidate_proba(sg_bundle, seg_work)
        except Exception as exc:
            error_rows.append({**base, "failure_type": "segment_predict_failure", "error_message": str(exc)})
            file_rows.append({**base, "partial_evidence_positive": False})
            continue

        seg_work["segment_index_chronological"] = (
            seg_work["start_sec"].rank(method="first").astype(int) - 1
        )
        seg_work["segment_probability"] = seg_probs
        seg_work = seg_work.sort_values("segment_probability", ascending=False).reset_index(drop=True)
        seg_work["segment_rank"] = np.arange(1, len(seg_work) + 1)
        seg_work["is_high_segment"] = seg_work["segment_probability"] >= float(thresholds["segment_threshold"])

        cascade = apply_p5c_cascade_rule(
            file_gate_probability=gate_proba,
            segment_probs=seg_probs,
            thresholds=thresholds,
        )
        best_row = seg_work.iloc[0]
        cand_start = float(best_row["start_sec"])
        cand_end = float(best_row["end_sec"])
        cand_prob = float(best_row["segment_probability"])
        cand_rank = int(best_row["segment_rank"])

        has_ts = bool(getattr(m, "has_timestamp_label", False))
        ts_start = pd.to_numeric(getattr(m, "timestamp_start", np.nan), errors="coerce")
        ts_end = pd.to_numeric(getattr(m, "timestamp_end", np.nan), errors="coerce")
        top1 = top3 = top5 = False
        if has_ts and np.isfinite(ts_start) and np.isfinite(ts_end):
            ranked = seg_work.sort_values("segment_probability", ascending=False)
            for k in (1, 3, 5):
                head = ranked.head(k)
                hit = False
                for _, srow in head.iterrows():
                    ov = segment_overlap_metrics(
                        float(srow["start_sec"]),
                        float(srow["end_sec"]),
                        float(ts_start),
                        float(ts_end),
                        P5D_TIMESTAMP_OVERLAP_THRESHOLD,
                    )
                    if ov.get("timestamp_region_label") == "inside_fabricated_region":
                        hit = True
                        break
                if k == 1:
                    top1 = hit
                elif k == 3:
                    top3 = hit
                else:
                    top5 = hit

        cand_ts_error = None
        if has_ts:
            cand_ts_error = compute_candidate_timestamp_error_seconds(
                float(ts_start),
                float(ts_end),
                cand_start,
                cand_end,
            )

        out_row = {
            **base,
            **live_ssl_fields,
            "error_status": "ok",
            "error_message": "",
            "file_gate_probability": gate_proba,
            **cascade,
            "candidate_segment_start": cand_start,
            "candidate_segment_end": cand_end,
            "candidate_segment_probability": cand_prob,
            "candidate_segment_rank": cand_rank,
            "has_timestamp_label": has_ts,
            "candidate_timestamp_error_seconds": cand_ts_error if cand_ts_error is not None else np.nan,
            "top1_timestamp_hit": top1,
            "top3_timestamp_hit": top3,
            "top5_timestamp_hit": top5,
        }
        file_rows.append(out_row)

        for _, srow in seg_work.iterrows():
            ov_known = False
            if has_ts and np.isfinite(ts_start) and np.isfinite(ts_end):
                ov = segment_overlap_metrics(
                    float(srow["start_sec"]),
                    float(srow["end_sec"]),
                    float(ts_start),
                    float(ts_end),
                    P5D_TIMESTAMP_OVERLAP_THRESHOLD,
                )
                ov_known = ov.get("timestamp_region_label") == "inside_fabricated_region"
            seg_file_name = str(mdict.get("file_name", path_basename(fp)))
            segment_rows.append(
                {
                    "file_path": fp,
                    "file_name": seg_file_name,
                    "segment_index": int(srow["segment_index_chronological"]),
                    "segment_index_chronological": int(srow["segment_index_chronological"]),
                    "segment_start": float(srow["start_sec"]),
                    "segment_end": float(srow["end_sec"]),
                    "segment_probability": float(srow["segment_probability"]),
                    "segment_rank": int(srow["segment_rank"]),
                    "is_high_segment": bool(srow["is_high_segment"]),
                    "overlaps_known_fabricated_timestamp": ov_known,
                    "expected_segment_label": int(ov_known),
                }
            )

        if show and progress_fn and i % 10 == 0:
            progress_fn(f"Evaluated {i}/{len(manifest)} files...")

    return pd.DataFrame(file_rows), pd.DataFrame(segment_rows), error_rows, robustness_stats


def p5d_run_status_path(out_dir: Path) -> Path:
    return out_dir / P5D_RUN_STATUS_FILENAME


def write_p5d_run_status(out_dir: Path, payload: dict[str, Any]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    p5d_run_status_path(out_dir).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def init_p5d_run_status(out_dir: Path, input_root: Path) -> dict[str, Any]:
    payload = {
        "phase": "Phase 9D-P5D",
        "run_started_at": now_utc_str(),
        "run_completed_at": "",
        "status": "running",
        "input_root": str(input_root),
        "error_message": "",
        "traceback_summary": "",
        "output_generation_complete": False,
    }
    write_p5d_run_status(out_dir, payload)
    return payload


def parse_p5d_run_timestamp(ts: str) -> datetime | None:
    if not ts or not str(ts).strip():
        return None
    text = str(ts).strip().replace(" UTC", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        pass
    try:
        base = text.replace("+00:00", "").strip()
        return datetime.strptime(base, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def outputs_newer_than_run_start(out_dir: Path, run_started_at: str) -> tuple[bool, str]:
    """Return (ok, detail) — required outputs must be newer than run_started_at."""
    started = parse_p5d_run_timestamp(run_started_at)
    if started is None:
        return False, "run_started_at unparseable"
    required = [
        "phase9d_p5d_independent_evaluation_report.md",
        "phase9d_p5d_independent_metrics.json",
        "phase9d_p5d_file_predictions.csv",
        "phase9d_p5d_segment_predictions.csv",
        P5D_RUN_STATUS_FILENAME,
    ]
    stale: list[str] = []
    for name in required:
        path = out_dir / name
        if not path.is_file():
            stale.append(f"missing:{name}")
            continue
        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        if mtime < started:
            stale.append(f"stale:{name}")
    if stale:
        return False, ", ".join(stale)
    return True, "outputs refreshed after run_started_at"
