"""
Phase 7A: Run Phase 6 inference over a forensic test manifest and aggregate results.

Does not train models. Reuses code/phase6/explain_prediction.py predict_file().
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import pandas as pd
import torch
from tqdm import tqdm

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "code"))

from phase3.hybrid_resnet_environmental import HybridResNetEnvironmental
from phase6.explain_prediction import ATTACK_TYPE_NAMES, parse_args as phase6_parse_args, predict_file
from phase7.analyze_forensic_test_results import (
    build_forensic_summary,
    compute_partial_region_metrics,
    evaluate_correct_origin_basic,
    evaluate_failure_type,
    has_valid_suspicious_timestamps,
    parse_bool,
    print_terminal_summary,
)
from features.environmental_features import EnvironmentalFeatureExtractor


RESULT_CSV_COLUMNS = [
    "test_id",
    "filename",
    "audio_path",
    "priority",
    "source_origin",
    "manipulation_type",
    "language",
    "speaker_type",
    "device_chain",
    "platform",
    "ground_truth_origin",
    "ground_truth_manipulation",
    "origin_label",
    "manipulation_label",
    "attack_hint",
    "risk_level",
    "partial_fabrication_detected",
    "suspicious_start_time",
    "suspicious_end_time",
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
    "n_chunks_inside",
    "n_chunks_outside",
    "inside_region_avg_spoof",
    "outside_region_avg_spoof",
    "inside_region_max_spoof",
    "outside_region_max_spoof",
    "inside_region_dominant_attack",
    "outside_region_dominant_attack",
    "partial_region_detected",
    "forensic_summary",
    "correct_origin_basic",
    "failure_type",
    "notes",
    "error",
]


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


def _save_chunk_timeline(test_id: str, chunk_timeline: list, timeline_dir: Path) -> None:
    if not chunk_timeline:
        return
    timeline_dir.mkdir(parents=True, exist_ok=True)
    json_path = timeline_dir / f"{test_id}_chunks.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(chunk_timeline, f, indent=2)
    csv_path = timeline_dir / f"{test_id}_chunks.csv"
    pd.DataFrame(chunk_timeline).to_csv(csv_path, index=False)


def _build_args(inference_argv: list[str]):
    """Build Phase 6 args namespace from forensic CLI + forwarded inference flags."""
    saved_argv = sys.argv
    try:
        sys.argv = ["explain_prediction.py", *inference_argv]
        args = phase6_parse_args()
    finally:
        sys.argv = saved_argv
    return args


def _manifest_row_to_base(row: pd.Series) -> dict:
    return {
        "test_id": str(row.get("test_id", "")).strip(),
        "audio_path": str(row.get("audio_path", "")).strip(),
        "priority": str(row.get("priority", "")).strip(),
        "source_origin": str(row.get("source_origin", "")).strip(),
        "manipulation_type": str(row.get("manipulation_type", "")).strip(),
        "language": str(row.get("language", "")).strip(),
        "speaker_type": str(row.get("speaker_type", "")).strip(),
        "device_chain": str(row.get("device_chain", "")).strip(),
        "platform": str(row.get("platform", "")).strip(),
        "ground_truth_origin": str(row.get("ground_truth_origin", "")).strip(),
        "ground_truth_manipulation": str(row.get("ground_truth_manipulation", "")).strip(),
        "origin_label": str(row.get("origin_label", "")).strip(),
        "manipulation_label": str(row.get("manipulation_label", "")).strip(),
        "attack_hint": str(row.get("attack_hint", "")).strip(),
        "risk_level": str(row.get("risk_level", "")).strip(),
        "partial_fabrication_detected": parse_bool(row.get("partial_fabrication_detected")),
        "suspicious_start_time": row.get("suspicious_start_time", ""),
        "suspicious_end_time": row.get("suspicious_end_time", ""),
        "notes": str(row.get("notes", "") or row.get("expected_forensic_result", "")).strip(),
    }


def _merge_inference_row(base: dict, inference: dict, partial_metrics: dict) -> dict:
    attack_row = _attack_probs_row(inference.get("attack_probs"))
    row = {
        **base,
        "filename": inference.get("filename") or Path(base["audio_path"]).name,
        "audio_path": inference.get("filepath") or base["audio_path"],
        "prediction": inference.get("prediction", ""),
        "confidence": inference.get("confidence", ""),
        "decision_score": inference.get("decision_score", inference.get("spoof_prob", "")),
        "effective_threshold": inference.get("effective_threshold", ""),
        "attack_type": inference.get("attack_type", ""),
        "attack_type_conf": inference.get("attack_type_conf", ""),
        **attack_row,
        "n_chunks_used": inference.get("n_chunks_used", inference.get("n_chunks", "")),
        "n_chunks_total": inference.get("n_chunks_total", ""),
        **partial_metrics,
        "forensic_summary": build_forensic_summary(base, inference, partial_metrics),
        "error": "",
    }
    row["correct_origin_basic"] = evaluate_correct_origin_basic(row)
    row["failure_type"] = evaluate_failure_type(row)
    return row


def run_suite(
    manifest_path: Path,
    ckpt: Path,
    output_dir: Path,
    inference_argv: list[str],
    repo_root: Path,
    device_name: str = "cuda",
) -> pd.DataFrame:
    manifest_path = manifest_path.resolve()
    if not manifest_path.is_file():
        template = manifest_path.parent / "forensic_test_manifest_template.csv"
        hint = (
            f"Manifest not found: {manifest_path}\n"
            f"Copy the template and fill your test cases:\n"
            f'  copy "{template}" "{manifest_path}"'
        )
        raise FileNotFoundError(hint)

    output_dir = output_dir.resolve()
    json_dir = output_dir / "json_outputs"
    timeline_dir = output_dir / "chunk_timelines"
    json_dir.mkdir(parents=True, exist_ok=True)

    manifest_df = pd.read_csv(manifest_path, low_memory=False)
    if "audio_path" not in manifest_df.columns:
        raise ValueError(f"Manifest missing audio_path column: {manifest_path}")

    args = _build_args(inference_argv)
    args.save_chunk_timeline = "--save_chunk_timeline" in inference_argv or getattr(args, "save_chunk_timeline", False)

    device = torch.device(device_name if (device_name == "cpu" or torch.cuda.is_available()) else "cpu")
    print(f"[DEVICE] {device}")

    ckpt = ckpt.resolve()
    ckpt_data = torch.load(str(ckpt), map_location=device, weights_only=False)
    state_dict = ckpt_data.get("model_state_dict", ckpt_data)
    model = HybridResNetEnvironmental(n_attack_types=4, dropout=0.3).to(device)
    model.load_state_dict(state_dict)
    model.eval()
    print(f"[OK] Loaded checkpoint: {ckpt}")

    env_extractor = EnvironmentalFeatureExtractor(sr=16000)
    results: list[dict] = []
    errors = 0

    for _, manifest_row in tqdm(manifest_df.iterrows(), total=len(manifest_df), desc="Forensic tests", colour="cyan"):
        base = _manifest_row_to_base(manifest_row)
        test_id = base["test_id"] or f"row_{len(results)}"
        audio_path = _resolve_audio_path(base["audio_path"], repo_root)

        if not audio_path.is_file():
            err_row = {col: "" for col in RESULT_CSV_COLUMNS}
            err_row.update(base)
            err_row["test_id"] = test_id
            err_row["filename"] = audio_path.name
            err_row["audio_path"] = str(audio_path)
            err_row["error"] = f"audio_not_found: {audio_path}"
            err_row["correct_origin_basic"] = "no"
            err_row["failure_type"] = "missing_audio"
            results.append(err_row)
            errors += 1
            print(f"[ERROR] {test_id}: missing audio {audio_path}")
            continue

        try:
            inference = predict_file(str(audio_path), model, device, args, env_extractor=env_extractor)
            partial_metrics = compute_partial_region_metrics(
                chunk_timeline=inference.get("chunk_timeline") or [],
                suspicious_start=base.get("suspicious_start_time"),
                suspicious_end=base.get("suspicious_end_time"),
                manifest_partial_gt=base.get("partial_fabrication_detected"),
            )
            if (
                str(base.get("manipulation_type", "")).lower() == "partial_ai_insert"
                and not has_valid_suspicious_timestamps(
                    base.get("suspicious_start_time"), base.get("suspicious_end_time")
                )
            ):
                partial_metrics["partial_eval_status"] = "partial_not_evaluated_missing_timestamp"

            out_json = {
                "test_id": test_id,
                "manifest": base,
                "inference": inference,
                "partial_fabrication_analysis": partial_metrics,
            }
            json_path = json_dir / f"{test_id}.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(out_json, f, indent=2)

            if args.save_chunk_timeline and inference.get("chunk_timeline"):
                _save_chunk_timeline(test_id, inference["chunk_timeline"], timeline_dir)

            row = _merge_inference_row(base, inference, partial_metrics)
            results.append(row)
        except Exception as exc:
            err_row = {col: "" for col in RESULT_CSV_COLUMNS}
            err_row.update(base)
            err_row["test_id"] = test_id
            err_row["filename"] = audio_path.name
            err_row["audio_path"] = str(audio_path)
            err_row["error"] = str(exc)
            err_row["correct_origin_basic"] = "no"
            err_row["failure_type"] = "inference_error"
            results.append(err_row)
            errors += 1
            print(f"[ERROR] {test_id}: {exc}")

    results_df = pd.DataFrame(results)
    for col in RESULT_CSV_COLUMNS:
        if col not in results_df.columns:
            results_df[col] = ""
    results_df = results_df[RESULT_CSV_COLUMNS + [c for c in results_df.columns if c not in RESULT_CSV_COLUMNS]]

    csv_path = output_dir / "forensic_test_results.csv"
    results_df.to_csv(csv_path, index=False)
    print(f"[SAVE] Results CSV -> {csv_path}")
    print_terminal_summary(results_df, errors=errors, title="Phase 7A forensic test suite")
    return results_df


def parse_forensic_args():
    p = argparse.ArgumentParser(description="Phase 7A — run forensic test suite via Phase 6 inference")
    p.add_argument("--manifest", type=str, required=True, help="Filled forensic_test_manifest.csv")
    p.add_argument("--ckpt", type=str, required=True, help="Phase 4/6 hybrid checkpoint (.pth)")
    p.add_argument("--output_dir", type=str, default="reports/phase7/phase7_forensic_tests/results")
    p.add_argument("--repo_root", type=str, default=str(_REPO_ROOT), help="Repo root for relative audio paths")
    p.add_argument("--device", type=str, default="cuda", choices=["cuda", "cpu"])
    p.add_argument(
        "--inference_args",
        type=str,
        default="",
        help="Optional extra Phase 6 flags as a single quoted string",
    )
    known, remainder = p.parse_known_args()
    return known, remainder


def main():
    known, remainder = parse_forensic_args()
    inference_argv = list(remainder)
    if known.inference_args:
        inference_argv.extend(known.inference_args.split())

    if "--ckpt" not in inference_argv:
        inference_argv.extend(["--ckpt", known.ckpt])

    run_suite(
        manifest_path=Path(known.manifest),
        ckpt=Path(known.ckpt),
        output_dir=Path(known.output_dir),
        inference_argv=inference_argv,
        repo_root=Path(known.repo_root),
        device_name=known.device,
    )


if __name__ == "__main__":
    main()
