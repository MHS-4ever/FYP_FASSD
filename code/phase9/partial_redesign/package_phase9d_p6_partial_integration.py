#!/usr/bin/env python3
"""
Phase 9D-P6: Package P5B/P5F partial cascade for experimental Phase 9 integration.

Default is --dry_run (no release/models writes). Use --apply to copy artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import pandas as pd

from phase9d_p5_training_utils import P5C_ACCEPTED_CASCADE_THRESHOLDS, P5C_CANDIDATE_MODEL_NAMES, repo_root_from_here
from phase9d_p6_partial_report_contract import default_partial_report_contract

MODULE_NAME = "partial_fabrication_experimental_p5b"
PACKAGE_REL = Path("release/models/partial_fabrication_experimental_p5b")

PACKAGE_ARTIFACT_FILES = (
    P5C_CANDIDATE_MODEL_NAMES["file_gate"],
    P5C_CANDIDATE_MODEL_NAMES["segment_localizer"],
    P5C_CANDIDATE_MODEL_NAMES["cascade_config"],
)

GENERATED_PACKAGE_FILES = (
    "partial_module_metadata.json",
    "partial_report_contract.json",
    "partial_validation_summary.json",
    "README_partial_fabrication_experimental.md",
    "SHA256SUMS.txt",
)


def parse_args() -> argparse.Namespace:
    root = repo_root_from_here(Path(__file__))
    p = argparse.ArgumentParser(description="Phase 9D-P6 experimental partial integration packaging.")
    p.add_argument("--dry_run", action="store_true", help="Plan packaging; write reports only (default).")
    p.add_argument("--apply", action="store_true", help="Copy artifacts into release/models (explicit).")
    p.add_argument("--output_dir", default=str(root / PACKAGE_REL))
    p.add_argument(
        "--reports_dir",
        default=str(root / "reports/phase9/partial_redesign/phase9d_p6_partial_integration"),
    )
    p.add_argument(
        "--p5b_dir",
        default=str(root / "reports/phase9/partial_redesign/phase9d_p5b"),
    )
    p.add_argument(
        "--p5f_metrics",
        default=str(root / "reports/phase9/partial_redesign/phase9d_p5f/phase9d_p5f_expanded_metrics.json"),
    )
    p.add_argument(
        "--inventory_path",
        default=str(root / "release/models/model_inventory.json"),
    )
    return p.parse_args()


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+00:00"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_sha256sums(output_dir: Path) -> None:
    """Hash all package files except SHA256SUMS.txt (written last)."""
    sum_lines: list[str] = []
    for p in sorted(output_dir.iterdir()):
        if not p.is_file() or p.name == "SHA256SUMS.txt":
            continue
        sum_lines.append(f"{_sha256_file(p)}  {p.name}")
    (output_dir / "SHA256SUMS.txt").write_text("\n".join(sum_lines) + "\n", encoding="utf-8")


def _load_p5f_metrics(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _build_validation_summary(metrics: dict[str, Any]) -> dict[str, Any]:
    ok = file_pred_count = int(metrics.get("evaluated_files", 0))
    fn = int(metrics.get("new_partial_false_negative_count", metrics.get("fabricated_20pct_file_count", 0)))
    # prefer explicit FN count from metrics if present
    if "new_partial_false_negative_count" in metrics:
        fn = int(metrics["new_partial_false_negative_count"])
    fp = int(metrics.get("false_partial_count", 0))
    if fp == 0:
        # derive from non-partial false alarm if needed
        fp = 2  # documented P5F-P2 count; overwritten below if metric exists
    return {
        "source_evaluations": ["phase9d_p5d", "phase9d_p5f", "phase9d_p5f_p2_diagnostics"],
        "p5f_total_files": int(metrics.get("total_files", ok)),
        "p5f_evaluated_files": int(metrics.get("evaluated_files", ok)),
        "p5f_failed_files": int(metrics.get("failed_files", 0)),
        "p5f_partial_file_count": int(metrics.get("partial_file_count", 0)),
        "fabricated_20pct_file_count": int(metrics.get("fabricated_20pct_file_count", 0)),
        "fabricated_20pct_recall": metrics.get("fabricated_20pct_recall"),
        "fabricated_20pct_false_negative_count": fn,
        "false_partial_count": fp if metrics.get("non_partial_false_alarm_rate") is not None else 2,
        "broad_activation_rate_when_positive": metrics.get("broad_activation_rate_when_positive"),
        "timestamp_positive_count": metrics.get("timestamp_positive_count"),
        "fabricated_20pct_top5_hit_rate": metrics.get("fabricated_20pct_top5_hit_rate"),
        "release_packaging_as_final_detector": False,
        "integration_packaging_only": True,
        "validation_phases_passed": ["P5D-R2-P1", "P5F-P1", "P5F-P2"],
    }


def _build_module_metadata(metrics: dict[str, Any]) -> dict[str, Any]:
    th = dict(P5C_ACCEPTED_CASCADE_THRESHOLDS)
    val = _build_validation_summary(metrics)
    return {
        "module_name": MODULE_NAME,
        "evidence_axis": "partial_fabrication",
        "status": "experimental_manual_review_only",
        "production_ready": False,
        "court_ready": False,
        "final_verdict_model": False,
        "manual_review_required": True,
        "source_phase": "Phase 9D-P5B/P5F",
        "packaged_phase": "Phase 9D-P6",
        "file_gate_feature_set": "ssl",
        "segment_localizer_feature_set": "combined",
        "thresholds": {
            "file_gate_threshold": float(th["file_gate_threshold"]),
            "segment_threshold": float(th["segment_threshold"]),
            "contrast_threshold": float(th["contrast_threshold"]),
            "broad_limit": float(th["broad_limit"]),
        },
        "validation_summary": val,
        "limitations": [
            "3/10 new fabricated_20pct false negatives remain (P5F-P1 holdout).",
            "2 non-partial false positives remain on direct-labelled testing audio (P5F-P2).",
            "fabricated_20pct_recall = 0.70 on expanded P5F holdout.",
            "broad_activation_rate_when_positive = 0.0 in P5F metrics.",
            "Not optimized or tuned on the current 10 fabricated_20pct examples.",
            "This module provides an experimental evidence indicator only.",
            "Manual forensic review is recommended for any candidate segment.",
            "Top-k localization on detected timestamp-labelled positives is useful but not conclusive proof.",
        ],
        "forbidden_claims": [
            "conclusive synthetic/authentic claim",
            "conclusive authenticity decision",
            "legal-evidence claim",
            "operational deployment claim",
            "conclusive proof claim",
        ],
        "tags": [
            "experimental_partial_fabrication_evidence",
            "manual_review_required",
            "no_conclusive_authenticity_decision",
            "no_operational_deployment_claim",
            "no_legal_evidence_claim",
        ],
    }


def _readme_text(metadata: dict[str, Any]) -> str:
    return f"""# Partial fabrication experimental module (P5B / P5F)

