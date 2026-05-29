#!/usr/bin/env python3
"""
Phase 9B-R: copy legacy/reference AASIST and HybridResNet checkpoints into release/models/reference/.

Manual-run only. Does not modify active release model folders or models_saved/active/.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REFERENCE_STATUS = "legacy_reference_experimental"
ARTIFACT_SCHEMA_VERSION = "phase9br_reference_v1"
ALLOWED_EXTENSIONS = {".pt", ".pth", ".ckpt", ".joblib", ".pkl", ".json", ".yaml", ".yml"}

AASIST_PATTERNS = (re.compile(r"aasist", re.I),)
HYBRID_PATTERNS = (
    re.compile(r"hybrid", re.I),
    re.compile(r"resnet", re.I),
    re.compile(r"hybridresnet", re.I),
    re.compile(r"hybrid_resnet", re.I),
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def resolve_path(root: Path, path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else (root / p).resolve()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _matches_family(name: str, patterns: tuple[re.Pattern, ...]) -> bool:
    return any(p.search(name) for p in patterns)


def classify_candidate(path: Path) -> str | None:
    if path.suffix.lower() not in ALLOWED_EXTENSIONS:
        return None
    name = path.name
    if _matches_family(name, AASIST_PATTERNS):
        return "aasist"
    if _matches_family(name, HYBRID_PATTERNS):
        return "hybrid_resnet"
    return None


def discover_candidates(scan_roots: list[Path]) -> dict[str, list[Path]]:
    found: dict[str, list[Path]] = {"aasist": [], "hybrid_resnet": []}
    seen: set[str] = set()
    for root in scan_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            key = str(path.resolve())
            if key in seen:
                continue
            family = classify_candidate(path)
            if family:
                seen.add(key)
                found[family].append(path.resolve())
    return found


def build_group_metadata(model_family: str, files: list[dict[str, Any]]) -> dict[str, Any]:
    purpose = (
        "legacy/reference spoofing or deepfake-audio baseline model"
        if model_family == "AASIST"
        else "legacy/reference hybrid ResNet baseline model"
    )
    return {
        "artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
        "model_family": model_family,
        "status": REFERENCE_STATUS,
        "active_in_fusion": False,
        "used_by_default": False,
        "not_final_forensic_decision": True,
        "source_phase": "earlier Phase 7/8 baseline experiment",
        "purpose": purpose,
        "allowed_use": [
            "reference comparison",
            "historical baseline documentation",
            "future validation candidate",
        ],
        "forbidden_use": [
            "active Phase 9C inference without validation",
            "final fake/real decision",
            "court-ready proof",
            "replacement for multi-axis fusion",
        ],
        "limitations": [
            "not integrated into current multi-axis evidence architecture",
            "may not distinguish AI origin from replay/channel artifacts",
            "requires separate validation before active use",
        ],
        "phase9c_note": (
            "Not part of active Phase 9C inference unless separately validated and explicitly enabled."
        ),
        "files": files,
        "created_at": now_iso(),
        "created_by_script": "copy_phase9br_reference_models.py",
    }


def copy_file(src: Path, dest: Path, mode: str, force: bool) -> str:
    if dest.exists() and not force:
        return f"skipped_exists: {dest.as_posix()}"
    if mode == "manifest_only":
        return f"manifest_only: {src.as_posix()} -> {dest.as_posix()}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return f"copied: {src.as_posix()} -> {dest.as_posix()}"


def process_family(
    family_key: str,
    model_family: str,
    sources: list[Path],
    output_root: Path,
    copy_mode: str,
    force: bool,
) -> tuple[list[dict[str, Any]], list[str]]:
    dest_dir = output_root / family_key
    logs: list[str] = []
    file_records: list[dict[str, Any]] = []
    for src in sources:
        dest = dest_dir / src.name
        action = copy_file(src, dest, copy_mode, force)
        logs.append(action)
        file_records.append(
            {
                "source_path": str(src.as_posix()),
                "dest_path": str(dest.as_posix()),
                "action": action.split(":")[0],
            }
        )
    if file_records:
        meta_path = dest_dir / "metadata.json"
        meta_path.parent.mkdir(parents=True, exist_ok=True)
        meta_path.write_text(
            json.dumps(build_group_metadata(model_family, file_records), indent=2),
            encoding="utf-8",
        )
        logs.append(f"metadata_written: {meta_path.as_posix()}")
    return file_records, logs


def write_inventory(
    output_root: Path,
    aasist_files: list[dict[str, Any]],
    hybrid_files: list[dict[str, Any]],
    warnings: list[str],
) -> None:
    missing = []
    if not aasist_files:
        missing.append("aasist")
    if not hybrid_files:
        missing.append("hybrid_resnet")
    payload = {
        "inventory_schema_version": ARTIFACT_SCHEMA_VERSION,
        "created_at": now_iso(),
        "reference_models": ["aasist", "hybrid_resnet"],
        "aasist": {"files": aasist_files},
        "hybrid_resnet": {"files": hybrid_files},
        "missing_reference_models": missing,
        "warnings": warnings,
        "active_release_models_unchanged": True,
        "status": REFERENCE_STATUS,
    }
    path = output_root / "reference_model_inventory.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_report(path: Path, logs: list[str], warnings: list[str]) -> None:
    lines = [
        "# Phase 9B-R Reference Model Copy Report",
        "",
        f"**Generated:** {now_iso()}",
        "",
        f"- status: {REFERENCE_STATUS}",
        "- active_in_fusion: false",
        "- used_by_default: false",
        "- active release model folders unchanged",
        "",
        "## Actions",
        "",
    ]
    for line in logs:
        lines.append(f"- {line}")
    if warnings:
        lines.extend(["", "## Warnings", ""])
        for w in warnings:
            lines.append(f"- {w}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Copy legacy reference AASIST/HybridResNet checkpoints.")
    p.add_argument("--aasist_paths", nargs="*", default=[])
    p.add_argument("--hybrid_resnet_paths", nargs="*", default=[])
    p.add_argument("--auto_scan", action="store_true")
    p.add_argument("--scan_roots", nargs="*", default=["models_saved", "models", "checkpoints", "reports", "code"])
    p.add_argument("--output_root", default="release/models/reference")
    p.add_argument("--copy_mode", choices=["copy", "manifest_only"], default="copy")
    p.add_argument("--force", action="store_true")
    p.add_argument(
        "--report",
        default="reports/phase9/release/phase9br_reference_model_copy_report.md",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()
    output_root = resolve_path(root, args.output_root)
    warnings: list[str] = []
    logs: list[str] = []

    aasist_sources = [resolve_path(root, p) for p in args.aasist_paths]
    hybrid_sources = [resolve_path(root, p) for p in args.hybrid_resnet_paths]

    for p in aasist_sources + hybrid_sources:
        if not p.is_file():
            warnings.append(f"explicit path not found: {p}")

    aasist_sources = [p for p in aasist_sources if p.is_file()]
    hybrid_sources = [p for p in hybrid_sources if p.is_file()]

    if args.auto_scan:
        scan_roots = [resolve_path(root, s) for s in args.scan_roots]
        discovered = discover_candidates(scan_roots)
        aasist_sources = sorted(set(aasist_sources + discovered["aasist"]))
        hybrid_sources = sorted(set(hybrid_sources + discovered["hybrid_resnet"]))
        logs.append(f"auto_scan_roots: {[s.as_posix() for s in scan_roots]}")

    if not aasist_sources:
        warnings.append("no AASIST candidates found")
    if not hybrid_sources:
        warnings.append("no HybridResNet candidates found")

    aasist_files, a_logs = process_family(
        "aasist", "AASIST", aasist_sources, output_root, args.copy_mode, args.force
    )
    hybrid_files, h_logs = process_family(
        "hybrid_resnet",
        "HybridResNet",
        hybrid_sources,
        output_root,
        args.copy_mode,
        args.force,
    )
    logs.extend(a_logs)
    logs.extend(h_logs)
    write_inventory(output_root, aasist_files, hybrid_files, warnings)
    write_report(resolve_path(root, args.report), logs, warnings)
    print(f"Reference copy complete. output={output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
