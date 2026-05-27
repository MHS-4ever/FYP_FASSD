"""
Organize FASSD model checkpoints into models_saved/ (copy only — never move originals).

Usage:
  python code/phase8/validation/organize_model_checkpoints.py --models_root models_saved
  python code/phase8/validation/organize_model_checkpoints.py --models_root models_saved --dry_run
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]

REGISTRY_COLUMNS = [
    "asset_id",
    "category",
    "status",
    "usage",
    "source_path",
    "target_path",
    "sha256",
    "size_mb",
    "action",
    "notes",
]


@dataclass
class CheckpointSpec:
    asset_id: str
    category: str
    status: str
    usage: str
    source_candidates: list[str]
    target_relpath: str
    required: bool = False
    notes: str = ""


CHECKPOINT_SPECS: list[CheckpointSpec] = [
    CheckpointSpec(
        asset_id="hybrid_resnet_environmental_best",
        category="active",
        status="active_evidence_model",
        usage="HybridResNet baseline evidence branch for replay/mixer/partial sensitivity.",
        source_candidates=["models_saved/hybrid_resnet_environmental_best.pth"],
        target_relpath="active/hybrid_resnet_environmental_best.pth",
        required=True,
        notes="Not a final standalone forensic product model.",
    ),
    CheckpointSpec(
        asset_id="phase7c3_r2_best_product",
        category="prototype_evidence",
        status="prototype_evidence_only",
        usage="Rejected as standalone; reproduce Phase 7C4-v2 decision-layer analysis only.",
        source_candidates=[
            "reports/phase7/phase7c3_finetune_r2/training/checkpoints/hybrid_resnet_environmental_phase7c3_r2_best_product.pth",
            "reports/phase7c3_finetune_r2/training/checkpoints/hybrid_resnet_environmental_phase7c3_r2_best_product.pth",
        ],
        target_relpath="prototype_evidence/phase7c3_r2_best_product_rejected_standalone.pth",
    ),
    CheckpointSpec(
        asset_id="phase7c3_r2_best_loss",
        category="prototype_evidence",
        status="prototype_evidence_only",
        usage="Rejected as standalone; reproduce Phase 7C4-v2 decision-layer analysis only.",
        source_candidates=[
            "reports/phase7/phase7c3_finetune_r2/training/checkpoints/hybrid_resnet_environmental_phase7c3_r2_best_loss.pth",
            "reports/phase7c3_finetune_r2/training/checkpoints/hybrid_resnet_environmental_phase7c3_r2_best_loss.pth",
        ],
        target_relpath="prototype_evidence/phase7c3_r2_best_loss_rejected_standalone.pth",
    ),
    CheckpointSpec(
        asset_id="aasist_l_official_pretrained",
        category="pretrained_reference",
        status="pretrained_reference_only",
        usage="Official AASIST-L reference only; rejected as current product solution.",
        source_candidates=["code/phase7/aasist/vendor/AASIST/models/weights/AASIST-L.pth"],
        target_relpath="pretrained_reference/aasist_l_official_pretrained_reference.pth",
    ),
    CheckpointSpec(
        asset_id="aasist_official_pretrained",
        category="pretrained_reference",
        status="pretrained_reference_only",
        usage="Official AASIST reference only; rejected as current product solution.",
        source_candidates=["code/phase7/aasist/vendor/AASIST/models/weights/AASIST.pth"],
        target_relpath="pretrained_reference/aasist_official_pretrained_reference.pth",
    ),
    CheckpointSpec(
        asset_id="aasist_l_phase7e3c_best_product",
        category="rejected_archive",
        status="rejected_checkpoint",
        usage="Do not use in product. Archive only.",
        source_candidates=[
            "reports/phase7/phase7e_aasist_experiment/phase7e3c_finetune/training/checkpoints/aasist_l_phase7e3c_best_product.pth",
            "reports/phase7e_aasist_experiment/phase7e3c_finetune/training/checkpoints/aasist_l_phase7e3c_best_product.pth",
        ],
        target_relpath="rejected_archive/aasist_l_phase7e3c_best_product_rejected.pth",
    ),
    CheckpointSpec(
        asset_id="aasist_l_phase7e3c_best_loss",
        category="rejected_archive",
        status="rejected_checkpoint",
        usage="Do not use in product. Archive only.",
        source_candidates=[
            "reports/phase7/phase7e_aasist_experiment/phase7e3c_finetune/training/checkpoints/aasist_l_phase7e3c_best_loss.pth",
            "reports/phase7e_aasist_experiment/phase7e3c_finetune/training/checkpoints/aasist_l_phase7e3c_best_loss.pth",
        ],
        target_relpath="rejected_archive/aasist_l_phase7e3c_best_loss_rejected.pth",
    ),
]


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            block = f.read(chunk_size)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def size_mb(path: Path) -> float:
    return round(path.stat().st_size / (1024 * 1024), 3)


def resolve_repo_path(rel: str) -> Path:
    return (REPO_ROOT / rel).resolve()


def find_source(spec: CheckpointSpec) -> Path | None:
    for rel in spec.source_candidates:
        p = resolve_repo_path(rel)
        if p.is_file():
            return p
    return None


def ensure_dirs(models_root: Path) -> None:
    for sub in ("active", "prototype_evidence", "pretrained_reference", "rejected_archive", "registry"):
        (models_root / sub).mkdir(parents=True, exist_ok=True)


def process_spec(
    spec: CheckpointSpec,
    models_root: Path,
    *,
    dry_run: bool,
    overwrite: bool,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Returns registry row and optional warning row."""
    target = (models_root / spec.target_relpath).resolve()
    source = find_source(spec)

    row: dict[str, Any] = {
        "asset_id": spec.asset_id,
        "category": spec.category,
        "status": spec.status,
        "usage": spec.usage,
        "source_path": str(source) if source else "",
        "target_path": str(target),
        "sha256": "",
        "size_mb": "",
        "action": "",
        "notes": spec.notes,
    }
    warning: dict[str, Any] | None = None

    if source is None:
        if target.is_file():
            row["sha256"] = sha256_file(target)
            row["size_mb"] = size_mb(target)
            row["action"] = "present_at_target_no_source"
            row["notes"] = (spec.notes + " Source not found; target already exists.").strip()
            return row, warning
        row["action"] = "missing"
        if spec.required:
            warning = {
                "asset_id": spec.asset_id,
                "severity": "error",
                "message": f"Required checkpoint missing: {spec.asset_id}",
                "candidates": "; ".join(spec.source_candidates),
            }
        else:
            warning = {
                "asset_id": spec.asset_id,
                "severity": "warning",
                "message": f"Optional checkpoint missing: {spec.asset_id}",
                "candidates": "; ".join(spec.source_candidates),
            }
        return row, warning

    source = source.resolve()
    if source == target:
        row["sha256"] = sha256_file(source)
        row["size_mb"] = size_mb(source)
        row["action"] = "skip_same_path"
        return row, warning

    source_hash = sha256_file(source)
    row["sha256"] = source_hash
    row["size_mb"] = size_mb(source)

    if target.is_file():
        target_hash = sha256_file(target)
        if target_hash == source_hash:
            row["action"] = "skipped_hash_match"
            return row, warning
        if not overwrite:
            row["action"] = "skipped_hash_mismatch"
            warning = {
                "asset_id": spec.asset_id,
                "severity": "warning",
                "message": "Target exists with different hash; use --overwrite to replace",
                "source_path": str(source),
                "target_path": str(target),
            }
            return row, warning

    if dry_run:
        row["action"] = "dry_run_would_copy"
        return row, warning

    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    row["action"] = "copied"
    row["sha256"] = sha256_file(target)
    row["size_mb"] = size_mb(target)
    return row, warning


