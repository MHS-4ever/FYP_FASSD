"""Validate Phase 9A release skeleton structure without running inference."""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
RELEASE_ROOT = REPO_ROOT / "release"
REPORT_PATH = (
    REPO_ROOT
    / "reports"
    / "phase9"
    / "validation"
    / "phase9a_release_structure_validation_report.md"
)


REQUIRED_DIRS = [
    "release/config",
    "release/models/origin",
    "release/models/replay",
    "release/models/mixer",
    "release/models/partial_segment",
    "release/src",
    "release/docs",
    "release/sample_audio",
    "release/sample_outputs",
]

REQUIRED_FILES = [
    "release/app_fastapi.py",
    "release/app_gradio.py",
    "release/run_fastapi.bat",
    "release/run_gradio.bat",
    "release/requirements_release.txt",
    "release/README_RELEASE.md",
    "release/INTEGRATION_GUIDE.md",
    "release/MODEL_REGISTRY.md",
    "release/config/fusion_thresholds.yaml",
    "release/config/model_paths.yaml",
    "release/config/label_schema.yaml",
    "release/config/runtime_config.yaml",
    "release/src/schemas.py",
    "release/src/audio_io.py",
    "release/src/segmentation.py",
    "release/src/feature_extraction.py",
    "release/src/ssl_embeddings.py",
    "release/src/model_loader.py",
    "release/src/inference_pipeline.py",
    "release/src/fusion_rules.py",
    "release/src/report_generator.py",
    "release/src/utils.py",
    "release/docs/API_CONTRACT.md",
    "release/docs/MODEL_DETAILS.md",
    "release/docs/FORENSIC_REPORT_WORDING.md",
    "release/docs/TROUBLESHOOTING.md",
    "release/docs/PHASE9_RELEASE_PLAN.md",
    "reports/phase9/roadmap/phase9a_status.md",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def validate() -> tuple[bool, list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []

    if not RELEASE_ROOT.exists():
        failures.append("release folder does not exist")

    for rel in REQUIRED_DIRS:
        if not (REPO_ROOT / rel).exists():
            failures.append(f"missing required folder: {rel}")

    for rel in REQUIRED_FILES:
        if not (REPO_ROOT / rel).exists():
            failures.append(f"missing required file: {rel}")

    if any((REPO_ROOT / "models_saved" / "active").glob("*")) if (REPO_ROOT / "models_saved" / "active").exists() else False:
        warnings.append(
            "models_saved/active contains files (pre-existing or external); "
            "validator cannot prove they were created by Phase 9A."
        )

    # Metadata constraints.
    runtime_cfg = _read(REPO_ROOT / "release/config/runtime_config.yaml")
    readme = _read(REPO_ROOT / "release/README_RELEASE.md")
    roadmap = _read(REPO_ROOT / "reports/phase9/roadmap/phase9a_status.md")
    if "experimental_forensic_prototype" not in (runtime_cfg + "\n" + readme):
        failures.append("experimental_forensic_prototype marker missing from runtime/readme docs")

    forbidden_claim_tokens = ["production-ready", "court-ready", "production readiness"]
    safety_context_tokens = ["forbidden wording", "forbidden fields", "avoid", "do not", "not "]
    for doc in (REPO_ROOT / "release").rglob("*.md"):
        text = _read(doc).lower()
        if "forbidden wording" in text:
            # This document is expected to list forbidden examples explicitly.
            continue
        for token in forbidden_claim_tokens:
            if token not in text:
                continue
            # Only fail on claim-like usage, not on warning/guidance usage.
            for line in text.splitlines():
                if token in line and not any(ctx in line for ctx in safety_context_tokens):
                    failures.append(
                        "forbidden production claim found outside warning context: "
                        f"{doc.as_posix()} ({token})"
                    )

    # fake_score / real_score rule:
    source_and_config_paths = list((REPO_ROOT / "release/src").glob("*.py")) + list(
        (REPO_ROOT / "release/config").glob("*.yaml")
    )
    for path in source_and_config_paths:
        text = _read(path).lower()
        if "fake_score" in text or "real_score" in text:
            failures.append(f"forbidden field found in source/config: {path.as_posix()}")

    # Docs may mention forbidden fields only under forbidden sections.
    for doc in (REPO_ROOT / "release/docs").glob("*.md"):
        text = _read(doc)
        lowered = text.lower()
        if "fake_score" in lowered or "real_score" in lowered:
            if "forbidden wording" not in lowered and "forbidden fields" not in lowered:
                failures.append(
                    f"fake_score/real_score in docs without Forbidden section: {doc.as_posix()}"
                )

    if "Phase 9B status: NOT STARTED" not in roadmap:
        failures.append("Phase 9B status marker missing or changed")
    if "Phase 9C status: NOT STARTED" not in roadmap:
        failures.append("Phase 9C status marker missing or changed")

    return (len(failures) == 0, failures, warnings)


def write_report(ok: bool, failures: list[str], warnings: list[str]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    status = "PASS" if ok else "FAIL"
    lines = [
        "# Phase 9A Release Structure Validation Report",
        "",
        f"- Status: {status}",
    ]
    if ok:
        lines += [
            "- release skeleton structure found",
            "- experimental_forensic_prototype markers found",
            "- no forbidden source/config fields found",
            "- Phase 9B/9C remain NOT STARTED",
        ]
    else:
        lines.append("- Failures:")
        for issue in failures:
            lines.append(f"  - {issue}")
    if warnings:
        lines.append("- Warnings:")
        for issue in warnings:
            lines.append(f"  - {issue}")
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    ok_result, failure_list, warning_list = validate()
    write_report(ok_result, failure_list, warning_list)
    print("PASS" if ok_result else "FAIL")
