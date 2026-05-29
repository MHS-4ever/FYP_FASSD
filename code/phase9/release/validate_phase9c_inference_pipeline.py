#!/usr/bin/env python3
"""Validate Phase 9C inference pipeline structure (optional sample JSON)."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


REQUIRED_SRC = [
    "release/src/audio_io.py",
    "release/src/segmentation.py",
    "release/src/feature_extraction.py",
    "release/src/ssl_embeddings.py",
    "release/src/model_loader.py",
    "release/src/inference_pipeline.py",
    "release/src/fusion_rules.py",
    "release/src/report_generator.py",
    "release/src/schemas.py",
    "release/src/utils.py",
    "release/analyze_audio_cli.py",
]

REQUIRED_ACTIVE_ARTIFACTS = [
    "release/models/origin/origin_file_model__ssl__experimental.joblib",
    "release/models/replay/replay_file_model__acoustic__experimental.joblib",
    "release/models/mixer/mixer_file_model__acoustic__experimental.joblib",
    "release/models/partial_segment/partial_segment_model__combined__experimental.joblib",
]

REQUIRED_RESULT_FIELDS = [
    "case_id",
    "status",
    "audio_metadata",
    "origin_evidence",
    "replay_evidence",
    "mixer_channel_evidence",
    "partial_fabrication_evidence",
    "segment_candidates",
    "fusion_status",
    "forensic_summary",
    "manual_review_required",
    "limitations",
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate Phase 9C inference pipeline.")
    p.add_argument("--release_root", default="release")
    p.add_argument("--sample_output", default=None)
    p.add_argument(
        "--output_report",
        default="reports/phase9/validation/phase9c_inference_pipeline_validation_report.md",
    )
    return p.parse_args()


def _validate_inference_source(root: Path, failures: list[str]) -> None:
    path = root / "release/src/inference_pipeline.py"
    if not path.is_file():
        failures.append("inference_pipeline.py missing")
        return
    text = path.read_text(encoding="utf-8")
    if "get_model_input_feature_names" not in text:
        failures.append("inference_pipeline.py must import/use get_model_input_feature_names")
    if "from .model_loader import get_model_input_feature_names" not in text:
        failures.append("inference_pipeline.py must import get_model_input_feature_names from model_loader")
    if "_partial_segment_diagnostics" not in text:
        failures.append("inference_pipeline.py must include partial segment diagnostics helper")
    if "_apply_partial_fusion_fields" not in text:
        failures.append("inference_pipeline.py must define _apply_partial_fusion_fields")
    if "_apply_replay_mixer_partial_arbitration" not in text:
        failures.append("inference_pipeline.py must define replay/mixer partial arbitration")

    fusion_path = root / "release/src/fusion_rules.py"
    if fusion_path.is_file():
        ftext = fusion_path.read_text(encoding="utf-8")
        if "_resolve_live_fusion_status" not in ftext:
            failures.append("fusion_rules.py must resolve fusion using partial_fusion_eligible")
        if "partial_fusion_eligible" not in ftext:
            failures.append("fusion_rules.py must use partial_fusion_eligible for fusion")

    # Disallow using metadata selected-feature list directly for alignment.
    bad_patterns = [
        r'align_features_to_metadata\([^)]*meta\.get\("feature_names"',
        r'align_features_to_metadata\([^)]*metadata\["feature_names"\]',
        r'feature_names\s*=\s*list\(meta\.get\("feature_names"',
    ]
    for pat in bad_patterns:
        if re.search(pat, text):
            failures.append(
                "inference_pipeline.py aligns predictions using metadata feature_names directly"
            )
            break

    loader = root / "release/src/model_loader.py"
    if loader.is_file():
        ltext = loader.read_text(encoding="utf-8")
        if "def get_model_input_feature_names" not in ltext:
            failures.append("model_loader.py missing get_model_input_feature_names")


ELEVATED_STRENGTHS = frozenset({"moderate", "high"})


def _case_hint_blob(payload: dict[str, Any]) -> str:
    case = str(payload.get("case_id", "")).lower()
    path = str(payload.get("audio_metadata", {}).get("path", "")).lower()
    return f"{case} {path}"


def _fusion_eligible_elevated_axis_count(payload: dict[str, Any]) -> int:
    axes = payload
    count = 0
    for key in ("origin_evidence", "replay_evidence", "mixer_channel_evidence"):
        ev = axes.get(key, {})
        if str(ev.get("evidence_strength", "")) in ELEVATED_STRENGTHS:
            count += 1
    partial = axes.get("partial_fabrication_evidence", {})
    if partial.get("partial_fusion_eligible") is True and str(
        partial.get("partial_evidence_strength_for_fusion", "")
    ) in ELEVATED_STRENGTHS:
        count += 1
    return count


def _axis_prediction_success(axis: dict[str, Any]) -> bool:
    if axis.get("prediction_success") is True:
        return True
    return str(axis.get("evidence_label", axis.get("label", ""))).lower() not in {
        "prediction_error",
        "not_evaluated",
    } and axis.get("probability") is not None


def validate(root: Path, release_root: Path, sample_output: Path | None) -> tuple[bool, list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []

    _validate_inference_source(root, failures)

    for rel in REQUIRED_SRC:
        if not (root / rel).is_file():
            failures.append(f"missing source file: {rel}")

    if not (release_root / "analyze_audio_cli.py").is_file():
        failures.append("analyze_audio_cli.py missing")

    for rel in REQUIRED_ACTIVE_ARTIFACTS:
        if not (root / rel).is_file():
            failures.append(f"missing active artifact: {rel}")
        meta = root / rel.replace("__experimental.joblib", "__metadata.json")
        if not meta.is_file():
            failures.append(f"missing active metadata: {meta.as_posix()}")

    paths_yaml = (release_root / "config" / "model_paths.yaml").read_text(encoding="utf-8").lower()
    if "reference/aasist" in paths_yaml or "reference/hybrid" in paths_yaml:
        failures.append("model_paths.yaml must not point to reference models")

    forbidden_tokens = ["fake_score", "real_score"]
    for rel in REQUIRED_SRC:
        text = (root / rel).read_text(encoding="utf-8").lower()
        if any(tok in text for tok in forbidden_tokens):
            if "no fake_score" not in text and "forbidden" not in text:
                failures.append(f"forbidden token in source: {rel}")

    if sample_output and sample_output.is_file():
        payload = json.loads(sample_output.read_text(encoding="utf-8"))
        blob = json.dumps(payload)
        blob_lower = blob.lower()

        for field in REQUIRED_RESULT_FIELDS:
            if field not in payload:
                failures.append(f"sample output missing field: {field}")
        if payload.get("status") != "experimental_forensic_prototype":
            failures.append("sample output status must be experimental_forensic_prototype")
        if "final_fake_real" in blob_lower:
            failures.append("sample output contains final fake/real decision field")

        if "the feature names should match" in blob_lower:
            failures.append("sample output contains sklearn feature-name mismatch text")
        if "feature names seen at fit time" in blob_lower:
            failures.append("sample output references missing fit-time feature names")
        if "prediction_error" in blob_lower:
            failures.append('sample output contains "prediction_error"')

        axes = {
            "origin": payload.get("origin_evidence", {}),
            "replay": payload.get("replay_evidence", {}),
            "mixer": payload.get("mixer_channel_evidence", {}),
            "partial": payload.get("partial_fabrication_evidence", {}),
        }

        def _is_prob(v: Any) -> bool:
            if v is None:
                return False
            s = str(v).strip().lower()
            return s not in {"", "none", "nan"}

        file_axes = [axes["origin"], axes["replay"], axes["mixer"]]
        file_probs = [a.get("probability") for a in file_axes]

        if all(not _is_prob(p) for p in file_probs):
            failures.append("origin/replay/mixer probabilities are all null")
        if all(not _axis_prediction_success(a) for a in file_axes):
            failures.append("origin/replay/mixer prediction_success all false or missing")
        if all(str(a.get("evidence_strength", "")) == "not_evaluated" for a in file_axes):
            failures.append("all file-level evidence axes are not_evaluated")

        partial = axes["partial"]
        if not partial.get("prediction_success"):
            failures.append("partial prediction_success is not true")

        required_partial_fields = (
            "partial_localization_gate",
            "high_segment_fraction",
            "topk_minus_rest_probability",
            "probability_std",
            "localized_pattern_score",
            "gated_partial_probability",
            "segment_count",
            "high_segment_count",
            "raw_max_segment_probability",
            "partial_fusion_eligible",
            "partial_evidence_strength_for_fusion",
            "partial_fusion_block_reason",
            "partial_arbitration_note",
            "broad_activation_warning",
            "localization_confidence_note",
            "top_segment_ranges",
            "high_probability_ranges",
        )
        for field in required_partial_fields:
            if field not in partial:
                failures.append(f"partial_fabrication_evidence missing field: {field}")

        if partial.get("prediction_success") is True:
            for field in (
                "partial_fusion_eligible",
                "partial_evidence_strength_for_fusion",
                "partial_fusion_block_reason",
                "broad_activation_warning",
                "localization_confidence_note",
            ):
                val = partial.get(field)
                if val is None:
                    failures.append(f"partial_fabrication_evidence.{field} is null with prediction_success=true")
            if not isinstance(partial.get("partial_fusion_eligible"), bool):
                failures.append("partial_fusion_eligible must be boolean when prediction_success=true")
            if not isinstance(partial.get("broad_activation_warning"), bool):
                failures.append("broad_activation_warning must be boolean when prediction_success=true")
            if not str(partial.get("localization_confidence_note", "")).strip():
                failures.append("localization_confidence_note must be non-empty when prediction_success=true")

        partial_prob = partial.get("probability")
        partial_max = partial.get("max_segment_probability")
        if not _is_prob(partial_prob) and not _is_prob(partial_max):
            failures.append("partial_fabrication_evidence probability/max_segment_probability is null")

        partial_gate = str(partial.get("partial_localization_gate", ""))
        fusion = str(payload.get("fusion_status", ""))
        if partial_gate == "global_activation_not_localized" and fusion in {
            "suspicious_partial_fabrication_experimental",
            "suspicious_mixed_evidence_experimental",
        }:
            failures.append(
                "global partial activation must not produce suspicious_partial or suspicious_mixed fusion alone"
            )

        hint = _case_hint_blob(payload)
        is_ai_direct = "ai_direct" in hint or "ai_001_direct" in hint
        is_human_direct = "human_direct" in hint
        is_ai_mixer = "ai_mixer" in hint
        is_replay_case = "replay" in hint

        origin_prob = axes["origin"].get("probability")
        replay_prob = axes["replay"].get("probability")
        mixer_prob = axes["mixer"].get("probability")
        origin_strength = str(axes["origin"].get("evidence_strength", ""))
        replay_strength = str(axes["replay"].get("evidence_strength", ""))
        mixer_strength = str(axes["mixer"].get("evidence_strength", ""))
        partial_fusion_eligible = partial.get("partial_fusion_eligible") is True

        if (is_ai_direct or is_human_direct) and partial_gate == "global_activation_not_localized":
            if fusion == "suspicious_mixed_evidence_experimental":
                failures.append("broad partial activation caused suspicious_mixed on direct-origin audio")

        if is_ai_direct and origin_strength in ELEVATED_STRENGTHS:
            if replay_strength not in ELEVATED_STRENGTHS and mixer_strength not in ELEVATED_STRENGTHS:
                if not partial_fusion_eligible and fusion != "suspicious_origin_experimental":
                    failures.append(
                        "ai_direct with high origin and low replay/mixer should fuse to suspicious_origin_experimental"
                    )

        if is_ai_mixer and mixer_strength in ELEVATED_STRENGTHS and not partial_fusion_eligible:
            if fusion == "suspicious_mixed_evidence_experimental":
                failures.append(
                    "ai_mixer must not be suspicious_mixed when partial_fusion_eligible is false"
                )
            if fusion != "suspicious_mixer_channel_experimental":
                failures.append(
                    "ai_mixer with high mixer and partial not fusion-eligible should be suspicious_mixer_channel_experimental"
                )

        if is_replay_case and replay_strength in ELEVATED_STRENGTHS and not partial_fusion_eligible:
            if fusion == "suspicious_mixed_evidence_experimental":
                failures.append(
                    "replay case must not be suspicious_mixed when partial_fusion_eligible is false"
                )
            if fusion != "suspicious_replay_experimental":
                failures.append(
                    "replay case with high replay and partial not fusion-eligible should be suspicious_replay_experimental"
                )

        if fusion == "suspicious_mixed_evidence_experimental":
            eligible_count = _fusion_eligible_elevated_axis_count(payload)
            if eligible_count < 2:
                failures.append(
                    "suspicious_mixed_evidence_experimental requires at least two fusion-eligible elevated axes"
                )

        partial_probs = [s.get("partial_probability") for s in payload.get("segment_candidates", [])]
        if partial_probs and all(not _is_prob(p) for p in partial_probs):
            failures.append("all segment candidates have null partial_probability")

        numeric_axis_count = sum(
            1 for a in axes.values() if _is_prob(a.get("probability")) or _is_prob(a.get("max_segment_probability"))
        )
        if numeric_axis_count == 0:
            failures.append("no active axis has numeric probability")

        if numeric_axis_count == 0 and fusion == "inconclusive_manual_review_experimental":
            failures.append("fusion inconclusive only because all predictions failed")

        summary = str(payload.get("forensic_summary", "")).lower()
        if numeric_axis_count == 0 and "did not succeed" not in summary and "prediction" in summary:
            failures.append("summary inconsistent with failed predictions")

        for seg in payload.get("segment_candidates", []):
            wording = str(seg.get("candidate_wording", "")).lower()
            if "candidate" not in wording and seg:
                warnings.append("segment candidate wording may be missing 'candidate'")
            if "suspicious_segment_flag" in wording:
                failures.append("segment output must not use suspicious_segment_flag wording")
    else:
        warnings.append("no sample_output provided for result JSON validation")

    return len(failures) == 0, failures, warnings


def write_report(path: Path, ok: bool, failures: list[str], warnings: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Phase 9C Inference Pipeline Validation Report",
        "",
        f"- Status: {'PASS' if ok else 'FAIL'}",
    ]
    if failures:
        lines.append("- Failures:")
        for f in failures:
            lines.append(f"  - {f}")
    if warnings:
        lines.append("- Warnings:")
        for w in warnings:
            lines.append(f"  - {w}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    root = repo_root()
    release_root = root / args.release_root
    sample = Path(args.sample_output) if args.sample_output else None
    if sample and not sample.is_absolute():
        sample = (root / sample).resolve()
    ok, failures, warnings = validate(root, release_root, sample)
    report = root / args.output_report
    write_report(report, ok, failures, warnings)
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
