#!/usr/bin/env python3
"""Validate Phase 8E-0 assembled datasets."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]

FORBIDDEN_DECISION_COLUMNS = {
    "fake_score",
    "real_score",
    "ai_score",
    "predicted_label",
    "prediction",
    "replay_decision",
    "mixer_decision",
    "final_forensic_status",
    "suspicious_segment_flag",
    "evidence_origin_score",
    "origin_score",
}

PHASE8B_PLACEHOLDER_COLUMNS = {
    "evidence_origin_human_score",
    "evidence_origin_ai_score",
    "evidence_origin_mixed_score",
    "evidence_origin_unknown_score",
    "evidence_replay_score",
    "evidence_mixer_channel_score",
    "evidence_partial_fabrication_score",
    "evidence_splice_score",
    "evidence_quality_score",
    "calibrated_origin_label",
    "calibrated_manipulation_labels",
    "forensic_risk_level",
    "manual_review_required",
    "manual_review_reason",
    "fusion_trace",
    "forensic_summary",
    "evidence_source_paths",
    "segment_origin_human_score",
    "segment_origin_ai_score",
    "segment_origin_mixed_score",
    "segment_origin_unknown_score",
    "replay_score",
    "mixer_channel_score",
    "partial_fabrication_score",
    "splice_score",
    "quality_score",
    "segment_reason",
    "segment_evidence_source",
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate Phase 8E-0 datasets.")
    p.add_argument("--input_dir", default="reports/phase8/models/phase8e0")
    p.add_argument("--file_table", default="reports/phase8/evidence_table/phase8b_file_evidence_table.csv")
    p.add_argument("--segment_table", default="reports/phase8/evidence_table/phase8b_segment_evidence_table.csv")
    p.add_argument(
        "--output_report",
        default="reports/phase8/validation/phase8e0_dataset_validation_report.md",
    )
    return p.parse_args()


def _resolve(path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else (REPO_ROOT / p).resolve()


def _read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def validate(args: argparse.Namespace) -> dict[str, object]:
    blocking: list[str] = []
    warnings: list[str] = []

    base = _resolve(args.input_dir)
    expected = {
        "file_master": base / "phase8e0_file_level_master_dataset.csv",
        "segment_master": base / "phase8e0_segment_level_master_dataset.csv",
        "origin": base / "phase8e0_origin_file_dataset.csv",
        "replay": base / "phase8e0_replay_file_dataset.csv",
        "mixer": base / "phase8e0_mixer_file_dataset.csv",
        "partial": base / "phase8e0_partial_fabrication_localization_prep.csv",
        "audit": base / "phase8e0_leakage_audit.csv",
        "summary": base / "phase8e0_dataset_summary.csv",
    }
    for name, p in expected.items():
        if not p.is_file():
            blocking.append(f"Missing required output CSV ({name}): {p}")
    if blocking:
        return {"status": "FAIL", "blocking": blocking, "warnings": warnings}

    f8b = _read(_resolve(args.file_table))
    s8b = _read(_resolve(args.segment_table))
    fm = _read(expected["file_master"])
    sm = _read(expected["segment_master"])
    od = _read(expected["origin"])
    rd = _read(expected["replay"])
    md = _read(expected["mixer"])
    pdp = _read(expected["partial"])
    audit = _read(expected["audit"])

    dataset_frames = [
        ("file_master", fm),
        ("segment_master", sm),
        ("origin", od),
        ("replay", rd),
        ("mixer", md),
        ("partial", pdp),
    ]

    for name, df in dataset_frames:
        schema_cols = [c for c in df.columns if c == "schema_version"]
        if len(schema_cols) != 1:
            blocking.append(f"{name} must contain exactly one schema_version column")
        schema_artifacts = [c for c in df.columns if c.startswith("schema_version_")]
        if schema_artifacts:
            blocking.append(f"{name} contains schema_version merge artifacts: {schema_artifacts}")
        if "schema_version" in df.columns:
            bad_schema = df[df["schema_version"] != "phase8e0_v1"]
            if len(bad_schema):
                blocking.append(f"{name} has non-phase8e0_v1 schema_version rows: {len(bad_schema)}")

    if len(fm) != 184:
        blocking.append(f"File master rows mismatch: expected 184 found {len(fm)}")
    if len(sm) != 4189:
        blocking.append(f"Segment master rows mismatch: expected 4189 found {len(sm)}")
    if fm["file_id"].duplicated().any():
        blocking.append("file_id is not unique in file master")
    if sm["segment_id"].duplicated().any():
        blocking.append("segment_id is not unique in segment master")

    for col in [
        "target_origin_multiclass",
        "target_is_replay",
        "target_is_mixer_channel",
        "target_is_partial_fabrication_file",
    ]:
        if col not in fm.columns:
            blocking.append(f"Missing file target column: {col}")
    for col in [
        "eligible_origin_file_model",
        "eligible_replay_file_model",
        "eligible_mixer_file_model",
        "eligible_partial_segment_training",
    ]:
        if col not in fm.columns:
            blocking.append(f"Missing file eligibility flag: {col}")
    if "segment_label_source" not in sm.columns:
        blocking.append("segment_label_source missing in segment master")

    clean_counts = fm.get("target_is_clean", pd.Series(dtype=str)).value_counts().to_dict()
    if clean_counts.get("1", 0) != 46 or clean_counts.get("0", 0) != 138:
        blocking.append(f"target_is_clean counts mismatch (expected 1=46,0=138): {clean_counts}")

    # Task filters
    if len(od):
        bad_origin = od[
            (~od["target_origin_multiclass"].isin(["human", "ai_synthetic"]))
            | (od["target_is_replay"] == "1")
            | (od["target_is_mixer_channel"] == "1")
            | (od["target_is_partial_fabrication_file"] == "1")
        ]
        if len(bad_origin):
            blocking.append(f"Origin dataset contains excluded rows: {len(bad_origin)}")
        if not od["known_manipulation_labels"].astype(str).str.strip().str.lower().eq("clean").all():
            blocking.append("Origin dataset contains non-clean manipulation rows")
        if not od["known_origin_label"].isin(["human", "ai_synthetic"]).all():
            blocking.append("Origin dataset has invalid origin labels")
    if len(od) != 46:
        blocking.append(f"Origin dataset row count mismatch: expected 46 found {len(od)}")
    if len(rd):
        bad_replay = rd[~rd["target_is_replay"].isin(["0", "1"])]
        if len(bad_replay):
            blocking.append(f"Replay dataset has invalid labels: {len(bad_replay)}")
        bad_replay_domain = rd[
            ~(
                ((rd["target_is_replay"] == "1") & (rd["target_is_clean"] == "0"))
                | ((rd["target_is_replay"] == "0") & (rd["target_is_clean"] == "1"))
            )
        ]
        if len(bad_replay_domain):
            blocking.append(f"Replay dataset not clean-vs-replay only: {len(bad_replay_domain)}")
        allowed_replay_labels = {"clean", "replay_rerecorded"}
        if not rd["known_manipulation_labels"].astype(str).str.strip().str.lower().isin(allowed_replay_labels).all():
            blocking.append("Replay dataset contains non clean/replay labels")
    if len(rd) != 92:
        blocking.append(f"Replay dataset row count mismatch: expected 92 found {len(rd)}")
    if len(md):
        bad_mixer = md[~md["target_is_mixer_channel"].isin(["0", "1"])]
        if len(bad_mixer):
            blocking.append(f"Mixer dataset has invalid labels: {len(bad_mixer)}")
        bad_mixer_domain = md[
            ~(
                ((md["target_is_mixer_channel"] == "1") & (md["target_is_clean"] == "0"))
                | ((md["target_is_mixer_channel"] == "0") & (md["target_is_clean"] == "1"))
            )
        ]
        if len(bad_mixer_domain):
            blocking.append(f"Mixer dataset not clean-vs-mixer only: {len(bad_mixer_domain)}")
        allowed_mixer_labels = {"clean", "mixer_channel_processed"}
        if not md["known_manipulation_labels"].astype(str).str.strip().str.lower().isin(allowed_mixer_labels).all():
            blocking.append("Mixer dataset contains non clean/mixer labels")
    if len(md) != 92:
        blocking.append(f"Mixer dataset row count mismatch: expected 92 found {len(md)}")

    if len(pdp):
        if not (pdp["eligible_partial_segment_training"] == "false").all():
            blocking.append("Partial localization has rows with eligible_partial_segment_training != false")
        if "reason_not_training_label" not in pdp.columns:
            blocking.append("Partial localization missing reason_not_training_label")
        else:
            if pdp["reason_not_training_label"].astype(str).str.strip().eq("").any():
                blocking.append("Partial localization has blank reason_not_training_label")
        wrong_partial = pdp[
            (pdp["inherited_target_is_partial_fabrication_file"] == "1")
            & (pdp["segment_label_source"] != "true_segment_timestamp")
            & (pdp["eligible_partial_segment_training"] != "false")
        ]
        if len(wrong_partial):
            blocking.append(f"Partial localization has unsafe segment training eligibility: {len(wrong_partial)}")

    # Forbidden decision columns + evidence scores filled
    for df_name, df in dataset_frames:
        for col in FORBIDDEN_DECISION_COLUMNS:
            if col in df.columns:
                blocking.append(f"{df_name} contains forbidden prediction/decision column: {col}")
        placeholder_cols = sorted(PHASE8B_PLACEHOLDER_COLUMNS.intersection(set(df.columns)))
        if placeholder_cols:
            blocking.append(f"{df_name} contains Phase 8B placeholder columns: {placeholder_cols}")
        evidence_cols = [c for c in df.columns if c.startswith("evidence_")]
        for c in evidence_cols:
            if df[c].astype(str).str.strip().ne("").any():
                blocking.append(f"{df_name} has filled evidence score column: {c}")

    # Feature presence
    acoustic_cols_f = [c for c in fm.columns if c.startswith("mfcc_") or c in {"rms_mean", "spectral_centroid_mean", "snr_proxy"}]
    acoustic_cols_s = [c for c in sm.columns if c.startswith("mfcc_") or c in {"rms_mean", "spectral_centroid_mean", "snr_proxy"}]
    if not acoustic_cols_f or not acoustic_cols_s:
        blocking.append("Acoustic feature columns not found in master datasets")
    ssl_cols_f = [c for c in fm.columns if c.startswith("ssl_emb_")]
    ssl_cols_s = [c for c in sm.columns if c.startswith("ssl_emb_")]
    if not ssl_cols_f or not ssl_cols_s:
        blocking.append("SSL embedding columns not found in master datasets")

    # Leakage audit checks
    if "severity" not in audit.columns:
        blocking.append("Leakage audit missing severity column")
    blocking_audit = audit[audit.get("severity", pd.Series(dtype=str)) == "blocking"]
    blocking_audit_count = int(len(blocking_audit))
    expected_partial_risk = audit[
        (audit.get("audit_item", pd.Series(dtype=str)) == "partial_inherited_label_risk")
        & (audit.get("severity", pd.Series(dtype=str)).isin(["warning", "blocked_task", "blocking"]))
    ]
    if len(expected_partial_risk) == 0:
        warnings.append("Partial inherited-label risk entry is missing from leakage audit")
    if blocking_audit_count > 0:
        # Keep all other blocking leakage items as validation blockers.
        non_partial_blocking = blocking_audit[blocking_audit["audit_item"] != "partial_inherited_label_risk"]
        if len(non_partial_blocking):
            blocking.append(f"Leakage audit contains blocking items: {len(non_partial_blocking)}")
        else:
            warnings.append("Partial fabrication segment training is intentionally blocked.")

    # Checkpoint/model artifacts should not be created by this phase
    model_artifacts = list(base.glob("*.pt")) + list(base.glob("*.pth")) + list(base.glob("*.ckpt"))
    if model_artifacts:
        blocking.append(f"Unexpected model artifacts found: {[str(p.name) for p in model_artifacts]}")

    return {
        "status": "FAIL" if blocking else "PASS",
        "blocking": blocking,
        "warnings": warnings,
        "file_rows": len(fm),
        "segment_rows": len(sm),
        "origin_rows": len(od),
        "replay_rows": len(rd),
        "mixer_rows": len(md),
        "partial_rows": len(pdp),
        "origin_dist": dict(od["target_origin_multiclass"].value_counts()) if "target_origin_multiclass" in od.columns else {},
        "replay_dist": dict(rd["target_is_replay"].value_counts()) if "target_is_replay" in rd.columns else {},
        "mixer_dist": dict(md["target_is_mixer_channel"].value_counts()) if "target_is_mixer_channel" in md.columns else {},
        "partial_elig_dist": dict(pdp["eligible_partial_segment_training"].value_counts()) if "eligible_partial_segment_training" in pdp.columns else {},
        "blocking_audit_count": blocking_audit_count,
        "clean_counts": clean_counts,
    }


def write_report(path: Path, result: dict[str, object]) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        "# Phase 8E-0 Dataset Validation Report",
        "",
        f"**Generated:** {now}",
        f"**Status:** **{result.get('status', 'FAIL')}**",
        "",
        "> Phase 8E-0 validates assembled datasets only. It does not train models.",
        "",
        "## Row Counts",
        "",
        f"- file master rows: {result.get('file_rows', 0)}",
        f"- segment master rows: {result.get('segment_rows', 0)}",
        f"- origin task rows: {result.get('origin_rows', 0)}",
        f"- replay task rows: {result.get('replay_rows', 0)}",
        f"- mixer task rows: {result.get('mixer_rows', 0)}",
        f"- partial localization prep rows: {result.get('partial_rows', 0)}",
        "",
        "## Label Distributions",
        "",
        f"- target_is_clean: {result.get('clean_counts', {})}",
        f"- origin: {result.get('origin_dist', {})}",
        f"- replay: {result.get('replay_dist', {})}",
        f"- mixer: {result.get('mixer_dist', {})}",
        f"- partial eligibility: {result.get('partial_elig_dist', {})}",
        "",
        "## Leakage Summary",
        "",
        f"- blocking leakage items: {result.get('blocking_audit_count', 0)}",
    ]
    if result.get("blocking"):
        lines.extend(["", "## Blocking Errors", ""])
        lines.extend(f"- {x}" for x in result["blocking"])  # type: ignore[index]
    if result.get("warnings"):
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {x}" for x in result["warnings"])  # type: ignore[index]
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- No model artifacts/checkpoints should be created in Phase 8E-0.",
            "- No prediction columns or evidence score filling is allowed.",
            "- Partial fabrication segment training remains blocked unless true segment timestamps exist.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    result = validate(args)
    out = _resolve(args.output_report)
    write_report(out, result)
    print(f"Validation: {result.get('status')}")
    print(f"Report -> {out}")
    return 1 if result.get("status") == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
