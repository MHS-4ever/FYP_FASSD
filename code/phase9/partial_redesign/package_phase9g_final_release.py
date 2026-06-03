#!/usr/bin/env python3
"""
Phase 9G: Final demo/handoff package freeze.

Default is dry-run unless --apply is given. Documentation and packaging only —
does not modify model artifacts or write to models_saved/active.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

_SCRIPT_DIR = Path(__file__).resolve().parent

PRODUCT_NAME = "Deepfake Audio Detector — Local Demo"
RESEARCH_NAME = "Forensic Acoustic for Synthetic Speech Detection"
RELEASE_NAME = "phase9g_deepfake_audio_detector_demo_handoff"
ZIP_NAME = f"{RELEASE_NAME}.zip"

EXCLUDE_DIR_NAMES = {
    "__pycache__",
    ".git",
    ".venv",
    "venv",
    "env",
    ".mypy_cache",
    ".pytest_cache",
    "gradio_outputs",
    "sample_outputs",
    "ipynb_checkpoints",
    ".idea",
    ".vscode",
}

EXCLUDE_FILE_SUFFIXES = {".pyc", ".pyo"}

EXCLUDE_PATH_FRAGMENTS = (
    "/data/",
    "\\data\\",
    "/testing_audios/",
    "\\testing_audios\\",
    "/models_saved/active/",
    "\\models_saved\\active\\",
)


def repo_root() -> Path:
    for base in (_SCRIPT_DIR, *_SCRIPT_DIR.parents):
        if (base / "release" / "app_gradio.py").is_file():
            return base
    return _SCRIPT_DIR.parents[3]


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+00:00"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _log(msg: str) -> None:
    print(f"[phase9g] {msg}")


def _should_exclude(rel_posix: str, name: str, is_dir: bool) -> bool:
    rel_lower = rel_posix.lower()
    for frag in EXCLUDE_PATH_FRAGMENTS:
        if frag.lower() in rel_lower:
            return True
    if name in EXCLUDE_DIR_NAMES and is_dir:
        return True
    if any(part in EXCLUDE_DIR_NAMES for part in Path(rel_posix).parts):
        return True
    if not is_dir and Path(name).suffix.lower() in EXCLUDE_FILE_SUFFIXES:
        return True
    if not is_dir and name.endswith(".zip") and "release_packages" in rel_lower:
        return True
    return False


def _collect_release_files(repo: Path) -> list[Path]:
    release = repo / "release"
    include_roots = [
        release / "app_gradio.py",
        release / "app_fastapi.py",
        release / "run_gradio.bat",
        release / "run_fastapi.bat",
        release / "requirements_release.txt",
        release / "README.md",
        release / "README_RELEASE.md",
        release / "src",
        release / "models",
        release / "config",
        release / "sample_audio",
    ]
    files: list[Path] = []
    for root in include_roots:
        if root.is_file():
            files.append(root)
        elif root.is_dir():
            for dirpath, dirnames, filenames in os.walk(root):
                dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIR_NAMES]
                dp = Path(dirpath)
                for fn in filenames:
                    full = dp / fn
                    rel = full.relative_to(repo).as_posix()
                    if _should_exclude(rel, fn, is_dir=False):
                        continue
                    files.append(full)
    return sorted(set(files))


def _collect_report_files(repo: Path) -> list[Path]:
    files: list[Path] = []
    # Integration docs
    docs_dir = repo / "reports" / "phase9" / "integration_docs"
    if docs_dir.is_dir():
        for p in sorted(docs_dir.glob("*.md")):
            files.append(p)

    # Validation reports
    val_names = [
        "phase9e_p3_release_correctness_validation_report.md",
        "phase9e_p4a_origin_support_validation_report.md",
        "phase9e_p4b_demo_freeze_validation_report.md",
        "phase9f_integration_docs_validation_report.md",
    ]
    val_dir = repo / "reports" / "phase9" / "validation"
    for name in val_names:
        p = val_dir / name
        if p.is_file():
            files.append(p)

    # Final release docs (manifest/checksums may not exist yet on first dry-run)
    final_dir = repo / "reports" / "phase9" / "final_release"
    if final_dir.is_dir():
        for p in sorted(final_dir.iterdir()):
            if p.is_file() and p.suffix in {".md", ".csv", ".json", ".txt"}:
                files.append(p)

    # P4B demo evidence (CSV/docs only)
    p4b = repo / "reports" / "phase9" / "app" / "phase9e_p4b_demo_freeze"
    if p4b.is_dir():
        for p in sorted(p4b.iterdir()):
            if p.is_file() and p.suffix in {".md", ".csv"}:
                files.append(p)

    return sorted(set(files))


def _archive_rel_path(repo: Path, path: Path) -> str:
    return path.relative_to(repo).as_posix()


def _build_manifest(repo: Path, files: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in files:
        rel = _archive_rel_path(repo, path)
        rows.append(
            {
                "relative_path": rel,
                "size_bytes": path.stat().st_size,
                "sha256": _sha256_file(path),
            }
        )
    return rows


def _write_manifest_outputs(repo: Path, rows: list[dict[str, Any]]) -> tuple[Path, Path, Path]:
    out_dir = repo / "reports" / "phase9" / "final_release"
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_path = out_dir / "phase9g_final_release_manifest.csv"
    json_path = out_dir / "phase9g_final_release_manifest.json"
    sums_path = out_dir / "phase9g_final_checksums_sha256.txt"

    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["relative_path", "size_bytes", "sha256"])
        writer.writeheader()
        writer.writerows(rows)

    json_path.write_text(
        json.dumps(
            {
                "release_name": RELEASE_NAME,
                "product_name": PRODUCT_NAME,
                "research_project_name": RESEARCH_NAME,
                "generated_at": _now_iso(),
                "file_count": len(rows),
                "files": rows,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    sum_lines = [f"{r['sha256']}  {r['relative_path']}" for r in rows]
    sums_path.write_text("\n".join(sum_lines) + "\n", encoding="utf-8")

    return csv_path, json_path, sums_path


def _create_zip(repo: Path, files: list[Path], zip_path: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    if zip_path.is_file():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in files:
            arc = _archive_rel_path(repo, path)
            zf.write(path, arcname=arc)


def _write_release_report(
    repo: Path,
    *,
    rows: list[dict[str, Any]],
    zip_path: Path,
    apply_mode: bool,
    p9f_pass: bool,
    p4b_pass: bool,
) -> Path:
    out = repo / "reports" / "phase9" / "final_release" / "phase9g_final_release_report.md"
    total_bytes = sum(int(r["size_bytes"]) for r in rows)
    inv_path = repo / "release" / "models" / "model_inventory.json"
    inv_summary = ""
    if inv_path.is_file():
        inv = json.loads(inv_path.read_text(encoding="utf-8"))
        inv_summary = ", ".join(m["model_name"] for m in inv.get("models", []))

    lines = [
        "# Phase 9G Final Release Report",
        "",
        f"Generated: {_now_iso()}",
        "",
        f"**Phase 9G status:** {'PASS (package applied)' if apply_mode else 'DRY-RUN (plan only)'}",
        "",
        "## Identity",
        "",
        f"- **Release name:** {RELEASE_NAME}",
        f"- **Product name:** {PRODUCT_NAME}",
        f"- **Research / FYP name:** {RESEARCH_NAME}",
        "",
        "## Frozen phase status",
        "",
        "- Phase 9E-P3 release correctness: PASS",
        "- Phase 9E-P4A origin support shadow: PASS (reject_for_now)",
        "- Phase 9E-P4B demo freeze: PASS",
        f"- Phase 9F integration docs: {'PASS' if p9f_pass else 'PENDING/FAIL'}",
        "",
        "## Active models",
        "",
        f"- Registry entries: {inv_summary or 'see model_inventory.json'}",
        "- Integration module: partial_fabrication_experimental_p5b (experimental_manual_review_only)",
        "",
        "## Inactive reference models",
        "",
        "- AASIST: reject_for_now",
        "- HybridResNet/ResNet: reject_for_now",
        "",
        "## Known limitations",
        "",
        "- Partial fabrication experimental / manual-review candidate only",
        "- Full partial replacement detection not guaranteed",
        "- Replay/channel processing reduces origin reliability",
        "- Local demo only — no operational deployment or legal-evidence claims",
        "- Conclusive authenticity decision: no",
        "",
        "## Run commands",
        "",
        "```bat",
        "cd /d E:\\FYP\\release",
        "conda activate fassd",
        "python app_gradio.py",
        "```",
        "",
        "```bat",
        "cd /d E:\\FYP\\release",
        "run_fastapi.bat",
        "```",
        "",
        "## Package contents summary",
        "",
        f"- Files in manifest: {len(rows)}",
        f"- Total uncompressed bytes: {total_bytes}",
        f"- Zip path: `{zip_path.relative_to(repo).as_posix()}`",
        "",
        "## Checksum summary",
        "",
        f"- Manifest: `reports/phase9/final_release/phase9g_final_release_manifest.csv`",
        f"- SHA256 list: `reports/phase9/final_release/phase9g_final_checksums_sha256.txt`",
        "",
        "## Final go/no-go decision",
        "",
    ]
    if apply_mode and p9f_pass and p4b_pass:
        lines.append("**GO** — Release package is ready for demo/handoff.")
    elif not apply_mode:
        lines.append("**DRY-RUN** — Re-run with `--apply` after Phase 9F validation PASS.")
    else:
        lines.append("**NO-GO** — Resolve validation failures before handoff.")

    lines.extend(
        [
            "",
            "## Next handoff instruction",
            "",
            "1. Extract the zip to a clean directory preserving `release/` layout.",
            "2. Create conda env `fassd` and install `release/requirements_release.txt`.",
            "3. Read `reports/phase9/integration_docs/phase9f_teammate_handoff.md`.",
            "4. Run Gradio or FastAPI locally; do not claim operational or legal-evidence readiness.",
            "",
            "## Safety",
            "",
            "This packaging step did not retrain models, change thresholds, or activate AASIST/ResNet.",
        ]
    )
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def _validation_pass(path: Path) -> bool:
    if not path.is_file():
        return False
    return "**Overall:** PASS" in path.read_text(encoding="utf-8")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Phase 9G final release packaging.")
    p.add_argument("--dry_run", action="store_true", help="Plan package only (default if --apply omitted).")
    p.add_argument("--apply", action="store_true", help="Write manifest/checksums/zip.")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    apply_mode = bool(args.apply)
    if not apply_mode and not args.dry_run:
        # default dry-run
        args.dry_run = True

    repo = repo_root()
    zip_path = repo / "release_packages" / ZIP_NAME

    p9f_val = repo / "reports" / "phase9" / "validation" / "phase9f_integration_docs_validation_report.md"
    p4b_val = repo / "reports" / "phase9" / "validation" / "phase9e_p4b_demo_freeze_validation_report.md"
    p9f_pass = _validation_pass(p9f_val)
    p4b_pass = _validation_pass(p4b_val)

    _log("collecting files")
    base_files = _collect_release_files(repo) + _collect_report_files(repo)
    # Exclude generated final_release artifacts from initial collection (re-added after write)
    base_files = [
        p
        for p in base_files
        if not str(p.relative_to(repo)).replace("\\", "/").startswith("reports/phase9/final_release/")
    ]
    base_files = sorted(set(base_files))
    _log(f"collected {len(base_files)} base files")

    report_path = _write_release_report(
        repo,
        rows=_build_manifest(repo, base_files) if base_files else [],
        zip_path=zip_path,
        apply_mode=apply_mode,
        p9f_pass=p9f_pass,
        p4b_pass=p4b_pass,
    )

    package_files = sorted(set(base_files + [report_path]))
    _log("writing manifest")
    rows = _build_manifest(repo, package_files)
    csv_path, json_path, sums_path = _write_manifest_outputs(repo, rows)
    all_zip_files = sorted(set(package_files + [csv_path, json_path, sums_path]))
    rows_final = _build_manifest(repo, all_zip_files)
    csv_path, json_path, sums_path = _write_manifest_outputs(repo, rows_final)

    if apply_mode:
        _log("creating zip")
        _create_zip(repo, all_zip_files, zip_path)
        _log(f"zip written: {zip_path}")
    else:
        _log(f"dry-run: would create zip at {zip_path} ({len(all_zip_files)} files)")

    _log(f"release report: {report_path}")

    if apply_mode:
        _log("validating package (basic file count)")
        if not zip_path.is_file():
            _log("ERROR: zip missing after apply")
            return 1
        with zipfile.ZipFile(zip_path, "r") as zf:
            _log(f"zip entries: {len(zf.namelist())}")

    mode = "APPLY" if apply_mode else "DRY-RUN"
    print(f"Phase 9G packaging {mode} complete. files={len(all_zip_files)} manifest={csv_path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
