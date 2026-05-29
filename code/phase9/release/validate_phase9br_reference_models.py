#!/usr/bin/env python3
"""Validate Phase 9B-R legacy/reference model copy layout and inactive metadata."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REFERENCE_STATUS = "legacy_reference_experimental"
REQUIRED_META_KEYS = (
    "status",
    "active_in_fusion",
    "used_by_default",
    "not_final_forensic_decision",
    "allowed_use",
    "forbidden_use",
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def resolve_path(root: Path, path_str: str) -> Path:
    p = Path(path_str)
    return p if p.is_absolute() else (root / p).resolve()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_metadata(path: Path, family: str) -> list[str]:
    issues: list[str] = []
    if not path.is_file():
        return [f"{family}: metadata missing at {path.as_posix()}"]
    meta = _read_json(path)
    if meta.get("status") != REFERENCE_STATUS:
        issues.append(f"{family}: status must be {REFERENCE_STATUS}")
    if meta.get("active_in_fusion") is not False:
        issues.append(f"{family}: active_in_fusion must be false")
    if meta.get("used_by_default") is not False:
        issues.append(f"{family}: used_by_default must be false")
    if meta.get("not_final_forensic_decision") is not True:
        issues.append(f"{family}: not_final_forensic_decision must be true")
    for key in REQUIRED_META_KEYS:
        if key not in meta:
            issues.append(f"{family}: missing metadata key {key}")
    note = str(meta.get("phase9c_note", "")).lower()
    if "phase 9c" not in note and "9c" not in note:
        issues.append(f"{family}: metadata should warn about Phase 9C inactive use")
    text = json.dumps(meta).lower()
    scrubbed = str(meta.get("forbidden_use", "")).lower()
    if "fake_score" in text.replace(scrubbed, "") or "real_score" in text.replace(scrubbed, ""):
        issues.append(f"{family}: fake_score/real_score must not appear outside forbidden_use")
    return issues


def validate(reference_root: Path, root: Path) -> tuple[bool, list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []

    if not reference_root.exists():
        failures.append("reference root missing")

    for family, sub in (("AASIST", "aasist"), ("HybridResNet", "hybrid_resnet")):
        folder = reference_root / sub
        if not folder.exists():
            warnings.append(f"{family}: folder missing (no files copied yet?)")
            continue
        files = [p for p in folder.iterdir() if p.is_file() and p.name != "metadata.json"]
        if files and not (folder / "metadata.json").is_file():
            failures.append(f"{family}: files present but metadata.json missing")
        if files:
            failures.extend(_validate_metadata(folder / "metadata.json", family))

    inv = reference_root / "reference_model_inventory.json"
    if not inv.is_file():
        warnings.append("reference_model_inventory.json missing (run copy script first)")
    else:
        payload = _read_json(inv)
        if payload.get("active_release_models_unchanged") is not True:
            failures.append("inventory active_release_models_unchanged must be true")

    active_saved = root / "models_saved" / "active"
    if active_saved.exists() and any(active_saved.glob("*")):
        warnings.append("models_saved/active has files; ensure copy script did not write there")

    for active_dir in ("origin", "replay", "mixer", "partial_segment"):
        p = root / "release" / "models" / active_dir
        # Only warn if reference files accidentally placed in active dirs.
        if p.exists():
            for ref_name in ("aasist", "hybrid", "resnet"):
                hits = list(p.rglob(f"*{ref_name}*"))
                if hits:
                    failures.append(
                        f"reference-like file found in active folder {active_dir}: {hits[0].as_posix()}"
                    )

    return len(failures) == 0, failures, warnings


def write_report(path: Path, ok: bool, failures: list[str], warnings: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    status = "PASS" if ok else "FAIL"
    lines = ["# Phase 9B-R Reference Model Validation Report", "", f"- Status: {status}"]
    if failures:
        lines.append("- Failures:")
        for f in failures:
            lines.append(f"  - {f}")
    if warnings:
        lines.append("- Warnings:")
        for w in warnings:
            lines.append(f"  - {w}")
    if ok and not warnings:
        lines.append("- reference models correctly marked inactive")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate Phase 9B-R reference models.")
    p.add_argument("--reference_root", default="release/models/reference")
    p.add_argument(
        "--output_report",
        default="reports/phase9/validation/phase9br_reference_model_validation_report.md",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()
    reference_root = resolve_path(root, args.reference_root)
    ok, failures, warnings = validate(reference_root, root)
    write_report(resolve_path(root, args.output_report), ok, failures, warnings)
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