def write_registry_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=REGISTRY_COLUMNS)
        w.writeheader()
        w.writerows(rows)


def write_warnings_csv(path: Path, warnings: list[dict[str, Any]]) -> None:
    if not warnings:
        path.write_text("asset_id,severity,message,candidates,source_path,target_path\n", encoding="utf-8")
        return
    fields = ["asset_id", "severity", "message", "candidates", "source_path", "target_path"]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(warnings)


def write_registry_md(path: Path, rows: list[dict[str, Any]], warnings: list[dict[str, Any]], models_root: Path) -> None:
    ts = datetime.now(timezone.utc).isoformat()

    def _section(title: str, category: str) -> list[str]:
        lines = [f"## {title}", ""]
        subset = [r for r in rows if r["category"] == category]
        if not subset:
            lines.append("_No entries._")
            lines.append("")
            return lines
        lines.append("| asset_id | action | target | sha256 (prefix) | size_mb |")
        lines.append("| --- | --- | --- | --- | --- |")
        for r in subset:
            h = r.get("sha256") or ""
            prefix = h[:16] + "…" if len(h) > 16 else h
            lines.append(
                f"| {r['asset_id']} | {r['action']} | `{Path(r['target_path']).name}` | `{prefix}` | {r.get('size_mb', '')} |"
            )
        lines.append("")
        return lines

    lines = [
        "# Model Checkpoint Registry",
        "",
        f"**Generated:** {ts}",
        f"**Models root:** `{models_root.resolve()}`",
        "",
        "Original experiment paths are preserved. This registry documents **copies** only.",
        "",
    ]
    lines.extend(_section("1. Active Product/Evidence Checkpoints", "active"))
    lines.extend(_section("2. Prototype Evidence Checkpoints", "prototype_evidence"))
    lines.extend(_section("3. Pretrained Reference Checkpoints", "pretrained_reference"))
    lines.extend(_section("4. Rejected Archive Checkpoints", "rejected_archive"))

    lines.extend(["## 5. Missing / Warnings", ""])
    if warnings:
        for w in warnings:
            lines.append(f"- **{w.get('severity', 'warning')}** `{w.get('asset_id', '')}`: {w.get('message', '')}")
    else:
        lines.append("_None._")
    lines.append("")

    lines.extend(
        [
            "## 6. Usage Rules",
            "",
            "- Only `models_saved/active/` is allowed for the current production/evidence pipeline by default.",
            "- `prototype_evidence/` may be used only to reproduce Phase 7C4-v2 prototype results.",
            "- `pretrained_reference/` is reference only (AASIST rejected as current solution).",
            "- `rejected_archive/` must **not** be used in product decisions.",
            "- Do not treat HybridResNet as a final forensic classifier.",
            "- Phase 8 must use multi-axis evidence fusion, not binary fake/real classification alone.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Organize model checkpoints into models_saved/ (copy only)")
    parser.add_argument("--models_root", type=str, default="models_saved", help="Root folder (relative to repo)")
    parser.add_argument("--dry_run", action="store_true", help="Plan copies without writing files")
    parser.add_argument("--overwrite", action="store_true", help="Replace targets when hash differs")
    args = parser.parse_args()

    models_root = (REPO_ROOT / args.models_root).resolve()
    if not args.dry_run:
        ensure_dirs(models_root)
    else:
        ensure_dirs(models_root)

    registry_rows: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for spec in CHECKPOINT_SPECS:
        row, warn = process_spec(spec, models_root, dry_run=args.dry_run, overwrite=args.overwrite)
        registry_rows.append(row)
        if warn:
            warnings.append(warn)
            if warn.get("severity") == "error":
                errors.append(warn)

    reg_dir = models_root / "registry"
    if not args.dry_run:
        reg_dir.mkdir(parents=True, exist_ok=True)
        write_registry_csv(reg_dir / "CHECKPOINT_REGISTRY.csv", registry_rows)
        (reg_dir / "CHECKPOINT_REGISTRY.json").write_text(
            json.dumps({"generated": datetime.now(timezone.utc).isoformat(), "entries": registry_rows}, indent=2),
            encoding="utf-8",
        )
        write_registry_md(reg_dir / "CHECKPOINT_REGISTRY.md", registry_rows, warnings, models_root)
        write_warnings_csv(reg_dir / "CHECKPOINT_MISSING_OR_WARNING_ITEMS.csv", warnings)

    copied = sum(1 for r in registry_rows if r["action"] == "copied")
    skipped = sum(1 for r in registry_rows if r["action"].startswith("skipped") or r["action"] == "skip_same_path")
    missing = sum(1 for r in registry_rows if r["action"] == "missing")

    print("=== organize_model_checkpoints ===")
    print(f"models_root: {models_root}")
    print(f"dry_run: {args.dry_run}")
    print(f"copied: {copied}")
    print(f"skipped: {skipped}")
    print(f"missing: {missing}")
    print(f"warnings: {len(warnings)}")
    if not args.dry_run:
        print(f"registry: {reg_dir / 'CHECKPOINT_REGISTRY.md'}")
    print("Reminder: copy only — originals are not moved or deleted.")

    if errors:
        print("\nERROR: required checkpoint(s) missing:", file=sys.stderr)
        for e in errors:
            print(f"  - {e.get('asset_id')}: {e.get('message')}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