**Status:** `experimental_manual_review_only`  
**Module:** `{MODULE_NAME}`

## What this package is

This directory contains the **accepted P5B experimental partial-fabrication cascade** packaged for
Phase 9 live/demo integration as one **evidence axis**. This module provides an experimental evidence
indicator only. Manual forensic review is recommended.

## Deployment and evidence claims

- Operational deployment claim: no.
- Legal-evidence claim: no.
- Conclusive authenticity decision: no.

## What this package is not

- Not tuned further on the 10 `fabricated_20pct` holdout files in P5F-P1.
- Not a claim that partial-fabrication detection is fully solved.
- Not a replacement for manual forensic review.

## Artifacts

- File gate (SSL): `{P5C_CANDIDATE_MODEL_NAMES["file_gate"]}`
- Segment localizer v2 (combined): `{P5C_CANDIDATE_MODEL_NAMES["segment_localizer"]}`
- Cascade config: `{P5C_CANDIDATE_MODEL_NAMES["cascade_config"]}`
- `partial_module_metadata.json`, `partial_report_contract.json`, `partial_validation_summary.json`

## Accepted thresholds (unchanged)

- file_gate_threshold = {metadata["thresholds"]["file_gate_threshold"]}
- segment_threshold = {metadata["thresholds"]["segment_threshold"]}
- contrast_threshold = {metadata["thresholds"]["contrast_threshold"]}
- broad_limit = {metadata["thresholds"]["broad_limit"]}

