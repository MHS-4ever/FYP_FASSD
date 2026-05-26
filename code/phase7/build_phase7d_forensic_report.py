"""
Phase 7D1: Generate JSON + Markdown forensic reports from Phase 7C4-v2 decisions.

No training. No changes to 7C4-v2 logic.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "code"))

from phase7.phase7d_common import (  # noqa: E402
    ANALYSIS_PROFILE,
    DECISION_LAYER_VERSION,
    MANDATORY_DISCLAIMER,
    PROJECT_NAME,
    REPORT_VERSION,
    RISK_DEFAULT_ACTIONS,
    CONFIDENCE_EXPLANATIONS,
    build_limitations,
    build_suspicious_segments,
    estimate_duration_s,
    find_chunk_timeline,
    iso_timestamp,
    lint_full_report,
    load_chunk_timeline,
    load_error_ids,
    load_indexed_csv,
    map_status,
    model_disagreement_flags,
    attack_hint_from_baseline,
    _f,
    _s,
)
from phase7.phase7_paths import (  # noqa: E402
    BASELINE_PARTIAL,
    BASELINE_RESULTS,
    C4_V2_DECISIONS,
    C4_V2_ERRORS,
    P7,
    R2_LOSS_7C1,
    R2_PRODUCT_7C1,
    resolve_phase7_report_path,
)

DEFAULT_OUTPUT = f"{P7}/phase7d_report_layer/outputs"
DEFAULT_CHUNK_DIR = f"{P7}/phase7c1_baseline/results/chunk_timelines"

SAMPLE_STATUS_PRIORITY: list[tuple[str, str]] = [
    ("clean_human_accepted", "clean_human_accepted"),
    ("clean_human_borderline", "clean_human_borderline"),
    ("clean_human_false_alarm", "clean_human_false_alarm"),
    (
        "direct_ai_segment",
        "direct_ai_file_level_missed_but_segment_suspicious",
    ),
    ("human_replay", "human_replay_manipulation_detected"),
    ("ai_replay", "ai_replay_detected"),
    ("ai_replay_seg", "ai_replay_file_level_missed_but_segment_suspicious"),
    ("human_mixer", "human_mixer_manipulation_detected"),
    ("ai_mixer", "ai_mixer_detected"),
    ("partial_fab", "partial_fabrication_detected"),
]


def _parse_bool(val: Any, default: bool) -> bool:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return default
    if isinstance(val, bool):
        return val
    return str(val).strip().lower() in ("true", "1", "yes", "y")


def _row_get(row: pd.Series | None, key: str, default: Any = None) -> Any:
    if row is None:
        return default
    if key in row.index:
        return row[key]
    return default


def build_report(
    decision: pd.Series,
    baseline: pd.Series | None,
    partial: pd.Series | None,
    r2_product: pd.Series | None,
    r2_loss: pd.Series | None,
    chunks: pd.DataFrame,
    is_error_case: bool,
    analysis_ts: str,
) -> dict:
    sample_id = _s(decision["sample_id"])
    calibrated_status = _s(decision.get("calibrated_status")) or "unknown_review_required"
    suspicious_ratio = _f(decision.get("max_chunk_spoof_baseline"))
    if baseline is not None:
        suspicious_ratio = _f(baseline.get("suspicious_chunk_ratio")) or suspicious_ratio

    mapping = map_status(calibrated_status, suspicious_ratio)
    audio_path = _s(_row_get(baseline, "audio_path")) or _s(_row_get(decision, "audio_path"))
    if not audio_path:
        audio_path = f"data/phase7c1/raw/{sample_id}.wav"

    baseline_score = _f(decision.get("decision_score_baseline")) or _f(
        _row_get(baseline, "decision_score")
    )
    r2_p_score = _f(decision.get("decision_score_r2_product"))
    r2_l_score = _f(decision.get("decision_score_r2_loss"))
    max_chunk_b = _f(decision.get("max_chunk_spoof_baseline")) or _f(
        _row_get(baseline, "max_chunk_spoof")
    )
    max_chunk_rp = _f(_row_get(r2_product, "max_chunk_spoof"))
    max_chunk_rl = _f(_row_get(r2_loss, "max_chunk_spoof"))

    baseline_status = _s(decision.get("baseline_status_baseline")) or _s(
        _row_get(baseline, "baseline_status")
    )
    r2_p_status = _s(decision.get("baseline_status_r2_product")) or _s(
        _row_get(r2_product, "baseline_status")
    )
    r2_l_status = _s(_row_get(r2_loss, "baseline_status"))

    flags = model_disagreement_flags(
        baseline_status, r2_p_status, r2_l_status, baseline_score, r2_p_score
    )
    selected_evidence = _s(decision.get("selected_model_evidence"))
    evidence_summary = _s(decision.get("evidence_summary"))
    if not evidence_summary:
        evidence_summary = (
            f"Phase 7C4-v2 assigned `{calibrated_status}`. "
            f"Primary evidence source: {selected_evidence or 'fused rules'}."
        )

    segments = build_suspicious_segments(
        sample_id=sample_id,
        chunks=chunks,
        partial_row=partial if partial is not None else baseline,
        calibrated_status=calibrated_status,
    )

    origin_hint = _s(decision.get("origin_hint")) or mapping.origin_hint
    manip_hint = _s(decision.get("manipulation_hint")) or mapping.manipulation_hint
    attack_hint = attack_hint_from_baseline(baseline)

    conf_level = mapping.confidence_level
    conf_expl = CONFIDENCE_EXPLANATIONS.get(conf_level, CONFIDENCE_EXPLANATIONS["medium"])
    conf_expl += " This reflects analytic evidence strength, not legal certainty."

    recommended = mapping.recommended_action or RISK_DEFAULT_ACTIONS.get(
        mapping.overall_risk_level, RISK_DEFAULT_ACTIONS["medium"]
    )

    technical = (
        f"Phase 7C4-v2 status `{calibrated_status}` (risk `{mapping.overall_risk_level}`). "
        f"Baseline status `{baseline_status}`; R2 product `{r2_p_status}`; R2 loss `{r2_l_status}`. "
        f"Baseline decision score {baseline_score}; R2 product {r2_p_score}; R2 loss {r2_l_score}. "
        f"Max chunk spoof baseline {max_chunk_b}; suspicious chunk ratio {suspicious_ratio}. "
        f"Profile: {ANALYSIS_PROFILE}."
    )
    if _s(decision.get("source_origin")):
        technical += f" Source origin label: {decision.get('source_origin')}."

    agreement_summary = "Model outputs were compared across baseline and R2 checkpoints."
    if flags:
        agreement_summary += " Disagreement flags: " + ", ".join(flags) + "."
    else:
        agreement_summary += " No major disagreement flags were raised."

    disagreement_summary = (
        "Disagreement between checkpoints should be resolved by expert listen, not by automated verdict."
        if flags
        else "Checkpoints were broadly consistent for this file under current rules."
    )

    partial_start = _f(_row_get(partial, "suspicious_start_time")) or _f(
        _row_get(baseline, "suspicious_start_time")
    )
    partial_end = _f(_row_get(partial, "suspicious_end_time")) or _f(
        _row_get(baseline, "suspicious_end_time")
    )

    report: dict = {
        "report_id": f"{sample_id}_{analysis_ts.replace(':', '').replace('-', '')[:15]}",
        "report_version": REPORT_VERSION,
        "project_name": PROJECT_NAME,
        "analysis_timestamp": analysis_ts,
        "input_audio_path": audio_path,
        "audio_filename": Path(audio_path).name,
        "audio_duration_s": estimate_duration_s(chunks, baseline),
        "sample_rate_hz": None,
        "channels": 1,
        "analysis_profile": ANALYSIS_PROFILE,
        "decision_layer_version": DECISION_LAYER_VERSION,
        "overall_risk_level": mapping.overall_risk_level,
        "overall_status": mapping.overall_status,
        "origin_hint": origin_hint,
        "manipulation_hint": manip_hint,
        "attack_hint": attack_hint,
        "manual_review_required": _parse_bool(
            decision.get("needs_manual_review"), mapping.manual_review_required
        ),
        "confidence_level": conf_level,
        "confidence_explanation": conf_expl,
        "file_level_evidence": {
            "summary": mapping.executive_wording,
            "baseline_prediction": _s(_row_get(baseline, "prediction")),
            "baseline_decision_score": baseline_score,
            "r2_product_decision_score": r2_p_score,
            "r2_loss_decision_score": r2_l_score,
            "selected_evidence_source": selected_evidence,
            "calibrated_status": calibrated_status,
        },
        "chunk_level_evidence": {
            "n_chunks_used": int(_row_get(baseline, "n_chunks_used", 0) or 0),
            "n_chunks_total": int(_row_get(baseline, "n_chunks_total", 0) or 0),
            "suspicious_chunk_ratio": suspicious_ratio,
            "max_chunk_spoof_baseline": max_chunk_b,
            "max_chunk_spoof_r2_product": max_chunk_rp,
            "max_chunk_spoof_r2_loss": max_chunk_rl,
            "high_spoof_chunk_count": int(_row_get(baseline, "suspicious_chunk_count", 0) or 0),
        },
        "segment_level_evidence": {
            "labeled_suspicious_start_s": partial_start,
            "labeled_suspicious_end_s": partial_end,
            "partial_inside_max_spoof": _f(_row_get(partial, "inside_region_max_spoof"))
            or _f(_row_get(baseline, "inside_region_max_spoof")),
            "partial_outside_max_spoof": _f(_row_get(partial, "outside_region_max_spoof"))
            or _f(_row_get(baseline, "outside_region_max_spoof")),
            "partial_region_delta": _f(_row_get(partial, "region_delta"))
            or _f(_row_get(baseline, "region_delta")),
            "partial_region_detected": bool(_row_get(partial, "partial_region_detected"))
            if partial is not None
            else (
                bool(_row_get(baseline, "partial_region_detected"))
                if baseline is not None
                else None
            ),
        },
        "model_agreement": {
            "agreement_summary": agreement_summary,
            "baseline_status": baseline_status,
            "r2_product_status": r2_p_status,
            "r2_loss_status": r2_l_status,
            "disagreement_flags": flags,
        },
        "model_disagreement": {"summary": disagreement_summary},
        "selected_model_evidence": selected_evidence,
        "suspicious_segments": segments,
        "executive_summary": (
            f"Overall risk is assessed as **{mapping.overall_risk_level}**. "
            f"{mapping.executive_wording}"
        ),
        "technical_summary": technical,
        "evidence_summary": evidence_summary,
        "recommended_action": recommended,
        "limitations": build_limitations(calibrated_status, is_error_case),
        "disclaimer": MANDATORY_DISCLAIMER,
        "technical_traceability": {
            "phase7c4_status": calibrated_status,
            "baseline_status": baseline_status,
            "r2_product_status": r2_p_status,
            "r2_loss_status": r2_l_status,
            "baseline_decision_score": baseline_score,
            "r2_product_decision_score": r2_p_score,
            "r2_loss_decision_score": r2_l_score,
            "baseline_max_chunk_spoof": max_chunk_b,
            "r2_product_max_chunk_spoof": max_chunk_rp,
            "r2_loss_max_chunk_spoof": max_chunk_rl,
            "suspicious_chunk_ratio": suspicious_ratio,
            "partial_region_delta": _f(_row_get(partial, "region_delta")),
            "partial_inside_max_spoof": _f(_row_get(partial, "inside_region_max_spoof")),
            "is_error_case": is_error_case,
            "manipulation_type": _s(decision.get("manipulation_type")),
            "source_origin": _s(decision.get("source_origin")),
        },
    }
    return report


def report_to_markdown(report: dict) -> str:
    fl = report["file_level_evidence"]
    ch = report["chunk_level_evidence"]
    seg_ev = report["segment_level_evidence"]
    ma = report["model_agreement"]
    lines: list[str] = [
        "# FASSD Forensic Analysis Report",
        "",
        "## 1. Report Header",
        "",
        f"| Field | Value |",
        f"|-------|-------|",
        f"| Report ID | `{report['report_id']}` |",
        f"| Report version | `{report['report_version']}` |",
        f"| Analysis time | `{report['analysis_timestamp']}` |",
        f"| Decision layer | `{report['decision_layer_version']}` |",
        f"| Project | {report['project_name']} |",
        "",
        "## 2. Audio Metadata",
        "",
        f"| Field | Value |",
        f"|-------|-------|",
        f"| Audio file | `{report['audio_filename']}` |",
        f"| Path | `{report['input_audio_path']}` |",
        f"| Duration (s) | {report['audio_duration_s']} |",
        f"| Sample rate (Hz) | {report['sample_rate_hz']} |",
        f"| Channels | {report['channels']} |",
        f"| Analysis profile | `{report['analysis_profile']}` |",
        "",
        "## 3. Executive Summary",
        "",
        report["executive_summary"],
        "",
        "## 4. Final Risk Assessment",
        "",
        f"| Field | Value |",
        f"|-------|-------|",
        f"| Overall risk level | **{report['overall_risk_level']}** |",
        f"| Overall status | `{report['overall_status']}` |",
        f"| Manual review required | **{report['manual_review_required']}** |",
        f"| Confidence | {report['confidence_level']} — {report['confidence_explanation']} |",
        "",
        "## 5. Origin and Manipulation Hints",
        "",
        f"| Hint | Value |",
        f"|------|-------|",
        f"| Origin hint | {report['origin_hint']} |",
        f"| Manipulation hint | {report['manipulation_hint']} |",
        f"| Attack hint (auxiliary) | {report['attack_hint']} |",
        "",
        "Origin and manipulation are reported separately. A human-origin assessment does not imply an unmodified original recording.",
        "",
        "## 6. Evidence Table",
        "",
        "### File-level",
        "",
        fl["summary"],
        "",
        f"| Metric | Baseline | R2 product | R2 loss |",
        f"|--------|----------|------------|---------|",
        f"| Decision score | {fl.get('baseline_decision_score')} | {fl.get('r2_product_decision_score')} | {fl.get('r2_loss_decision_score')} |",
        f"| Prediction | {fl.get('baseline_prediction')} | — | — |",
        f"| Phase 7C4-v2 status | **{fl.get('calibrated_status')}** | | |",
        f"| Selected evidence | {report.get('selected_model_evidence')} | | |",
        "",
        "### Chunk-level",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Chunks used / total | {ch.get('n_chunks_used')} / {ch.get('n_chunks_total')} |",
        f"| Suspicious chunk ratio | {ch.get('suspicious_chunk_ratio')} |",
        f"| Max chunk spoof (baseline) | {ch.get('max_chunk_spoof_baseline')} |",
        f"| Max chunk spoof (R2 product) | {ch.get('max_chunk_spoof_r2_product')} |",
        f"| Max chunk spoof (R2 loss) | {ch.get('max_chunk_spoof_r2_loss')} |",
        "",
        "### Segment-level (partial fabrication)",
        "",
        f"| Field | Value |",
        f"|-------|-------|",
        f"| Labeled region (s) | {seg_ev.get('labeled_suspicious_start_s')} – {seg_ev.get('labeled_suspicious_end_s')} |",
        f"| Inside max spoof | {seg_ev.get('partial_inside_max_spoof')} |",
        f"| Outside max spoof | {seg_ev.get('partial_outside_max_spoof')} |",
        f"| Region delta | {seg_ev.get('partial_region_delta')} |",
        f"| Partial region detected | {seg_ev.get('partial_region_detected')} |",
        "",
        "## 7. Suspicious Segment Analysis",
        "",
    ]
    segs = report.get("suspicious_segments") or []
    if segs:
        lines.append(
            "| Start (s) | End (s) | Type | Score | Source | Priority | Explanation |"
        )
        lines.append("|-----------|---------|------|-------|--------|----------|-------------|")
        for s in segs:
            lines.append(
                f"| {s['start_time']} | {s['end_time']} | {s['segment_type']} | "
                f"{s['evidence_score']} | {s['evidence_source']} | {s['review_priority']} | "
                f"{s['explanation']} |"
            )
    else:
        lines.append(
            "No suspicious segments were listed above the reporting threshold. "
            "Manual review may still be required based on file-level status."
        )
    lines.extend(
        [
            "",
            "## 8. Model Agreement / Disagreement",
            "",
            ma.get("agreement_summary", ""),
            "",
            f"**Disagreement flags:** {', '.join(ma.get('disagreement_flags') or []) or 'none'}",
            "",
            report.get("model_disagreement", {}).get("summary", ""),
            "",
            "## 9. Recommended Human Review Actions",
            "",
            report["recommended_action"],
            "",
            "## 10. Limitations",
            "",
        ]
    )
    for lim in report.get("limitations") or []:
        lines.append(f"- {lim}")
    lines.extend(["", "## 11. Disclaimer", "", report["disclaimer"], ""])
    tt = report["technical_traceability"]
    lines.extend(
        [
            "## 12. Technical Traceability Appendix",
            "",
            f"| Field | Value |",
            f"|-------|-------|",
            f"| phase7c4_status | {tt.get('phase7c4_status')} |",
            f"| baseline_status | {tt.get('baseline_status')} |",
            f"| r2_product_status | {tt.get('r2_product_status')} |",
            f"| r2_loss_status | {tt.get('r2_loss_status')} |",
            f"| manipulation_type | {tt.get('manipulation_type')} |",
            f"| source_origin | {tt.get('source_origin')} |",
            f"| is_error_case | {tt.get('is_error_case')} |",
            "",
            "*Internal traceability for audit; not a user verdict.*",
            "",
        ]
    )
    return "\n".join(lines)


def select_sample_ids(
    decisions: pd.DataFrame,
    sample_count: int,
    explicit_ids: list[str] | None,
) -> list[str]:
    if explicit_ids:
        return explicit_ids[:sample_count] if sample_count else explicit_ids

    by_status: dict[str, list[str]] = {}
    for _, row in decisions.iterrows():
        st = _s(row["calibrated_status"])
        by_status.setdefault(st, []).append(_s(row["sample_id"]))

    chosen: list[str] = []
    used: set[str] = set()

    for _label, status in SAMPLE_STATUS_PRIORITY:
        for sid in by_status.get(status, []):
            if sid not in used:
                chosen.append(sid)
                used.add(sid)
                break
        if len(chosen) >= sample_count:
            break

    if len(chosen) < sample_count:
        for sid in decisions["sample_id"].astype(str).tolist():
            if sid not in used:
                chosen.append(sid)
                used.add(sid)
            if len(chosen) >= sample_count:
                break
    return chosen[:sample_count]


def write_summary(
    path: Path,
    *,
    total: int,
    generated: int,
    failed: int,
    samples: list[str],
    status_counts: Counter,
    risk_counts: Counter,
    review_counts: Counter,
    warnings: list[str],
) -> None:
    lines = [
        "# Phase 7D Report Generation Summary",
        "",
        f"- Decision rows read: **{total}**",
        f"- JSON/Markdown pairs generated: **{generated}**",
        f"- Failed / rejected: **{failed}**",
        f"- Sample pack size: **{len(samples)}**",
        "",
        "## Counts by calibrated_status",
        "",
    ]
    for k, v in status_counts.most_common():
        lines.append(f"- `{k}`: {v}")
    lines.extend(["", "## Counts by overall_risk_level", ""])
    for k, v in risk_counts.most_common():
        lines.append(f"- `{k}`: {v}")
    lines.extend(["", "## Counts by manual_review_required", ""])
    for k, v in review_counts.most_common():
        lines.append(f"- `{k}`: {v}")
    if samples:
        lines.extend(["", "## Sample pack", ""])
        for sid in samples:
            lines.append(f"- `{sid}`")
    if warnings:
        lines.extend(["", "## Warnings", ""])
        for w in warnings:
            lines.append(f"- {w}")
    lines.extend(
        [
            "",
            "## Next step",
            "",
            "```text",
            "python code/phase7/validate_phase7d_reports.py "
            "--json_dir reports/phase7/phase7d_report_layer/outputs/json "
            "--markdown_dir reports/phase7/phase7d_report_layer/outputs/markdown "
            "--output_md reports/phase7/phase7d_report_layer/outputs/phase7d_report_validation_report.md "
            "--output_csv reports/phase7/phase7d_report_layer/outputs/phase7d_rejected_or_failed_reports.csv",
            "```",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser(description="Phase 7D1 — forensic report generator")
    p.add_argument("--decisions_csv", type=str, default=C4_V2_DECISIONS)
    p.add_argument("--error_csv", type=str, default=C4_V2_ERRORS)
    p.add_argument("--baseline_csv", type=str, default=BASELINE_RESULTS)
    p.add_argument("--baseline_partial_csv", type=str, default=BASELINE_PARTIAL)
    p.add_argument("--r2_product_csv", type=str, default=R2_PRODUCT_7C1)
    p.add_argument("--r2_loss_csv", type=str, default=R2_LOSS_7C1)
    p.add_argument("--baseline_chunk_dir", type=str, default=DEFAULT_CHUNK_DIR)
    p.add_argument("--output_dir", type=str, default=DEFAULT_OUTPUT)
    p.add_argument("--generate_samples", action="store_true")
    p.add_argument("--no_samples", action="store_true")
    p.add_argument("--sample_count", type=int, default=8)
    p.add_argument("--sample_ids", type=str, default="")
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--strict", action="store_true")
    args = p.parse_args()

    out_dir = resolve_phase7_report_path(args.output_dir, for_write=True)
    json_dir = out_dir / "json"
    md_dir = out_dir / "markdown"
    json_dir.mkdir(parents=True, exist_ok=True)
    md_dir.mkdir(parents=True, exist_ok=True)

    decisions_path = resolve_phase7_report_path(args.decisions_csv)
    decisions = pd.read_csv(decisions_path, low_memory=False)
    decisions["sample_id"] = decisions["sample_id"].astype(str)
    if args.limit > 0:
        decisions = decisions.head(args.limit)

    baseline_idx = load_indexed_csv(resolve_phase7_report_path(args.baseline_csv))
    partial_idx = load_indexed_csv(resolve_phase7_report_path(args.baseline_partial_csv))
    r2_p_idx = load_indexed_csv(resolve_phase7_report_path(args.r2_product_csv))
    r2_l_idx = load_indexed_csv(resolve_phase7_report_path(args.r2_loss_csv))
    error_ids = load_error_ids(resolve_phase7_report_path(args.error_csv))
    chunk_dir = resolve_phase7_report_path(args.baseline_chunk_dir)

    analysis_ts = iso_timestamp()
    manifest_rows: list[dict] = []
    failed_rows: list[dict] = []
    status_counts: Counter = Counter()
    risk_counts: Counter = Counter()
    review_counts: Counter = Counter()
    generated = 0
    warnings: list[str] = []

    for _, dec in decisions.iterrows():
        sample_id = _s(dec["sample_id"])
        baseline = baseline_idx.get(sample_id)
        partial = partial_idx.get(sample_id)
        chunk_path = find_chunk_timeline(chunk_dir, sample_id)
        chunks = load_chunk_timeline(chunk_path)

        report = build_report(
            dec,
            baseline,
            partial,
            r2_p_idx.get(sample_id),
            r2_l_idx.get(sample_id),
            chunks,
            sample_id in error_ids,
            analysis_ts,
        )
        lint_issues = lint_full_report(report)
        if lint_issues:
            failed_rows.append(
                {
                    "sample_id": sample_id,
                    "calibrated_status": _s(dec.get("calibrated_status")),
                    "issues": "; ".join(lint_issues),
                }
            )
            if args.strict:
                continue

        json_path = json_dir / f"{sample_id}_forensic_report.json"
        md_path = md_dir / f"{sample_id}_forensic_report.md"
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        md_path.write_text(report_to_markdown(report), encoding="utf-8")

        st = report["technical_traceability"]["phase7c4_status"]
        status_counts[st] += 1
        risk_counts[report["overall_risk_level"]] += 1
        review_counts[str(report["manual_review_required"])] += 1
        generated += 1

        manifest_rows.append(
            {
                "sample_id": sample_id,
                "calibrated_status": st,
                "overall_risk_level": report["overall_risk_level"],
                "manual_review_required": report["manual_review_required"],
                "json_path": str(json_path.relative_to(_REPO_ROOT)).replace("\\", "/"),
                "markdown_path": str(md_path.relative_to(_REPO_ROOT)).replace("\\", "/"),
                "lint_passed": len(lint_issues) == 0,
                "lint_issues": "; ".join(lint_issues),
            }
        )

    manifest_path = out_dir / "phase7d_report_generation_manifest.csv"
    pd.DataFrame(manifest_rows).to_csv(manifest_path, index=False)

    rejected_path = out_dir / "phase7d_rejected_or_failed_reports.csv"
    if failed_rows:
        pd.DataFrame(failed_rows).to_csv(rejected_path, index=False)
    elif rejected_path.is_file():
        rejected_path.unlink()

    sample_ids: list[str] = []
    if args.generate_samples and not args.no_samples:
        explicit = [_s(x) for x in args.sample_ids.split(",") if _s(x)]
        sample_ids = select_sample_ids(decisions, args.sample_count, explicit or None)
        s_json = out_dir / "samples" / "json"
        s_md = out_dir / "samples" / "markdown"
        s_json.mkdir(parents=True, exist_ok=True)
        s_md.mkdir(parents=True, exist_ok=True)
        index_lines = [
            "# Phase 7D Sample Report Index",
            "",
            "| sample_id | calibrated_status | risk_level | json | markdown |",
            "|-----------|-------------------|------------|------|----------|",
        ]
        for sid in sample_ids:
            src_j = json_dir / f"{sid}_forensic_report.json"
            src_m = md_dir / f"{sid}_forensic_report.md"
            if not src_j.is_file():
                warnings.append(f"sample_missing:{sid}")
                continue
            shutil.copy2(src_j, s_json / src_j.name)
            shutil.copy2(src_m, s_md / src_m.name)
            rep = json.loads(src_j.read_text(encoding="utf-8"))
            rel_j = f"samples/json/{src_j.name}"
            rel_m = f"samples/markdown/{src_m.name}"
            index_lines.append(
                f"| {sid} | {rep['technical_traceability']['phase7c4_status']} | "
                f"{rep['overall_risk_level']} | {rel_j} | {rel_m} |"
            )
        (out_dir / "samples" / "SAMPLE_REPORT_INDEX.md").write_text(
            "\n".join(index_lines) + "\n", encoding="utf-8"
        )

    write_summary(
        out_dir / "phase7d_report_summary.md",
        total=len(decisions),
        generated=generated,
        failed=len(failed_rows),
        samples=sample_ids,
        status_counts=status_counts,
        risk_counts=risk_counts,
        review_counts=review_counts,
        warnings=warnings,
    )

    print(f"[READ] {len(decisions)} decision rows from {decisions_path}")
    print(f"[SAVE] {generated} JSON + Markdown pairs -> {out_dir}")
    print(f"[SAVE] manifest -> {manifest_path}")
    if failed_rows:
        print(f"[WARN] {len(failed_rows)} lint failures -> {rejected_path}")
    if sample_ids:
        print(f"[SAVE] {len(sample_ids)} sample reports -> {out_dir / 'samples'}")
    print(f"[SAVE] summary -> {out_dir / 'phase7d_report_summary.md'}")
    print(
        "\nNext validation:\n"
        "python code/phase7/validate_phase7d_reports.py "
        "--json_dir reports/phase7/phase7d_report_layer/outputs/json "
        "--markdown_dir reports/phase7/phase7d_report_layer/outputs/markdown "
        "--output_md reports/phase7/phase7d_report_layer/outputs/phase7d_report_validation_report.md "
        "--output_csv reports/phase7/phase7d_report_layer/outputs/phase7d_rejected_or_failed_reports.csv"
    )
    return 1 if args.strict and failed_rows else 0


if __name__ == "__main__":
    raise SystemExit(main())
