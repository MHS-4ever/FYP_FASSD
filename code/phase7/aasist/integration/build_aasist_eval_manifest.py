"""
Phase 7E2: Build AASIST evaluation manifests from Phase 7C1 / Phase 7A CSVs.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd

from _common import ensure_dir, resolve_path, utc_now_iso, write_markdown
from aasist_eval_common import load_selected_paths, map_expected_risk_fields

OUTPUT_COLUMNS = [
    "sample_id",
    "audio_path",
    "dataset_name",
    "source_origin",
    "manipulation_type",
    "ground_truth_origin",
    "ground_truth_manipulation",
    "partial_fabrication_binary",
    "suspicious_start_time",
    "suspicious_end_time",
    "expected_role",
    "expected_risk_binary",
    "expected_notes",
]


def _pick_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for c in candidates:
        if c in df.columns:
            return c
    return None


def build_manifest(df: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
    id_col = _pick_column(df, ["sample_id", "test_id"]) or "sample_id"
    audio_col = _pick_column(df, ["audio_path"]) or "audio_path"

    rows = []
    for _, r in df.iterrows():
        sample_id = str(r.get(id_col, "")).strip()
        audio_path = str(r.get(audio_col, "")).strip()
        manip = str(r.get("manipulation_type", "")).strip()
        origin = str(r.get("source_origin", "")).strip()
        gt_origin = str(r.get("ground_truth_origin", origin)).strip()
        gt_manip = str(r.get("ground_truth_manipulation", "")).strip()
        partial_bin = r.get("partial_fabrication_binary", r.get("partial_fabrication_detected", ""))

        risk_bin, role, notes = map_expected_risk_fields(manip, origin, gt_manip, partial_bin)

        rows.append(
            {
                "sample_id": sample_id,
                "audio_path": audio_path,
                "dataset_name": dataset_name,
                "source_origin": origin,
                "manipulation_type": manip,
                "ground_truth_origin": gt_origin,
                "ground_truth_manipulation": gt_manip,
                "partial_fabrication_binary": partial_bin,
                "suspicious_start_time": r.get("suspicious_start_time", ""),
                "suspicious_end_time": r.get("suspicious_end_time", ""),
                "expected_role": role,
                "expected_risk_binary": risk_bin,
                "expected_notes": notes,
            }
        )

    return pd.DataFrame(rows, columns=OUTPUT_COLUMNS)


def write_validation(df: pd.DataFrame, output_md: Path, dataset_name: str, input_manifest: Path) -> None:
    risk_counts = Counter(df["expected_risk_binary"].fillna("").astype(str))
    role_counts = Counter(df["expected_role"].fillna("").astype(str))
    blank_risk = int((df["expected_risk_binary"].fillna("").astype(str) == "").sum())
    lines = [
        f"# Phase 7E2 — AASIST Eval Manifest Validation ({dataset_name})",
        "",
        f"**Generated:** {utc_now_iso()}",
        f"**Input:** `{input_manifest}`",
        f"**Rows:** {len(df)}",
        "",
        "## expected_risk_binary counts",
        "",
    ]
    for k, v in sorted(risk_counts.items()):
        lines.append(f"- `{k or '(blank)'}`: {v}")
    lines.extend(["", "## expected_role counts", ""])
    for k, v in sorted(role_counts.items()):
        lines.append(f"- `{k}`: {v}")
    lines.extend(
        [
            "",
            f"**Blank expected_risk_binary (needs_review):** {blank_risk}",
            "",
            "## Notes",
            "",
            "`expected_risk_binary=1` means forensic-risk positive, **not** necessarily AI-generated.",
            "",
        ]
    )
    write_markdown(output_md, lines)


def resolve_input_manifest(
    args: argparse.Namespace,
) -> Path:
    """Use explicit --input_manifest unless --use_selected_paths overrides."""
    explicit = resolve_path(args.input_manifest)
    if not args.use_selected_paths:
        return explicit

    paths = load_selected_paths(resolve_path(args.selected_paths_json))
    if args.dataset_name == "phase7c1" and "phase7c1_collection_manifest" in paths:
        return resolve_path(paths["phase7c1_collection_manifest"])
    if args.dataset_name == "phase7a" and "phase7a_forensic_test_manifest" in paths:
        return resolve_path(paths["phase7a_forensic_test_manifest"])
    return explicit


def main() -> int:
    parser = argparse.ArgumentParser(description="Build AASIST eval manifest")
    parser.add_argument("--input_manifest", type=str, required=True)
    parser.add_argument("--dataset_name", type=str, required=True, choices=("phase7c1", "phase7a"))
    parser.add_argument("--output_csv", type=str, required=True)
    parser.add_argument(
        "--use_selected_paths",
        action="store_true",
        help="Override --input_manifest with paths from phase7e0_selected_paths.json",
    )
    parser.add_argument(
        "--selected_paths_json",
        type=str,
        default="reports/phase7/phase7e_aasist_experiment/audit/phase7e0_selected_paths.json",
    )
    args = parser.parse_args()

    input_path = resolve_input_manifest(args)
    if not input_path.is_file():
        print(f"Input manifest not found: {input_path}")
        return 1

    df = pd.read_csv(input_path)
    out_df = build_manifest(df, args.dataset_name)
    out_csv = resolve_path(args.output_csv)
    ensure_dir(out_csv.parent)
    out_df.to_csv(out_csv, index=False)

    val_md = out_csv.parent / f"{args.dataset_name}_aasist_eval_manifest_validation.md"
    write_validation(out_df, val_md, args.dataset_name, input_path)

    src_note = "selected_paths_json" if args.use_selected_paths else "input_manifest_cli"
    print(f"Input source: {src_note} -> {input_path}")
    print(f"Wrote {len(out_df)} rows to {out_csv}")
    print(f"Wrote {val_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
