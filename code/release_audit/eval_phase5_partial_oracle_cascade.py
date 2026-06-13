"""Phase 5 — oracle + cascade eval on testing_audios partial subset.

Uses trained phase5_partial_segment_localizer.joblib (F9-free features).
Does not modify release models. Long run when extracting WavLM per file.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from phase5_partial_common import (
    CASCADE_GATING,
    DEFAULT_OUT,
    TESTING_MANIFEST,
    TESTING_NEGATIVE_IDS,
    TESTING_PARTIAL_IDS,
    progress,
    setup_import_paths,
)

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / "release"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT))
    parser.add_argument("--model-joblib", default="")
    parser.add_argument(
        "--ids",
        nargs="*",
        default=TESTING_PARTIAL_IDS + TESTING_NEGATIVE_IDS,
    )
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"])
    parser.add_argument("--cpu-ids", nargs="*", default=["T4.3"])
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def resolve_audio(path_str: str) -> Path | None:
    p = Path(path_str)
    if p.is_file():
        return p.resolve()
    q = (ROOT / p).resolve()
    return q if q.is_file() else None


def overlap_sec(a0: float, a1: float, b0: float, b1: float) -> float:
    return max(0.0, min(a1, b1) - max(a0, b0))


def localization_gate(
    probs: list[float],
    *,
    threshold: float,
    broad_limit: float,
) -> dict[str, Any]:
    if not probs:
        return {
            "high_segment_fraction": None,
            "topk_minus_rest_probability": None,
            "partial_localization_gate": "not_evaluated",
            "partial_fusion_eligible": False,
        }
    arr = np.asarray(probs, dtype=float)
    high_frac = float((arr >= threshold).mean())
    topk = np.sort(arr)[-5:] if len(arr) >= 5 else np.sort(arr)
    rest = np.sort(arr)[: max(len(arr) - 5, 0)]
    topk_mr = float(topk.mean() - rest.mean()) if len(rest) else float(topk.mean())
    if high_frac >= broad_limit:
        gate = "global_activation_not_localized"
        eligible = False
    elif topk_mr >= CASCADE_GATING["topk_minus_rest_min"] and high_frac <= CASCADE_GATING["localization_hsf_max"]:
        gate = "localized_pattern_supported"
        eligible = True
    else:
        gate = "weak_or_nonlocalized_partial"
        eligible = False
    return {
        "high_segment_fraction": high_frac,
        "topk_minus_rest_probability": topk_mr,
        "partial_localization_gate": gate,
        "partial_fusion_eligible": eligible,
    }


def extract_and_predict(audio_path: Path, bundle: dict, *, device: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    setup_import_paths()
    from src.audio_io import load_audio  # noqa: E402
    from src.feature_extraction import (  # noqa: E402
        compute_live_localization_features,
        extract_segment_acoustic_features,
    )
    from src.segmentation import make_segments  # noqa: E402
    from src.model_loader import load_all_active_models  # noqa: E402
    from src.ssl_embeddings import extract_segment_ssl_embeddings, load_ssl_extractor  # noqa: E402
    from phase9d_p5_training_utils import clean_feature_matrix  # noqa: E402

    runtime_path = RELEASE / "config" / "runtime_config.yaml"
    import yaml

    runtime = yaml.safe_load(runtime_path.read_text(encoding="utf-8")) if runtime_path.is_file() else {}
    seg_dur = float(runtime.get("segment_duration_sec", 4.0))
    seg_hop = float(runtime.get("segment_hop_sec", 2.0))

    y, sr = load_audio(str(audio_path), target_sample_rate=16000)
    segments = make_segments(y, sr, segment_duration_sec=seg_dur, hop_sec=seg_hop)
    seg_acoustic = extract_segment_acoustic_features(segments, y, sr, mode="full")
    ssl_model, ssl_processor, ssl_device = load_ssl_extractor(device=device)
    seg_ssl = extract_segment_ssl_embeddings(segments, y, sr, ssl_model, ssl_processor, ssl_device)
    ssl_cols = [c for c in seg_ssl.columns if c.startswith("ssl_emb_")]
    seg_df = seg_acoustic.merge(seg_ssl[["segment_id"] + ssl_cols], on="segment_id", how="left")
    seg_df = compute_live_localization_features(seg_df)

    model = bundle["model"]
    features = bundle["features"]
    threshold = float(bundle.get("segment_threshold", 0.5))
    x, cols, _, _ = clean_feature_matrix(seg_df, features)
    seg_df = seg_df.copy()
    seg_df["segment_probability"] = model.predict_proba(x)[:, 1]
    seg_df = seg_df.sort_values("segment_probability", ascending=False)

    models = load_all_active_models()
    file_feats = {}  # replay/mixer for cascade context only
    from src.feature_extraction import extract_file_acoustic_features  # noqa: E402
    from src.ssl_embeddings import extract_file_ssl_embedding  # noqa: E402
    from src.inference_pipeline import _run_file_axis  # noqa: E402

    file_acoustic = extract_file_acoustic_features(y, sr)
    file_ssl = extract_file_ssl_embedding(y, sr, ssl_model, ssl_processor, ssl_device)
    file_feats = {**file_acoustic, **file_ssl}
    replay = _run_file_axis(models, "replay", file_feats)
    mixer = _run_file_axis(models, "mixer", file_feats)

    gate = localization_gate(
        seg_df["segment_probability"].astype(float).tolist(),
        threshold=threshold,
        broad_limit=CASCADE_GATING["broad_limit"],
    )
    top = seg_df.iloc[0] if len(seg_df) else None
    aux = {
        "segment_threshold": threshold,
        "max_segment_probability": float(seg_df["segment_probability"].max()) if len(seg_df) else None,
        "replay_probability": replay.get("probability"),
        "mixer_probability": mixer.get("probability"),
        **gate,
    }
    if top is not None:
        aux["top_start_sec"] = float(top["start_sec"])
        aux["top_end_sec"] = float(top["end_sec"])
        aux["top_probability"] = float(top["segment_probability"])
    return seg_df, aux


def main() -> int:
    args = parse_args()
    setup_import_paths()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    model_path = Path(args.model_joblib) if args.model_joblib else out_dir / "phase5_partial_segment_localizer.joblib"
    if not model_path.is_file():
        raise FileNotFoundError(f"Phase 5 model not found: {model_path}. Run train_phase5_partial_segment.py first.")

    bundle = joblib.load(model_path)
    manifest = pd.read_csv(TESTING_MANIFEST, dtype=str, keep_default_na=False)
    manifest = manifest[manifest["test_id"].isin(args.ids)].copy()

    rows: list[dict[str, Any]] = []
    for _, row in tqdm_manifest(manifest):
        test_id = row["test_id"]
        audio = resolve_audio(row["audio_path"])
        out = row.to_dict()
        out["resolved_audio_path"] = str(audio) if audio else ""
        if audio is None:
            out["eval_status"] = "missing_audio"
            rows.append(out)
            continue
        device = "cpu" if test_id in args.cpu_ids else args.device
        try:
            seg_df, aux = extract_and_predict(audio, bundle, device=device)
            out.update(aux)
            out["eval_status"] = "ok"
            out["n_segments"] = int(len(seg_df))

            # Timestamp oracle when labels exist
            partial_gt = str(row.get("partial_fabrication_detected", "")).lower() in {"true", "1"}
            try:
                ts0 = float(row["suspicious_start_time"])
                ts1 = float(row["suspicious_end_time"])
                has_ts = True
            except (TypeError, ValueError):
                has_ts = False
                ts0 = ts1 = float("nan")

            if has_ts and partial_gt and aux.get("top_start_sec") is not None:
                ov = overlap_sec(
                    float(aux["top_start_sec"]),
                    float(aux["top_end_sec"]),
                    ts0,
                    ts1,
                )
                seg_len = max(float(aux["top_end_sec"]) - float(aux["top_start_sec"]), 1e-6)
                out["timestamp_overlap_sec"] = ov
                out["timestamp_overlap_ratio"] = ov / seg_len
                out["oracle_top1_overlaps_label"] = ov > 0
            else:
                out["oracle_top1_overlaps_label"] = ""

            out["cascade_partial_positive"] = bool(
                partial_gt
                and aux.get("partial_fusion_eligible")
                and float(aux.get("max_segment_probability") or 0) >= float(bundle.get("segment_threshold", 0.5))
            )
        except Exception as exc:
            out["eval_status"] = f"error: {exc}"
        rows.append(out)
        progress(f"[phase5-eval] {test_id}: {out.get('eval_status')}")

    pred = pd.DataFrame(rows)
    pred.to_csv(out_dir / "phase5_testing_audios_oracle_cascade.csv", index=False)

    partial_rows = pred[pred["test_id"].isin(TESTING_PARTIAL_IDS)]
    neg_rows = pred[pred["test_id"].isin(TESTING_NEGATIVE_IDS)]

    report = [
        "# Phase 5 — testing_audios oracle + cascade eval",
        "",
        f"Generated: {utc_now()}",
        "",
        f"Model: `{model_path}`",
        f"Evaluated: {', '.join(args.ids)}",
        "",
        "## Partial positives",
        "",
    ]
    if len(partial_rows):
        report.append(partial_rows[["test_id", "max_segment_probability", "partial_localization_gate", "partial_fusion_eligible", "oracle_top1_overlaps_label", "top_start_sec", "top_end_sec"]].to_string(index=False))
    report.extend(["", "## Negatives (should not broad-activate", ""])
    if len(neg_rows):
        report.append(
            neg_rows[["test_id", "max_segment_probability", "high_segment_fraction", "partial_localization_gate"]].to_string(
                index=False
            )
        )
    (out_dir / "phase5_testing_audios_eval_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    progress(f"[phase5-eval] complete -> {out_dir}")
    return 0


def tqdm_manifest(manifest: pd.DataFrame):
    try:
        from phase3_common import tqdm_iter

        return tqdm_iter(list(manifest.iterrows()), desc="phase5 testing", unit="file")
    except Exception:
        return manifest.iterrows()


if __name__ == "__main__":
    raise SystemExit(main())