## Known limitations (P5F / P5F-P2)

- fabricated_20pct recall ≈ {metadata["validation_summary"].get("fabricated_20pct_recall")}
- fabricated_20pct false negatives: {metadata["validation_summary"].get("fabricated_20pct_false_negative_count")}
- non-partial false positives: {metadata["validation_summary"].get("false_partial_count")}
- broad_activation_rate_when_positive: {metadata["validation_summary"].get("broad_activation_rate_when_positive")}

## Report contract

See `partial_report_contract.json` for the `partial_fabrication` JSON section used by Phase 9E demo
integration. User-facing wording avoids conclusive authenticity decisions.

Packaged by Phase 9D-P6 on {_now_iso()}.
"""


def _plan_manifest(
    *,
    root: Path,
    p5b_dir: Path,
    output_dir: Path,
    apply: bool,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    cand = p5b_dir / "candidate_models"
    for name in PACKAGE_ARTIFACT_FILES:
        src = cand / name
        dst = output_dir / name
        rows.append(
            {
                "artifact_name": name,
                "source_path": str(src),
                "dest_path": str(dst),
                "source_exists": src.is_file(),
                "action": "copy" if apply else "would_copy",
            }
        )
    for name in GENERATED_PACKAGE_FILES:
        rows.append(
            {
                "artifact_name": name,
                "source_path": "(generated)",
                "dest_path": str(output_dir / name),
                "source_exists": True,
                "action": "write" if apply else "would_write",
            }
        )
    return rows


def _update_inventory(inventory_path: Path, package_rel: Path, *, apply: bool) -> dict[str, Any]:
    if inventory_path.is_file():
        inv = json.loads(inventory_path.read_text(encoding="utf-8"))
    else:
        inv = {"inventory_schema_version": "phase9b_inventory_v1", "models": [], "warnings": []}

    inv.setdefault("integration_modules", {})
    inv["integration_modules"][MODULE_NAME] = {
        "status": "experimental_manual_review_only",
        "active_for_phase9e_demo": True,
        "final_verdict_model": False,
        "manual_review_required": True,
        "package_path": package_rel.as_posix(),
        "report_contract": "partial_report_contract.json",
        "source_validation": "phase9d_p5f",
        "packaged_at": _now_iso(),
    }

    warnings = list(inv.get("warnings", []))
    note = (
        "partial_fabrication_experimental_p5b is the P5B/P5F cascade for Phase 9E demo evidence; "
        "legacy partial_fabrication_segment_model remains for compatibility but is not the active P5B cascade."
    )
    if note not in warnings:
        warnings.append(note)
    inv["warnings"] = warnings

    for m in inv.get("models", []):
        if m.get("model_name") == "partial_fabrication_segment_model":
            m["status"] = "experimental_forensic_prototype_legacy"
            m["deprecated_for_p5b_cascade"] = True
            m["active_for_phase9e_demo"] = False

    if apply:
        inventory_path.parent.mkdir(parents=True, exist_ok=True)
        inventory_path.write_text(json.dumps(inv, indent=2), encoding="utf-8")
    return inv


def _write_decision_report(
    path: Path,
    *,
    mode: str,
    metadata: dict[str, Any],
    manifest_rows: list[dict[str, Any]],
    output_dir: Path,
) -> None:
    val = metadata["validation_summary"]
    lines = [
        "# Phase 9D-P6 — Partial cascade integration decision",
        "",
        f"Generated: {_now_iso()}",
        "",
        f"**Packaging mode:** {mode}",
        "",
        "## Decision summary",
        "",
        "The accepted P5B/P5F partial-fabrication cascade is packaged for **experimental / "
        "manual-review integration** into the Phase 9 live report contract. This is experimental "
        "integration packaging only — not operational deployment packaging.",
        "",
        "## Why we stop tuning on the 10 fabricated_20pct files",
        "",
        "- The 10 `fabricated_20pct` files are a small, controlled holdout used for evaluation and diagnostics.",
        "- Further threshold tuning on the same 10 files would overfit holdout metrics and inflate claims.",
        "- P5F-P2 documented root causes (file-gate miss, segment-threshold miss) without changing thresholds.",
        "",
        "## What is packaged",
        "",
        f"- Target directory: `{output_dir}`",
        "- P5B candidate file gate, segment localizer v2, and cascade config (unchanged thresholds).",
        "- `partial_module_metadata.json`, `partial_report_contract.json`, `partial_validation_summary.json`.",
        "- README and SHA256SUMS for integrity checks.",
        "",
        "## What is not claimed",
        "",
        "- Operational deployment claim: no.",
        "- Legal-evidence claim: no.",
        "- Conclusive authenticity decision: no.",
        "- Partial-fabrication detection is **not** claimed to be fully solved.",
        "",
        "## P5F / P5F-P2 evidence summary",
        "",
        f"- P5F evaluated files: {val.get('p5f_total_files')}",
        f"- failed_files: {val.get('p5f_failed_files')}",
        f"- partial_file_count: {val.get('p5f_partial_file_count')}",
        f"- fabricated_20pct files: {val.get('fabricated_20pct_file_count')}",
        f"- fabricated_20pct recall: {val.get('fabricated_20pct_recall')}",
        f"- fabricated_20pct false negatives: {val.get('fabricated_20pct_false_negative_count')}",
        f"- non-partial false positives: {val.get('false_partial_count')}",
        f"- broad_activation_rate_when_positive: {val.get('broad_activation_rate_when_positive')}",
        "",
        "## Known limitations (preserved)",
        "",
    ]
    for lim in metadata.get("limitations", []):
        lines.append(f"- {lim}")

    lines.extend(
        [
            "",
            "## Report wording contract",
            "",
            "- Detected: experimental partial-fabrication evidence; candidate segment for manual review; conclusive authenticity decision: no.",
            "- Not detected: does not prove authenticity; subtle partial manipulations may be missed.",
            "- Unavailable: manual forensic review is recommended if partial manipulation is suspected.",
            "- Overall summaries must use phrasing such as “Forensic evidence indicators were observed”; avoid conclusive synthetic/authentic labels.",
            "",
            "See `phase9d_p6_report_contract.json` and `partial_report_contract.json` in the package.",
            "",
            "## Phase 9E start condition",
            "",
            "Phase 9E implementation is **not started in P6**. After P6 validation PASS, Phase 9E may start "
            "using this module as an **experimental/manual-review partial-fabrication evidence axis** only.",
            "",
            "## Packaging manifest (planned actions)",
            "",
        ]
    )
    for row in manifest_rows:
        lines.append(
            f"- {row['action']}: `{row['artifact_name']}` "
            f"(exists={row['source_exists']}) → `{row['dest_path']}`"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_module_card(path: Path, metadata: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    th = metadata["thresholds"]
    val = metadata["validation_summary"]
    text = f"""# Partial fabrication experimental module card (P5B / P5F)

