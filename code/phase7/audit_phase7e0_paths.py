"""
Phase 7E0.5: Path, artifact, and environment audit for AASIST preparation.

Checks canonical (reports/phase7/...) and legacy (reports/phase7c1_.../) paths.
Does not train, download models, move files, or create code/phase7/aasist/.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------------------
# Artifact registry
# ---------------------------------------------------------------------------

@dataclass
class ArtifactSpec:
    artifact_id: str
    category: str
    canonical_path: str
    legacy_path: str
    critical: bool = True
    is_directory: bool = False
    create_if_missing: bool = False  # only output audit dir uses this via CLI
    expected_columns: list[str] = field(default_factory=list)
    column_profile: str = ""  # training_manifest | baseline_results | candidate_decisions


def _artifacts() -> list[ArtifactSpec]:
    return [
        # A) 7C2 training manifests
        ArtifactSpec(
            "phase7c2_train_manifest",
            "phase7c2_training",
            "reports/phase7/phase7c2_training_prep/phase7c2_train_manifest.csv",
            "reports/phase7c2_training_prep/phase7c2_train_manifest.csv",
            expected_columns=[
                "audio_path",
                "sample_id",
                "split",
                "data_source",
                "source_origin",
                "manipulation_type",
                "risk_level",
                "sample_weight",
            ],
            column_profile="training_manifest",
        ),
        ArtifactSpec(
            "phase7c2_val_manifest",
            "phase7c2_training",
            "reports/phase7/phase7c2_training_prep/phase7c2_val_manifest.csv",
            "reports/phase7c2_training_prep/phase7c2_val_manifest.csv",
            expected_columns=[
                "audio_path",
                "sample_id",
                "split",
                "data_source",
                "source_origin",
                "manipulation_type",
                "risk_level",
                "sample_weight",
            ],
            column_profile="training_manifest",
        ),
        ArtifactSpec(
            "phase7c2_test_manifest",
            "phase7c2_training",
            "reports/phase7/phase7c2_training_prep/phase7c2_test_manifest.csv",
            "reports/phase7c2_training_prep/phase7c2_test_manifest.csv",
            expected_columns=[
                "audio_path",
                "sample_id",
                "split",
                "data_source",
                "source_origin",
                "manipulation_type",
                "risk_level",
                "sample_weight",
            ],
            column_profile="training_manifest",
        ),
        # B) 7C1 collection
        ArtifactSpec(
            "phase7c1_collection_manifest",
            "phase7c1_collection",
            "reports/phase7/phase7c1_collection/phase7c1_collection_manifest.csv",
            "reports/phase7c1_collection/phase7c1_collection_manifest.csv",
            critical=True,
            expected_columns=["audio_path", "sample_id", "split", "source_origin", "manipulation_type"],
            column_profile="training_manifest",
        ),
        # C) 7C1 baseline
        ArtifactSpec(
            "phase7c1_baseline_results",
            "phase7c1_baseline",
            "reports/phase7/phase7c1_baseline/results/phase7c1_baseline_results.csv",
            "reports/phase7c1_baseline/results/phase7c1_baseline_results.csv",
            expected_columns=[
                "sample_id",
                "prediction",
                "decision_score",
                "max_chunk_spoof",
                "suspicious_chunk_ratio",
                "baseline_status",
            ],
            column_profile="baseline_results",
        ),
        ArtifactSpec(
            "phase7c1_partial_fabrication_analysis",
            "phase7c1_baseline",
            "reports/phase7/phase7c1_baseline/results/phase7c1_partial_fabrication_analysis.csv",
            "reports/phase7c1_baseline/results/phase7c1_partial_fabrication_analysis.csv",
            critical=False,
            expected_columns=["sample_id"],
            column_profile="baseline_results",
        ),
        # D) 7A holdout
        ArtifactSpec(
            "phase7a_forensic_test_manifest",
            "phase7a_holdout",
            "reports/phase7/phase7_forensic_tests/forensic_test_manifest.csv",
            "reports/phase7_forensic_tests/forensic_test_manifest.csv",
            expected_columns=["audio_path", "test_id"],
            column_profile="training_manifest",
        ),
        ArtifactSpec(
            "phase7a_forensic_test_results_product",
            "phase7a_holdout",
            "reports/phase7/phase7_forensic_tests/results/forensic_test_results_product.csv",
            "reports/phase7_forensic_tests/results/forensic_test_results_product.csv",
            expected_columns=["test_id", "prediction", "decision_score"],
            column_profile="baseline_results",
        ),
        # E) 7C4-v2
        ArtifactSpec(
            "phase7c4_v2_candidate_decisions",
            "phase7c4_v2",
            "reports/phase7/phase7c4_calibration_v2/calibration_outputs/phase7c4_v2_candidate_decisions.csv",
            "reports/phase7c4_calibration_v2/calibration_outputs/phase7c4_v2_candidate_decisions.csv",
            expected_columns=[
                "sample_id",
                "calibrated_status",
                "calibrated_risk_level",
                "manual_review_required",
            ],
            column_profile="candidate_decisions",
        ),
        ArtifactSpec(
            "phase7c4_v2_error_cases",
            "phase7c4_v2",
            "reports/phase7/phase7c4_calibration_v2/calibration_outputs/phase7c4_v2_error_cases.csv",
            "reports/phase7c4_calibration_v2/calibration_outputs/phase7c4_v2_error_cases.csv",
            critical=False,
            expected_columns=["sample_id"],
            column_profile="candidate_decisions",
        ),
        ArtifactSpec(
            "phase7c4_v2_final_recommendation",
            "phase7c4_v2",
            "reports/phase7/phase7c4_calibration_v2/phase7c4_v2_final_recommendation.md",
            "reports/phase7c4_calibration_v2/phase7c4_v2_final_recommendation.md",
            critical=False,
            is_directory=False,
        ),
        # F) 7C3-R2 checkpoints
        ArtifactSpec(
            "phase7c3_r2_best_product_ckpt",
            "phase7c3_r2_checkpoints",
            "reports/phase7/phase7c3_finetune_r2/training/checkpoints/hybrid_resnet_environmental_phase7c3_r2_best_product.pth",
            "reports/phase7c3_finetune_r2/training/checkpoints/hybrid_resnet_environmental_phase7c3_r2_best_product.pth",
            critical=False,
        ),
        ArtifactSpec(
            "phase7c3_r2_best_loss_ckpt",
            "phase7c3_r2_checkpoints",
            "reports/phase7/phase7c3_finetune_r2/training/checkpoints/hybrid_resnet_environmental_phase7c3_r2_best_loss.pth",
            "reports/phase7c3_finetune_r2/training/checkpoints/hybrid_resnet_environmental_phase7c3_r2_best_loss.pth",
            critical=False,
        ),
        # G) Base checkpoint
        ArtifactSpec(
            "hybrid_resnet_environmental_best",
            "base_checkpoint",
            "models_saved/hybrid_resnet_environmental_best.pth",
            "models_saved/hybrid_resnet_environmental_best.pth",
        ),
        # H) Future workspace (directories)
        ArtifactSpec(
            "aasist_code_workspace",
            "aasist_workspace",
            "code/phase7/aasist",
            "code/phase7/aasist",
            critical=False,
            is_directory=True,
        ),
        ArtifactSpec(
            "phase7e_experiment_root",
            "aasist_workspace",
            "reports/phase7/phase7e_aasist_experiment",
            "reports/phase7/phase7e_aasist_experiment",
            critical=False,
            is_directory=True,
        ),
        ArtifactSpec(
            "phase7e_audit_dir",
            "aasist_workspace",
            "reports/phase7/phase7e_aasist_experiment/audit",
            "reports/phase7/phase7e_aasist_experiment/audit",
            critical=False,
            is_directory=True,
            create_if_missing=True,
        ),
        ArtifactSpec(
            "phase7e_outputs_dir",
            "aasist_workspace",
            "reports/phase7/phase7e_aasist_experiment/outputs",
            "reports/phase7/phase7e_aasist_experiment/outputs",
            critical=False,
            is_directory=True,
        ),
    ]


# Extra columns accepted as aliases for candidate decisions profile
_CANDIDATE_DECISION_ALIASES = {
    "manual_review_required": ["needs_manual_review", "manual_review_required"],
}


def _resolve_repo_path(rel: str) -> Path:
    return (_REPO_ROOT / rel).resolve()


def _path_exists(p: Path, *, is_directory: bool) -> bool:
    if is_directory:
        return p.is_dir()
    return p.is_file()


def _file_size_mb(p: Path) -> float | None:
    try:
        return round(p.stat().st_size / (1024 * 1024), 4)
    except OSError:
        return None


def _inspect_csv(path: Path, expected_columns: list[str], column_profile: str) -> dict[str, Any]:
    out: dict[str, Any] = {
        "csv_inspected": True,
        "row_count": None,
        "column_count": None,
        "columns_first_5": [],
        "all_columns": [],
        "file_size_mb": _file_size_mb(path),
        "missing_expected_columns": [],
        "column_warnings": [],
    }
    try:
        with path.open("r", encoding="utf-8", errors="replace", newline="") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if header is None:
                out["column_warnings"].append("empty_csv")
                return out
            out["all_columns"] = [c.strip() for c in header]
            out["columns_first_5"] = out["all_columns"][:5]
            out["column_count"] = len(out["all_columns"])
            row_count = 0
            for _ in reader:
                row_count += 1
            out["row_count"] = row_count
    except OSError as e:
        out["csv_inspected"] = False
        out["column_warnings"].append(f"read_error:{e}")
        return out

    cols_set = set(out["all_columns"])
    missing = [c for c in expected_columns if c not in cols_set]
    if column_profile == "candidate_decisions":
        for canonical, aliases in _CANDIDATE_DECISION_ALIASES.items():
            if canonical in expected_columns and canonical in missing:
                if any(a in cols_set for a in aliases):
                    missing = [m for m in missing if m != canonical]
                    out["column_warnings"].append(f"used_alias_for_{canonical}")
    out["missing_expected_columns"] = missing
    if missing:
        out["column_warnings"].append("missing_expected_columns")
    return out


def _audit_artifact(spec: ArtifactSpec) -> dict[str, Any]:
    canonical = _resolve_repo_path(spec.canonical_path)
    legacy = _resolve_repo_path(spec.legacy_path)
    exists_canonical = _path_exists(canonical, is_directory=spec.is_directory)
    exists_legacy = _path_exists(legacy, is_directory=spec.is_directory)

    notes: list[str] = []
    if spec.canonical_path == spec.legacy_path:
        exists_legacy = exists_canonical  # same path (checkpoints, workspace)

    if exists_canonical and exists_legacy and canonical != legacy:
        notes.append("both_canonical_and_legacy_exist")
        try:
            if not spec.is_directory and canonical.stat().st_size != legacy.stat().st_size:
                notes.append("canonical_legacy_size_mismatch")
        except OSError:
            pass

    if exists_canonical:
        selected = canonical
        status = "found_canonical"
        selected_rel = spec.canonical_path
    elif exists_legacy:
        selected = legacy
        status = "found_legacy"
        selected_rel = spec.legacy_path
        notes.append("using_legacy_path")
    else:
        selected = None
        status = "missing"
        selected_rel = ""

    if spec.artifact_id == "aasist_code_workspace" and status == "missing":
        notes.append("expected_missing_before_7e1")
    elif spec.is_directory and status != "missing":
        notes.append("directory_exists")

    row: dict[str, Any] = {
        "artifact_id": spec.artifact_id,
        "category": spec.category,
        "critical": spec.critical,
        "is_directory": spec.is_directory,
        "canonical_path": spec.canonical_path,
        "legacy_path": spec.legacy_path,
        "exists_canonical": exists_canonical,
        "exists_legacy": exists_legacy,
        "selected_path": selected_rel,
        "selected_path_absolute": str(selected) if selected else "",
        "status": status,
        "notes": "; ".join(notes) if notes else "",
    }

    if selected and not spec.is_directory and str(selected).lower().endswith(".csv"):
        insp = _inspect_csv(selected, spec.expected_columns, spec.column_profile)
        row.update(insp)
    elif selected and not spec.is_directory:
        row["file_size_mb"] = _file_size_mb(selected)
    elif selected and spec.is_directory:
        row["file_size_mb"] = None

    return row


def _package_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _collect_environment() -> dict[str, Any]:
    env: dict[str, Any] = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "sys_executable": sys.executable,
        "python_version": sys.version,
        "cwd": os.getcwd(),
        "repo_root": str(_REPO_ROOT),
        "conda_env": os.environ.get("CONDA_DEFAULT_ENV"),
        "packages": {},
        "torch": {},
    }

    for pkg in ("pandas", "numpy", "librosa", "soundfile", "h5py", "torch"):
        env["packages"][pkg] = {
            "installed": _package_available(pkg),
        }
        if pkg == "torch" and _package_available("torch"):
            import torch

            env["torch"] = {
                "version": torch.__version__,
                "cuda_available": bool(torch.cuda.is_available()),
                "cuda_version": getattr(torch.version, "cuda", None),
                "device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
            }
            if torch.cuda.is_available():
                try:
                    env["torch"]["gpu_name"] = torch.cuda.get_device_name(0)
                    props = torch.cuda.get_device_properties(0)
                    env["torch"]["gpu_total_memory_gb"] = round(
                        props.total_memory / (1024**3), 3
                    )
                    free, total = torch.cuda.mem_get_info(0)
                    env["torch"]["gpu_free_memory_gb"] = round(free / (1024**3), 3)
                    env["torch"]["gpu_total_memory_reported_gb"] = round(
                        total / (1024**3), 3
                    )
                except Exception as e:  # noqa: BLE001
                    env["torch"]["gpu_info_error"] = str(e)
        elif pkg != "torch" and _package_available(pkg):
            mod = importlib.import_module(pkg)
            env["packages"][pkg]["version"] = getattr(mod, "__version__", "unknown")

    return env


def _compute_verdict(
    rows: list[dict[str, Any]],
    env: dict[str, Any],
) -> tuple[str, list[str]]:
    reasons: list[str] = []
    warnings: list[str] = []

    critical_missing = [
        r["artifact_id"]
        for r in rows
        if r["critical"] and r["status"] == "missing"
    ]
    if critical_missing:
        reasons.append(f"critical_artifacts_missing:{','.join(critical_missing)}")

    optional_missing = [
        r["artifact_id"]
        for r in rows
        if not r["critical"] and r["status"] == "missing"
    ]
    if optional_missing:
        warnings.append(f"optional_artifacts_missing:{','.join(optional_missing)}")

    legacy_used = [r["artifact_id"] for r in rows if "using_legacy_path" in r.get("notes", "")]
    if legacy_used:
        warnings.append(f"legacy_paths_selected:{','.join(legacy_used)}")

    both_exist = [r["artifact_id"] for r in rows if "both_canonical_and_legacy_exist" in r.get("notes", "")]
    if both_exist:
        warnings.append(f"canonical_and_legacy_both_present:{','.join(both_exist)}")

    for r in rows:
        if r.get("missing_expected_columns"):
            warnings.append(
                f"{r['artifact_id']}:missing_columns:{','.join(r['missing_expected_columns'])}"
            )

    torch_info = env.get("torch", {})
    if not env["packages"].get("torch", {}).get("installed"):
        reasons.append("pytorch_not_installed")
    elif not torch_info.get("cuda_available"):
        reasons.append("cuda_not_available")

    if reasons:
        return "FAIL", reasons + warnings

    if warnings:
        return "PASS_WITH_WARNINGS", warnings

    return "PASS", []


def _write_markdown(
    path: Path,
    verdict: str,
    reasons: list[str],
    rows: list[dict[str, Any]],
    env: dict[str, Any],
    output_dir: Path,
) -> None:
    lines = [
        "# Phase 7E0.5 — Path, Artifact, and Environment Audit",
        "",
        f"**Generated:** {env['timestamp_utc']}  ",
        f"**Verdict:** `{verdict}`  ",
        f"**Output directory:** `{output_dir.relative_to(_REPO_ROOT).as_posix()}`  ",
        "",
        "## Summary",
        "",
    ]
    if reasons:
        lines.append("### Notes")
        for r in reasons:
            lines.append(f"- {r}")
        lines.append("")

    lines.extend(
        [
            "## Environment",
            "",
            f"| Item | Value |",
            f"|------|-------|",
            f"| Python | `{env['python_version'].split()[0]}` |",
            f"| Executable | `{env['sys_executable']}` |",
            f"| CWD | `{env['cwd']}` |",
            f"| Repo root | `{env['repo_root']}` |",
            f"| Conda env | `{env.get('conda_env') or '(not set)'}` |",
            f"| PyTorch | `{env.get('torch', {}).get('version', 'N/A')}` |",
            f"| CUDA available | `{env.get('torch', {}).get('cuda_available', False)}` |",
            f"| GPU | `{env.get('torch', {}).get('gpu_name', 'N/A')}` |",
            "",
            "## Artifact audit",
            "",
            "| artifact_id | status | selected_path | critical | notes |",
            "|-------------|--------|---------------|----------|-------|",
        ]
    )
    for r in rows:
        lines.append(
            f"| {r['artifact_id']} | {r['status']} | `{r['selected_path'] or '-'}` | "
            f"{r['critical']} | {r.get('notes', '')} |"
        )

    lines.extend(
        [
            "",
            "## CSV inspection (selected files)",
            "",
        ]
    )
    for r in rows:
        if not r.get("csv_inspected"):
            continue
        lines.append(f"### {r['artifact_id']}")
        lines.append("")
        lines.append(f"- Rows: {r.get('row_count')}")
        lines.append(f"- Columns: {r.get('column_count')}")
        lines.append(f"- Size (MB): {r.get('file_size_mb')}")
        lines.append(f"- First 5 columns: `{', '.join(r.get('columns_first_5', []))}`")
        if r.get("missing_expected_columns"):
            lines.append(f"- **Missing expected:** `{', '.join(r['missing_expected_columns'])}`")
        lines.append("")

    lines.extend(
        [
            "## Outputs",
            "",
            "- `phase7e0_path_artifact_audit.csv`",
            "- `phase7e0_selected_paths.json`",
            "- `phase7e0_environment_report.json`",
            "- `phase7e0_missing_or_warning_items.csv`",
            "",
            "## Next step",
            "",
            "If verdict is `PASS` or `PASS_WITH_WARNINGS`, review `phase7e0_selected_paths.json` before Phase **7E1**.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run_audit(output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    specs = _artifacts()
    rows = [_audit_artifact(s) for s in specs]

    env = _collect_environment()
    verdict, verdict_notes = _compute_verdict(rows, env)

    selected_paths = {
        r["artifact_id"]: {
            "selected_path": r["selected_path"],
            "selected_path_absolute": r["selected_path_absolute"],
            "status": r["status"],
            "category": r["category"],
        }
        for r in rows
        if r["selected_path"]
    }

    # Warnings / missing CSV
    warn_rows: list[dict[str, Any]] = []
    for r in rows:
        if r["status"] == "missing":
            warn_rows.append(
                {
                    "artifact_id": r["artifact_id"],
                    "severity": "critical" if r["critical"] else "optional",
                    "issue": "missing",
                    "detail": r["canonical_path"],
                }
            )
        if r.get("missing_expected_columns"):
            warn_rows.append(
                {
                    "artifact_id": r["artifact_id"],
                    "severity": "warning",
                    "issue": "missing_expected_columns",
                    "detail": ",".join(r["missing_expected_columns"]),
                }
            )
        if "using_legacy_path" in r.get("notes", ""):
            warn_rows.append(
                {
                    "artifact_id": r["artifact_id"],
                    "severity": "info",
                    "issue": "legacy_path_selected",
                    "detail": r["selected_path"],
                }
            )
        if "canonical_legacy_size_mismatch" in r.get("notes", ""):
            warn_rows.append(
                {
                    "artifact_id": r["artifact_id"],
                    "severity": "warning",
                    "issue": "canonical_legacy_size_mismatch",
                    "detail": f"{r['canonical_path']} vs {r['legacy_path']}",
                }
            )

    if not env["packages"].get("torch", {}).get("installed"):
        warn_rows.append(
            {
                "artifact_id": "(environment)",
                "severity": "critical",
                "issue": "pytorch_not_installed",
                "detail": sys.executable,
            }
        )
    elif not env.get("torch", {}).get("cuda_available"):
        warn_rows.append(
            {
                "artifact_id": "(environment)",
                "severity": "critical",
                "issue": "cuda_not_available",
                "detail": env.get("torch", {}).get("version", ""),
            }
        )

    audit_csv = output_dir / "phase7e0_path_artifact_audit.csv"
    _write_csv(audit_csv, rows)

    selected_json = output_dir / "phase7e0_selected_paths.json"
    selected_json.write_text(
        json.dumps(
            {
                "verdict": verdict,
                "generated_utc": env["timestamp_utc"],
                "repo_root": env["repo_root"],
                "paths": selected_paths,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    env_json = output_dir / "phase7e0_environment_report.json"
    env_json.write_text(json.dumps(env, indent=2), encoding="utf-8")

    warn_csv = output_dir / "phase7e0_missing_or_warning_items.csv"
    _write_csv(warn_csv, warn_rows)

    md_path = output_dir / "phase7e0_path_artifact_audit.md"
    _write_markdown(md_path, verdict, verdict_notes, rows, env, output_dir)

    return {
        "verdict": verdict,
        "verdict_notes": verdict_notes,
        "output_dir": str(output_dir),
        "audit_csv": str(audit_csv),
        "selected_json": str(selected_json),
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    # Flatten list fields for CSV
    flat: list[dict[str, Any]] = []
    for r in rows:
        fr = dict(r)
        for k, v in list(fr.items()):
            if isinstance(v, list):
                fr[k] = "|".join(str(x) for x in v)
        flat.append(fr)
    fieldnames: list[str] = []
    for fr in flat:
        for k in fr:
            if k not in fieldnames:
                fieldnames.append(k)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(flat)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Phase 7E0.5 path/artifact/environment audit for AASIST prep."
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="reports/phase7/phase7e_aasist_experiment/audit",
        help="Directory for audit reports (created if missing).",
    )
    args = parser.parse_args()
    out = _REPO_ROOT / args.output_dir
    result = run_audit(out)
    print(f"Phase 7E0.5 audit verdict: {result['verdict']}")
    print(f"Wrote: {result['audit_csv']}")
    print(f"Wrote: {result['selected_json']}")
    if result["verdict"] == "FAIL":
        for note in result["verdict_notes"]:
            if not note.startswith("optional_") and "legacy" not in note:
                print(f"  - {note}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
