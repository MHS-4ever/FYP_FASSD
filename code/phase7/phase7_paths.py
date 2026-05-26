"""
Canonical paths under reports/phase7/ (post-reorg layout).

Legacy CLI paths like reports/phase7c1_baseline/... are remapped automatically.
"""

from __future__ import annotations

from pathlib import Path

P7 = "reports/phase7"

# Phase 7C1 baseline
BASELINE_RESULTS = f"{P7}/phase7c1_baseline/results/phase7c1_baseline_results.csv"
BASELINE_PARTIAL = f"{P7}/phase7c1_baseline/results/phase7c1_partial_fabrication_analysis.csv"

# R2 evaluation on 7C1
R2_PRODUCT_7C1 = (
    f"{P7}/phase7c3_finetune_r2/evaluation/best_product/phase7c1_after_r2/phase7c1_baseline_results.csv"
)
R2_LOSS_7C1 = (
    f"{P7}/phase7c3_finetune_r2/evaluation/best_loss/phase7c1_after_r2/phase7c1_baseline_results.csv"
)
R2_PRODUCT_PARTIAL = (
    f"{P7}/phase7c3_finetune_r2/evaluation/best_product/phase7c1_after_r2/phase7c1_partial_fabrication_analysis.csv"
)
R2_LOSS_PARTIAL = (
    f"{P7}/phase7c3_finetune_r2/evaluation/best_loss/phase7c1_after_r2/phase7c1_partial_fabrication_analysis.csv"
)

# Phase 7A holdout
HOLDOUT_PRODUCT = f"{P7}/phase7_forensic_tests/results/forensic_test_results_product.csv"
R2_HOLDOUT_PRODUCT = (
    f"{P7}/phase7c3_finetune_r2/evaluation/best_product/phase7a_holdout_after_r2/forensic_test_results_product.csv"
)
R2_HOLDOUT_LOSS = (
    f"{P7}/phase7c3_finetune_r2/evaluation/best_loss/phase7a_holdout_after_r2/forensic_test_results_product.csv"
)

# Phase 7C4 calibration outputs
C4_V1_DECISIONS = f"{P7}/phase7c4_calibration/calibration_outputs/phase7c4_candidate_decisions.csv"
C4_V2_DECISIONS = f"{P7}/phase7c4_calibration_v2/calibration_outputs/phase7c4_v2_candidate_decisions.csv"
C4_V2_ERRORS = f"{P7}/phase7c4_calibration_v2/calibration_outputs/phase7c4_v2_error_cases.csv"
C4_V2_REPORT = f"{P7}/phase7c4_calibration_v2/phase7c4_v2_decision_layer_report.md"
C4_V2_FINAL = f"{P7}/phase7c4_calibration_v2/phase7c4_v2_final_recommendation.md"


def relocate_phase7_report_path(path: str | Path) -> Path | None:
    """Map `reports/phase7c1_...` → `reports/phase7/phase7c1_...` (relative or absolute)."""
    p = Path(path)
    parts = p.parts
    try:
        i = parts.index("reports")
    except ValueError:
        return None
    if i + 1 >= len(parts):
        return None
    seg = parts[i + 1]
    if seg.startswith("phase7") and seg != "phase7":
        return Path(*parts[: i + 1], "phase7", *parts[i + 1 :])
    return None


def resolve_phase7_report_path(path: str | Path, *, for_write: bool = False) -> Path:
    """Resolve report path; accept legacy pre-reorg locations."""
    p = Path(path)
    if p.is_file():
        return p.resolve()
    relocated = relocate_phase7_report_path(p)
    if relocated is not None:
        if relocated.is_file() or for_write:
            return relocated.resolve()
    if for_write:
        return p.resolve()
    return p


def add_phase7c4_calibration_args(
    parser,
    *,
    output_subdir: str = "phase7c4_calibration",
    output_csv: str | None = None,
    output_md: str | None = None,
    include_v1_outputs: bool = False,
    include_v2_outputs: bool = False,
    v1_decisions_default: str = C4_V1_DECISIONS,
) -> None:
    """Register standard Phase 7C4 calibration CLI paths (with sensible defaults)."""
    out = f"{P7}/{output_subdir}/calibration_outputs"
    parser.add_argument("--baseline_csv", type=str, default=BASELINE_RESULTS)
    parser.add_argument("--r2_product_csv", type=str, default=R2_PRODUCT_7C1)
    parser.add_argument("--r2_loss_csv", type=str, default=R2_LOSS_7C1)
    parser.add_argument("--baseline_partial_csv", type=str, default=BASELINE_PARTIAL)
    parser.add_argument("--r2_product_partial_csv", type=str, default=R2_PRODUCT_PARTIAL)
    parser.add_argument("--r2_loss_partial_csv", type=str, default=R2_LOSS_PARTIAL)
    if include_v2_outputs:
        parser.add_argument("--output_csv", type=str, default=output_csv or C4_V2_DECISIONS)
        parser.add_argument("--error_csv", type=str, default=C4_V2_ERRORS)
        parser.add_argument("--output_md", type=str, default=output_md or C4_V2_REPORT)
        parser.add_argument("--final_md", type=str, default=C4_V2_FINAL)
        parser.add_argument("--v1_decisions_csv", type=str, default=v1_decisions_default)
    elif include_v1_outputs:
        parser.add_argument("--output_csv", type=str, default=output_csv or f"{out}/phase7c4_candidate_decisions.csv")
        parser.add_argument("--error_csv", type=str, default=f"{out}/phase7c4_error_cases.csv")
        parser.add_argument("--output_md", type=str, default=output_md or f"{P7}/{output_subdir}/phase7c4_decision_layer_report.md")
        parser.add_argument("--acceptance_csv", type=str, default="")
        parser.add_argument("--final_recommendation_md", type=str, default="")
    elif output_csv or output_md:
        if output_csv:
            parser.add_argument("--output_csv", type=str, default=output_csv)
        if output_md:
            parser.add_argument("--output_md", type=str, default=output_md)


def fix_legacy_path_string(text: str) -> str:
    """Rewrite legacy report path strings to reports/phase7/ layout."""
    out = text
    # longest prefixes first
    prefixes = [
        "reports/phase7c4_calibration_v2",
        "reports/phase7c4_calibration",
        "reports/phase7c3_finetune_r2",
        "reports/phase7c3_finetune",
        "reports/phase7c2_training_prep",
        "reports/phase7c1_collection",
        "reports/phase7c1_baseline",
        "reports/phase7_current_dataset_audit",
        "reports/phase7_forensic_tests",
        "reports/phase7_dataset",
    ]
    for pref in prefixes:
        sub = pref.split("/", 1)[1]
        out = out.replace(pref, f"reports/phase7/{sub}")
        old_win = "reports" + "\\" + sub.replace("/", "\\")
        new_win = "reports" + "\\" + "phase7" + "\\" + sub.replace("/", "\\")
        out = out.replace(old_win, new_win)
    return out