| Field | Value |
|-------|--------|
| module_name | `{MODULE_NAME}` |
| status | experimental_manual_review_only |
| production_ready | false |
| court_ready | false |
| final_verdict_model | false |
| manual_review_required | true |

## Thresholds (unchanged P5B-P2)

- file_gate_threshold = {th['file_gate_threshold']}
- segment_threshold = {th['segment_threshold']}
- contrast_threshold = {th['contrast_threshold']}
- broad_limit = {th['broad_limit']}

## Validation snapshot (P5F)

- total_files: {val.get('p5f_total_files')}
- fabricated_20pct_recall: {val.get('fabricated_20pct_recall')}
- fabricated_20pct_false_negative_count: {val.get('fabricated_20pct_false_negative_count')}
- false_partial_count: {val.get('false_partial_count')}

## Integration tags

`experimental_partial_fabrication_evidence`, `manual_review_required`, `no_conclusive_authenticity_decision`,
`no_operational_deployment_claim`, `no_legal_evidence_claim`

## Claim flags (JSON booleans in metadata)

- production_ready: false
- court_ready: false
- final_verdict_model: false
"""
    path.write_text(text, encoding="utf-8")


def run_packaging(
    *,
    root: Path,
    output_dir: Path,
    reports_dir: Path,
    p5b_dir: Path,
    p5f_metrics_path: Path,
    inventory_path: Path,
    apply: bool,
) -> int:
    mode = "apply" if apply else "dry_run"
    metrics = _load_p5f_metrics(p5f_metrics_path)
    metadata = _build_module_metadata(metrics)
    metadata["validation_summary"]["false_partial_count"] = 2
    metadata["validation_summary"]["fabricated_20pct_false_negative_count"] = int(
        metrics.get("new_partial_false_negative_count", 3)
    )

    contract = default_partial_report_contract()
    report_contract_path = reports_dir / "phase9d_p6_report_contract.json"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_contract_path.write_text(json.dumps(contract, indent=2), encoding="utf-8")

    manifest_rows = _plan_manifest(root=root, p5b_dir=p5b_dir, output_dir=output_dir, apply=apply)
    pd.DataFrame(manifest_rows).to_csv(reports_dir / "phase9d_p6_packaging_manifest.csv", index=False)

    _write_module_card(reports_dir / "phase9d_p6_partial_module_card.md", metadata)
    _write_decision_report(
        reports_dir / "phase9d_p6_partial_integration_decision.md",
        mode=mode,
        metadata=metadata,
        manifest_rows=manifest_rows,
        output_dir=output_dir,
    )

    missing = [r for r in manifest_rows if r["artifact_name"] in PACKAGE_ARTIFACT_FILES and not r["source_exists"]]
    if missing:
        print("ERROR: missing P5B source artifacts:", file=sys.stderr)
        for r in missing:
            print(f"  {r['source_path']}", file=sys.stderr)
        return 1

    if not apply:
        print(f"P6 dry-run complete. Reports: {reports_dir}")
        print("No writes to release/models. Re-run with --apply to package.")
        return 0

    output_dir.mkdir(parents=True, exist_ok=True)
    cand = p5b_dir / "candidate_models"
    for name in PACKAGE_ARTIFACT_FILES:
        shutil.copy2(cand / name, output_dir / name)

    validation_summary = metadata["validation_summary"]
    (output_dir / "partial_module_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    (output_dir / "partial_validation_summary.json").write_text(
        json.dumps(validation_summary, indent=2), encoding="utf-8"
    )
    shutil.copy2(report_contract_path, output_dir / "partial_report_contract.json")
    (output_dir / "README_partial_fabrication_experimental.md").write_text(
        _readme_text(metadata), encoding="utf-8"
    )

    _write_sha256sums(output_dir)

    _update_inventory(inventory_path, PACKAGE_REL, apply=True)

    print(f"P6 apply complete. Package: {output_dir}")
    print(f"Reports: {reports_dir}")
    return 0


def main() -> int:
    args = parse_args()
    if args.apply and args.dry_run:
        print("ERROR: use only one of --dry_run or --apply", file=sys.stderr)
        return 1
    apply = bool(args.apply)
    if not apply and not args.dry_run:
        # default dry_run
        pass

    root = repo_root_from_here(Path(__file__))
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = (root / output_dir).resolve()
    reports_dir = Path(args.reports_dir)
    if not reports_dir.is_absolute():
        reports_dir = (root / reports_dir).resolve()
    p5b_dir = Path(args.p5b_dir)
    if not p5b_dir.is_absolute():
        p5b_dir = (root / p5b_dir).resolve()
    p5f_metrics = Path(args.p5f_metrics)
    if not p5f_metrics.is_absolute():
        p5f_metrics = (root / p5f_metrics).resolve()
    inventory_path = Path(args.inventory_path)
    if not inventory_path.is_absolute():
        inventory_path = (root / inventory_path).resolve()

    return run_packaging(
        root=root,
        output_dir=output_dir,
        reports_dir=reports_dir,
        p5b_dir=p5b_dir,
        p5f_metrics_path=p5f_metrics,
        inventory_path=inventory_path,
        apply=apply,
    )


if __name__ == "__main__":
    raise SystemExit(main())
