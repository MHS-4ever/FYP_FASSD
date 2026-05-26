"""
Phase 7C3: Build HDF5 feature cache from Phase 7C2 training manifests.

Uses same log-mel / environmental extraction as Phase 6 inference (checkpoint-compatible).
Partial-fabrication rows use a 4s window centered on the suspicious region (not first 4s).
Does not train models.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import h5py
import librosa
import numpy as np
import pandas as pd
from tqdm import tqdm

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "code"))

from features.environmental_features import EnvironmentalFeatureExtractor
from phase6.explain_prediction import extract_env_features, extract_logmel

SAMPLE_RATE = 16000
CHUNK_SECONDS = 4.0
CHUNK_SAMPLES = int(SAMPLE_RATE * CHUNK_SECONDS)
ORIGIN_IGNORE = -1
ATTACK_IGNORE = -1

# Per-row float32 feature size estimate (logmel + env + metadata scalars)
BYTES_PER_ROW_EST = 64 * 400 * 4 + 12 * 4 + 64

ATTACK_HINT_TO_TARGET = {
    "bonafide": 0,
    "synthesis": 1,
    "voice_conversion": 2,
    "conversion": 2,
    "replay": 3,
    "unknown": ATTACK_IGNORE,
}

ORIGIN_BINARY_TO_TARGET = {
    "human": 0,
    "ai": 1,
    "mixed": 1,
    "unknown": ORIGIN_IGNORE,
}


def _safe_str(val) -> str:
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return ""
    return str(val).strip()


def _to_float(val, default=None):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return default
    s = _safe_str(val)
    if s == "":
        return default
    try:
        return float(s)
    except ValueError:
        return default


def _parse_bool(val) -> bool:
    s = _safe_str(val).lower()
    return s in {"true", "1", "yes", "y"}


def _resolve_audio(path_str: str, repo_root: Path) -> Path:
    p = Path(path_str)
    if p.is_file():
        return p.resolve()
    c = (repo_root / path_str).resolve()
    if c.is_file():
        return c
    return p.resolve()


def is_partial_fabrication_row(row: pd.Series) -> bool:
    if _parse_bool(row.get("partial_fabrication_binary")):
        return True
    return _safe_str(row.get("manipulation_type")).lower() == "partial_ai_insert"


def has_valid_partial_timestamps(row: pd.Series) -> bool:
    start = _to_float(row.get("suspicious_start_time"))
    end = _to_float(row.get("suspicious_end_time"))
    return start is not None and end is not None and end > start


def select_training_window(
    y: np.ndarray, sr: int, row: pd.Series
) -> tuple[np.ndarray, float, float, str]:
    """
    Choose a 4s training clip.

    Normal rows: first 4 seconds.
    Partial fabrication: 4s centered on suspicious [start, end], clamped to file length.
    """
    duration_sec = len(y) / float(sr)
    if is_partial_fabrication_row(row):
        if not has_valid_partial_timestamps(row):
            raise ValueError("partial_fabrication_missing_timestamps")
        region_start = _to_float(row.get("suspicious_start_time"))
        region_end = _to_float(row.get("suspicious_end_time"))
        region_center = 0.5 * (region_start + region_end)
        half = CHUNK_SECONDS / 2.0
        win_start = region_center - half
        win_end = region_center + half
        strategy = "partial_suspicious_region_centered"
        clamped = False
        if win_start < 0:
            win_start = 0.0
            win_end = min(CHUNK_SECONDS, duration_sec)
            clamped = True
        if win_end > duration_sec:
            win_end = duration_sec
            win_start = max(0.0, win_end - CHUNK_SECONDS)
            clamped = True
        if clamped:
            strategy = "partial_suspicious_region_centered_clamped"
    else:
        win_start = 0.0
        win_end = min(CHUNK_SECONDS, duration_sec)
        strategy = "first_4s"

    i0 = int(win_start * sr)
    i1 = int(win_end * sr)
    y_win = y[i0:i1].astype(np.float32, copy=False)
    if len(y_win) < CHUNK_SAMPLES:
        y_win = np.pad(y_win, (0, CHUNK_SAMPLES - len(y_win)))
    elif len(y_win) > CHUNK_SAMPLES:
        y_win = y_win[:CHUNK_SAMPLES]
    return y_win, float(win_start), float(win_end), strategy


def map_row_targets(row: pd.Series) -> dict:
    origin_bin = _safe_str(row.get("origin_binary")).lower()
    origin_target = ORIGIN_BINARY_TO_TARGET.get(origin_bin, ORIGIN_IGNORE)

    hint = _safe_str(row.get("attack_hint")).lower()
    attack_target = ATTACK_HINT_TO_TARGET.get(hint, ATTACK_IGNORE)

    partial = int(is_partial_fabrication_row(row))

    use_origin = _parse_bool(row.get("use_origin_loss")) and origin_target != ORIGIN_IGNORE
    use_attack = _parse_bool(row.get("use_attack_loss")) and attack_target != ATTACK_IGNORE
    use_partial = _parse_bool(row.get("use_partial_loss"))

    weight = float(row.get("sample_weight", 1.0) or 1.0)

    return {
        "origin_target": int(origin_target),
        "attack_target": int(attack_target),
        "partial_target": int(partial),
        "sample_weight": float(weight),
        "use_origin_loss": int(use_origin),
        "use_attack_loss": int(use_attack),
        "use_partial_loss": int(use_partial),
    }


def extract_features_for_window(
    y_window: np.ndarray,
    audio_path: Path,
    env_extractor: EnvironmentalFeatureExtractor,
):
    logmel, _ = extract_logmel(y_window, sr=SAMPLE_RATE)
    if logmel.shape != (64, 400):
        raise ValueError(f"logmel shape {logmel.shape}, expected (64, 400)")
    _, env_vec = extract_env_features(env_extractor, str(audio_path), y=y_window)
    env_vec = np.asarray(env_vec, dtype=np.float32).reshape(-1)
    if env_vec.shape[0] != 12:
        raise ValueError(f"env shape {env_vec.shape}, expected (12,)")
    if not np.isfinite(logmel).all() or not np.isfinite(env_vec).all():
        raise ValueError("NaN/Inf in features")
    return logmel.astype(np.float32), env_vec.astype(np.float32)


def _encode_strings(values: list[str], max_len: int = 512) -> np.ndarray:
    return np.array([v[:max_len] for v in values], dtype=h5py.string_dtype(encoding="utf-8"))


def write_h5(output_h5: Path, records: list[dict], split: str) -> None:
    n = len(records)
    output_h5.parent.mkdir(parents=True, exist_ok=True)
    with h5py.File(output_h5, "w") as h5f:
        h5f.attrs["split"] = split
        h5f.attrs["n_samples"] = n
        h5f.attrs["logmel_shape"] = json.dumps([64, 400])
        h5f.attrs["env_dim"] = 12
        h5f.attrs["chunk_seconds"] = CHUNK_SECONDS

        if n == 0:
            return

        logmel = np.stack([r["logmel"] for r in records], axis=0).astype(np.float32)
        env = np.stack([r["env"] for r in records], axis=0).astype(np.float32)

        h5f.create_dataset("features_logmel", data=logmel, compression="gzip", compression_opts=4)
        h5f.create_dataset("features_env", data=env, compression="gzip", compression_opts=4)
        h5f.create_dataset("origin_target", data=np.array([r["origin_target"] for r in records], dtype=np.int8))
        h5f.create_dataset("attack_target", data=np.array([r["attack_target"] for r in records], dtype=np.int8))
        h5f.create_dataset("partial_target", data=np.array([r["partial_target"] for r in records], dtype=np.int8))
        h5f.create_dataset("sample_weight", data=np.array([r["sample_weight"] for r in records], dtype=np.float32))
        h5f.create_dataset("use_origin_loss", data=np.array([r["use_origin_loss"] for r in records], dtype=np.uint8))
        h5f.create_dataset("use_attack_loss", data=np.array([r["use_attack_loss"] for r in records], dtype=np.uint8))
        h5f.create_dataset("use_partial_loss", data=np.array([r["use_partial_loss"] for r in records], dtype=np.uint8))
        h5f.create_dataset(
            "window_start_time",
            data=np.array([r["window_start_time"] for r in records], dtype=np.float32),
        )
        h5f.create_dataset(
            "window_end_time",
            data=np.array([r["window_end_time"] for r in records], dtype=np.float32),
        )
        h5f.create_dataset("window_strategy", data=_encode_strings([r["window_strategy"] for r in records]))

        h5f.create_dataset("sample_id", data=_encode_strings([r["sample_id"] for r in records]))
        h5f.create_dataset("audio_path", data=_encode_strings([r["audio_path"] for r in records]))
        h5f.create_dataset("data_source", data=_encode_strings([r["data_source"] for r in records]))
        h5f.create_dataset("split", data=_encode_strings([r["split"] for r in records]))
        h5f.create_dataset("manipulation_type", data=_encode_strings([r["manipulation_type"] for r in records]))
        h5f.create_dataset("source_origin", data=_encode_strings([r["source_origin"] for r in records]))


def _window_stats(records: list[dict]) -> dict:
    stats = {
        "first_4s": 0,
        "partial_suspicious_region_centered": 0,
        "partial_suspicious_region_centered_clamped": 0,
        "partial_missing_timestamp_skipped": 0,
    }
    for r in records:
        s = r.get("window_strategy", "")
        if s in stats:
            stats[s] += 1
        elif s.startswith("partial_suspicious"):
            stats["partial_suspicious_region_centered"] += 1
    return stats


def _write_validation_md(
    path: Path,
    manifest_path: Path,
    output_h5: Path,
    split: str,
    rows_read: int,
    records: list[dict],
    failed: list[dict],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ws = _window_stats(records)
    partial_failed_ts = sum(
        1 for f in failed if "partial_fabrication_missing_timestamps" in str(f.get("error", ""))
    )

    lines = [
        "# Phase 7C3 Feature Cache Validation",
        "",
        f"- Manifest: `{manifest_path}`",
        f"- Output H5: `{output_h5}`",
        f"- Split: **{split}**",
        f"- Rows read: **{rows_read}**",
        f"- Rows cached: **{len(records)}**",
        f"- Rows failed: **{len(failed)}**",
        "",
        "## Window selection",
        "",
        f"- Normal `first_4s` windows: **{ws['first_4s']}**",
        f"- Partial suspicious-region centered: **{ws['partial_suspicious_region_centered']}**",
        f"- Partial centered (clamped to file bounds): **{ws['partial_suspicious_region_centered_clamped']}**",
        f"- Partial rows skipped (missing timestamps): **{partial_failed_ts}**",
        "",
    ]
    if records:
        ot = [r["origin_target"] for r in records]
        at = [r["attack_target"] for r in records]
        w = [r["sample_weight"] for r in records]
        lines.extend(
            [
                "## Class / weight stats",
                "",
                f"- Origin: human(0)={ot.count(0)}, ai/mixed(1)={ot.count(1)}, masked(-1)={ot.count(-1)}",
                f"- Attack: bonafide={at.count(0)}, syn={at.count(1)}, conv={at.count(2)}, replay={at.count(3)}, masked={at.count(-1)}",
                f"- Partial target=1: {sum(r['partial_target'] for r in records)}",
                f"- sample_weight mean: {np.mean(w):.4f}, min: {np.min(w):.4f}, max: {np.max(w):.4f}",
                "",
                "## Feature shapes",
                "",
                "- logmel: `[N, 64, 400]` float32",
                "- env: `[N, 12]` float32",
                "",
            ]
        )
    if failed:
        lines.append("## Failed rows")
        lines.append("")
        for f in failed[:25]:
            lines.append(f"- `{f.get('sample_id')}`: {f.get('error')}")
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[SAVE] {path}")


def _registry_path(validation_md: Path) -> Path:
    return validation_md.parent / "feature_cache_validation_registry.json"


def _update_validation_summary(validation_md: Path, split: str, read: int, cached: int, failed: int) -> None:
    """Rewrite summary from registry (no stale split lines after reruns)."""
    reg_path = _registry_path(validation_md)
    reg_path.parent.mkdir(parents=True, exist_ok=True)
    registry: dict = {}
    if reg_path.is_file():
        registry = json.loads(reg_path.read_text(encoding="utf-8"))
    registry[split] = {
        "read": read,
        "cached": cached,
        "failed": failed,
        "updated_utc": datetime.now(timezone.utc).isoformat(),
    }
    reg_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")

    lines = [
        "# Phase 7C3 Feature Cache Validation (summary)",
        "",
        "Regenerated from registry on each split run.",
        "",
    ]
    for sp in ("train", "val", "test"):
        if sp not in registry:
            continue
        e = registry[sp]
        lines.append(
            f"- **{sp}**: read={e['read']}, cached={e['cached']}, failed={e['failed']} "
            f"(updated {e.get('updated_utc', '')})"
        )
    lines.append("")
    validation_md.write_text("\n".join(lines), encoding="utf-8")


def build_cache(
    manifest_path: Path,
    output_h5: Path,
    split: str,
    repo_root: Path,
    strict: bool,
    validation_md: Path,
    limit: int | None,
    force: bool,
) -> int:
    if output_h5.is_file() and not force:
        raise FileExistsError(
            f"H5 exists: {output_h5}. Pass --force to overwrite, or delete the file first."
        )
    if output_h5.is_file() and force:
        print(f"[WARN] Overwriting existing H5: {output_h5}")

    df = pd.read_csv(manifest_path, low_memory=False)
    if limit is not None and limit > 0:
        df = df.head(limit)

    est_mb = len(df) * BYTES_PER_ROW_EST / (1024 * 1024)
    print(f"[INFO] Rows to process: {len(df)} | Est. uncompressed feature payload ~{est_mb:.1f} MB")
    print("[INFO] Feature extraction: single-process (safe on Windows; use --num_workers only if tested)")

    env_extractor = EnvironmentalFeatureExtractor(sr=SAMPLE_RATE)
    records: list[dict] = []
    failed: list[dict] = []

    for _, row in tqdm(df.iterrows(), total=len(df), desc=f"7C3 features [{split}]"):
        audio_path = _resolve_audio(_safe_str(row.get("audio_path") or row.get("filepath")), repo_root)
        sample_id = _safe_str(row.get("sample_id")) or audio_path.stem
        meta = {
            "sample_id": sample_id,
            "audio_path": str(audio_path),
            "data_source": _safe_str(row.get("data_source")),
            "split": split,
            "manipulation_type": _safe_str(row.get("manipulation_type")),
            "source_origin": _safe_str(row.get("source_origin")),
        }

        if is_partial_fabrication_row(row) and not has_valid_partial_timestamps(row):
            failed.append({**meta, "error": "partial_fabrication_missing_timestamps"})
            continue

        if not audio_path.is_file():
            failed.append({**meta, "error": "audio_not_found"})
            if strict:
                raise FileNotFoundError(audio_path)
            continue

        try:
            targets = map_row_targets(row)
            y, _ = librosa.load(str(audio_path), sr=SAMPLE_RATE, mono=True)
            y_window, w_start, w_end, w_strategy = select_training_window(y, SAMPLE_RATE, row)
            logmel, env_vec = extract_features_for_window(y_window, audio_path, env_extractor)
            records.append(
                {
                    **meta,
                    **targets,
                    "logmel": logmel,
                    "env": env_vec,
                    "window_start_time": w_start,
                    "window_end_time": w_end,
                    "window_strategy": w_strategy,
                }
            )
            del y, y_window, logmel, env_vec
        except Exception as exc:
            failed.append({**meta, "error": str(exc)})
            if strict:
                raise

    write_h5(output_h5, records, split)
    del records

    fail_path = validation_md.parent / "feature_cache_failed_rows.csv"
    if failed:
        pd.DataFrame(failed).to_csv(fail_path, index=False)
        print(f"[SAVE] Failed rows -> {fail_path} ({len(failed)})")
    elif fail_path.is_file():
        fail_path.unlink(missing_ok=True)

    with h5py.File(output_h5, "r") as h5f:
        n_cached = int(h5f.attrs.get("n_samples", 0))

    split_md = validation_md.parent / f"feature_cache_validation_{split}.md"
    _write_validation_md(
        split_md,
        manifest_path,
        output_h5,
        split,
        len(df),
        _load_records_summary(output_h5),
        failed,
    )
    _update_validation_summary(validation_md, split, len(df), n_cached, len(failed))

    on_disk_mb = output_h5.stat().st_size / (1024 * 1024) if output_h5.is_file() else 0
    print(f"[SAVE] {output_h5} ({n_cached} cached, {len(failed)} failed, ~{on_disk_mb:.1f} MB on disk)")
    return n_cached


def _load_records_summary(output_h5: Path) -> list[dict]:
    """Minimal record dicts for validation stats from written H5."""
    out = []
    with h5py.File(output_h5, "r") as h5f:
        n = int(h5f.attrs.get("n_samples", 0))
        if n == 0:
            return out
        strategies = [s.decode("utf-8") if isinstance(s, bytes) else str(s) for s in h5f["window_strategy"][:]]
        for i in range(n):
            out.append(
                {
                    "origin_target": int(h5f["origin_target"][i]),
                    "attack_target": int(h5f["attack_target"][i]),
                    "partial_target": int(h5f["partial_target"][i]),
                    "sample_weight": float(h5f["sample_weight"][i]),
                    "use_origin_loss": int(h5f["use_origin_loss"][i]),
                    "use_attack_loss": int(h5f["use_attack_loss"][i]),
                    "window_strategy": strategies[i],
                }
            )
    return out


def parse_args():
    p = argparse.ArgumentParser(description="Phase 7C3 — build HDF5 feature cache")
    p.add_argument("--manifest", type=str, required=True)
    p.add_argument("--output_h5", type=str, required=True)
    p.add_argument("--split", type=str, required=True, choices=["train", "val", "test"])
    p.add_argument("--repo_root", type=str, default=str(_REPO_ROOT))
    p.add_argument(
        "--validation_md",
        type=str,
        default="reports/phase7/phase7c3_finetune/validation/feature_cache_validation_report.md",
    )
    p.add_argument("--strict", action="store_true", help="Fail on first bad file")
    p.add_argument("--limit", type=int, default=None, help="Process only first N manifest rows (debug)")
    p.add_argument("--force", action="store_true", help="Overwrite existing output H5")
    p.add_argument(
        "--num_workers",
        type=int,
        default=0,
        help="Reserved: multiprocess extraction not enabled on Windows by default; keep 0.",
    )
    return p.parse_args()


def main():
    args = parse_args()
    if args.num_workers and args.num_workers > 0:
        print(
            "[WARN] --num_workers > 0 is not implemented for feature extraction; "
            "using single-process. Safe default on Windows is 0."
        )
    build_cache(
        manifest_path=Path(args.manifest),
        output_h5=Path(args.output_h5),
        split=args.split,
        repo_root=Path(args.repo_root),
        strict=args.strict,
        validation_md=Path(args.validation_md),
        limit=args.limit,
        force=args.force,
    )


if __name__ == "__main__":
    main()
