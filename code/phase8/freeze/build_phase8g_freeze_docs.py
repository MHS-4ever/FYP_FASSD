#!/usr/bin/env python3
"""
Phase 8G: build Phase 8 freeze documentation bundle.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]

CORE_REQUIRED_FILES = [
    "reports/phase8/fusion/phase8f/phase8f_file_fusion_records.csv",
    "reports/phase8/fusion/phase8f/phase8f_fusion_summary.csv",
    "reports/phase8/fusion/phase8f/phase8f_fusion_report.md",
    "reports/phase8/validation/phase8f_fusion_validation_report.md",
    "reports/phase8/models/phase8e1/phase8e1_metrics_summary.csv",
    "reports/phase8/models/phase8e1a/phase8e1a_threshold_recommendations.csv",
    "reports/phase8/models/phase8e3/phase8e3_partial_segment_metrics_summary.csv",
    "reports/phase8/validation/phase8e3_results_validation_report.md",
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build Phase 8G freeze docs.")
    p.add_argument("--output_dir", default="reports/phase8/freeze")
    p.add_argument("--fusion_dir", default="reports/phase8/fusion/phase8f")
    p.add_argument("--phase8e1_dir", default="reports/phase8/models/phase8e1")
    p.add_argument("--phase8e1a_dir", default="reports/phase8/models/phase8e1a")
    p.add_argument("--phase8e2_dir", default="reports/phase8/models/phase8e2")
    p.add_argument("--phase8e3_dir", default="reports/phase8/models/phase8e3")
    p.add_argument("--roadmap_output", default="reports/phase8/roadmap/phase8g_status.md")
    p.add_argument("--no_progress", action="store_true")
    return p.parse_args()


def _resolve(path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else (REPO_ROOT / p).resolve()


def _safe_read_csv(path: Path) -> pd.DataFrame:
    if not path.is_file():
        return pd.DataFrame()
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def _to_str(v: Any) -> str:
    return "" if v is None else str(v)


def _build_manifest_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    tracked = [
        ("output_csv", "8B", "reports/phase8/evidence_table/phase8b_build_report.md", "phase8b evidence table build report", "accepted"),
        ("output_csv", "8C", "reports/phase8/features/phase8c_feature_extraction_report.md", "phase8c feature extraction report", "accepted"),
        ("output_csv", "8C-A1", "reports/phase8/features/audit/phase8c_a1_acoustic_feature_audit_report.md", "phase8c audit report", "accepted"),
        ("output_csv", "8D", "reports/phase8/embeddings/phase8d_ssl_embedding_extraction_report.md", "phase8d embeddings extraction report", "accepted"),
        ("output_csv", "8D-A1", "reports/phase8/embeddings/audit/phase8d_a1_ssl_embedding_audit_report.md", "phase8d audit report", "accepted"),
        ("output_csv", "8E-0", "reports/phase8/models/phase8e0/phase8e0_assembly_report.md", "phase8e0 dataset assembly report", "accepted"),
        ("output_csv", "8E-1", "reports/phase8/models/phase8e1/phase8e1_metrics_summary.csv", "phase8e1 file-level metrics summary", "accepted"),
        ("output_csv", "8E-1A", "reports/phase8/models/phase8e1a/phase8e1a_threshold_recommendations.csv", "phase8e1a threshold recommendations", "accepted"),
        ("output_csv", "8E-2", "reports/phase8/models/phase8e2/phase8e2_partial_localization_report.md", "phase8e2 partial localization report", "accepted"),
        ("output_csv", "8E-3", "reports/phase8/models/phase8e3/phase8e3_partial_segment_metrics_summary.csv", "phase8e3 segment metrics summary", "accepted_with_limitations"),
        ("output_csv", "8F", "reports/phase8/fusion/phase8f/phase8f_file_fusion_records.csv", "phase8f file fusion records", "accepted_with_limitations"),
        ("output_csv", "8F", "reports/phase8/fusion/phase8f/phase8f_fusion_summary.csv", "phase8f fusion summary", "accepted_with_limitations"),
        ("output_md", "8F", "reports/phase8/fusion/phase8f/phase8f_fusion_report.md", "phase8f fusion report", "accepted_with_limitations"),
        ("validation", "8F", "reports/phase8/validation/phase8f_fusion_validation_report.md", "phase8f validation report", "accepted"),
        ("validation", "8E-3", "reports/phase8/validation/phase8e3_results_validation_report.md", "phase8e3 validation report", "accepted"),
    ]
    for item_type, phase, rel, role, freeze_status in tracked:
        p = _resolve(rel)
        exists = "true" if p.is_file() else "false"
        status = freeze_status
        if exists == "false":
            status = "missing_required" if rel in CORE_REQUIRED_FILES else "missing_optional"
        rows.append(
            {
                "item_type": item_type,
                "phase": phase,
                "file_path": rel.replace("\\", "/"),
                "exists": exists,
                "role": role,
                "freeze_status": status,
                "notes": "core_freeze_input" if rel in CORE_REQUIRED_FILES else "",
            }
        )
    return rows


def main() -> int:
    args = parse_args()
    out_dir = _resolve(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    fusion_dir = _resolve(args.fusion_dir)
    e1_dir = _resolve(args.phase8e1_dir)
    e1a_dir = _resolve(args.phase8e1a_dir)
    e3_dir = _resolve(args.phase8e3_dir)

    fusion_summary = _safe_read_csv(fusion_dir / "phase8f_fusion_summary.csv")
    thresh_df = _safe_read_csv(e1a_dir / "phase8e1a_threshold_recommendations.csv")
    e1_metrics = _safe_read_csv(e1_dir / "phase8e1_metrics_summary.csv")
    e3_metrics = _safe_read_csv(e3_dir / "phase8e3_partial_segment_metrics_summary.csv")

    # Final summary doc
    (out_dir / "phase8g_phase8_final_summary.md").write_text(
        "\n".join(
            [
                "# Phase 8 Final Summary (Phase 8G)",
                "",
                "## What Phase 8 Did",
                "Phase 8 built a multi-axis forensic evidence engine for audio analysis.",
                "It focuses on evidence indicators instead of a single fake/real score.",
                "",
                "## Why No Binary Fake/Real",
                "- replay indicators can happen for human or AI-origin audio",
                "- mixer/channel processing can happen for human or AI-origin audio",
                "- partial fabrication can be local inside a file",
                "- one score would hide important forensic context",
                "",
                "## Phase-by-Phase Achievements",
                "- Phase 8B: evidence table builder complete",
                "- Phase 8C / 8C-A1: acoustic features and audit complete",
                "- Phase 8D / 8D-A1: frozen SSL embeddings and audit complete",
                "- Phase 8E-0: dataset assembly and leakage audit complete",
                "- Phase 8E-1 / 8E-1A: file-level evidence models + threshold review complete",
                "- Phase 8E-2 / 8E-3: timestamp-based partial localization + segment model complete",
                "- Phase 8F: multi-axis fusion layer complete and accepted",
                "",
                "## Evidence Axes",
                "- origin evidence",
                "- replay/rerecording evidence",
                "- mixer/channel evidence",
                "- partial fabrication segment evidence",
                "",
                "## What Fusion Does",
                "Fusion combines available axis evidence, assigns an experimental status, and triggers manual review when needed.",
                "Missing retrospective axes are treated as `not_evaluated`, not suspicious.",
                "",
                "## What Phase 8 Does Not Claim",
                "- no final court-proof verdict",
                "- no guaranteed perfect detection",
                "- no single fake/real final score",
                "",
                "## Why Phase 9 Is Separate",
                "Phase 8 is the research/evidence engine.",
                "Phase 9 is the release/integration phase for local inference, API, and demo packaging.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    # Evidence model registry
    def _pick_threshold(task: str, feature: str, fallback: str) -> str:
        if len(thresh_df) == 0:
            return fallback
        rows = thresh_df[(thresh_df["task_name"] == task) & (thresh_df["feature_set"] == feature)]
        if len(rows) == 0:
            return fallback
        return _to_str(rows.iloc[0].get("recommended_threshold_candidate", fallback))

    (out_dir / "phase8g_evidence_model_registry.md").write_text(
        "\n".join(
            [
                "# Phase 8 Evidence Model Registry",
                "",
                "All models below are experimental forensic evidence models on controlled Phase 7C1 data.",
                "",
                "## 1) origin_file_model",
                "- phase created: 8E-1",
                "- dataset: Phase 8E-0 origin file dataset",
                "- target: clean human vs clean AI synthetic origin evidence",
                "- feature set: ssl",
                "- model type: logistic_regression_l2",
                f"- threshold candidate: {_pick_threshold('origin_file_model', 'ssl', '0.20')}",
                "- allowed use: origin evidence indicator for fusion/manual review",
                "- forbidden use: final fake/real verdict or court-ready claim",
                "- limitations: controlled dataset; domain shift risk",
                "- status: experimental_forensic_evidence_model",
                "",
                "## 2) replay_file_model",
                "- phase created: 8E-1",
                "- dataset: Phase 8E-0 replay file dataset",
                "- target: replay/rerecording evidence",
                "- feature set: acoustic",
                "- model type: logistic_regression_l2",
                f"- threshold candidate: {_pick_threshold('replay_file_model', 'acoustic', '0.65')}",
                "- allowed use: replay evidence indicator in fusion",
                "- forbidden use: direct AI-origin claim from replay alone",
                "- limitations: controlled dataset; replay is not origin class",
                "- status: experimental_forensic_evidence_model",
                "",
                "## 3) mixer_file_model",
                "- phase created: 8E-1",
                "- dataset: Phase 8E-0 mixer file dataset",
                "- target: mixer/channel processing evidence",
                "- feature set: acoustic",
                "- model type: logistic_regression_l2",
                f"- threshold candidate: {_pick_threshold('mixer_file_model', 'acoustic', '0.75')}",
                "- allowed use: mixer/channel evidence indicator in fusion",
                "- forbidden use: direct AI-origin claim from mixer alone",
                "- limitations: controlled dataset; channel effects vary in real-world audio",
                "- status: experimental_forensic_evidence_model",
                "",
                "## 4) partial_fabrication_segment_model",
                "- phase created: 8E-3",
                "- dataset: timestamp-aligned segment labels from Phase 8E-2",
                "- target: fabricated_region vs outside_fabricated_region",
                "- feature set: combined",
                "- model type: logistic_regression_l2",
                "- threshold candidate: selected from Phase 8E-3 threshold grid",
                "- allowed use: candidate segment localization evidence",
                "- forbidden use: final proof of fabrication",
                "- limitations: timestamp annotation quality and controlled dataset scope",
                "- status: experimental_forensic_evidence_model",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    # Fusion summary doc
    status_dist = "{}"
    review_count = ""
    if len(fusion_summary):
        s = fusion_summary[fusion_summary["metric_name"] == "status_distribution"]
        if len(s):
            status_dist = _to_str(s.iloc[0]["metric_value"])
        r = fusion_summary[fusion_summary["metric_name"] == "manual_review_required_count"]
        if len(r):
            review_count = _to_str(r.iloc[0]["metric_value"])
    (out_dir / "phase8g_fusion_summary.md").write_text(
        "\n".join(
            [
                "# Phase 8 Fusion Summary",
                "",
                "## Fusion Inputs",
                "- Phase 8E-1 file-level OOF evidence outputs",
                "- Phase 8E-1A threshold recommendations",
                "- Phase 8E-3 segment-level outputs",
                "- Phase 8E-2 top candidate segments",
                "",
                "## Accepted Fusion Statuses",
                "- accept_human_clean_experimental",
                "- suspicious_origin_experimental",
                "- suspicious_replay_experimental",
                "- suspicious_mixer_channel_experimental",
                "- suspicious_partial_fabrication_experimental",
                "- suspicious_mixed_evidence_experimental",
                "- inconclusive_manual_review_experimental",
                "",
                "## Risk Levels",
                "- low, medium, high, inconclusive",
                "",
                "## Manual Review Rules",
                "Manual review is required for suspicious or inconclusive outcomes, borderline evidence, and multi-axis conflicts.",
                "",
                "## Final Phase 8F Distribution",
                f"- status_distribution: `{status_dist}`",
                f"- manual_review_required_count: `{review_count}`",
                "",
                "## Safe Interpretation Notes",
                "- replay high does not mean AI-origin",
                "- mixer high does not mean AI-origin",
                "- partial high needs timestamp/segment context and manual review",
                "- missing axes are `not_evaluated` in retrospective OOF fusion",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    # Limitations/claims
    (out_dir / "phase8g_limitations_and_claims.md").write_text(
        "\n".join(
            [
                "# Phase 8 Limitations and Claims",
                "",
                "## Allowed Claims",
                "- system extracts multi-axis forensic evidence",
                "- system produces experimental evidence indicators",
                "- system can localize timestamp-aligned partial fabrication candidates",
                "- system avoids binary fake/real collapse",
                "- system uses manual-review and abstention logic",
                "",
                "## Not Allowed Claims",
                "- detects all deepfakes perfectly",
                "- proves audio is fake",
                "- court-ready forensic proof",
                "- detects every manipulation type",
                "- robust on all real-world audio",
                "- final production system",
                "",
                "## Known Limitations",
                "- controlled dataset size and scope",
                "- broader external testing still needed",
                "- possible domain shift in real-world audio",
                "- Phase 8 fusion is retrospective OOF, not live inference",
                "- thresholds are candidate values, not deployment-certified",
                "- Phase 9 is required for local deployment/API/demo packaging",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    # Phase 9 handoff plan
    (out_dir / "phase8g_phase9_handoff_plan.md").write_text(
        "\n".join(
            [
                "# Phase 9 Handoff Plan",
                "",
                "Phase 8 is the research/evidence engine.",
                "Phase 9 is the local release and teammate-integration prototype phase.",
                "",
                "## Phase 9A",
                "Release folder architecture.",
                "",
                "## Phase 9B",
                "Package accepted experimental models into `release/models`.",
                "",
                "## Phase 9C",
                "Single-audio inference pipeline.",
                "",
                "## Phase 9D",
                "FastAPI backend for teammate integration.",
                "",
                "## Phase 9E",
                "Gradio local demo.",
                "",
                "## Phase 9F",
                "Integration docs, model registry, and API contract.",
                "",
                "## Phase 9G",
                "End-to-end testing and release freeze.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    manifest_df = pd.DataFrame(_build_manifest_rows())
    manifest_df.to_csv(out_dir / "phase8g_freeze_manifest.csv", index=False)

    missing_required = manifest_df[manifest_df["freeze_status"] == "missing_required"]
    missing_optional = manifest_df[manifest_df["freeze_status"] == "missing_optional"]
    (out_dir / "phase8g_freeze_report.md").write_text(
        "\n".join(
            [
                "# Phase 8 Freeze Report",
                "",
                "## Final Decision",
                "Phase 8 final decision: **COMPLETE**",
                "",
                "## Accepted Models",
                "- origin_file_model (ssl)",
                "- replay_file_model (acoustic)",
                "- mixer_file_model (acoustic)",
                "- partial_fabrication_segment_model (combined)",
                "",
                "## Accepted Fusion Status",
                "Phase 8F accepted as experimental multi-axis fusion.",
                "",
                "## Validation Summary",
                f"- missing required freeze inputs: {len(missing_required)}",
                f"- missing optional freeze inputs: {len(missing_optional)}",
                "- key validation references: Phase 8E-3 and Phase 8F validation reports",
                "",
                "## Remaining Limitations",
                "- controlled dataset scope",
                "- domain shift risk",
                "- experimental evidence outputs only",
                "",
                "## Phase 9 Start Criteria",
                "- freeze docs reviewed",
                "- accepted model registry confirmed",
                "- phase9 architecture plan approved",
                "",
                "Phase 9 status: **NOT STARTED**",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    # Roadmap status baseline (pre-run state)
    roadmap_out = _resolve(args.roadmap_output)
    roadmap_out.parent.mkdir(parents=True, exist_ok=True)
    roadmap_out.write_text(
        "\n".join(
            [
                "# Phase 8G Status",
                "",
                "- Phase 8F status: **COMPLETED**",
                "- Phase 8G status: **SCRIPT CREATED / NOT YET EXECUTED**",
                "- Phase 9 status: **NOT STARTED**",
                "",
                "## Next Action",
                "User reviews and runs Phase 8 freeze doc builder manually.",
                "",
                "## Next Phase",
                "Phase 9A release architecture.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    core_missing = [p for p in CORE_REQUIRED_FILES if not _resolve(p).is_file()]
    if core_missing:
        print("Core freeze files missing:")
        for p in core_missing:
            print(f"- {p}")
        return 1

    print("Phase 8G freeze docs generated.")
    print(f"Output dir: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
