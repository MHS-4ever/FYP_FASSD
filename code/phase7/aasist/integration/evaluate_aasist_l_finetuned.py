"""
Phase 7E3C: Evaluate a fine-tuned AASIST-L checkpoint.

Goals:
- Reuse the Phase 7E3A pretrained-eval runner logic and output format.
- Allow custom checkpoint path.
- Support two window modes:
  - chunks: use the existing multi-window logic (Phase 7C1 / Phase 7A eval manifests)
  - manifest_windows: use window_start_time/window_end_time from fine-tune manifests (val/test)

Constraints:
- Do not overwrite Phase 7E3A outputs; choose a new output_dir for fine-tune results.
- Do not modify vendor AASIST source.
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

from _common import ensure_dir, resolve_path, utc_now_iso, write_json, write_markdown
from aasist_eval_common import (
    OFFICIAL_SPOOF_CLASS_INDEX,
    TARGET_SAMPLE_RATE,
    build_class_convention_fields,
    extract_aasist_logits,
    load_aasist_model,
    load_audio_mono_16k,
    resolve_audio_path,
)
from run_aasist_pretrained_eval import process_file as process_file_chunks


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


def _extract_manifest_window(wav: np.ndarray, start_sec: float, end_sec: float, nb_samp: int) -> np.ndarray:
    start = max(0, int(round(start_sec * TARGET_SAMPLE_RATE)))
    end = max(start, int(round(end_sec * TARGET_SAMPLE_RATE)))
    seg = wav[start:end]
    if len(seg) >= nb_samp:
        return seg[:nb_samp].astype(np.float32, copy=False)
    out = np.zeros((nb_samp,), dtype=np.float32)
    if len(seg) > 0:
        out[: len(seg)] = seg.astype(np.float32, copy=False)
    return out


def process_row_manifest_window(
    row: pd.Series,
    model,
    model_meta: dict[str, Any],
    device: str,
    threshold: float,
    spoof_class_index: int,
    convention: dict[str, Any],
) -> tuple[dict[str, Any], list[dict], dict[str, Any]]:
    """
    Evaluate a single manifest window row (n_windows=1).
    Output row format mirrors run_aasist_pretrained_eval.py (file_row + windows + json).
    """
    nb_samp = int(model_meta["nb_samp"])
    audio_path = resolve_audio_path(str(row["audio_path"]))
    if audio_path is None:
        return (
            {**row.to_dict(), **convention, "error": f"audio_not_found:{row['audio_path']}", "n_windows": 0},
            [],
            {},
        )

    try:
        wav, audio_meta = load_audio_mono_16k(audio_path)
        s = float(row.get("window_start_time", 0.0))
        e = float(row.get("window_end_time", (nb_samp / TARGET_SAMPLE_RATE)))
        x = _extract_manifest_window(wav, s, e, nb_samp)

        # infer_window_probabilities already exists, but to avoid another dependency surface,
        # we run the model directly here and compute softmax in a stable way.
        import torch
        from torch.nn import functional as F

        dev = device
        if dev == "cuda" and not torch.cuda.is_available():
            dev = "cpu"
        model = model.to(dev)
        model.eval()
        with torch.no_grad():
            t = torch.from_numpy(x[None, :].astype(np.float32)).to(dev)
            logits = extract_aasist_logits(model(t))
            probs = F.softmax(logits, dim=1).detach().cpu().numpy()[0].astype(np.float64)

        prob0 = float(probs[0])
        prob1 = float(probs[1])
        spoof_score = float(probs[spoof_class_index])
        bonafide_score = float(probs[1 - spoof_class_index])

        win = {
            "window_index": 0,
            "start_time": round(s, 4),
            "end_time": round(e, 4),
            "prob_class_0": prob0,
            "prob_class_1": prob1,
            "spoof_score": spoof_score,
            "bonafide_score": bonafide_score,
            "predicted_window_risk": int(spoof_score >= threshold),
        }

        file_row: dict[str, Any] = {
            **row.to_dict(),
            **convention,
            "audio_path_resolved": str(audio_path),
            "audio_load_meta": json.dumps(audio_meta),
            "n_windows": 1,
            "prob_class_0": prob0,
            "prob_class_1": prob1,
            "spoof_score": spoof_score,
            "bonafide_score": bonafide_score,
            "mean_spoof_score": spoof_score,
            "max_spoof_score": spoof_score,
            "median_spoof_score": spoof_score,
            "max_window_spoof": spoof_score,
            "suspicious_window_count": int(spoof_score >= threshold),
            "suspicious_window_ratio": float(int(spoof_score >= threshold)),
            "predicted_risk_binary": int(spoof_score >= threshold),
            "threshold_used": threshold,
            "suspicious_region_window_included": True,
            "error": "",
            # partial metrics not applicable for window-level eval
            "n_windows_inside_region": "",
            "n_windows_outside_region": "",
            "inside_region_avg_spoof": "",
            "outside_region_avg_spoof": "",
            "inside_region_max_spoof": "",
            "outside_region_max_spoof": "",
            "region_delta": "",
            "partial_region_detected": "",
            "aasist_status": "",
        }

        json_out = {
            "sample_id": row.get("sample_id", ""),
            "audio_path": str(row.get("audio_path", "")),
            "class_convention": convention,
            "scores": {
                "prob_class_0": prob0,
                "prob_class_1": prob1,
                "spoof_score": spoof_score,
                "bonafide_score": bonafide_score,
            },
            "windowing": {
                "mode": "manifest_windows",
                "manifest_start_time": s,
                "manifest_end_time": e,
                "nb_samp": nb_samp,
            },
            "windows": [win],
            "config_path": model_meta.get("config_path"),
            "checkpoint_path": model_meta.get("checkpoint_path"),
        }
        return file_row, [win], json_out

    except Exception as e:  # noqa: BLE001
        return ({**row.to_dict(), **convention, "error": repr(e), "n_windows": 0}, [], {})


def write_run_md(output_dir: Path, args: argparse.Namespace, model_meta: dict[str, Any]) -> None:
    lines = [
        "# Phase 7E3C — Fine-tuned AASIST-L evaluation run",
        "",
        f"**Generated:** {utc_now_iso()}",
        "",
        "## Inputs",
        "",
        f"- eval_manifest: `{args.eval_manifest}`",
        f"- checkpoint_path: `{args.checkpoint_path}`",
        f"- config_path: `{args.config_path}`",
        f"- window_mode: `{args.window_mode}`",
        "",
        "## Model meta",
        "",
        "```json",
        json.dumps(model_meta, indent=2),
        "```",
        "",
        "## Outputs",
        "",
        "- `aasist_l_predictions.csv`",
        "- `aasist_l_chunk_timeline.jsonl` (if enabled)",
        "",
    ]
    write_markdown(output_dir / "run_summary.md", lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 7E3C: Evaluate fine-tuned AASIST-L checkpoint")
    parser.add_argument("--eval_manifest", required=True, type=str)
    parser.add_argument("--aasist_src", required=True, type=str)
    parser.add_argument("--config_path", required=True, type=str)
    parser.add_argument("--checkpoint_path", required=True, type=str)
    parser.add_argument("--output_dir", required=True, type=str)
    parser.add_argument("--device", default="cuda", type=str)
    parser.add_argument("--batch_size", default=16, type=int)
    parser.add_argument("--window_mode", default="chunks", type=str, choices=("chunks", "manifest_windows"))
    parser.add_argument("--save_chunk_timeline", action="store_true")
    parser.add_argument("--spoof_class_index", default=OFFICIAL_SPOOF_CLASS_INDEX, type=int)
    parser.add_argument("--threshold", default=0.5, type=float)
    args = parser.parse_args()

    eval_manifest = resolve_path(args.eval_manifest)
    out_dir = ensure_dir(resolve_path(args.output_dir))
    aasist_src = resolve_path(args.aasist_src)
    config_path = resolve_path(args.config_path)
    checkpoint_path = resolve_path(args.checkpoint_path)

    df = pd.read_csv(eval_manifest)
    model, meta = load_aasist_model(
        aasist_src=aasist_src,
        config_path=config_path,
        checkpoint_path=checkpoint_path,
        device=str(args.device),
        spoof_class_index=int(args.spoof_class_index),
    )
    meta["eval_manifest"] = str(eval_manifest)
    meta["window_mode"] = str(args.window_mode)

    convention = build_class_convention_fields(int(args.spoof_class_index), aasist_src, user_override=True)

    pred_rows: list[dict[str, Any]] = []
    timeline: list[dict[str, Any]] = []

    for _, row in tqdm(df.iterrows(), total=len(df), desc="evaluate"):
        if args.window_mode == "manifest_windows":
            file_row, windows, json_out = process_row_manifest_window(
                row=row,
                model=model,
                model_meta=meta,
                device=meta.get("device", str(args.device)),
                threshold=float(args.threshold),
                spoof_class_index=int(args.spoof_class_index),
                convention=convention,
            )
        else:
            file_row, windows, json_out = process_file_chunks(
                row=row,
                model=model,
                model_meta=meta,
                device=meta.get("device", str(args.device)),
                batch_size=int(args.batch_size),
                threshold=float(args.threshold),
                spoof_class_index=int(args.spoof_class_index),
                convention=convention,
            )

        pred_rows.append(file_row)
        if args.save_chunk_timeline and json_out:
            timeline.append(json_out)

    out_csv = out_dir / "aasist_l_predictions.csv"
    pd.DataFrame(pred_rows).to_csv(out_csv, index=False)
    if args.save_chunk_timeline:
        # JSONL to keep file sizes manageable.
        out_jsonl = out_dir / "aasist_l_chunk_timeline.jsonl"
        with out_jsonl.open("w", encoding="utf-8") as f:
            for obj in timeline:
                f.write(json.dumps(obj) + "\n")

    write_json(out_dir / "run_meta.json", meta)
    write_run_md(out_dir, args, meta)
    print(f"Wrote: {out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

