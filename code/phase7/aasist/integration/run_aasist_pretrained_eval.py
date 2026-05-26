"""
Phase 7E3A: Run pretrained AASIST-L inference on eval manifests (no training).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd
from tqdm import tqdm

from _common import ensure_dir, resolve_path, utc_now_iso, vram_snapshot, write_json, write_markdown
from aasist_eval_common import (
    OFFICIAL_SPOOF_CLASS_INDEX,
    TARGET_SAMPLE_RATE,
    build_class_convention_fields,
    check_run_readiness,
    compute_partial_region_metrics,
    evaluate_aasist_status,
    extract_window,
    generate_window_starts,
    infer_window_probabilities,
    load_aasist_model,
    load_audio_mono_16k,
    resolve_audio_path,
)

THRESHOLD_DEFAULT = 0.5


def _to_float(v, default=None):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return default
    s = str(v).strip()
    if not s:
        return default
    try:
        return float(s)
    except ValueError:
        return default


def process_file(
    row: pd.Series,
    model,
    model_meta: dict[str, Any],
    device: str,
    batch_size: int,
    threshold: float,
    spoof_class_index: int,
    convention: dict[str, Any],
) -> tuple[dict[str, Any], list[dict], dict[str, Any]]:
    nb_samp = int(model_meta["nb_samp"])
    hop = max(1, nb_samp // 2)
    audio_path = resolve_audio_path(str(row["audio_path"]))
    if audio_path is None:
        return (
            {
                **row.to_dict(),
                **convention,
                "error": f"audio_not_found:{row['audio_path']}",
                "n_windows": 0,
            },
            [],
            {},
        )

    try:
        wav, audio_meta = load_audio_mono_16k(audio_path)
        sus_start = _to_float(row.get("suspicious_start_time"))
        sus_end = _to_float(row.get("suspicious_end_time"))
        starts, window_meta = generate_window_starts(
            len(wav),
            nb_samp,
            hop,
            suspicious_start=sus_start,
            suspicious_end=sus_end,
        )
        window_arrays = [extract_window(wav, s, nb_samp) for s in starts]
        prob_rows = infer_window_probabilities(
            model, window_arrays, device, batch_size, spoof_class_index=spoof_class_index
        )

        windows: list[dict] = []
        for idx, (start, probs) in enumerate(zip(starts, prob_rows)):
            start_sec = start / TARGET_SAMPLE_RATE
            end_sec = (start + nb_samp) / TARGET_SAMPLE_RATE
            score = probs["spoof_score"]
            windows.append(
                {
                    "window_index": idx,
                    "start_time": round(start_sec, 4),
                    "end_time": round(end_sec, 4),
                    "prob_class_0": probs["prob_class_0"],
                    "prob_class_1": probs["prob_class_1"],
                    "spoof_score": score,
                    "bonafide_score": probs["bonafide_score"],
                    "predicted_window_risk": int(score >= threshold),
                }
            )

        if not prob_rows:
            raise RuntimeError("no_windows_generated")

        spoof_scores = np.array([w["spoof_score"] for w in windows], dtype=np.float64)
        p0 = np.array([w["prob_class_0"] for w in windows], dtype=np.float64)
        p1 = np.array([w["prob_class_1"] for w in windows], dtype=np.float64)
        bonafide_scores = np.array([w["bonafide_score"] for w in windows], dtype=np.float64)

        suspicious_count = int((spoof_scores >= threshold).sum())
        n_win = len(windows)

        partial_metrics = compute_partial_region_metrics(windows, sus_start, sus_end, threshold)
        is_partial = str(row.get("manipulation_type", "")).strip().lower() == "partial_ai_insert" or str(
            row.get("partial_fabrication_binary", "")
        ).strip() in ("1", "true", "True")

        file_row: dict[str, Any] = {
            **row.to_dict(),
            **convention,
            "audio_path_resolved": str(audio_path),
            "audio_load_meta": json.dumps(audio_meta),
            "n_windows": n_win,
            "prob_class_0": float(p0.mean()),
            "prob_class_1": float(p1.mean()),
            "spoof_score": float(spoof_scores.mean()),
            "bonafide_score": float(bonafide_scores.mean()),
            "mean_spoof_score": float(spoof_scores.mean()),
            "max_spoof_score": float(spoof_scores.max()),
            "median_spoof_score": float(np.median(spoof_scores)),
            "max_window_spoof": float(spoof_scores.max()),
            "suspicious_window_count": suspicious_count,
            "suspicious_window_ratio": float(suspicious_count / n_win),
            "predicted_risk_binary": int(float(spoof_scores.mean()) >= threshold),
            "threshold_used": threshold,
            "suspicious_region_window_included": bool(window_meta.get("suspicious_region_window_included")),
            "error": "",
        }

        if is_partial:
            file_row.update(partial_metrics)
        else:
            file_row.update(
                {
                    "n_windows_inside_region": "",
                    "n_windows_outside_region": "",
                    "inside_region_avg_spoof": "",
                    "outside_region_avg_spoof": "",
                    "inside_region_max_spoof": "",
                    "outside_region_max_spoof": "",
                    "region_delta": "",
                    "partial_region_detected": "",
                }
            )

        file_row["aasist_status"] = evaluate_aasist_status(file_row)

        json_out = {
            "sample_id": row["sample_id"],
            "audio_path": str(row["audio_path"]),
            "class_convention": convention,
            "scores": {
                "prob_class_0": file_row["prob_class_0"],
                "prob_class_1": file_row["prob_class_1"],
                "spoof_score": file_row["spoof_score"],
                "bonafide_score": file_row["bonafide_score"],
                "mean_spoof_score": file_row["mean_spoof_score"],
                "max_spoof_score": file_row["max_spoof_score"],
                "median_spoof_score": file_row["median_spoof_score"],
            },
            "partial_region": partial_metrics if is_partial else None,
            "windowing": window_meta,
            "windows": windows,
            "config_path": model_meta.get("config_path"),
            "checkpoint_path": model_meta.get("checkpoint_path"),
        }
        return file_row, windows, json_out

    except Exception as e:  # noqa: BLE001
        return (
            {
                **row.to_dict(),
                **convention,
                "error": repr(e),
                "n_windows": 0,
            },
            [],
            {},
        )


def write_readiness_report(readiness: dict[str, Any], output_dir: Path) -> Path:
    convention = readiness.get("class_convention", {})
    lines = [
        "# Phase 7E3A — Run Readiness Check",
        "",
        f"**Generated:** {utc_now_iso()}",
        f"**READY_TO_RUN:** `{readiness.get('ready')}`",
        "",
        "## Checks",
        "",
    ]
    for name, ok in readiness.get("checks", {}).items():
        lines.append(f"- `{name}`: **{'PASS' if ok else 'FAIL'}**")
    lines.extend(
        [
            "",
            "## Class convention",
            "",
            f"- **spoof_class_index_used:** {convention.get('spoof_class_index_used')}",
            f"- **bonafide_class_index_used:** {convention.get('bonafide_class_index_used')}",
            f"- **class_convention_source:** `{convention.get('class_convention_source') or '(none)'}`",
            f"- **class_convention_warning:** `{convention.get('class_convention_warning') or '(none)'}`",
            f"- **audit notes:** {convention.get('class_convention_audit_notes', '')}",
            "",
        ]
    )
    path = output_dir / "phase7e3a_run_readiness.md"
    write_markdown(path, lines)
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run pretrained AASIST eval")
    parser.add_argument("--eval_manifest", type=str, required=True)
    parser.add_argument("--aasist_src", type=str, default="code/phase7/aasist/vendor/AASIST")
    parser.add_argument("--config_path", type=str, default="")
    parser.add_argument("--checkpoint_path", type=str, default="")
    parser.add_argument("--output_dir", type=str, required=True)
    parser.add_argument("--device", type=str, default="cuda", choices=("cuda", "cpu"))
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--window_mode", type=str, default="chunks", choices=("chunks",))
    parser.add_argument("--threshold", type=float, default=THRESHOLD_DEFAULT)
    parser.add_argument("--save_chunk_timeline", action="store_true")
    parser.add_argument("--model_variant", type=str, default="AASIST-L", choices=("AASIST-L", "AASIST"))
    parser.add_argument(
        "--spoof_class_index",
        type=int,
        default=OFFICIAL_SPOOF_CLASS_INDEX,
        choices=(0, 1),
        help="Softmax index treated as spoof/risk score (default 0 per official ASVspoof labels)",
    )
    parser.add_argument(
        "--skip_readiness_check",
        action="store_true",
        help="Skip pre-flight readiness (not recommended)",
    )
    args = parser.parse_args()

    aasist_src = resolve_path(args.aasist_src)
    out_dir = resolve_path(args.output_dir)
    ensure_dir(out_dir)
    logs_dir = ensure_dir(out_dir.parent / "logs")

    if args.config_path:
        config_path = resolve_path(args.config_path)
    else:
        suffix = "AASIST-L.conf" if args.model_variant == "AASIST-L" else "AASIST.conf"
        config_path = aasist_src / "config" / suffix

    if args.checkpoint_path:
        ckpt_path = resolve_path(args.checkpoint_path)
    else:
        ckpt_name = "AASIST-L.pth" if args.model_variant == "AASIST-L" else "AASIST.pth"
        ckpt_path = aasist_src / "models" / "weights" / ckpt_name

    manifest_path = resolve_path(args.eval_manifest)

    user_override = args.spoof_class_index != OFFICIAL_SPOOF_CLASS_INDEX
    convention = build_class_convention_fields(
        args.spoof_class_index, aasist_src, user_override=user_override
    )

    if not args.skip_readiness_check:
        ready, readiness = check_run_readiness(
            aasist_src=aasist_src,
            config_path=config_path,
            checkpoint_path=ckpt_path,
            eval_manifest=manifest_path,
            output_dir=out_dir,
            spoof_class_index=args.spoof_class_index,
        )
        readiness_path = write_readiness_report(readiness, out_dir)
        write_json(out_dir / "phase7e3a_run_readiness.json", readiness)
        print(f"READY_TO_RUN={str(ready).lower()}")
        print(f"Readiness report: {readiness_path}")
        if not ready:
            print("Critical readiness check failed — fix paths/config before running inference.")
            for name, ok in readiness.get("checks", {}).items():
                if not ok:
                    print(f"  FAIL: {name}")
            return 1

    vram_before = vram_snapshot()
    model, model_meta = load_aasist_model(
        aasist_src, config_path, ckpt_path if ckpt_path.is_file() else None, args.device, args.spoof_class_index
    )
    model_meta["config_path"] = str(config_path)
    model_meta["checkpoint_path"] = str(ckpt_path) if ckpt_path.is_file() else None
    model_meta["model_variant"] = args.model_variant
    model_meta["class_convention"] = convention

    run_log = {
        "timestamp_utc": utc_now_iso(),
        "eval_manifest": str(manifest_path),
        "aasist_src": str(aasist_src),
        "model_variant": args.model_variant,
        "config_path": str(config_path),
        "checkpoint_path": str(ckpt_path),
        "device": args.device,
        "batch_size": args.batch_size,
        "window_mode": args.window_mode,
        "threshold": args.threshold,
        "spoof_class_index": args.spoof_class_index,
        "vram_before": vram_before,
        "class_convention": convention,
    }
    write_json(logs_dir / f"run_aasist_pretrained_{out_dir.name}_{utc_now_iso().replace(':', '-')}.json", run_log)

    df = pd.read_csv(manifest_path)
    results: list[dict] = []
    timeline_dir = ensure_dir(out_dir / "chunk_timelines") if args.save_chunk_timeline else None
    json_dir = ensure_dir(out_dir / "json_outputs") if args.save_chunk_timeline else None

    for _, row in tqdm(df.iterrows(), total=len(df), desc="AASIST eval"):
        file_row, windows, json_out = process_file(
            row,
            model,
            model_meta,
            args.device,
            args.batch_size,
            args.threshold,
            args.spoof_class_index,
            convention,
        )
        results.append(file_row)
        if timeline_dir and windows:
            tid = str(row["sample_id"]).replace("/", "_")
            pd.DataFrame(windows).to_csv(timeline_dir / f"{tid}_windows.csv", index=False)
        if json_dir and json_out:
            tid = str(row["sample_id"]).replace("/", "_")
            write_json(json_dir / f"{tid}.json", json_out)

    out_df = pd.DataFrame(results)
    if out_dir.name in ("phase7c1", "phase7a"):
        out_name = "aasist_l_predictions.csv"
    else:
        out_name = "aasist_l_predictions.csv"

    out_csv = out_dir / out_name
    out_df.to_csv(out_csv, index=False)

    vram_after = vram_snapshot()
    print(f"Wrote {len(out_df)} rows to {out_csv}")
    print(f"VRAM before: {vram_before} after: {vram_after}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
