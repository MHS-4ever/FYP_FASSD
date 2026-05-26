"""
Phase 7C1: Baseline evaluation — run current Phase 6 hybrid model on collection manifest.

Does not train or fine-tune. Reuses phase6.explain_prediction.predict_file().
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd
import torch
from tqdm import tqdm

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "code"))

from phase3.hybrid_resnet_environmental import HybridResNetEnvironmental
from phase6.explain_prediction import parse_args as phase6_parse_args, predict_file
from phase7.analyze_forensic_test_results import (
    compute_partial_region_metrics,
    compute_suspicious_chunk_metrics,
    has_valid_suspicious_timestamps,
    parse_bool,
    _to_float,
)

MANIPULATION_DETECT_SCORE = 0.65
SEGMENT_SUSPICIOUS_MAX_SPOOF = 0.95
SEGMENT_SUSPICIOUS_RATIO = 0.30
BORDERLINE_MARGIN = 0.05

RESULT_CSV_COLUMNS = [
    "sample_id",
    "audio_path",
    "base_id",
    "variant_id",
    "speaker_id",
    "speaker_gender",
    "language",
    "source_origin",
    "manipulation_type",
    "ground_truth_origin",
    "ground_truth_manipulation",
    "origin_label",
    "manipulation_label",
    "attack_hint",
    "risk_level",
    "partial_fabrication_binary",
    "suspicious_start_time",
    "suspicious_end_time",
    "split",
    "split_group_id",
    "prediction",
    "confidence",
    "decision_score",
    "effective_threshold",
    "attack_type",
    "attack_type_conf",
    "bonafide_prob",
    "synthesis_prob",
    "conversion_prob",
    "replay_prob",
    "n_chunks_used",
    "n_chunks_total",
    "suspicious_chunk_count",
    "suspicious_chunk_ratio",
    "max_chunk_spoof",
    "mean_chunk_spoof",
    "median_chunk_spoof",
    "dominant_chunk_attack",
    "n_chunks_inside",
    "n_chunks_outside",
    "inside_region_avg_spoof",
    "outside_region_avg_spoof",
    "inside_region_max_spoof",
    "outside_region_max_spoof",
    "inside_region_dominant_attack",
    "outside_region_dominant_attack",
    "partial_region_detected",
    "baseline_status",
    "final_baseline_interpretation",
    "error",
]

PARTIAL_CSV_COLUMNS = [
    "sample_id",
    "audio_path",
    "base_id",
    "variant_id",
    "suspicious_start_time",
    "suspicious_end_time",
    "n_chunks_inside",
    "n_chunks_outside",
    "inside_region_avg_spoof",
    "outside_region_avg_spoof",
    "inside_region_max_spoof",
    "outside_region_max_spoof",
    "inside_region_dominant_attack",
    "outside_region_dominant_attack",
    "region_delta",
    "partial_region_detected",
    "notes",
]

MANIFEST_COPY_COLUMNS = [
    "sample_id",
    "audio_path",
    "base_id",
    "variant_id",
    "speaker_id",
    "speaker_gender",
    "language",
    "source_origin",
    "manipulation_type",
    "ground_truth_origin",
    "ground_truth_manipulation",
    "origin_label",
    "manipulation_label",
    "attack_hint",
    "risk_level",
    "partial_fabrication_binary",
    "suspicious_start_time",
    "suspicious_end_time",
    "split",
    "split_group_id",
]


def _has_error(value) -> bool:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return False
    return str(value).strip() != ""


def _is_borderline(row: dict) -> bool:
    score = _to_float(row.get("decision_score"))
    threshold = _to_float(row.get("effective_threshold"), 0.70)
    if score is None or threshold is None:
        return False
    return abs(score - threshold) <= BORDERLINE_MARGIN


def _manipulation_detected(row: dict) -> bool:
    pred = str(row.get("prediction", "")).strip().upper()
    score = _to_float(row.get("decision_score"), 0.0) or 0.0
    return pred == "FAKE" or score >= MANIPULATION_DETECT_SCORE


def _segment_suspicious(row: dict) -> bool:
    max_spoof = _to_float(row.get("max_chunk_spoof"))
    ratio = _to_float(row.get("suspicious_chunk_ratio"), 0.0) or 0.0
    if max_spoof is not None and max_spoof >= SEGMENT_SUSPICIOUS_MAX_SPOOF:
        return True
    return ratio >= SEGMENT_SUSPICIOUS_RATIO


def evaluate_baseline_status(row: dict) -> str:
    """Product-level baseline status for Phase 7C1 (pre fine-tuning benchmark)."""
    if _has_error(row.get("error")):
        return "unknown_review_required"

    gt_origin = str(row.get("ground_truth_origin", "")).strip().lower()
    manip = str(row.get("manipulation_type", "")).strip().lower()
    pred = str(row.get("prediction", "")).strip().upper()
    borderline = _is_borderline(row)
    partial_bin = parse_bool(row.get("partial_fabrication_binary"))

    if partial_bin is True or manip == "partial_ai_insert":
        if not has_valid_suspicious_timestamps(
            row.get("suspicious_start_time"), row.get("suspicious_end_time")
        ):
            return "partial_fabrication_not_evaluable"
        if parse_bool(row.get("partial_region_detected")) is True:
            return "partial_fabrication_detected"
        return "partial_fabrication_missed"

    if manip == "clean_direct" and gt_origin == "human":
        if borderline:
            return "clean_human_borderline"
        if pred == "REAL":
            return "clean_human_accepted"
        if pred == "FAKE":
            return "clean_human_false_alarm"
        return "borderline_needs_review"

    if manip == "clean_direct" and gt_origin == "ai":
        if pred == "FAKE":
            return "direct_ai_detected"
        if pred == "REAL" and _segment_suspicious(row):
            return "direct_ai_file_level_missed_but_segment_suspicious"
        if pred == "REAL":
            return "direct_ai_missed"
        return "borderline_needs_review"

    if manip == "human_replay":
        if _manipulation_detected(row):
            return "human_replay_manipulation_detected"
        return "human_replay_missed"

    if manip == "ai_replay":
        if _manipulation_detected(row):
            return "ai_replay_detected"
        if pred == "REAL" and _segment_suspicious(row):
            return "ai_replay_file_level_missed_but_segment_suspicious"
        return "ai_replay_missed"

    if manip == "mixer_processed" and gt_origin == "human":
        if _manipulation_detected(row):
            return "human_mixer_manipulation_detected"
        return "human_mixer_missed"

    if manip == "mixer_processed" and gt_origin == "ai":
        if _manipulation_detected(row):
            return "ai_mixer_detected"
        if pred == "REAL" and _segment_suspicious(row):
            return "ai_mixer_file_level_missed_but_segment_suspicious"
        return "ai_mixer_missed"

    if borderline:
        return "borderline_needs_review"
    return "unknown_review_required"


def build_final_baseline_interpretation(row: dict) -> str:
    status = str(row.get("baseline_status", "")).strip()
    pred = str(row.get("prediction", "")).strip().upper()
    score = _to_float(row.get("decision_score"))
    score_s = f"{score:.3f}" if score is not None else "n/a"
    attack = str(row.get("attack_type", "")).strip() or "n/a"

    messages = {
        "clean_human_accepted": f"Clean human accepted as REAL (score={score_s}).",
        "clean_human_false_alarm": f"Clean human false alarm: predicted {pred} (score={score_s}).",
        "clean_human_borderline": f"Clean human borderline near threshold (score={score_s}).",
        "direct_ai_detected": f"Direct AI detected as {pred} (score={score_s}, attack={attack}).",
        "direct_ai_missed": f"Direct AI missed at file level (REAL, score={score_s}).",
        "direct_ai_file_level_missed_but_segment_suspicious": (
            f"Direct AI file-level REAL but segment-suspicious chunks (max spoof elevated)."
        ),
        "human_replay_manipulation_detected": (
            f"Human replay manipulation signal detected ({pred}, score={score_s})."
        ),
        "human_replay_missed": f"Human replay manipulation not detected (REAL, score={score_s}).",
        "ai_replay_detected": f"AI replay detected ({pred}, score={score_s}).",
        "ai_replay_missed": f"AI replay missed at file level (score={score_s}).",
        "ai_replay_file_level_missed_but_segment_suspicious": (
            "AI replay file-level REAL but segment-suspicious chunks present."
        ),
        "human_mixer_manipulation_detected": (
            f"Human mixer channel manipulation detected ({pred}, score={score_s})."
        ),
        "human_mixer_missed": f"Human mixer manipulation missed (score={score_s}).",
        "ai_mixer_detected": f"AI mixer detected ({pred}, score={score_s}).",
        "ai_mixer_missed": f"AI mixer missed at file level (score={score_s}).",
        "ai_mixer_file_level_missed_but_segment_suspicious": (
            "AI mixer file-level REAL but segment-suspicious chunks present."
        ),
        "partial_fabrication_detected": (
            "Partial fabrication: suspicious region shows higher spoof signal than outside."
        ),
        "partial_fabrication_missed": (
            "Partial fabrication: region-level detection criteria not met (file-level label secondary)."
        ),
        "partial_fabrication_not_evaluable": "Partial fabrication: missing or invalid suspicious timestamps.",
        "borderline_needs_review": f"Borderline case near decision threshold (score={score_s}).",
        "unknown_review_required": f"Unclassified case — review manually (pred={pred}, score={score_s}).",
    }
    return messages.get(status, f"Baseline status={status}; pred={pred}; score={score_s}.")


def _resolve_audio_path(audio_path: str, repo_root: Path) -> Path:
    p = Path(audio_path)
    if p.is_file():
        return p.resolve()
    candidate = (repo_root / audio_path).resolve()
    if candidate.is_file():
        return candidate
    return p.resolve()


def _attack_probs_row(attack_probs: list[float] | None) -> dict:
    probs = attack_probs or [0.0, 0.0, 0.0, 0.0]
    while len(probs) < 4:
        probs.append(0.0)
    return {
        "bonafide_prob": float(probs[0]),
        "synthesis_prob": float(probs[1]),
        "conversion_prob": float(probs[2]),
        "replay_prob": float(probs[3]),
    }


def _save_chunk_timeline(sample_id: str, chunk_timeline: list, timeline_dir: Path) -> None:
    if not chunk_timeline:
        return
    timeline_dir.mkdir(parents=True, exist_ok=True)
    json_path = timeline_dir / f"{sample_id}_chunks.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(chunk_timeline, f, indent=2)
    pd.DataFrame(chunk_timeline).to_csv(timeline_dir / f"{sample_id}_chunks.csv", index=False)


def _manifest_row_to_base(row: pd.Series) -> dict:
    out = {}
    for col in MANIFEST_COPY_COLUMNS:
        out[col] = row.get(col, "")
    out["partial_fabrication_binary"] = row.get("partial_fabrication_binary", "")
    return out


def _region_delta(inside_avg, outside_avg) -> str | float:
    ia = _to_float(inside_avg)
    oa = _to_float(outside_avg)
    if ia is not None and oa is not None:
        return round(ia - oa, 6)
    return ""


def _partial_analysis_row(base: dict, partial_metrics: dict) -> dict:
    return {
        "sample_id": base.get("sample_id", ""),
        "audio_path": base.get("audio_path", ""),
        "base_id": base.get("base_id", ""),
        "variant_id": base.get("variant_id", ""),
        "suspicious_start_time": base.get("suspicious_start_time", ""),
        "suspicious_end_time": base.get("suspicious_end_time", ""),
        "n_chunks_inside": partial_metrics.get("n_chunks_inside", ""),
        "n_chunks_outside": partial_metrics.get("n_chunks_outside", ""),
        "inside_region_avg_spoof": partial_metrics.get("inside_region_avg_spoof", ""),
        "outside_region_avg_spoof": partial_metrics.get("outside_region_avg_spoof", ""),
        "inside_region_max_spoof": partial_metrics.get("inside_region_max_spoof", ""),
        "outside_region_max_spoof": partial_metrics.get("outside_region_max_spoof", ""),
        "inside_region_dominant_attack": partial_metrics.get("inside_region_dominant_attack", ""),
        "outside_region_dominant_attack": partial_metrics.get("outside_region_dominant_attack", ""),
        "region_delta": _region_delta(
            partial_metrics.get("inside_region_avg_spoof"),
            partial_metrics.get("outside_region_avg_spoof"),
        ),
        "partial_region_detected": partial_metrics.get("partial_region_detected", False),
        "notes": partial_metrics.get("partial_eval_status", ""),
    }


def _build_args(inference_argv: list[str]):
    saved_argv = sys.argv
    try:
        sys.argv = ["explain_prediction.py", *inference_argv]
        return phase6_parse_args()
    finally:
        sys.argv = saved_argv


def _merge_result_row(base: dict, inference: dict, partial_metrics: dict, chunk_metrics: dict) -> dict:
    attack_row = _attack_probs_row(inference.get("attack_probs"))
    row = {
        **base,
        "prediction": inference.get("prediction", ""),
        "confidence": inference.get("confidence", ""),
        "decision_score": inference.get("decision_score", inference.get("spoof_prob", "")),
        "effective_threshold": inference.get("effective_threshold", ""),
        "attack_type": inference.get("attack_type", ""),
        "attack_type_conf": inference.get("attack_type_conf", ""),
        **attack_row,
        "n_chunks_used": inference.get("n_chunks_used", inference.get("n_chunks", "")),
        "n_chunks_total": inference.get("n_chunks_total", ""),
        **chunk_metrics,
        **{
            k: partial_metrics.get(k, "")
            for k in (
                "n_chunks_inside",
                "n_chunks_outside",
                "inside_region_avg_spoof",
                "outside_region_avg_spoof",
                "inside_region_max_spoof",
                "outside_region_max_spoof",
                "inside_region_dominant_attack",
                "outside_region_dominant_attack",
                "partial_region_detected",
            )
        },
        "error": "",
    }
    row["baseline_status"] = evaluate_baseline_status(row)
    row["final_baseline_interpretation"] = build_final_baseline_interpretation(row)
    return row


def print_baseline_terminal_summary(results_df: pd.DataFrame, errors: int, output_dir: Path) -> None:
    def count_status(*statuses: str) -> int:
        if results_df.empty or "baseline_status" not in results_df.columns:
            return 0
        return int(results_df["baseline_status"].isin(statuses).sum())

    n = len(results_df)
    print("\n" + "=" * 60)
    print("Phase 7C1 baseline evaluation — summary")
    print("=" * 60)
    print(f"Total files processed: {n}")
    print(f"Inference errors: {errors}")
    print(f"Clean human accepted: {count_status('clean_human_accepted')}")
    print(f"Clean human false alarms: {count_status('clean_human_false_alarm')}")
    print(f"Clean human borderline: {count_status('clean_human_borderline')}")
    print(f"Direct AI detected: {count_status('direct_ai_detected')}")
    print(f"Direct AI missed: {count_status('direct_ai_missed')}")
    print(
        f"Direct AI file missed / segment suspicious: "
        f"{count_status('direct_ai_file_level_missed_but_segment_suspicious')}"
    )
    print(f"Human replay manipulation detected: {count_status('human_replay_manipulation_detected')}")
    print(f"AI replay detected: {count_status('ai_replay_detected')}")
    print(f"AI replay missed: {count_status('ai_replay_missed')}")
    print(
        f"AI replay file missed / segment suspicious: "
        f"{count_status('ai_replay_file_level_missed_but_segment_suspicious')}"
    )
    print(f"Human mixer detected: {count_status('human_mixer_manipulation_detected')}")
    print(f"AI mixer detected: {count_status('ai_mixer_detected')}")
    print(f"AI mixer missed: {count_status('ai_mixer_missed')}")
    print(
        f"AI mixer file missed / segment suspicious: "
        f"{count_status('ai_mixer_file_level_missed_but_segment_suspicious')}"
    )
    print(f"Partial fabrication detected: {count_status('partial_fabrication_detected')}")
    print(f"Partial fabrication missed: {count_status('partial_fabrication_missed')}")
    print(f"Partial not evaluable: {count_status('partial_fabrication_not_evaluable')}")
    print(f"Borderline / unknown: {count_status('borderline_needs_review', 'unknown_review_required')}")
    print("-" * 60)
    print(f"Results CSV: {output_dir / 'phase7c1_baseline_results.csv'}")
    print(f"Partial analysis: {output_dir / 'phase7c1_partial_fabrication_analysis.csv'}")
    print(f"JSON outputs: {output_dir / 'json_outputs'}")
    print(f"Chunk timelines: {output_dir / 'chunk_timelines'}")
    print("=" * 60 + "\n")


def run_baseline(
    manifest_path: Path,
    ckpt: Path,
    output_dir: Path,
    inference_argv: list[str],
    repo_root: Path,
    device_name: str = "cuda",
) -> pd.DataFrame:
    manifest_path = manifest_path.resolve()
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    output_dir = output_dir.resolve()
    json_dir = output_dir / "json_outputs"
    timeline_dir = output_dir / "chunk_timelines"
    logs_dir = output_dir.parent / "logs"
    json_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    manifest_df = pd.read_csv(manifest_path, low_memory=False)
    if "audio_path" not in manifest_df.columns:
        raise ValueError("Manifest must include audio_path column")

    args = _build_args(inference_argv)
    args.save_chunk_timeline = "--save_chunk_timeline" in inference_argv or getattr(
        args, "save_chunk_timeline", False
    )

    device = torch.device(device_name if (device_name == "cpu" or torch.cuda.is_available()) else "cpu")
    print(f"[DEVICE] {device}")

    ckpt = ckpt.resolve()
    ckpt_data = torch.load(str(ckpt), map_location=device, weights_only=False)
    state_dict = ckpt_data.get("model_state_dict", ckpt_data)
    model = HybridResNetEnvironmental(n_attack_types=4, dropout=0.3).to(device)
    model.load_state_dict(state_dict)
    model.eval()
    print(f"[OK] Loaded checkpoint: {ckpt}")

    from features.environmental_features import EnvironmentalFeatureExtractor

    env_extractor = EnvironmentalFeatureExtractor(sr=16000)
    results: list[dict] = []
    partial_rows: list[dict] = []
    errors = 0

    for _, manifest_row in tqdm(manifest_df.iterrows(), total=len(manifest_df), desc="7C1 baseline", colour="cyan"):
        base = _manifest_row_to_base(manifest_row)
        sample_id = str(base.get("sample_id", "")).strip() or f"row_{len(results)}"
        audio_path = _resolve_audio_path(str(base.get("audio_path", "")), repo_root)

        if not audio_path.is_file():
            err_row = {col: "" for col in RESULT_CSV_COLUMNS}
            err_row.update(base)
            err_row["sample_id"] = sample_id
            err_row["audio_path"] = str(audio_path)
            err_row["error"] = f"audio_not_found: {audio_path}"
            err_row["baseline_status"] = "unknown_review_required"
            err_row["final_baseline_interpretation"] = "Audio file missing."
            results.append(err_row)
            errors += 1
            continue

        try:
            inference = predict_file(str(audio_path), model, device, args, env_extractor=env_extractor)
            partial_metrics = compute_partial_region_metrics(
                chunk_timeline=inference.get("chunk_timeline") or [],
                suspicious_start=base.get("suspicious_start_time"),
                suspicious_end=base.get("suspicious_end_time"),
                manifest_partial_gt=parse_bool(base.get("partial_fabrication_binary")),
            )
            n_used = int(_to_float(inference.get("n_chunks_used"), 0) or 0)
            chunk_metrics = compute_suspicious_chunk_metrics(
                inference.get("chunk_timeline") or [],
                n_chunks_used=n_used,
            )

            out_json = {
                "sample_id": sample_id,
                "manifest": base,
                "inference": inference,
                "partial_fabrication_analysis": partial_metrics,
                "chunk_metrics": chunk_metrics,
            }
            with open(json_dir / f"{sample_id}.json", "w", encoding="utf-8") as f:
                json.dump(out_json, f, indent=2)

            if args.save_chunk_timeline and inference.get("chunk_timeline"):
                _save_chunk_timeline(sample_id, inference["chunk_timeline"], timeline_dir)

            row = _merge_result_row(base, inference, partial_metrics, chunk_metrics)
            results.append(row)

            manip = str(base.get("manipulation_type", "")).lower()
            if parse_bool(base.get("partial_fabrication_binary")) is True or manip == "partial_ai_insert":
                partial_rows.append(_partial_analysis_row(base, partial_metrics))

        except Exception as exc:
            err_row = {col: "" for col in RESULT_CSV_COLUMNS}
            err_row.update(base)
            err_row["sample_id"] = sample_id
            err_row["audio_path"] = str(audio_path)
            err_row["error"] = str(exc)
            err_row["baseline_status"] = "unknown_review_required"
            err_row["final_baseline_interpretation"] = f"Inference error: {exc}"
            results.append(err_row)
            errors += 1
            print(f"[ERROR] {sample_id}: {exc}")

    results_df = pd.DataFrame(results)
    for col in RESULT_CSV_COLUMNS:
        if col not in results_df.columns:
            results_df[col] = ""
    results_df = results_df[RESULT_CSV_COLUMNS]

    csv_path = output_dir / "phase7c1_baseline_results.csv"
    results_df.to_csv(csv_path, index=False)
    print(f"[SAVE] Baseline results -> {csv_path}")

    partial_df = pd.DataFrame(partial_rows)
    for col in PARTIAL_CSV_COLUMNS:
        if col not in partial_df.columns:
            partial_df[col] = ""
    if not partial_df.empty:
        partial_df = partial_df[PARTIAL_CSV_COLUMNS]
    partial_path = output_dir / "phase7c1_partial_fabrication_analysis.csv"
    partial_df.to_csv(partial_path, index=False)
    print(f"[SAVE] Partial fabrication analysis -> {partial_path} ({len(partial_df)} rows)")

    print_baseline_terminal_summary(results_df, errors=errors, output_dir=output_dir)
    return results_df


def parse_baseline_args():
    p = argparse.ArgumentParser(description="Phase 7C1 — baseline evaluation (no training)")
    p.add_argument("--manifest", type=str, required=True)
    p.add_argument("--ckpt", type=str, required=True)
    p.add_argument("--output_dir", type=str, default="reports/phase7/phase7c1_baseline/results")
    p.add_argument("--repo_root", type=str, default=str(_REPO_ROOT))
    p.add_argument("--device", type=str, default="cuda", choices=["cuda", "cpu"])
    p.add_argument("--pooling", type=str, default="pct_vote")
    p.add_argument("--chunk_threshold", type=float, default=0.65)
    p.add_argument("--vote_threshold", type=float, default=0.70)
    p.add_argument("--vad_mode", type=str, default="file_percentile")
    p.add_argument("--vad_rms_percentile", type=float, default=40.0)
    p.add_argument("--vad_min_speech_ratio", type=float, default=0.40)
    p.add_argument("--batch_size", type=int, default=32)
    p.add_argument("--save_chunk_timeline", action="store_true")
    known, remainder = p.parse_known_args()
    return known, remainder


def main():
    known, remainder = parse_baseline_args()
    inference_argv = list(remainder)
    inference_argv.extend(
        [
            "--ckpt",
            known.ckpt,
            "--pooling",
            known.pooling,
            "--chunk_threshold",
            str(known.chunk_threshold),
            "--vote_threshold",
            str(known.vote_threshold),
            "--vad_mode",
            known.vad_mode,
            "--vad_rms_percentile",
            str(known.vad_rms_percentile),
            "--vad_min_speech_ratio",
            str(known.vad_min_speech_ratio),
            "--batch_size",
            str(known.batch_size),
        ]
    )
    if known.save_chunk_timeline and "--save_chunk_timeline" not in inference_argv:
        inference_argv.append("--save_chunk_timeline")

    run_baseline(
        manifest_path=Path(known.manifest),
        ckpt=Path(known.ckpt),
        output_dir=Path(known.output_dir),
        inference_argv=inference_argv,
        repo_root=Path(known.repo_root),
        device_name=known.device,
    )


if __name__ == "__main__":
    main()
