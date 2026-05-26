"""
Phase 7E3A: Analyze pretrained AASIST-L predictions against Phase 7E0 gates (7C1 only).
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd

from _common import ensure_dir, resolve_path, utc_now_iso, write_markdown
from aasist_eval_common import evaluate_aasist_status

# Phase 7E0 locked gates — Phase 7C1 only
GATES_7C1 = {
    "clean_human_false_alarm": {"max": 7, "denom": 23, "mode": "max"},
    "direct_ai_detected_or_segment_suspicious": {"min": 15, "denom": 23, "mode": "min"},
    "ai_replay_detected_or_segment_suspicious": {"min": 15, "denom": 23, "mode": "min"},
    "human_replay_detected": {"min": 20, "denom": 23, "mode": "min"},
    "human_mixer_detected": {"min": 20, "denom": 23, "mode": "min"},
    "ai_mixer_detected": {"min": 20, "denom": 23, "mode": "min"},
    "partial_fabrication_detected": {"min": 40, "denom": 46, "mode": "min"},
}

GATES_BRANCH = {
    "direct_ai_detected_or_segment_suspicious": {"min": 15, "denom": 23, "mode": "min"},
    "clean_human_false_alarm": {"max": 10, "denom": 23, "mode": "max"},
}


def _has_error(value) -> bool:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return False
    return str(value).strip() != ""


def _status_counts(df: pd.DataFrame, col: str = "aasist_status") -> Counter:
    if df.empty or col not in df.columns:
        return Counter()
    return Counter(df[col].fillna("").astype(str))


def _sc(statuses: Counter, *keys: str) -> int:
    return sum(statuses.get(k, 0) for k in keys)


def _pct(n: int, d: int) -> str:
    if d <= 0:
        return "n/a"
    return f"{100.0 * n / d:.1f}%"


def ensure_status_column(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "aasist_status" not in out.columns or out["aasist_status"].isna().all():
        out["aasist_status"] = out.apply(lambda r: evaluate_aasist_status(r.to_dict()), axis=1)
    return out


def compute_7c1_metrics(df: pd.DataFrame) -> dict[str, int]:
    statuses = _status_counts(df)
    return {
        "clean_human_false_alarm": _sc(statuses, "clean_human_false_alarm"),
        "clean_human_accepted": _sc(statuses, "clean_human_accepted"),
        "clean_human_borderline": _sc(statuses, "clean_human_borderline"),
        "direct_ai_detected": _sc(statuses, "direct_ai_detected"),
        "direct_ai_missed": _sc(statuses, "direct_ai_missed"),
        "direct_ai_detected_or_segment_suspicious": _sc(
            statuses, "direct_ai_detected", "direct_ai_file_level_missed_but_segment_suspicious"
        ),
        "human_replay_detected": _sc(statuses, "human_replay_manipulation_detected"),
        "ai_replay_detected": _sc(statuses, "ai_replay_detected"),
        "ai_replay_detected_or_segment_suspicious": _sc(
            statuses, "ai_replay_detected", "ai_replay_file_level_missed_but_segment_suspicious"
        ),
        "human_mixer_detected": _sc(statuses, "human_mixer_manipulation_detected"),
        "ai_mixer_detected": _sc(statuses, "ai_mixer_detected"),
        "ai_mixer_detected_or_segment_suspicious": _sc(
            statuses,
            "ai_mixer_detected",
            "ai_mixer_file_level_missed_but_segment_suspicious",
        ),
        "partial_fabrication_detected": _sc(statuses, "partial_fabrication_detected"),
        "partial_fabrication_missed": _sc(statuses, "partial_fabrication_missed"),
        "partial_fabrication_not_evaluable": _sc(statuses, "partial_fabrication_not_evaluable"),
        "errors": int(df["error"].apply(_has_error).sum()) if "error" in df.columns else 0,
        "total_files": len(df),
    }


def compute_7a_metrics(df: pd.DataFrame) -> dict[str, int]:
    """Holdout summary — no Phase 7E0 numeric gates."""
    statuses = _status_counts(df)
    return {
        "total_files": len(df),
        "errors": int(df["error"].apply(_has_error).sum()) if "error" in df.columns else 0,
        "clean_human_accepted": _sc(statuses, "clean_human_accepted"),
        "clean_human_false_alarm": _sc(statuses, "clean_human_false_alarm"),
        "clean_human_borderline": _sc(statuses, "clean_human_borderline"),
        "direct_ai_detected": _sc(statuses, "direct_ai_detected"),
        "direct_ai_missed": _sc(statuses, "direct_ai_missed"),
        "direct_ai_detected_or_segment_suspicious": _sc(
            statuses, "direct_ai_detected", "direct_ai_file_level_missed_but_segment_suspicious"
        ),
        "human_processed_detected": _sc(statuses, "human_processed_detected"),
        "human_processed_missed": _sc(statuses, "human_processed_missed"),
        "ai_processed_detected": _sc(statuses, "ai_processed_detected"),
        "ai_processed_missed": _sc(statuses, "ai_processed_missed"),
        "ai_processed_detected_or_segment_suspicious": _sc(
            statuses, "ai_processed_detected", "ai_processed_file_level_missed_but_segment_suspicious"
        ),
        "human_replay_detected": _sc(statuses, "human_replay_manipulation_detected"),
        "human_replay_missed": _sc(statuses, "human_replay_missed"),
        "ai_replay_detected": _sc(statuses, "ai_replay_detected"),
        "ai_replay_missed": _sc(statuses, "ai_replay_missed"),
        "ai_replay_detected_or_segment_suspicious": _sc(
            statuses, "ai_replay_detected", "ai_replay_file_level_missed_but_segment_suspicious"
        ),
        "partial_fabrication_detected": _sc(statuses, "partial_fabrication_detected"),
        "partial_fabrication_missed": _sc(statuses, "partial_fabrication_missed"),
        "partial_fabrication_not_evaluable": _sc(statuses, "partial_fabrication_not_evaluable"),
        "unknown_review_required": _sc(statuses, "unknown_review_required"),
        "borderline_needs_review": _sc(statuses, "borderline_needs_review"),
    }


def check_gates(metrics: dict[str, int], gates: dict) -> dict[str, dict]:
    results = {}
    for name, spec in gates.items():
        val = metrics.get(name, 0)
        denom = spec["denom"]
        if spec["mode"] == "max":
            passed = val <= spec["max"]
            threshold = f"<= {spec['max']}/{denom}"
        else:
            passed = val >= spec["min"]
            threshold = f">= {spec['min']}/{denom}"
        results[name] = {
            "value": val,
            "denom": denom,
            "threshold": threshold,
            "passed": passed,
        }
    return results


def recommend_role_7c1(gate_results: dict, branch_results: dict) -> str:
    if all(r["passed"] for r in gate_results.values()):
        return "standalone"
    fa_val = gate_results.get("clean_human_false_alarm", {}).get("value", 99)
    if fa_val > 10:
        return "reject"
    if all(r["passed"] for r in branch_results.values()):
        return "branch-only"
    return "needs_calibration"


def build_summary_csv(metrics: dict[str, int], gate_results: dict, role: str) -> pd.DataFrame:
    rows = [{"metric": k, "value": v} for k, v in metrics.items()]
    for name, gr in gate_results.items():
        rows.append(
            {
                "metric": f"gate_{name}",
                "value": gr["value"],
                "threshold": gr["threshold"],
                "passed": gr["passed"],
            }
        )
    rows.append({"metric": "role_recommendation", "value": role})
    return pd.DataFrame(rows)


def _md_table(headers: list[str], rows: list[list]) -> str:
    if not rows:
        return "_No rows._\n"
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for r in rows:
        lines.append("| " + " | ".join(str(x) for x in r) + " |")
    return "\n".join(lines) + "\n"


def _status_traceability_section() -> list[str]:
    """Definitions for AASIST analysis reports (Phase 7E3A)."""
    return [
        "## Status traceability (read before interpreting counts)",
        "",
        "- **`direct_ai_detected`** (and `ai_replay_detected`, `ai_mixer_detected`, `ai_processed_detected`): "
        "file-level mean spoof score crossed the threshold (`mean_spoof_score >= threshold_used`), "
        "or mean score reached the manipulation-detect floor.",
        "- **`*_file_level_missed_but_segment_suspicious`**: file-level mean did **not** cross the threshold, "
        "but chunk/window evidence is strong (`max_spoof_score` or `suspicious_window_ratio` rules).",
        "- **`expected_risk_binary=1`** / manifest **`risk_target=1`**: forensic-risk positive — "
        "**not** the same as “AI-generated”; includes replay, mixer, partial fabrication, and channel processing.",
        "",
    ]


def _class_convention_section(df: pd.DataFrame) -> list[str]:
    cols = [
        "spoof_class_index_used",
        "bonafide_class_index_used",
        "class_convention_source",
        "class_convention_warning",
    ]
    if not any(c in df.columns for c in cols):
        return ["_Class convention columns not present in predictions CSV._", ""]
    row = df.iloc[0]
    return [
        f"- **spoof_class_index_used:** {row.get('spoof_class_index_used', '')}",
        f"- **bonafide_class_index_used:** {row.get('bonafide_class_index_used', '')}",
        f"- **class_convention_source:** `{row.get('class_convention_source', '')}`",
        f"- **class_convention_warning:** `{row.get('class_convention_warning', '') or '(none)'}`",
        "",
    ]


def write_analysis_md_7c1(
    df: pd.DataFrame,
    metrics: dict[str, int],
    gate_results: dict,
    branch_results: dict,
    role: str,
    output_md: Path,
) -> None:
    statuses = _status_counts(df)
    n = len(df)
    lines = [
        "# Phase 7E3A — AASIST-L Pretrained Analysis (phase7c1)",
        "",
        f"**Generated:** {utc_now_iso()}",
        "**Model:** pretrained AASIST-L (no fine-tuning)",
        "",
        "## 1. Executive summary",
        "",
        f"- **Files evaluated:** {n}",
        f"- **Inference errors:** {metrics.get('errors', 0)}",
        f"- **Role recommendation:** **{role}**",
        "",
        f"- **Clean human accepted:** {metrics.get('clean_human_accepted', 0)} "
        f"(false alarms: {metrics.get('clean_human_false_alarm', 0)}, "
        f"borderline: {metrics.get('clean_human_borderline', 0)})",
        f"- **Direct AI detected / segment-suspicious:** "
        f"{metrics.get('direct_ai_detected_or_segment_suspicious', 0)}",
        f"- **Partial fabrication detected:** {metrics.get('partial_fabrication_detected', 0)}",
        "",
        "## 2. Class convention (from predictions)",
        "",
        *_class_convention_section(df),
        "## 3. Phase 7E0 standalone gates",
        "",
        _md_table(
            ["metric", "value", "threshold", "pass"],
            [
                [name, gr["value"], gr["threshold"], "YES" if gr["passed"] else "NO"]
                for name, gr in gate_results.items()
            ],
        ),
        "",
        "## 4. Branch-only gates",
        "",
        _md_table(
            ["metric", "value", "threshold", "pass"],
            [
                [name, gr["value"], gr["threshold"], "YES" if gr["passed"] else "NO"]
                for name, gr in branch_results.items()
            ],
        ),
        "",
        "## 5. Status distribution",
        "",
        _md_table(
            ["aasist_status", "count", "%"],
            [[st, cnt, _pct(cnt, n)] for st, cnt in statuses.most_common() if st],
        ),
        "",
        *_status_traceability_section(),
    ]
    write_markdown(output_md, lines)


def write_analysis_md_7a(df: pd.DataFrame, metrics: dict[str, int], output_md: Path) -> None:
    statuses = _status_counts(df)
    n = len(df)
    lines = [
        "# Phase 7E3A — AASIST-L Pretrained Analysis (phase7a holdout)",
        "",
        f"**Generated:** {utc_now_iso()}",
        "**Model:** pretrained AASIST-L (no fine-tuning)",
        "",
        "## 1. Executive summary",
        "",
        f"- **Files evaluated:** {n}",
        f"- **Inference errors:** {metrics.get('errors', 0)}",
        "- **Role recommendation:** **holdout_review** (7A does not use 7C1 standalone/branch-only gates)",
        "",
        "## 2. Class convention (from predictions)",
        "",
        *_class_convention_section(df),
        "## 3. Holdout category summary",
        "",
        _md_table(
            ["metric", "count"],
            [
                ["clean_human_accepted", metrics.get("clean_human_accepted", 0)],
                ["clean_human_false_alarm", metrics.get("clean_human_false_alarm", 0)],
                ["clean_human_borderline", metrics.get("clean_human_borderline", 0)],
                ["direct_ai_detected", metrics.get("direct_ai_detected", 0)],
                ["direct_ai_missed", metrics.get("direct_ai_missed", 0)],
                [
                    "direct_ai_detected_or_segment_suspicious",
                    metrics.get("direct_ai_detected_or_segment_suspicious", 0),
                ],
                ["human_processed_detected", metrics.get("human_processed_detected", 0)],
                ["human_processed_missed", metrics.get("human_processed_missed", 0)],
                ["ai_processed_detected", metrics.get("ai_processed_detected", 0)],
                ["ai_processed_missed", metrics.get("ai_processed_missed", 0)],
                [
                    "ai_processed_detected_or_segment_suspicious",
                    metrics.get("ai_processed_detected_or_segment_suspicious", 0),
                ],
                ["human_replay_detected", metrics.get("human_replay_detected", 0)],
                ["human_replay_missed", metrics.get("human_replay_missed", 0)],
                ["ai_replay_detected", metrics.get("ai_replay_detected", 0)],
                ["ai_replay_missed", metrics.get("ai_replay_missed", 0)],
        [
            "ai_replay_detected_or_segment_suspicious",
            metrics.get("ai_replay_detected_or_segment_suspicious", 0),
        ],
        [
            "ai_processed_detected_or_segment_suspicious",
            metrics.get("ai_processed_detected_or_segment_suspicious", 0),
        ],
        ["partial_fabrication_detected", metrics.get("partial_fabrication_detected", 0)],
                ["partial_fabrication_missed", metrics.get("partial_fabrication_missed", 0)],
                ["partial_fabrication_not_evaluable", metrics.get("partial_fabrication_not_evaluable", 0)],
            ],
        ),
        "",
        "## 4. Full status distribution",
        "",
        _md_table(
            ["aasist_status", "count", "%"],
            [[st, cnt, _pct(cnt, n)] for st, cnt in statuses.most_common() if st],
        ),
        "",
        "## 5. Interpretation",
        "",
        "Compare holdout behavior to Phase 7C1 and HybridResNet product CSV before any 7E3B fine-tune decision. "
        "Do **not** apply Phase 7C1 numeric acceptance gates directly to this holdout set.",
        "",
        *_status_traceability_section(),
    ]
    write_markdown(output_md, lines)


def detect_dataset_label(pred_path: Path) -> str:
    p = pred_path.as_posix().lower()
    if "phase7a" in p or "/phase7a/" in p:
        return "phase7a"
    return "phase7c1"


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze AASIST pretrained predictions")
    parser.add_argument("--predictions_csv", type=str, required=True)
    parser.add_argument("--output_md", type=str, required=True)
    parser.add_argument("--output_summary_csv", type=str, required=True)
    args = parser.parse_args()

    pred_path = resolve_path(args.predictions_csv)
    if not pred_path.is_file():
        print(f"Predictions not found: {pred_path}")
        return 1

    df = ensure_status_column(pd.read_csv(pred_path))
    dataset_label = detect_dataset_label(pred_path)

    out_md = resolve_path(args.output_md)
    out_csv = resolve_path(args.output_summary_csv)
    ensure_dir(out_md.parent)
    ensure_dir(out_csv.parent)

    if dataset_label == "phase7a":
        metrics = compute_7a_metrics(df)
        role = "holdout_review"
        write_analysis_md_7a(df, metrics, out_md)
        summary = pd.DataFrame([{"metric": k, "value": v} for k, v in metrics.items()])
        summary = pd.concat(
            [summary, pd.DataFrame([{"metric": "role_recommendation", "value": role}])],
            ignore_index=True,
        )
        summary.to_csv(out_csv, index=False)
    else:
        metrics = compute_7c1_metrics(df)
        gate_results = check_gates(metrics, GATES_7C1)
        branch_results = check_gates(metrics, GATES_BRANCH)
        role = recommend_role_7c1(gate_results, branch_results)
        write_analysis_md_7c1(df, metrics, gate_results, branch_results, role, out_md)
        summary_rows = build_summary_csv(metrics, gate_results, role)
        branch_df = pd.DataFrame(
            [
                {
                    "metric": f"branch_gate_{k}",
                    "value": v["value"],
                    "threshold": v["threshold"],
                    "passed": v["passed"],
                }
                for k, v in branch_results.items()
            ]
        )
        pd.concat([summary_rows, branch_df], ignore_index=True).to_csv(out_csv, index=False)

    print(f"Wrote {out_md}")
    print(f"Wrote {out_csv}")
    print(f"Role recommendation: {role}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
