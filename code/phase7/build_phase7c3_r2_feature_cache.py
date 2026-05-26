"""
Phase 7C3-R2: Build HDF5 feature cache for forensic-risk fine-tuning.

R2 changes vs v1:
- Binary target is forensic risk (not pure origin).
- Phase7C1 rows can emit multiple windows (start/mid/end) for better file coverage.
- Partial fabrication rows use suspicious-region centered windows only.

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
WINDOW_SECONDS = 4.0
WINDOW_SAMPLES = int(SAMPLE_RATE * WINDOW_SECONDS)
ATTACK_IGNORE = -1
RISK_IGNORE = -1
MAX_WEIGHT = 4.0

ATTACK_HINT_TO_TARGET = {
    "bonafide": 0,
    "synthesis": 1,
    "voice_conversion": 2,
    "conversion": 2,
    "replay": 3,
    "unknown": ATTACK_IGNORE,
}

R2_BASE_WEIGHTS_P7C1 = {
    "clean_human": 2.5,
    "direct_ai": 3.0,
    "human_replay": 2.5,
    "ai_replay": 2.5,
    "human_mixer": 2.5,
    "ai_mixer": 2.5,
    "partial_fabrication": 3.0,
}

R2_BONUS_BY_BASELINE = {
    "clean_human_false_alarm": 0.5,
    "direct_ai_missed": 0.75,
    "direct_ai_file_level_missed_but_segment_suspicious": 0.5,
    "partial_fabrication_missed": 0.75,
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
    return _safe_str(val).lower() in {"true", "1", "yes", "y"}


def _resolve_audio(path_str: str, repo_root: Path) -> Path:
    p = Path(path_str)
    if p.is_file():
        return p.resolve()
    c = (repo_root / path_str).resolve()
    if c.is_file():
        return c
    return p.resolve()


def is_partial_row(row: pd.Series) -> bool:
    if _parse_bool(row.get("partial_fabrication_binary")):
        return True
    return _safe_str(row.get("manipulation_type")).lower() == "partial_ai_insert"


def has_valid_partial_ts(row: pd.Series) -> bool:
    st = _to_float(row.get("suspicious_start_time"))
    en = _to_float(row.get("suspicious_end_time"))
    return st is not None and en is not None and en > st


def map_risk_target(row: pd.Series) -> tuple[int, bool]:
    """
    R2 forensic risk target:
    0 = clean/bonafide low-risk human
    1 = AI/replay/mixer/edited/partial/manipulated suspicious
    """
    ds = _safe_str(row.get("data_source")).lower()
    manip = _safe_str(row.get("manipulation_type")).lower()
    src_origin = _safe_str(row.get("source_origin")).lower()
    attack_hint = _safe_str(row.get("attack_hint")).lower()

    if ds == "old":
        if attack_hint == "bonafide":
            return 0, True
        if attack_hint in {"synthesis", "voice_conversion", "conversion", "replay"}:
            return 1, True
        return RISK_IGNORE, False

    # phase7c1
    if manip == "clean_direct" and src_origin == "human":
        return 0, True
    if manip in {"clean_direct", "human_replay", "ai_replay", "mixer_processed", "partial_ai_insert"}:
        return 1, True
    if _parse_bool(row.get("partial_fabrication_binary")):
        return 1, True
    # conservative fallback: manipulated labels => risk positive
    manip_label = _safe_str(row.get("manipulation_label")).lower()
    if manip_label and manip_label != "clean_original":
        return 1, True
    if src_origin in {"ai", "mixed"}:
        return 1, True
    if src_origin == "human":
        return 0, True
    return RISK_IGNORE, False


def map_attack_target(row: pd.Series) -> tuple[int, bool]:
    hint = _safe_str(row.get("attack_hint")).lower()
    target = ATTACK_HINT_TO_TARGET.get(hint, ATTACK_IGNORE)
    use_attack = _parse_bool(row.get("use_attack_loss")) if "use_attack_loss" in row else True
    use_attack = bool(use_attack and target != ATTACK_IGNORE)
    return int(target), use_attack


def map_sample_weight_r2(row: pd.Series) -> tuple[float, str]:
    ds = _safe_str(row.get("data_source")).lower()
    if ds == "old":
        return 1.0, "r2_old_uniform"

    manip = _safe_str(row.get("manipulation_type")).lower()
    src_origin = _safe_str(row.get("source_origin")).lower()
    base = 2.5
    reason = "r2_phase7c1_default"
    if manip == "clean_direct" and src_origin == "human":
        base = R2_BASE_WEIGHTS_P7C1["clean_human"]
        reason = "r2_p7c1_clean_human"
    elif manip == "clean_direct" and src_origin == "ai":
        base = R2_BASE_WEIGHTS_P7C1["direct_ai"]
        reason = "r2_p7c1_direct_ai"
    elif manip == "human_replay":
        base = R2_BASE_WEIGHTS_P7C1["human_replay"]
        reason = "r2_p7c1_human_replay"
    elif manip == "ai_replay":
        base = R2_BASE_WEIGHTS_P7C1["ai_replay"]
        reason = "r2_p7c1_ai_replay"
    elif manip == "mixer_processed" and src_origin == "human":
        base = R2_BASE_WEIGHTS_P7C1["human_mixer"]
        reason = "r2_p7c1_human_mixer"
    elif manip == "mixer_processed" and src_origin == "ai":
        base = R2_BASE_WEIGHTS_P7C1["ai_mixer"]
        reason = "r2_p7c1_ai_mixer"
    elif is_partial_row(row):
        base = R2_BASE_WEIGHTS_P7C1["partial_fabrication"]
        reason = "r2_p7c1_partial"

    bonus = R2_BONUS_BY_BASELINE.get(_safe_str(row.get("baseline_status")), 0.0)
    if bonus > 0:
        reason = f"{reason}+{_safe_str(row.get('baseline_status'))}"
    return min(MAX_WEIGHT, base + bonus), reason


def _window_from_start(y: np.ndarray, sr: int, start_sec: float, strategy: str):
    duration = len(y) / float(sr)
    ws = max(0.0, float(start_sec))
    we = ws + WINDOW_SECONDS
    clamped = False
    if we > duration:
        we = duration
        ws = max(0.0, we - WINDOW_SECONDS)
        clamped = True
    i0 = int(ws * sr)
    i1 = int(we * sr)
    yw = y[i0:i1].astype(np.float32, copy=False)
    if len(yw) < WINDOW_SAMPLES:
        yw = np.pad(yw, (0, WINDOW_SAMPLES - len(yw)))
        clamped = True
    elif len(yw) > WINDOW_SAMPLES:
        yw = yw[:WINDOW_SAMPLES]
    if clamped:
        strategy = f"{strategy}_clamped"
    return yw, float(ws), float(we), strategy


def select_windows_for_row(y: np.ndarray, sr: int, row: pd.Series, phase7c1_windows: int):
    ds = _safe_str(row.get("data_source")).lower()
    manip = _safe_str(row.get("manipulation_type")).lower()
    duration = len(y) / float(sr)

    if is_partial_row(row):
        if not has_valid_partial_ts(row):
            raise ValueError("partial_fabrication_missing_timestamps")
        st = _to_float(row.get("suspicious_start_time"))
        en = _to_float(row.get("suspicious_end_time"))
        center = 0.5 * (st + en)
        yield _window_from_start(y, sr, center - WINDOW_SECONDS / 2.0, "partial_suspicious_center")
        return

    # phase7c1 multi-window for non-partial forensic variants
    if ds == "phase7c1" and phase7c1_windows >= 3 and manip in {
        "clean_direct",
        "human_replay",
        "ai_replay",
        "mixer_processed",
    }:
        starts = [0.0, max(0.0, duration / 2.0 - WINDOW_SECONDS / 2.0), max(0.0, duration - WINDOW_SECONDS)]
        seen = set()
        for i, s in enumerate(starts):
            key = round(s, 3)
            if key in seen:
                continue
            seen.add(key)
            yield _window_from_start(y, sr, s, f"phase7c1_{['start','middle','end'][i]}")
        return

    # default first 4s
    yield _window_from_start(y, sr, 0.0, "first_4s")


def extract_features_for_window(y_window: np.ndarray, audio_path: Path, env_extractor: EnvironmentalFeatureExtractor):
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


def _encode_strings(values: list[str], max_len: int = 768) -> np.ndarray:
    return np.array([v[:max_len] for v in values], dtype=h5py.string_dtype(encoding="utf-8"))


def write_h5(output_h5: Path, records: list[dict], split: str):
    output_h5.parent.mkdir(parents=True, exist_ok=True)
    n = len(records)
    with h5py.File(output_h5, "w") as h5f:
        h5f.attrs["split"] = split
        h5f.attrs["n_samples"] = n
        h5f.attrs["logmel_shape"] = json.dumps([64, 400])
        h5f.attrs["env_dim"] = 12
        h5f.attrs["window_seconds"] = WINDOW_SECONDS
        if n == 0:
            return

        h5f.create_dataset(
            "features_logmel",
            data=np.stack([r["logmel"] for r in records]).astype(np.float32),
            compression="gzip",
            compression_opts=4,
        )
        h5f.create_dataset(
            "features_env",
            data=np.stack([r["env"] for r in records]).astype(np.float32),
            compression="gzip",
            compression_opts=4,
        )
        h5f.create_dataset("risk_target", data=np.array([r["risk_target"] for r in records], dtype=np.int8))
        h5f.create_dataset("attack_target", data=np.array([r["attack_target"] for r in records], dtype=np.int8))
        h5f.create_dataset("sample_weight", data=np.array([r["sample_weight"] for r in records], dtype=np.float32))
        h5f.create_dataset("use_risk_loss", data=np.array([r["use_risk_loss"] for r in records], dtype=np.uint8))
        h5f.create_dataset("use_attack_loss", data=np.array([r["use_attack_loss"] for r in records], dtype=np.uint8))
        h5f.create_dataset("sample_id", data=_encode_strings([r["sample_id"] for r in records]))
        h5f.create_dataset("audio_path", data=_encode_strings([r["audio_path"] for r in records]))
        h5f.create_dataset("data_source", data=_encode_strings([r["data_source"] for r in records]))
        h5f.create_dataset("split", data=_encode_strings([r["split"] for r in records]))
        h5f.create_dataset("window_strategy", data=_encode_strings([r["window_strategy"] for r in records]))
        h5f.create_dataset("window_start_time", data=np.array([r["window_start_time"] for r in records], dtype=np.float32))
        h5f.create_dataset("window_end_time", data=np.array([r["window_end_time"] for r in records], dtype=np.float32))
        h5f.create_dataset("manipulation_type", data=_encode_strings([r["manipulation_type"] for r in records]))
        h5f.create_dataset("source_origin", data=_encode_strings([r["source_origin"] for r in records]))


def _summarize(records: list[dict], failed: list[dict]) -> dict:
    win = {}
    for r in records:
        s = r["window_strategy"]
        win[s] = win.get(s, 0) + 1
    return {
        "rows_cached": len(records),
        "rows_failed": len(failed),
        "window_counts": win,
        "risk_counts": {
            "risk0": sum(1 for r in records if r["risk_target"] == 0),
            "risk1": sum(1 for r in records if r["risk_target"] == 1),
            "masked": sum(1 for r in records if r["risk_target"] < 0),
        },
        "attack_counts": {
            "bonafide": sum(1 for r in records if r["attack_target"] == 0),
            "synthesis": sum(1 for r in records if r["attack_target"] == 1),
            "voice_conversion": sum(1 for r in records if r["attack_target"] == 2),
            "replay": sum(1 for r in records if r["attack_target"] == 3),
            "masked": sum(1 for r in records if r["attack_target"] < 0),
        },
    }


def _update_validation_reports(validation_dir: Path, split: str, summary: dict, rows_read: int):
    validation_dir.mkdir(parents=True, exist_ok=True)
    reg = validation_dir / "feature_cache_validation_registry_r2.json"
    data = {}
    if reg.is_file():
        data = json.loads(reg.read_text(encoding="utf-8"))
    data[split] = {
        "rows_read": rows_read,
        **summary,
        "updated_utc": datetime.now(timezone.utc).isoformat(),
    }
    reg.write_text(json.dumps(data, indent=2), encoding="utf-8")

    lines = ["# Phase 7C3-R2 Feature Cache Validation (summary)", ""]
    for sp in ("train", "val", "test"):
        if sp not in data:
            continue
        e = data[sp]
        lines.append(
            f"- **{sp}**: read={e['rows_read']}, cached={e['rows_cached']}, failed={e['rows_failed']}, "
            f"risk1={e['risk_counts']['risk1']}, risk0={e['risk_counts']['risk0']}"
        )
    lines.append("")
    (validation_dir / "feature_cache_validation_report.md").write_text("\n".join(lines), encoding="utf-8")


def build_cache(
    manifest_path: Path,
    output_h5: Path,
    split: str,
    phase7c1_windows: int,
    force: bool,
    strict: bool,
    limit: int | None,
):
    if output_h5.is_file() and not force:
        raise FileExistsError(f"{output_h5} exists. Use --force.")
    if output_h5.is_file() and force:
        print(f"[WARN] Overwriting {output_h5}")

    df = pd.read_csv(manifest_path, low_memory=False)
    if limit and limit > 0:
        df = df.head(limit)

    env_extractor = EnvironmentalFeatureExtractor(sr=SAMPLE_RATE)
    records: list[dict] = []
    failed: list[dict] = []

    for _, row in tqdm(df.iterrows(), total=len(df), desc=f"R2 cache [{split}]"):
        audio_path = _resolve_audio(_safe_str(row.get("audio_path") or row.get("filepath")), _REPO_ROOT)
        sid = _safe_str(row.get("sample_id")) or audio_path.stem
        ds = _safe_str(row.get("data_source"))
        manip = _safe_str(row.get("manipulation_type"))
        src_origin = _safe_str(row.get("source_origin"))
        meta = {
            "sample_id": sid,
            "audio_path": str(audio_path),
            "data_source": ds,
            "split": split,
            "manipulation_type": manip,
            "source_origin": src_origin,
        }
        if not audio_path.is_file():
            failed.append({**meta, "error": "audio_not_found"})
            if strict:
                raise FileNotFoundError(audio_path)
            continue

        risk_target, use_risk = map_risk_target(row)
        attack_target, use_attack = map_attack_target(row)
        if risk_target == RISK_IGNORE:
            failed.append({**meta, "error": "risk_target_unknown"})
            if strict:
                raise ValueError("risk_target_unknown")
            continue
        weight, weight_reason = map_sample_weight_r2(row)

        try:
            y, _ = librosa.load(str(audio_path), sr=SAMPLE_RATE, mono=True)
            win_idx = 0
            for ywin, ws, we, strategy in select_windows_for_row(y, SAMPLE_RATE, row, phase7c1_windows):
                logmel, env = extract_features_for_window(ywin, audio_path, env_extractor)
                records.append(
                    {
                        **meta,
                        "sample_id": f"{sid}__w{win_idx}",
                        "risk_target": int(risk_target),
                        "attack_target": int(attack_target),
                        "sample_weight": float(weight),
                        "use_risk_loss": int(use_risk),
                        "use_attack_loss": int(use_attack),
                        "window_strategy": strategy,
                        "window_start_time": ws,
                        "window_end_time": we,
                        "weight_reason": weight_reason,
                        "logmel": logmel,
                        "env": env,
                    }
                )
                win_idx += 1
        except Exception as exc:
            failed.append({**meta, "error": str(exc)})
            if strict:
                raise

    write_h5(output_h5, records, split)
    validation_dir = output_h5.parent.parent / "validation"
    validation_dir.mkdir(parents=True, exist_ok=True)
    summary = _summarize(records, failed)
    _update_validation_reports(validation_dir, split, summary, len(df))

    split_md = validation_dir / f"feature_cache_validation_{split}.md"
    detail_lines = [
        f"# Phase 7C3-R2 Feature Cache Validation ({split})",
        "",
        f"- Manifest rows read: {len(df)}",
        f"- Cached windows: {summary['rows_cached']}",
        f"- Failed rows: {summary['rows_failed']}",
        "",
        "## Window strategy counts",
        "",
    ]
    for k, v in sorted(summary["window_counts"].items()):
        detail_lines.append(f"- {k}: {v}")
    detail_lines += ["", "## Risk counts", ""]
    for k, v in summary["risk_counts"].items():
        detail_lines.append(f"- {k}: {v}")
    detail_lines += ["", "## Attack counts", ""]
    for k, v in summary["attack_counts"].items():
        detail_lines.append(f"- {k}: {v}")
    split_md.write_text("\n".join(detail_lines), encoding="utf-8")

    failed_csv = validation_dir / "feature_cache_failed_rows.csv"
    if failed:
        pd.DataFrame(failed).to_csv(failed_csv, index=False)
        print(f"[SAVE] {failed_csv} ({len(failed)} rows)")

    on_disk_mb = output_h5.stat().st_size / (1024 * 1024) if output_h5.is_file() else 0.0
    print(
        f"[SAVE] {output_h5} | windows={summary['rows_cached']} failed={summary['rows_failed']} "
        f"~{on_disk_mb:.1f} MB"
    )


def parse_args():
    p = argparse.ArgumentParser(description="Phase 7C3-R2 feature cache builder")
    p.add_argument("--manifest", type=str, required=True)
    p.add_argument("--output_h5", type=str, required=True)
    p.add_argument("--split", type=str, required=True, choices=["train", "val", "test"])
    p.add_argument("--phase7c1_windows", type=int, default=3)
    p.add_argument("--force", action="store_true")
    p.add_argument("--strict", action="store_true")
    p.add_argument("--limit", type=int, default=None)
    return p.parse_args()


def main():
    args = parse_args()
    build_cache(
        manifest_path=Path(args.manifest),
        output_h5=Path(args.output_h5),
        split=args.split,
        phase7c1_windows=max(1, int(args.phase7c1_windows)),
        force=args.force,
        strict=args.strict,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()

