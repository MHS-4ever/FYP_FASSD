"""Shared helpers for Phase 9D-P5C/P5D cascade evaluation (experimental only)."""

from __future__ import annotations

import hashlib
import json
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
        return "load_failure", str(exc), None


def synthetic_segments(duration_sec: float) -> list[tuple[float, float]]:
    if duration_sec <= 0:
        return [(0.0, min(SEGMENT_DURATION_SEC, 0.25))]
    segs: list[tuple[float, float]] = []
    start = 0.0
    while start < duration_sec:
        end = min(start + SEGMENT_DURATION_SEC, duration_sec)
        if end - start >= 0.1:
            segs.append((start, end))
        start += SEGMENT_HOP_SEC
        if len(segs) > 500:
            break
    return segs or [(0.0, min(SEGMENT_DURATION_SEC, duration_sec))]


_SSL_CTX: dict[str, Any] | None = None


def _get_ssl_context() -> dict[str, Any] | None:
    global _SSL_CTX
    if _SSL_CTX is not None:
        return _SSL_CTX
    try:
        from phase8d_ssl_utils import (
            extract_ssl_embedding,
            get_device,
            load_ssl_model_and_processor,
            make_embedding_columns,
        )

        model_name = "microsoft/wavlm-base-plus"
        pooling = "mean"
        device = get_device("auto")
        model, processor = load_ssl_model_and_processor(model_name, device)
        _SSL_CTX = {
            "model": model,
            "processor": processor,
            "device": device,
            "meta": {"pooling": pooling, "model_name": model_name},
            "extract": extract_ssl_embedding,
            "columns": make_embedding_columns,
        }
        return _SSL_CTX
    except Exception:
        return None


def extract_live_feature_tables(
    abs_path: Path,
    *,
    segment_mode: str = "fast",
) -> tuple[pd.DataFrame, pd.DataFrame, str, str]:
    """Return (file_one_row_df, segment_df, error_status, error_message)."""
    from phase8c_feature_utils import (
        empty_feature_dict,
        extract_file_feature_dict,
        extract_segment_feature_dict,
        load_audio_mono,
        safe_audio_slice,
    )

    try:
        y, sr, _feature_source, load_err = load_audio_mono(str(abs_path), TARGET_SR)
    except Exception as exc:
        return pd.DataFrame(), pd.DataFrame(), "load_failure", str(exc)

    if y is None or sr is None:
        return pd.DataFrame(), pd.DataFrame(), "load_failure", load_err or "missing_audio"

    duration = len(y) / float(sr)
    if duration < 0.25:
        return pd.DataFrame(), pd.DataFrame(), "too_short", f"duration_sec={duration:.3f}"

    try:
        file_acoustic = extract_file_feature_dict(y, sr)
    except Exception as exc:
        return pd.DataFrame(), pd.DataFrame(), "feature_extraction_failure", f"acoustic_file: {exc}"

    ssl_ctx = _get_ssl_context()
    file_ssl: dict[str, float] = {}
    if ssl_ctx is None:
        return pd.DataFrame(), pd.DataFrame(), "ssl_embedding_failure", "SSL model unavailable"

    try:
        emb = ssl_ctx["extract"](y, sr, ssl_ctx["processor"], ssl_ctx["model"], ssl_ctx["device"], ssl_ctx["meta"]["pooling"])
        for i, col in enumerate(ssl_ctx["columns"](emb)):
            file_ssl[col] = float(emb[i])
    except Exception as exc:
        return pd.DataFrame(), pd.DataFrame(), "ssl_embedding_failure", str(exc)

    file_row = {**file_acoustic, **file_ssl}
    file_df = pd.DataFrame([file_row])

    seg_defs = synthetic_segments(duration)
    seg_rows: list[dict[str, Any]] = []
    for idx, (start, end) in enumerate(seg_defs):
        seg_audio, slice_err = safe_audio_slice(y, sr, start, end)
        if seg_audio is None:
            continue
        try:
            seg_ac = extract_segment_feature_dict(seg_audio, sr, mode=segment_mode)
        except Exception as exc:
            return file_df, pd.DataFrame(), "feature_extraction_failure", f"segment_acoustic: {exc}"
        try:
            seg_emb = ssl_ctx["extract"](
                seg_audio, sr, ssl_ctx["processor"], ssl_ctx["model"], ssl_ctx["device"], ssl_ctx["meta"]["pooling"]
            )
            seg_ssl = {col: float(seg_emb[i]) for i, col in enumerate(ssl_ctx["columns"](seg_emb))}
        except Exception as exc:
            return file_df, pd.DataFrame(), "ssl_embedding_failure", f"segment_ssl: {exc}"
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
        return file_df, pd.DataFrame(), "too_short", "no segments after slicing"

    seg_df = pd.DataFrame(seg_rows)
    seg_df = compute_live_localization_features(seg_df)
    return file_df, seg_df, "ok", ""


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
) -> tuple[pd.DataFrame, pd.DataFrame, list[dict[str, Any]]]:
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

        if err_status != "ok":
            error_rows.append({**base, "failure_type": err_status})
            file_rows.append({**base, "partial_evidence_positive": False, "file_gate_positive": False})
            continue

        fm = file_master[file_master["_path_norm"] == fp] if not file_master.empty else pd.DataFrame()
        sm = segment_master[segment_master["_path_norm"] == fp] if not segment_master.empty else pd.DataFrame()

        if fm.empty and sm.empty and use_live_extraction:
            try:
                fm, sm, live_st, live_msg = extract_live_feature_tables(abs_path, segment_mode=segment_mode)
                if live_st != "ok":
                    error_rows.append({**base, "failure_type": live_st, "error_message": live_msg})
                    file_rows.append(
                        {
                            **base,
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

        seg_work["segment_probability"] = seg_probs
        seg_work = seg_work.sort_values("segment_probability", ascending=False).reset_index(drop=True)
        seg_work["segment_rank"] = np.arange(1, len(seg_work) + 1)
        seg_work["is_high_segment"] = seg_work["segment_probability"] >= float(thresholds["segment_threshold"])

        cascade = apply_p5c_cascade_rule(
            file_gate_probability=gate_proba,
            segment_probs=seg_probs,
            thresholds=thresholds,
        )
        best_idx = int(np.argmax(seg_probs)) if len(seg_probs) else 0
        cand_start = float(seg_work.iloc[best_idx]["start_sec"])
        cand_end = float(seg_work.iloc[best_idx]["end_sec"])

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
            "error_status": "ok",
            "error_message": "",
            "file_gate_probability": gate_proba,
            **cascade,
            "candidate_segment_start": cand_start,
            "candidate_segment_end": cand_end,
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
                    "segment_index": int(srow["segment_rank"]) - 1,
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

    return pd.DataFrame(file_rows), pd.DataFrame(segment_rows), error_rows


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
