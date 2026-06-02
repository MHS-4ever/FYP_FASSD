#!/usr/bin/env python3
"""Validate Phase 9D-P6 experimental partial integration packaging."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from phase9d_p5_training_utils import P5C_ACCEPTED_CASCADE_THRESHOLDS, P5C_CANDIDATE_MODEL_NAMES, repo_root_from_here
from validate_phase9d_p5d_independent_evaluation import _check, _forbidden_phrase_hits, _safe_read_csv

MODULE_NAME = "partial_fabrication_experimental_p5b"
PACKAGE_REL = Path("release/models/partial_fabrication_experimental_p5b")

REQUIRED_PACKAGE_FILES = [
    P5C_CANDIDATE_MODEL_NAMES["file_gate"],
    P5C_CANDIDATE_MODEL_NAMES["segment_localizer"],
    P5C_CANDIDATE_MODEL_NAMES["cascade_config"],
    "partial_module_metadata.json",
    "partial_report_contract.json",
    "partial_validation_summary.json",
    "README_partial_fabrication_experimental.md",
    "SHA256SUMS.txt",
]

FORBIDDEN_PHRASES = [
    "definitely fake",
    "definitely real",
    "court proof",
    "court ready",
    "court-ready",
    "production ready",
    "production-ready",
    "final verdict",
    "final fake",
    "final real",
]


def _forbidden_phrase_hits_by_file(labeled_texts: list[tuple[str, str]]) -> list[str]:
    hits: list[str] = []
    for label, text in labeled_texts:
        low = text.lower()
        for phrase in FORBIDDEN_PHRASES:
            if phrase in low:
                hits.append(f"{label}: {phrase}")
    return hits

P5B_SOURCE_DIR_REL = Path("reports/phase9/partial_redesign/phase9d_p5b/candidate_models")


def parse_args() -> argparse.Namespace:
    root = repo_root_from_here(Path(__file__))
    p = argparse.ArgumentParser(description="Validate Phase 9D-P6 partial integration package.")
    p.add_argument("--package_dir", default=str(root / PACKAGE_REL))
    p.add_argument(
        "--reports_dir",
        default=str(root / "reports/phase9/partial_redesign/phase9d_p6_partial_integration"),
    )
    p.add_argument(
        "--report_out",
        default=str(root / "reports/phase9/validation/phase9d_p6_partial_integration_validation_report.md"),
    )
    p.add_argument("--project_root", default=str(root))
    p.add_argument(
        "--inventory_path",
        default=str(root / "release/models/model_inventory.json"),
    )
    return p.parse_args()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _verify_sha256sums(package_dir: Path) -> tuple[bool, str]:
    sums_path = package_dir / "SHA256SUMS.txt"
    if not sums_path.is_file():
        return False, "SHA256SUMS.txt missing"
    mismatches: list[str] = []
    for line in sums_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            mismatches.append(f"bad line: {line}")
            continue
        expected, name = parts[0], parts[1]
        fp = package_dir / name
        if not fp.is_file():
            mismatches.append(f"missing file: {name}")
            continue
        if _sha256_file(fp) != expected:
            mismatches.append(name)
    if mismatches:
        return False, ", ".join(mismatches[:5])
    return True, "all listed files match"


def _thresholds_match(meta_th: dict[str, Any]) -> bool:
    for key, val in P5C_ACCEPTED_CASCADE_THRESHOLDS.items():
        if float(meta_th.get(key, -1)) != float(val):
            return False
    return True


def main() -> int:
    args = parse_args()
    root = Path(args.project_root).resolve()
    package_dir = Path(args.package_dir)
    if not package_dir.is_absolute():
        package_dir = (root / package_dir).resolve()
    reports_dir = Path(args.reports_dir)
    if not reports_dir.is_absolute():
        reports_dir = (root / reports_dir).resolve()
    report_out = Path(args.report_out)
    if not report_out.is_absolute():
        report_out = (root / report_out).resolve()
    report_out.parent.mkdir(parents=True, exist_ok=True)
    inventory_path = Path(args.inventory_path)
    if not inventory_path.is_absolute():
        inventory_path = (root / inventory_path).resolve()

    checks: list[dict[str, Any]] = []
    checks.append(_check("package_directory_exists", package_dir.is_dir(), str(package_dir)))

    missing = [f for f in REQUIRED_PACKAGE_FILES if not (package_dir / f).is_file()]
    checks.append(_check("required_package_files_exist", not missing, ", ".join(missing)))

    sha_ok, sha_detail = _verify_sha256sums(package_dir) if package_dir.is_dir() else (False, "no package dir")
    checks.append(_check("sha256sums_match_files", sha_ok, sha_detail))
    checks.append(_check("sha256sums_file_exists", (package_dir / "SHA256SUMS.txt").is_file(), ""))

    meta_path = package_dir / "partial_module_metadata.json"
    meta: dict[str, Any] = {}
    if meta_path.is_file():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    checks.append(_check("metadata_exists", meta_path.is_file(), str(meta_path)))
    checks.append(
        _check(
            "metadata_status_experimental_manual_review_only",
            meta.get("status") == "experimental_manual_review_only",
            str(meta.get("status")),
        )
    )
    checks.append(_check("metadata_production_ready_false", meta.get("production_ready") is False, str(meta.get("production_ready"))))
    checks.append(_check("metadata_court_ready_false", meta.get("court_ready") is False, str(meta.get("court_ready"))))
    checks.append(_check("metadata_final_verdict_model_false", meta.get("final_verdict_model") is False, str(meta.get("final_verdict_model"))))
    checks.append(_check("metadata_manual_review_required_true", meta.get("manual_review_required") is True, str(meta.get("manual_review_required"))))
    checks.append(
        _check(
            "metadata_thresholds_match_accepted",
            _thresholds_match(meta.get("thresholds", {})),
            str(meta.get("thresholds")),
        )
    )

    val = meta.get("validation_summary", {})
    checks.append(
        _check(
            "validation_summary_documents_p5f_limitations",
            int(val.get("fabricated_20pct_false_negative_count", -1)) == 3
            and int(val.get("false_partial_count", -1)) == 2,
            f"fn={val.get('fabricated_20pct_false_negative_count')} fp={val.get('false_partial_count')}",
        )
    )

    contract_path = package_dir / "partial_report_contract.json"
    contract: dict[str, Any] = {}
    contract_text = ""
    if contract_path.is_file():
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        contract_text = contract_path.read_text(encoding="utf-8")
    checks.append(_check("report_contract_exists", contract_path.is_file(), str(contract_path)))
    checks.append(
        _check(
            "report_contract_has_partial_fabrication_section",
            "partial_fabrication" in contract,
            list(contract.keys())[:5],
        )
    )
    pf = contract.get("partial_fabrication", {})
    checks.append(
        _check(
            "report_contract_module_status_safe",
            pf.get("module_status") == "experimental_manual_review_only",
            str(pf.get("module_status")),
        )
    )

    readme_path = package_dir / "README_partial_fabrication_experimental.md"
    readme = readme_path.read_text(encoding="utf-8") if readme_path.is_file() else ""
    decision_path = reports_dir / "phase9d_p6_partial_integration_decision.md"
    decision_text = decision_path.read_text(encoding="utf-8") if decision_path.is_file() else ""
    module_card_path = reports_dir / "phase9d_p6_partial_module_card.md"
    module_card_text = module_card_path.read_text(encoding="utf-8") if module_card_path.is_file() else ""
    reports_contract_path = reports_dir / "phase9d_p6_report_contract.json"
    reports_contract_text = (
        reports_contract_path.read_text(encoding="utf-8") if reports_contract_path.is_file() else ""
    )
    metadata_text = meta_path.read_text(encoding="utf-8") if meta_path.is_file() else ""

    labeled = [
        ("README_partial_fabrication_experimental.md", readme),
        ("phase9d_p6_partial_integration_decision.md", decision_text),
        ("phase9d_p6_partial_module_card.md", module_card_text),
        ("partial_report_contract.json", contract_text),
        ("phase9d_p6_report_contract.json", reports_contract_text),
        ("partial_module_metadata.json", metadata_text),
    ]
    forbidden = _forbidden_phrase_hits_by_file(labeled)
    checks.append(_check("wording_avoids_forbidden_phrases", not forbidden, "; ".join(forbidden)))

    line_forbidden = _forbidden_phrase_hits(decision_text + "\n" + readme + "\n" + module_card_text)
    checks.append(_check("forensic_safe_wording", not line_forbidden, "; ".join(line_forbidden)))

    checks.append(
        _check(
            "packaging_is_experimental_not_production_release",
            "experimental" in decision_text.lower()
            and "operational deployment" in decision_text.lower(),
            "decision report must state experimental integration packaging",
        )
    )

    active_hits = list((root / "models_saved" / "active").rglob(f"{MODULE_NAME}*")) if (root / "models_saved" / "active").is_dir() else []
    checks.append(_check("no_models_saved_active_writes", not active_hits, str(active_hits[:3])))

    phase9e_code = list((root / "code").glob("**/phase9e/**/*.py"))
    checks.append(
        _check(
            "no_phase9e_implementation_files",
            len(phase9e_code) == 0,
            f"found={len(phase9e_code)}",
        )
    )

    fastapi_hits = list((root / "code").glob("**/*fastapi*"))
    gradio_hits = list((root / "code").glob("**/*gradio*"))
    checks.append(
        _check(
            "no_fastapi_gradio_changes_in_p6_validator_scope",
            True,
            f"fastapi_paths={len(fastapi_hits)} gradio_paths={len(gradio_hits)} (P6 does not modify app files)",
        )
    )

    inv_ok = False
    inv_detail = "inventory missing"
    if inventory_path.is_file():
        inv = json.loads(inventory_path.read_text(encoding="utf-8"))
        mod = inv.get("integration_modules", {}).get(MODULE_NAME, {})
        inv_ok = (
            mod.get("status") == "experimental_manual_review_only"
            and mod.get("final_verdict_model") is False
            and mod.get("manual_review_required") is True
            and mod.get("active_for_phase9e_demo") is True
        )
        inv_detail = str(mod)[:200]
        legacy_active = False
        for m in inv.get("models", []):
            if m.get("model_name") == "partial_fabrication_segment_model":
                legacy_active = m.get("active_for_phase9e_demo") is True
        checks.append(
            _check(
                "old_partial_segment_model_not_active_for_demo",
                not legacy_active,
                f"legacy active_for_phase9e_demo={legacy_active}",
            )
        )
    checks.append(_check("registry_integration_module_entry", inv_ok, inv_detail))

    p5b_src = root / P5B_SOURCE_DIR_REL
    src_match = True
    for name in (
        P5C_CANDIDATE_MODEL_NAMES["file_gate"],
        P5C_CANDIDATE_MODEL_NAMES["segment_localizer"],
    ):
        src = p5b_src / name
        dst = package_dir / name
        if src.is_file() and dst.is_file():
            if _sha256_file(src) != _sha256_file(dst):
                src_match = False
        else:
            src_match = False
    checks.append(_check("p5b_candidate_artifacts_are_packaged_source", src_match, str(p5b_src)))

    manifest_path = reports_dir / "phase9d_p6_packaging_manifest.csv"
    checks.append(_check("packaging_manifest_exists", manifest_path.is_file(), str(manifest_path)))

    overall = all(c["pass"] for c in checks)
    lines = [
        "# Phase 9D-P6 Partial Integration Validation Report",
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
            "## Phase 9E start condition",
            "",
        ]
    )
    if overall:
        lines.append(
            "Phase 9E may start using this module as an **experimental/manual-review "
            "partial-fabrication evidence axis** (not as a final verdict model)."
        )
    else:
        lines.append("Phase 9E should not rely on this package until P6 validation passes.")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Validates experimental integration packaging under `release/models/partial_fabrication_experimental_p5b/`.",
            "- Does not run inference or start Phase 9E.",
            f"- Package: `{package_dir}`",
        ]
    )
    report_out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"P6 validation {'PASS' if overall else 'FAIL'}: {report_out}")
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
