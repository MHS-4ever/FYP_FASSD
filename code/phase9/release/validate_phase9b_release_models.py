#!/usr/bin/env python3
"""Validate Phase 9B packaged release model artifacts and metadata."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import joblib
from sklearn.pipeline import Pipeline

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from phase9b_packaging_utils import (  # noqa: E402
    RELEASE_STATUS,
    is_forbidden_partial_feature,
    repo_root_from_here,
    resolve_path,
    validate_no_forbidden_fields_in_metadata,
)


EXPECTED_MODELS = {
    "origin_file_model": {
        "artifact": "origin/origin_file_model__ssl__experimental.joblib",
        "metadata": "origin/origin_file_model__ssl__metadata.json",
        "feature_set": "ssl",
    },
    "replay_file_model": {
        "artifact": "replay/replay_file_model__acoustic__experimental.joblib",
        "metadata": "replay/replay_file_model__acoustic__metadata.json",
        "feature_set": "acoustic",
    },
    "mixer_file_model": {
        "artifact": "mixer/mixer_file_model__acoustic__experimental.joblib",
        "metadata": "mixer/mixer_file_model__acoustic__metadata.json",
        "feature_set": "acoustic",
    },
    "partial_fabrication_segment_model": {
        "artifact": "partial_segment/partial_segment_model__combined__experimental.joblib",
        "metadata": "partial_segment/partial_segment_model__combined__metadata.json",
        "feature_set": "combined",
    },
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate Phase 9B release model artifacts.")
    p.add_argument("--release_models_root", default="release/models")
    p.add_argument(
        "--output_report",
        default="reports/phase9/validation/phase9b_release_model_validation_report.md",
    )
    p.add_argument("--require_artifacts", action="store_true", default=True)
    p.add_argument("--no_require_artifacts", dest="require_artifacts", action="store_false")
    return p.parse_args()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate(root: Path, models_root: Path, require_artifacts: bool) -> tuple[bool, list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []

    if not models_root.exists():
        failures.append(f"release models root missing: {models_root}")

    for folder in ("origin", "replay", "mixer", "partial_segment"):
        if not (models_root / folder).exists():
            failures.append(f"missing model folder: {folder}")

    inventory_path = models_root / "model_inventory.json"
    if not inventory_path.is_file():
        if require_artifacts:
            failures.append("model_inventory.json missing")
    else:
        inv = _read_json(inventory_path)
        if inv.get("status") != RELEASE_STATUS:
            failures.append("inventory status must be experimental_forensic_prototype")

    active_dir = root / "models_saved" / "active"
    if active_dir.exists() and any(active_dir.glob("*")):
        warnings.append("models_saved/active contains files (check no Phase 9B writes occurred)")

    for model_name, spec in EXPECTED_MODELS.items():
        art = models_root / spec["artifact"]
        meta = models_root / spec["metadata"]
        if not art.is_file():
            msg = f"missing artifact: {art.as_posix()}"
            if require_artifacts:
                failures.append(msg)
            else:
                warnings.append(msg)
            continue
        if not meta.is_file():
            msg = f"missing metadata: {meta.as_posix()}"
            if require_artifacts:
                failures.append(msg)
            else:
                warnings.append(msg)
            continue

        metadata = _read_json(meta)
        failures.extend(
            f"{model_name}: {issue}" for issue in validate_no_forbidden_fields_in_metadata(metadata)
        )
        if metadata.get("feature_set") != spec["feature_set"]:
            failures.append(
                f"{model_name}: expected feature_set={spec['feature_set']}, got {metadata.get('feature_set')}"
            )
        if "threshold_candidate" not in metadata:
            failures.append(f"{model_name}: threshold_candidate missing")
        if not metadata.get("feature_names"):
            failures.append(f"{model_name}: feature_names missing/empty")

        if model_name == "partial_fabrication_segment_model":
            for feat in metadata.get("feature_names", []):
                if is_forbidden_partial_feature(str(feat)):
                    failures.append(f"{model_name}: forbidden feature in metadata feature_names: {feat}")

        try:
            loaded = joblib.load(art)
            if not isinstance(loaded, Pipeline):
                failures.append(f"{model_name}: artifact is not sklearn Pipeline")
        except Exception as exc:
            failures.append(f"{model_name}: joblib load failed: {exc}")

    return len(failures) == 0, failures, warnings


def write_report(path: Path, ok: bool, failures: list[str], warnings: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    status = "PASS" if ok else "FAIL"
    lines = ["# Phase 9B Release Model Validation Report", "", f"- Status: {status}"]
    if ok:
        lines.append("- packaged artifacts and metadata validated")
    else:
        lines.append("- Failures:")
        for f in failures:
            lines.append(f"  - {f}")
    if warnings:
        lines.append("- Warnings:")
        for w in warnings:
            lines.append(f"  - {w}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    root = repo_root_from_here(Path(__file__))
    models_root = resolve_path(root, args.release_models_root)
    require = bool(args.require_artifacts)
    ok, failures, warnings = validate(root, models_root, require)
    write_report(resolve_path(root, args.output_report), ok, failures, warnings)
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
