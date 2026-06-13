"""Partial-axis evaluation on a selected testing_audios subset (uses full release pipeline)."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / "release"
OUT = ROOT / "reports" / "release_audit" / "testing_audios_partial_subset_eval_2026-06-13"
MANIFEST = (
    ROOT
    / "reports"
    / "phase7"
    / "phase7_forensic_tests"
    / "forensic_test_manifest_backup_before_T4_3_timestamp.csv"
)
DEFAULT_IDS = [
    "T4.3",        # true partial English
    "T5_FAB_001",  # true partial Urdu
    "T2.3",        # human replay negative
    "T3.2",        # AI replay negative
    "T3.4",        # AI mixer negative
    "T1.2",        # clean human negative
]

if str(RELEASE) not in sys.path:
    sys.path.insert(0, str(RELEASE))

from src.inference_pipeline import analyze_audio_file  # noqa: E402


def resolve_audio(path_str: str) -> Path | None:
    p = Path(path_str)
    if p.is_file():
        return p.resolve()
    q = (ROOT / p).resolve()
    return q if q.is_file() else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ids", nargs="*", default=DEFAULT_IDS, help="test_id values to evaluate")
    parser.add_argument(
        "--cpu-ids",
        nargs="*",
        default=["T4.1", "T4.3"],
        help="force CPU for long files to avoid CUDA OOM",
    )
    args = parser.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    raw_dir = OUT / "raw_pipeline_json"
    raw_dir.mkdir(exist_ok=True)

    manifest = pd.read_csv(MANIFEST, dtype=str, keep_default_na=False)
    manifest = manifest[manifest["test_id"].isin(args.ids)].copy()

    rows: list[dict] = []
    for _, row in manifest.iterrows():
        out = row.to_dict()
        audio = resolve_audio(row["audio_path"])
        out["resolved_audio_path"] = str(audio) if audio else ""
        if audio is None:
            out["partial_status"] = "missing_audio"
            rows.append(out)
            continue

        device = "cpu" if row["test_id"] in args.cpu_ids else "auto"
        try:
            result = analyze_audio_file(
                str(audio),
                case_id=f"PARTIAL-{row['test_id']}",
                output_dir=None,
                device=device,
                return_debug=True,
            )
            (raw_dir / f"{row['test_id']}.json").write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
            partial = result.get("partial_fabrication_evidence") or {}
            replay = result.get("replay_evidence") or {}
            mixer = result.get("mixer_channel_evidence") or {}
            out["partial_status"] = result.get("status", "ok")
            out["replay_probability"] = replay.get("probability")
            out["mixer_probability"] = mixer.get("probability")
            out["partial_max_segment_probability"] = partial.get("max_segment_probability")
            out["partial_high_segment_fraction"] = partial.get("high_segment_fraction")
            out["partial_localization_gate"] = partial.get("partial_localization_gate")
            out["partial_fusion_eligible"] = partial.get("partial_fusion_eligible")
            out["partial_fusion_block_reason"] = partial.get("partial_fusion_block_reason")
            cands = result.get("segment_candidates") or []
            if cands:
                out["partial_top_start_sec"] = cands[0].get("start_sec")
                out["partial_top_end_sec"] = cands[0].get("end_sec")
                out["partial_top_probability"] = cands[0].get("partial_probability")
        except Exception as exc:
            out["partial_status"] = f"error: {exc}"
        rows.append(out)
        print(f"{row['test_id']}: {out['partial_status']}")

    pred = pd.DataFrame(rows)
    pred["partial_target"] = pred["partial_fabrication_detected"].astype(str).str.lower().eq("true").astype(int)
    pred["partial_raw_pred"] = (pd.to_numeric(pred["partial_max_segment_probability"], errors="coerce") >= 0.5).astype(int)
    pred["partial_fusion_pred"] = pred["partial_fusion_eligible"].astype(str).str.lower().isin(["true", "1"]).astype(int)
    pred.to_csv(OUT / "testing_audios_partial_subset_predictions.csv", index=False)

    report = [
        "# Testing Audios Partial Subset Evaluation",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "Subset only. Uses full release pipeline with WavLM + segment partial model.",
        "",
        f"Evaluated ids: {', '.join(args.ids)}",
        "",
        pred.to_string(index=False),
        "",
        f"CSV: `{OUT / 'testing_audios_partial_subset_predictions.csv'}`",
    ]
    (OUT / "testing_audios_partial_subset_eval_report.md").write_text("\n".join(report), encoding="utf-8")
    print(f"Wrote partial subset evaluation to {OUT}")


if __name__ == "__main__":
    main()
