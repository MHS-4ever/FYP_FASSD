"""
Phase 7E3B: Build AASIST-L fine-tuning manifests from Phase 7C2 signed-off CSVs (no training).

This is the **fine-tune manifest builder** (not `build_aasist_eval_manifest.py`, which is for 7E2 eval only).

Reproducible entry point:
  python code/phase7/aasist/integration/build_aasist_finetune_manifest.py ...

Outputs under reports/phase7/phase7e_aasist_experiment/phase7e3b_finetune_prep/
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd

from _common import REPO_ROOT, ensure_dir, resolve_path, utc_now_iso, write_markdown
from aasist_eval_common import TARGET_SAMPLE_RATE, _parse_bool, map_expected_risk_fields, resolve_audio_path

AASIST_NB_SAMP = 64600
AASIST_WINDOW_SEC = AASIST_NB_SAMP / TARGET_SAMPLE_RATE
OLD_WINDOW_SEC = 4.0
MAX_SAMPLE_WEIGHT = 4.0

REJECTED_COLUMNS = ["row_id", "sample_id", "audio_path", "reason"]

OUTPUT_COLUMNS = [
    "finetune_row_id",
    "parent_row_id",
    "data_source",
    "split",
    "audio_path",
    "sample_id",
    "base_id",
    "split_group_id",
    "risk_target",
    "risk_label",
    "source_branch_role",
    "aasist_label",
    "sample_weight",
    "weight_reason",
    "window_strategy",
    "window_start_time",
    "window_end_time",
    "use_for_aasist_training",
    "manipulation_type",
    "source_origin",
    "partial_fabrication_binary",
    "suspicious_start_time",
    "suspicious_end_time",
    "notes",
]


def _to_float(v, default=None):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return default
    s = str(v).strip()
    if not s:
        return default
    try:
        return float(s)
    except ValueError:
        return default


def get_audio_duration_sec(audio_path: str) -> float | None:
    """Fast duration probe without full decode when possible."""
    p = resolve_audio_path(audio_path)
    if p is None:
        return None
    try:
        import torchaudio  # type: ignore[import-untyped]

        info = torchaudio.info(str(p))
        if info.num_frames and info.sample_rate:
            return float(info.num_frames) / float(info.sample_rate)
    except Exception:
        pass
    try:
        import librosa  # type: ignore[import-untyped]

        return float(librosa.get_duration(path=str(p)))
    except Exception:
        pass
    return None


def _rejected_row(row: pd.Series, reason: str) -> dict:
    return {
        "row_id": str(row.get("row_id", "")),
        "sample_id": str(row.get("sample_id", "")),
        "audio_path": str(row.get("audio_path", "")),
        "reason": reason,
    }


def write_rejected_csv(rejected: list[dict], out_path: Path) -> None:
    if rejected:
        df = pd.DataFrame(rejected)
        for col in REJECTED_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        df = df[REJECTED_COLUMNS]
    else:
        df = pd.DataFrame(columns=REJECTED_COLUMNS)
    df.to_csv(out_path, index=False)


def map_old_risk_target(row: pd.Series) -> tuple[int | None, str, str]:
    attack = str(row.get("attack_type_original", "")).strip().lower()
    label = str(row.get("label_original", "")).strip().lower()
    if attack == "bonafide" or label == "bonafide":
        return 0, "old_bonafide", "old_bonafide"
    if attack in ("synthesis", "conversion", "replay"):
        return 1, f"old_{attack}", f"old_{attack}"
    if label in ("spoof", "fake"):
        return 1, "old_spoof", f"old_{attack or label}"
    return None, "", ""


def map_row_risk_target(row: pd.Series) -> tuple[int | None, str, str, str]:
    data_source = str(row.get("data_source", "")).strip().lower()
    if data_source == "old":
        rt, role, label = map_old_risk_target(row)
        if rt is None:
            return None, "", "", "unmapped_old_attack"
        return rt, label, role, ""

    manip = str(row.get("manipulation_type", "")).strip().lower()
    origin = str(row.get("source_origin", "")).strip().lower()
    gt_manip = str(
        row.get("manipulation_binary", row.get("manipulation_label", row.get("ground_truth_manipulation", "")))
    ).strip().lower()
    partial = row.get("partial_fabrication_binary", 0)
    risk_s, role, notes = map_expected_risk_fields(manip, origin, gt_manip, partial)
    if risk_s == "":
        return None, "", role, "unmapped_phase7c1"
    return int(risk_s), role.replace("_", " "), role, notes


def assign_sample_weight(
    data_source: str,
    role: str,
    risk_target: int,
    existing_weight: float | None,
) -> tuple[float, str]:
    if data_source == "old":
        if risk_target == 0:
            w, reason = 1.0, "old_bonafide"
        else:
            w, reason = 1.0, f"old_{role or 'spoof'}"
    else:
        role_l = role.lower()
        if "clean_human" in role_l or (role_l == "clean_human"):
            w, reason = 4.0, "phase7c1_clean_human_boost"
        elif "direct_ai" in role_l:
            w, reason = 3.0, "phase7c1_direct_ai"
        elif "partial" in role_l:
            w, reason = 2.5, "phase7c1_partial_fabrication"
        elif "replay" in role_l or "mixer" in role_l or "processed" in role_l:
            w, reason = 2.0, f"phase7c1_{role}"
        else:
            w, reason = 2.0, f"phase7c1_{role or 'risk_positive'}"
    if existing_weight is not None and not np.isnan(existing_weight):
        w = min(MAX_SAMPLE_WEIGHT, max(w, float(existing_weight) * 0.5))
    return min(MAX_SAMPLE_WEIGHT, w), reason


def aasist_label_from_risk(risk_target: int) -> int:
    """Official AASIST: class 0=spoof, 1=bonafide."""
    return 1 if risk_target == 0 else 0


def expand_windows(
    row: pd.Series,
    *,
    phase7c1_windows: int,
    partial_window_mode: str,
    probe_duration: bool,
) -> list[dict]:
    audio_path = str(row.get("audio_path", "")).strip()
    duration = get_audio_duration_sec(audio_path) if probe_duration else None
    if duration is None and str(row.get("data_source", "")).lower() == "phase7c1":
        duration = get_audio_duration_sec(audio_path)

    data_source = str(row.get("data_source", "")).strip().lower()
    manip = str(row.get("manipulation_type", "")).strip().lower()
    partial = _parse_bool(row.get("partial_fabrication_binary")) is True or manip == "partial_ai_insert"

    win_len = min(OLD_WINDOW_SEC, AASIST_WINDOW_SEC) if data_source == "old" else AASIST_WINDOW_SEC
    windows: list[dict] = []

    if partial and partial_window_mode == "suspicious_region":
        s_start = _to_float(row.get("suspicious_start_time"))
        s_end = _to_float(row.get("suspicious_end_time"))
        if s_start is None or s_end is None or s_end <= s_start:
            return []
        center = (s_start + s_end) / 2.0
        start_t = max(0.0, center - win_len / 2.0)
        end_t = start_t + win_len
        windows.append(
            {
                "window_strategy": "partial_suspicious_region",
                "window_start_time": round(start_t, 4),
                "window_end_time": round(end_t, 4),
            }
        )
        return windows

    if data_source == "old":
        end_t = min(win_len, duration) if duration is not None else win_len
        windows.append(
            {
                "window_strategy": "old_first_window",
                "window_start_time": 0.0,
                "window_end_time": round(end_t, 4),
            }
        )
        return windows

    # Phase 7C1 non-partial: start / middle / end
    if duration is None or duration <= win_len:
        windows.append(
            {
                "window_strategy": "phase7c1_start_only",
                "window_start_time": 0.0,
                "window_end_time": round(min(win_len, duration or win_len), 4),
            }
        )
        return windows

    max_start = max(0.0, duration - win_len)
    starts = [0.0]
    if phase7c1_windows >= 2:
        starts.append(max_start / 2.0)
    if phase7c1_windows >= 3:
        starts.append(max_start)
    strategies = ["phase7c1_start", "phase7c1_middle", "phase7c1_end"][: len(starts)]
    for st, strat in zip(starts, strategies):
        windows.append(
            {
                "window_strategy": strat,
                "window_start_time": round(st, 4),
                "window_end_time": round(st + win_len, 4),
            }
        )
    return windows


def process_split_df(
    df: pd.DataFrame,
    split_name: str,
    *,
    phase7c1_windows: int,
    partial_window_mode: str,
    probe_duration: bool,
    row_id_prefix: str,
) -> tuple[list[dict], list[dict]]:
    out_rows: list[dict] = []
    rejected: list[dict] = []
    finetune_idx = 0

    for _, row in df.iterrows():
        parent_id = str(row.get("row_id", ""))
        audio_path = str(row.get("audio_path", "")).strip()
        data_source = str(row.get("data_source", "")).strip().lower()

        if not audio_path:
            rejected.append(_rejected_row(row, "missing_audio_path"))
            continue

        if resolve_audio_path(audio_path) is None:
            rejected.append(_rejected_row(row, "audio_not_found"))
            continue

        risk_target, risk_label, role, map_note = map_row_risk_target(row)
        if risk_target is None:
            rejected.append(_rejected_row(row, map_note or "unmapped_risk"))
            continue

        existing_w = _to_float(row.get("sample_weight"))
        weight, weight_reason = assign_sample_weight(data_source, role, risk_target, existing_w)
        aasist_lab = aasist_label_from_risk(risk_target)

        window_specs = expand_windows(
            row,
            phase7c1_windows=phase7c1_windows,
            partial_window_mode=partial_window_mode,
            probe_duration=probe_duration,
        )
        if not window_specs:
            rejected.append(_rejected_row(row, "no_windows_generated"))
            continue

        for wspec in window_specs:
            finetune_idx += 1
            out_rows.append(
                {
                    "finetune_row_id": f"{row_id_prefix}_{finetune_idx:06d}",
                    "parent_row_id": parent_id,
                    "data_source": data_source,
                    "split": split_name,
                    "audio_path": audio_path,
                    "sample_id": str(row.get("sample_id", "")),
                    "base_id": str(row.get("base_id", "")),
                    "split_group_id": str(row.get("split_group_id", "")),
                    "risk_target": risk_target,
                    "risk_label": risk_label,
                    "source_branch_role": role,
                    "aasist_label": aasist_lab,
                    "sample_weight": weight,
                    "weight_reason": weight_reason,
                    "window_strategy": wspec["window_strategy"],
                    "window_start_time": wspec["window_start_time"],
                    "window_end_time": wspec["window_end_time"],
                    "use_for_aasist_training": True,
                    "manipulation_type": str(row.get("manipulation_type", "")),
                    "source_origin": str(row.get("source_origin", "")),
                    "partial_fabrication_binary": row.get("partial_fabrication_binary", ""),
                    "suspicious_start_time": row.get("suspicious_start_time", ""),
                    "suspicious_end_time": row.get("suspicious_end_time", ""),
                    "notes": map_note or str(row.get("notes", ""))[:200],
                }
            )

    return out_rows, rejected


def write_summary_outputs(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    rejected_df: pd.DataFrame,
    output_dir: Path,
) -> None:
    all_df = pd.concat([train_df, val_df, test_df], ignore_index=True)
    label_rows = []
    for split_name, sdf in ("train", train_df), ("val", val_df), ("test", test_df):
        if sdf.empty:
            continue
        for (rt, role), cnt in Counter(zip(sdf["risk_target"], sdf["source_branch_role"])).items():
            label_rows.append({"split": split_name, "risk_target": rt, "source_branch_role": role, "count": cnt})
    label_df = pd.DataFrame(label_rows)
    label_df.to_csv(output_dir / "aasist_finetune_label_distribution.csv", index=False)

    weight_rows = []
    for split_name, sdf in ("train", train_df), ("val", val_df), ("test", test_df):
        if sdf.empty:
            continue
        for reason, cnt in Counter(sdf["weight_reason"]).items():
            weight_rows.append(
                {
                    "split": split_name,
                    "weight_reason": reason,
                    "count": cnt,
                    "mean_weight": float(sdf[sdf["weight_reason"] == reason]["sample_weight"].mean()),
                }
            )
    pd.DataFrame(weight_rows).to_csv(output_dir / "aasist_finetune_weight_distribution.csv", index=False)

    lines = [
        "# Phase 7E3B — AASIST Fine-Tune Manifest Summary",
        "",
        f"**Generated:** {utc_now_iso()}",
        "",
        "## Row counts (training windows)",
        "",
        f"- **Train:** {len(train_df)}",
        f"- **Val:** {len(val_df)}",
        f"- **Test:** {len(test_df)}",
        f"- **Rejected parent rows:** {len(rejected_df)}",
        "",
        "## risk_target balance (all splits)",
        "",
    ]
    for rt, cnt in Counter(all_df["risk_target"]).items():
        lines.append(f"- risk_target={rt}: **{cnt}**")
    lines.extend(["", "## Weighted risk balance (train)", ""])
    w0 = float(train_df.loc[train_df["risk_target"] == 0, "sample_weight"].sum()) if len(train_df) else 0
    w1 = float(train_df.loc[train_df["risk_target"] == 1, "sample_weight"].sum()) if len(train_df) else 0
    lines.append(f"- train weighted risk_target=0: **{w0:.1f}**")
    lines.append(f"- train weighted risk_target=1: **{w1:.1f}**")
    if w0 > 0:
        lines.append(f"- train weighted ratio 1:0 = **{w1 / w0:.2f}**")
    ch = train_df[train_df["source_branch_role"].astype(str).str.contains("clean_human", case=False, na=False)] if len(train_df) else train_df
    lines.append(f"- train clean_human windows: **{len(ch)}** (total weight **{ch['sample_weight'].sum():.1f}**)" if len(ch) else "0")
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- `risk_target=1` = forensic-risk positive, **not** AI-generated.",
            "- `aasist_label`: 1=bonafide (low risk), 0=spoof (forensic positive) per official AASIST convention.",
            "- Phase 7C1 clean-human windows use elevated `sample_weight` (up to 4.0).",
            "- **Do not train** with plain weighted CE only — use balanced sampler / class-balanced loss (see training plan).",
            "- Re-run `validate_aasist_finetune_manifest.py` after any manifest rebuild.",
            "",
        ]
    )
    write_markdown(output_dir / "aasist_finetune_manifest_summary.md", lines)

    plan_lines = [
        "# Phase 7E3B — AASIST Fine-Tune Plan (manifest)",
        "",
        f"**Generated:** {utc_now_iso()}",
        "",
        "## Next steps",
        "",
        "1. Run `validate_aasist_finetune_manifest.py` on train/val/test CSVs.",
        "2. Review label/weight distributions and rejected rows.",
        "3. Read `AASIST_L_FINETUNE_TRAINING_PLAN.md` before implementing training.",
        "4. **Do not** overwrite `models/weights/AASIST-L.pth` pretrained checkpoint.",
        "",
    ]
    write_markdown(output_dir / "aasist_finetune_plan.md", plan_lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build AASIST fine-tune manifests from Phase 7C2")
    parser.add_argument(
        "--train_manifest",
        type=str,
        default="reports/phase7/phase7c2_training_prep/phase7c2_train_manifest.csv",
    )
    parser.add_argument(
        "--val_manifest",
        type=str,
        default="reports/phase7/phase7c2_training_prep/phase7c2_val_manifest.csv",
    )
    parser.add_argument(
        "--test_manifest",
        type=str,
        default="reports/phase7/phase7c2_training_prep/phase7c2_test_manifest.csv",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="reports/phase7/phase7e_aasist_experiment/phase7e3b_finetune_prep",
    )
    parser.add_argument("--phase7c1_windows", type=int, default=3)
    parser.add_argument("--partial_window_mode", type=str, default="suspicious_region")
    parser.add_argument("--probe_duration", action="store_true", help="Probe audio duration for window placement")
    parser.add_argument("--random_seed", type=int, default=42)
    args = parser.parse_args()

    out_dir = ensure_dir(resolve_path(args.output_dir))
    train_path = resolve_path(args.train_manifest)
    val_path = resolve_path(args.val_manifest)
    test_path = resolve_path(args.test_manifest)

    for p in (train_path, val_path, test_path):
        if not p.is_file():
            print(f"Missing manifest: {p}")
            return 1

    train_rows, train_rej = process_split_df(
        pd.read_csv(train_path),
        "train",
        phase7c1_windows=args.phase7c1_windows,
        partial_window_mode=args.partial_window_mode,
        probe_duration=args.probe_duration,
        row_id_prefix="aft_train",
    )
    val_rows, val_rej = process_split_df(
        pd.read_csv(val_path),
        "val",
        phase7c1_windows=args.phase7c1_windows,
        partial_window_mode=args.partial_window_mode,
        probe_duration=args.probe_duration,
        row_id_prefix="aft_val",
    )
    test_rows, test_rej = process_split_df(
        pd.read_csv(test_path),
        "test",
        phase7c1_windows=args.phase7c1_windows,
        partial_window_mode=args.partial_window_mode,
        probe_duration=args.probe_duration,
        row_id_prefix="aft_test",
    )

    train_df = pd.DataFrame(train_rows, columns=OUTPUT_COLUMNS)
    val_df = pd.DataFrame(val_rows, columns=OUTPUT_COLUMNS)
    test_df = pd.DataFrame(test_rows, columns=OUTPUT_COLUMNS)
    all_rejected = train_rej + val_rej + test_rej
    rejected_path = out_dir / "aasist_finetune_rejected_rows.csv"
    write_rejected_csv(all_rejected, rejected_path)
    rejected_df = pd.read_csv(rejected_path)

    train_df.to_csv(out_dir / "aasist_train_manifest.csv", index=False)
    val_df.to_csv(out_dir / "aasist_val_manifest.csv", index=False)
    test_df.to_csv(out_dir / "aasist_test_manifest.csv", index=False)

    write_summary_outputs(train_df, val_df, test_df, rejected_df, out_dir)

    print(f"Wrote train={len(train_df)} val={len(val_df)} test={len(test_df)} rejected={len(rejected_df)}")
    print(f"Output: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
