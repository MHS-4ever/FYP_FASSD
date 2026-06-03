#!/usr/bin/env python3
"""Validate Phase 9G final release package and documentation."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SCRIPT_DIR = Path(__file__).resolve().parent


def _repo_root() -> Path:
    for base in (_SCRIPT_DIR, *_SCRIPT_DIR.parents):
        if (base / "release" / "app_gradio.py").is_file():
            return base
    return _SCRIPT_DIR.parents[3]


_REPO = _repo_root()
_RELEASE = _REPO / "release"
_ZIP = _REPO / "release_packages" / "phase9g_deepfake_audio_detector_demo_handoff.zip"
_FINAL = _REPO / "reports" / "phase9" / "final_release"
_P9F_VAL = _REPO / "reports" / "phase9" / "validation" / "phase9f_integration_docs_validation_report.md"
_P4B_VAL = _REPO / "reports" / "phase9" / "validation" / "phase9e_p4b_demo_freeze_validation_report.md"
_INV = _RELEASE / "models" / "model_inventory.json"
_INTEGRATION = _REPO / "reports" / "phase9" / "integration_docs"

FORBIDDEN = [
    "definitely fake",
    "definitely real",
    "final verdict",
    "final fake",
    "final real",
    "court proof",
    "court-ready",
    "court ready",
    "production-ready",
    "production ready",
]

FORBIDDEN_SECTION_MARKERS = [
    "forbidden wording",
    "never use",
    "must **not** appear",
]

REQUIRED_ZIP_PREFIXES = [
    "release/app_gradio.py",
    "release/app_fastapi.py",
    "release/run_gradio.bat",
    "release/run_fastapi.bat",
    "release/src/",
    "release/models/",
    "reports/phase9/integration_docs/",
    "reports/phase9/final_release/",
]

REQUIRED_INTEGRATION_DOCS = [
    "phase9f_teammate_handoff.md",
    "phase9f_api_contract.md",
    "phase9f_model_registry_guide.md",
]

FORBIDDEN_ZIP_FRAGMENTS = [
    "data/",
    "testing_audios/",
    "__pycache__/",
    ".git/",
    "models_saved/active/",
]


def _check(name: str, ok: bool, detail: str = "") -> dict[str, Any]:
    return {"check": name, "pass": ok, "detail": detail}


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _validation_pass(path: Path) -> bool:
    return path.is_file() and "**Overall:** PASS" in path.read_text(encoding="utf-8")


def _forbidden_hits(text: str) -> list[str]:
    hits: list[str] = []
    lower = text.lower()
    for phrase in FORBIDDEN:
        start = 0
        while True:
            idx = lower.find(phrase, start)
            if idx == -1:
                break
            window = lower[max(0, idx - 400) : idx + 200]
            if any(m in window for m in FORBIDDEN_SECTION_MARKERS):
                start = idx + len(phrase)
                continue
            hits.append(phrase)
            start = idx + len(phrase)
    return hits


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 9G final release.")
    parser.parse_args()

    report_out = _REPO / "reports" / "phase9" / "validation" / "phase9g_final_release_validation_report.md"
    report_out.parent.mkdir(parents=True, exist_ok=True)

    checks: list[dict[str, Any]] = []

    checks.append(_check("phase9f_validation_pass", _validation_pass(_P9F_VAL), str(_P9F_VAL)))
    checks.append(_check("phase9e_p4b_validation_pass", _validation_pass(_P4B_VAL), str(_P4B_VAL)))

    manifest_csv = _FINAL / "phase9g_final_release_manifest.csv"
    manifest_json = _FINAL / "phase9g_final_release_manifest.json"
    checksums = _FINAL / "phase9g_final_checksums_sha256.txt"
    final_report = _FINAL / "phase9g_final_release_report.md"

    checks.append(_check("final_package_zip_exists", _ZIP.is_file(), str(_ZIP)))
    checks.append(_check("manifest_csv_exists", manifest_csv.is_file(), str(manifest_csv)))
    checks.append(_check("manifest_json_exists", manifest_json.is_file(), str(manifest_json)))
    checks.append(_check("checksums_exist", checksums.is_file(), str(checksums)))
    checks.append(_check("final_release_report_exists", final_report.is_file(), str(final_report)))

    zip_names: list[str] = []
    if _ZIP.is_file():
        with zipfile.ZipFile(_ZIP, "r") as zf:
            zip_names = zf.namelist()

        for prefix in REQUIRED_ZIP_PREFIXES:
            found = any(n.replace("\\", "/").startswith(prefix) or n.replace("\\", "/") == prefix.rstrip("/") for n in zip_names)
            if prefix.endswith("/"):
                found = any(n.replace("\\", "/").startswith(prefix) for n in zip_names)
            checks.append(_check(f"zip_includes_{prefix.replace('/', '_')}", found, prefix))

        bad_entries = [
            n for n in zip_names for frag in FORBIDDEN_ZIP_FRAGMENTS if frag in n.replace("\\", "/").lower()
        ]
        checks.append(_check("no_dataset_testing_audios_in_zip", not bad_entries, "; ".join(bad_entries[:5])))

        for doc in REQUIRED_INTEGRATION_DOCS:
            arc = f"reports/phase9/integration_docs/{doc}"
            checks.append(_check(f"zip_doc_{doc}", arc in [x.replace("\\", "/") for x in zip_names], arc))

    # Checksum verification against manifest (stable package paths only)
    SKIP_CHECKSUM_PREFIXES = (
        "reports/phase9/final_release/",
        "reports/phase9/validation/phase9g_final_release_validation_report.md",
    )
    if manifest_csv.is_file():
        with manifest_csv.open(encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        mismatch: list[str] = []
        for row in rows:
            rel = row["relative_path"].replace("\\", "/")
            if any(rel.startswith(p) for p in SKIP_CHECKSUM_PREFIXES):
                continue
            expected = row["sha256"]
            src = _REPO / Path(rel)
            if not src.is_file():
                mismatch.append(f"missing:{rel}")
                continue
            if _sha256_file(src) != expected:
                mismatch.append(rel)
        checks.append(_check("checksum_verification_passes", not mismatch, "; ".join(mismatch[:5])))

    # Extract to temp and verify key files
    if _ZIP.is_file():
        with tempfile.TemporaryDirectory(prefix="phase9g_val_") as tmp:
            tmp_path = Path(tmp)
            with zipfile.ZipFile(_ZIP, "r") as zf:
                zf.extractall(tmp_path)
            extract_checks = [
                tmp_path / "release" / "app_fastapi.py",
                tmp_path / "release" / "app_gradio.py",
                tmp_path / "release" / "src" / "inference_pipeline.py",
                tmp_path / "release" / "models" / "model_inventory.json",
                tmp_path / "reports" / "phase9" / "integration_docs" / "phase9f_teammate_handoff.md",
            ]
            missing = [str(p.relative_to(tmp_path)) for p in extract_checks if not p.is_file()]
            checks.append(_check("extract_required_files_present", not missing, "; ".join(missing)))

    # Model inventory unchanged — no AASIST/ResNet
    if _INV.is_file():
        inv = json.loads(_INV.read_text(encoding="utf-8"))
        names = {str(m.get("model_name", "")).lower() for m in inv.get("models", [])}
        checks.append(
            _check(
                "model_inventory_active_unchanged",
                "origin_file_model" in names and "aasist" not in names and "hybrid_resnet" not in names,
                str(sorted(names)),
            )
        )

    # Final docs content checks
    if final_report.is_file():
        fr = final_report.read_text(encoding="utf-8")
        checks.append(_check("final_report_run_commands", "app_gradio.py" in fr and "run_fastapi" in fr, ""))
        checks.append(_check("final_report_known_limitations", "Known limitations" in fr or "limitations" in fr.lower(), ""))
        checks.append(_check("final_report_aasist_reject", "reject_for_now" in fr, ""))
        checks.append(_check("final_report_product_name", "Deepfake Audio Detector" in fr, ""))
        forb = _forbidden_hits(fr)
        checks.append(_check("final_report_forbidden_wording_absent", not forb, "; ".join(forb)))

    # Integration docs forbidden wording
    doc_hits: list[str] = []
    if _INTEGRATION.is_dir():
        for md in _INTEGRATION.glob("*.md"):
            for phrase in _forbidden_hits(md.read_text(encoding="utf-8")):
                doc_hits.append(f"{md.name}:{phrase}")
    checks.append(_check("integration_docs_forbidden_absent", not doc_hits, "; ".join(sorted(set(doc_hits))[:5])))

    # No models_saved/active writes in package script
    pkg_script = _SCRIPT_DIR / "package_phase9g_final_release.py"
    if pkg_script.is_file():
        ps = pkg_script.read_text(encoding="utf-8")
        checks.append(
            _check(
                "no_models_saved_active_writes_in_packager",
                "models_saved/active" not in ps or "write" not in ps.split("models_saved/active")[-1][:100],
                "",
            )
        )
        checks.append(
            _check(
                "packager_safety_no_aasist_activation",
                "did not retrain" in ps.lower() and "aasist/resnet" in ps.lower(),
                "",
            )
        )

    overall = all(c["pass"] for c in checks)

    # Update final report Phase 9G status if all pass
    if final_report.is_file() and overall:
        text = final_report.read_text(encoding="utf-8")
        text = re.sub(
            r"\*\*Phase 9G status:\*\*.*",
            "**Phase 9G status:** PASS",
            text,
            count=1,
        )
        if "**GO**" not in text:
            text = text.replace(
                "**NO-GO** — Resolve validation failures before handoff.",
                "**GO** — Release package is ready for demo/handoff.",
            )
        final_report.write_text(text, encoding="utf-8")

    lines = [
        "# Phase 9G Final Release Validation Report",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        f"**Overall:** {'PASS' if overall else 'FAIL'}",
        "",
        "## Checks",
        "",
    ]
    for c in checks:
        mark = "PASS" if c["pass"] else "FAIL"
        lines.append(f"- [{mark}] `{c['check']}` — {c.get('detail', '')}")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "Phase 9G validates the final demo/handoff zip and manifest checksums.",
            "No model retraining, threshold changes, or AASIST/ResNet activation.",
            "Package is for local demo/handoff only — not operational deployment.",
        ]
    )
    report_out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Phase 9G validation {'PASS' if overall else 'FAIL'}: {report_out}")
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
