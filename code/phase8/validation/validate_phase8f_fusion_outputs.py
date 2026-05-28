#!/usr/bin/env python3
"""Validate Phase 8F experimental fusion outputs."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]

ALLOWED_STATUS = {
    "accept_human_clean_experimental",
    "suspicious_origin_experimental",
    "suspicious_replay_experimental",
    "suspicious_mixer_channel_experimental",
    "suspicious_partial_fabrication_experimental",
    "suspicious_mixed_evidence_experimental",
    "inconclusive_manual_review_experimental",
}
ALLOWED_RISK = {"low", "medium", "high", "inconclusive"}
FORBIDDEN_COLS = {
    "fake_score",
    "real_score",
    "final_fake_real_label",
    "suspicious_segment_flag",
}
FORBIDDEN_ABSOLUTE_WORDS = [
    "definitely fake",
    "definitely real",
    "criminal proof",
    "court-proven",
    "guaranteed ai",
    "guaranteed human",
]
SAFE_EXPECTED_WORDS = [
    "evidence indicator",
    "experimental model output",
    "candidate segment",
    "manual review recommended",
    "does not by itself prove",
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate Phase 8F fusion outputs.")
    p.add_argument("--fusion_dir", default="reports/phase8/fusion/phase8f")
    p.add_argument("--output_report", default="reports/phase8/validation/phase8f_fusion_validation_report.md")
    return p.parse_args()


def _resolve(path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else (REPO_ROOT / p).resolve()


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def _to_float(s: object) -> float | None:
    try:
        txt = str(s).strip()
        if txt == "":
            return None
        return float(txt)
    except Exception:
        return None


def validate(args: argparse.Namespace) -> dict[str, object]:
    blocking: list[str] = []
    warnings: list[str] = []
    base = _resolve(args.fusion_dir)
    req = {
        "file_records": base / "phase8f_file_fusion_records.csv",
        "segment_records": base / "phase8f_segment_fusion_records.csv",
        "manual_review": base / "phase8f_manual_review_queue.csv",
        "jsonl": base / "phase8f_experimental_forensic_reports.jsonl",
        "md_reports": base / "phase8f_experimental_forensic_reports.md",
        "summary": base / "phase8f_fusion_summary.csv",
        "fusion_report": base / "phase8f_fusion_report.md",
    }
    missing = [k for k, p in req.items() if not p.is_file()]
    if missing:
        return {"status": "FAIL", "blocking": [f"Missing required files: {missing}"], "warnings": []}

    files_df = _read_csv(req["file_records"])
    seg_df = _read_csv(req["segment_records"])
    mr_df = _read_csv(req["manual_review"])

    required_file_cols = {
        "schema_version",
        "file_id",
        "origin_model_available",
        "origin_feature_set",
        "origin_ai_probability",
        "replay_model_available",
        "replay_probability",
        "mixer_model_available",
        "mixer_probability",
        "partial_model_available",
        "partial_max_segment_probability",
        "experimental_fusion_status",
        "forensic_risk_level",
        "manual_review_required",
        "manual_review_reason",
        "safe_report_text",
    }
    miss_cols = sorted(required_file_cols - set(files_df.columns))
    if miss_cols:
        blocking.append(f"file records missing columns: {miss_cols}")

    if "experimental_fusion_status" in files_df.columns:
        bad = sorted(set(files_df["experimental_fusion_status"]) - ALLOWED_STATUS)
        if bad:
            blocking.append(f"invalid experimental_fusion_status values: {bad}")
    if "forensic_risk_level" in files_df.columns:
        bad = sorted(set(files_df["forensic_risk_level"]) - ALLOWED_RISK)
        if bad:
            blocking.append(f"invalid forensic_risk_level values: {bad}")

    bad_forbidden = sorted(FORBIDDEN_COLS.intersection(set(files_df.columns) | set(seg_df.columns)))
    if bad_forbidden:
        blocking.append(f"forbidden columns found: {bad_forbidden}")
    if "final_forensic_status" in files_df.columns:
        blocking.append("unqualified final_forensic_status column is not allowed in Phase 8F outputs.")

    axis_cols = ["origin_ai_probability", "replay_probability", "mixer_probability", "partial_max_segment_probability"]
    for c in axis_cols:
        if c not in files_df.columns:
            blocking.append(f"missing axis evidence column: {c}")

    if {"replay_evidence_strength", "origin_evidence_strength", "experimental_fusion_status"}.issubset(files_df.columns):
        suspect = files_df[
            files_df["replay_evidence_strength"].isin(["high", "moderate"])
            & (files_df["experimental_fusion_status"] == "suspicious_origin_experimental")
            & (files_df["origin_evidence_strength"].isin(["low", "not_evaluated"]))
        ]
        if len(suspect):
            blocking.append("Replay-high rows incorrectly collapsed to origin-only suspicion.")

    if {"mixer_evidence_strength", "origin_evidence_strength", "experimental_fusion_status"}.issubset(files_df.columns):
        suspect = files_df[
            files_df["mixer_evidence_strength"].isin(["high", "moderate"])
            & (files_df["experimental_fusion_status"] == "suspicious_origin_experimental")
            & (files_df["origin_evidence_strength"].isin(["low", "not_evaluated"]))
        ]
        if len(suspect):
            blocking.append("Mixer-high rows incorrectly collapsed to origin-only suspicion.")

    if {"partial_evidence_strength", "manual_review_required"}.issubset(files_df.columns):
        bad = files_df[
            files_df["partial_evidence_strength"].isin(["high", "moderate"])
            & (files_df["manual_review_required"] != "true")
        ]
        if len(bad):
            blocking.append("Partial moderate/high rows must set manual_review_required=true.")
    if {"experimental_fusion_status", "manual_review_required"}.issubset(files_df.columns):
        bad = files_df[
            files_df["experimental_fusion_status"].eq("inconclusive_manual_review_experimental")
            & files_df["manual_review_required"].ne("true")
        ]
        if len(bad):
            blocking.append("Inconclusive status rows must have manual_review_required=true.")
        bad = files_df[
            files_df["experimental_fusion_status"].astype(str).str.startswith("suspicious_")
            & files_df["manual_review_required"].ne("true")
        ]
        if len(bad):
            blocking.append("All suspicious_*_experimental rows must have manual_review_required=true.")
    if {"forensic_risk_level", "manual_review_required"}.issubset(files_df.columns):
        bad = files_df[
            files_df["forensic_risk_level"].eq("inconclusive")
            & files_df["manual_review_required"].ne("true")
        ]
        if len(bad):
            blocking.append("Rows with forensic_risk_level=inconclusive must have manual_review_required=true.")
    if {"manual_review_reason", "manual_review_required"}.issubset(files_df.columns):
        bad = files_df[
            files_df["manual_review_reason"].astype(str).str.contains("insufficient_evidence_review", regex=False)
            & files_df["manual_review_required"].ne("true")
        ]
        if len(bad):
            blocking.append("Rows with insufficient_evidence_review reason must have manual_review_required=true.")

    # Missing probabilities must not map to moderate/high
    for axis, prob_col, strength_col, label_col, avail_col in [
        ("origin", "origin_ai_probability", "origin_evidence_strength", "origin_evidence_label", "origin_model_available"),
        ("replay", "replay_probability", "replay_evidence_strength", "replay_evidence_label", "replay_model_available"),
        ("mixer", "mixer_probability", "mixer_evidence_strength", "mixer_evidence_label", "mixer_model_available"),
        ("partial", "partial_max_segment_probability", "partial_evidence_strength", "partial_evidence_label", "partial_model_available"),
    ]:
        if {prob_col, strength_col}.issubset(files_df.columns):
            miss_prob = files_df[prob_col].astype(str).str.strip().eq("")
            bad_strength = files_df[strength_col].isin(["moderate", "high"])
            if (miss_prob & bad_strength).any():
                blocking.append(f"{axis}: missing probability rows cannot have moderate/high evidence strength.")
        if {avail_col, label_col}.issubset(files_df.columns):
            unavailable = files_df[avail_col].astype(str).str.lower().ne("true")
            bad_label = files_df[label_col].astype(str).str.contains("low_indicator|elevated_", regex=True)
            if (unavailable & bad_label).any():
                blocking.append(f"{axis}: unavailable axis cannot use low/elevated evidence labels.")

    if {"origin_evidence_strength", "replay_evidence_strength", "mixer_evidence_strength", "partial_evidence_strength", "manual_review_required"}.issubset(files_df.columns):
        borderline = files_df[
            (files_df["origin_evidence_strength"] == "borderline")
            | (files_df["replay_evidence_strength"] == "borderline")
            | (files_df["mixer_evidence_strength"] == "borderline")
            | (files_df["partial_evidence_strength"] == "borderline")
        ]
        if len(borderline) and (borderline["manual_review_required"] != "true").any():
            blocking.append("Borderline evidence rows must set manual_review_required=true.")
    if {
        "experimental_fusion_status",
        "manual_review_required",
        "manual_review_reason",
        "origin_evidence_strength",
        "replay_evidence_strength",
        "mixer_evidence_strength",
        "partial_evidence_strength",
    }.issubset(files_df.columns):
        clean_bad = files_df[
            files_df["experimental_fusion_status"].eq("accept_human_clean_experimental")
            & files_df["manual_review_required"].eq("true")
            & ~(
                files_df["origin_evidence_strength"].eq("borderline")
                | files_df["replay_evidence_strength"].eq("borderline")
                | files_df["mixer_evidence_strength"].eq("borderline")
                | files_df["partial_evidence_strength"].eq("borderline")
                | files_df["origin_evidence_strength"].isin(["moderate", "high"])
                | files_df["replay_evidence_strength"].isin(["moderate", "high"])
                | files_df["mixer_evidence_strength"].isin(["moderate", "high"])
                | files_df["partial_evidence_strength"].isin(["moderate", "high"])
                | files_df["manual_review_reason"].ne("none")
            )
        ]
        if len(clean_bad):
            blocking.append(
                "accept_human_clean_experimental rows cannot require manual review without borderline/elevated evidence or explicit reason."
            )

    required_mr_cols = {
        "file_id",
        "experimental_fusion_status",
        "forensic_risk_level",
        "manual_review_reason",
        "top_segment_ranges",
        "priority",
        "reviewer_action",
    }
    mr_missing = sorted(required_mr_cols - set(mr_df.columns))
    if mr_missing:
        blocking.append(f"manual review queue missing fields: {mr_missing}")
    if {"file_id", "manual_review_required"}.issubset(files_df.columns) and "file_id" in mr_df.columns:
        required_ids = set(files_df[files_df["manual_review_required"] == "true"]["file_id"].astype(str))
        queue_ids = set(mr_df["file_id"].astype(str))
        missing_ids = sorted(required_ids - queue_ids)
        if missing_ids:
            blocking.append(
                f"manual review queue missing rows with manual_review_required=true (sample: {missing_ids[:5]})."
            )

    report_text = req["md_reports"].read_text(encoding="utf-8").lower()
    for phrase in SAFE_EXPECTED_WORDS:
        if phrase not in report_text:
            warnings.append(f"safe wording phrase missing from report markdown: '{phrase}'")
    for bad_phrase in FORBIDDEN_ABSOLUTE_WORDS:
        if bad_phrase in report_text:
            blocking.append(f"forbidden absolute wording in report markdown: '{bad_phrase}'")

    safe_text_blob = "\n".join(files_df.get("safe_report_text", pd.Series(dtype=str)).astype(str).tolist()).lower()
    if "nan" in safe_text_blob:
        blocking.append("safe_report_text contains 'nan'.")
    if "candidate segment ranges from fusion summary: `nan`" in safe_text_blob:
        blocking.append("safe_report_text contains invalid nan candidate ranges phrase.")
    for bad_phrase in FORBIDDEN_ABSOLUTE_WORDS:
        if bad_phrase in safe_text_blob:
            blocking.append(f"forbidden absolute wording in safe_report_text: '{bad_phrase}'")
    if {"experimental_fusion_status", "safe_report_text"}.issubset(files_df.columns):
        bad = files_df[
            files_df["experimental_fusion_status"].eq("inconclusive_manual_review_experimental")
            & ~files_df["safe_report_text"].astype(str).str.contains("Manual review is recommended", regex=False)
        ]
        if len(bad):
            blocking.append("Inconclusive rows must include 'Manual review is recommended' in safe_report_text.")

    # Degenerate output checks
    if "manual_review_required" in files_df.columns:
        review_true = int((files_df["manual_review_required"] == "true").sum())
        if len(files_df) > 0 and review_true == len(files_df):
            if "manual_review_reason" in files_df.columns:
                reason_dist = files_df["manual_review_reason"].astype(str).value_counts(dropna=False).to_dict()
                if len(reason_dist) <= 1:
                    blocking.append("manual_review_required=true for all rows with non-informative reason distribution.")
            else:
                blocking.append("manual_review_required=true for all rows.")
    if "experimental_fusion_status" in files_df.columns:
        only = set(files_df["experimental_fusion_status"].astype(str).unique())
        if only.issubset({"suspicious_mixed_evidence_experimental", "suspicious_partial_fabrication_experimental"}):
            blocking.append("All rows collapsed to mixed/partial-only statuses.")

    # Expected status presence checks from evidence
    if {"known_origin_label", "origin_evidence_strength", "experimental_fusion_status"}.issubset(files_df.columns):
        clean_human_low = files_df[
            files_df["known_origin_label"].astype(str).str.lower().eq("human")
            & files_df["origin_evidence_strength"].astype(str).isin(["low", "not_evaluated"])
            & files_df.get("replay_evidence_strength", pd.Series([""] * len(files_df))).astype(str).isin(["low", "not_evaluated"])
            & files_df.get("mixer_evidence_strength", pd.Series([""] * len(files_df))).astype(str).isin(["low", "not_evaluated"])
            & files_df.get("partial_evidence_strength", pd.Series([""] * len(files_df))).astype(str).isin(["low", "not_evaluated"])
        ]
        if len(clean_human_low) and "accept_human_clean_experimental" not in set(files_df["experimental_fusion_status"]):
            blocking.append("Missing accept_human_clean_experimental despite clean-human low-evidence candidates.")
        clean_ai_high = files_df[
            files_df["known_origin_label"].astype(str).str.lower().eq("ai_synthetic")
            & files_df["origin_evidence_strength"].astype(str).isin(["moderate", "high"])
        ]
        if len(clean_ai_high) and "suspicious_origin_experimental" not in set(files_df["experimental_fusion_status"]):
            blocking.append("Missing suspicious_origin_experimental despite high origin-AI evidence candidates.")
    if {"known_manipulation_labels", "replay_evidence_strength", "experimental_fusion_status"}.issubset(files_df.columns):
        replay_high = files_df[
            files_df["known_manipulation_labels"].astype(str).str.contains("replay_rerecorded", case=False, regex=False)
            & files_df["replay_evidence_strength"].astype(str).isin(["moderate", "high"])
        ]
        if len(replay_high) and "suspicious_replay_experimental" not in set(files_df["experimental_fusion_status"]):
            blocking.append("Missing suspicious_replay_experimental despite high replay evidence candidates.")
    if {"known_manipulation_labels", "mixer_evidence_strength", "experimental_fusion_status"}.issubset(files_df.columns):
        mixer_high = files_df[
            files_df["known_manipulation_labels"].astype(str).str.contains("mixer_channel_processed", case=False, regex=False)
            & files_df["mixer_evidence_strength"].astype(str).isin(["moderate", "high"])
        ]
        if len(mixer_high) and "suspicious_mixer_channel_experimental" not in set(files_df["experimental_fusion_status"]):
            blocking.append("Missing suspicious_mixer_channel_experimental despite high mixer evidence candidates.")
    if {"known_manipulation_labels", "partial_evidence_strength", "experimental_fusion_status"}.issubset(files_df.columns):
        partial_high = files_df[
            files_df["known_manipulation_labels"].astype(str).str.contains("partial_fabrication", case=False, regex=False)
            & files_df["partial_evidence_strength"].astype(str).isin(["moderate", "high"])
        ]
        if len(partial_high) and "suspicious_partial_fabrication_experimental" not in set(files_df["experimental_fusion_status"]):
            blocking.append("Missing suspicious_partial_fabrication_experimental despite high partial evidence candidates.")

    # JSONL checks
    with req["jsonl"].open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            raw = line.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
                if not isinstance(obj, dict):
                    raise ValueError("JSONL row is not an object")
            except Exception as exc:
                blocking.append(f"invalid jsonl at line {i}: {exc}")
                break

    active_dir = _resolve("models_saved/active")
    if active_dir.is_dir() and list(active_dir.glob("**/*phase8f*")):
        blocking.append("Found phase8f artifacts in models_saved/active.")

    return {
        "status": "FAIL" if blocking else "PASS",
        "blocking": blocking,
        "warnings": warnings,
        "file_rows": len(files_df),
        "segment_rows": len(seg_df),
        "manual_review_rows": len(mr_df),
    }


def write_report(path: Path, result: dict[str, object]) -> None:
    lines = [
        "# Phase 8F Fusion Validation Report",
        "",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"**Status:** **{result.get('status', 'FAIL')}**",
        "",
        "## Counts",
        "",
        f"- file fusion rows: {result.get('file_rows', 0)}",
        f"- segment fusion rows: {result.get('segment_rows', 0)}",
        f"- manual review rows: {result.get('manual_review_rows', 0)}",
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
            "- Experimental fusion only; not final forensic proof.",
            "- Multi-axis evidence remains separated (origin/replay/mixer/partial).",
            "- Replay/mixer evidence must not be collapsed into AI-origin claims.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    result = validate(args)
    out = _resolve(args.output_report)
    write_report(out, result)
    print(f"Validation: {result['status']}")
    print(f"Report -> {out}")
    return 1 if result["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
