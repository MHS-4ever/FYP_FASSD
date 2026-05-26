"""
Phase 7C2: Build fine-tuning training manifests (balanced old subset + Phase 7C1).

Does not train or fine-tune models.
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "code"))

from phase7.phase7_paths import resolve_phase7_report_path  # noqa: E402

MANIFEST_COLUMNS = [
    "row_id",
    "data_source",
    "source_subset",
    "audio_path",
    "filepath",
    "filename",
    "sample_id",
    "base_id",
    "variant_id",
    "speaker_id",
    "speaker_gender",
    "language",
    "dataset",
    "domain",
    "attack_type_original",
    "label_original",
    "split",
    "split_group_id",
    "source_origin",
    "manipulation_type",
    "origin_label",
    "manipulation_label",
    "attack_hint",
    "risk_level",
    "origin_binary",
    "manipulation_binary",
    "partial_fabrication_binary",
    "suspicious_start_time",
    "suspicious_end_time",
    "baseline_status",
    "decision_score",
    "max_chunk_spoof",
    "suspicious_chunk_ratio",
    "sample_weight",
    "weight_reason",
    "use_origin_loss",
    "use_manipulation_loss",
    "use_attack_loss",
    "use_partial_loss",
    "review_status",
    "notes",
]

ATTACK_GROUPS = ("bonafide", "synthesis", "conversion", "replay")
MAX_SAMPLE_WEIGHT = 4.0
MIN_SAMPLE_WEIGHT = 0.1

P7C1_BASE_WEIGHTS = {
    ("clean_direct", "human"): 2.5,
    ("clean_direct", "ai"): 2.5,
    ("human_replay", None): 2.5,
    ("ai_replay", None): 2.0,
    ("mixer_processed", "human"): 2.5,
    ("mixer_processed", "ai"): 2.0,
    ("partial_ai_insert", None): 3.0,
}

BASELINE_WEIGHT_BONUS = {
    "clean_human_false_alarm": 0.5,
    "direct_ai_file_level_missed_but_segment_suspicious": 0.5,
    "direct_ai_missed": 0.75,
    "partial_fabrication_missed": 0.75,
}


def _safe_str(val) -> str:
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return ""
    return str(val).strip()


def _norm_path(p: str) -> str:
    return _safe_str(p).replace("\\", "/").lower()


def _basename(p: str) -> str:
    return Path(_safe_str(p).replace("\\", "/")).name.lower()


def _parse_partial_bin(val) -> int:
    s = _safe_str(val).lower()
    if s in {"1", "true", "yes"}:
        return 1
    return 0


def _bool_str(val: bool) -> str:
    return "true" if val else "false"


def classify_old_attack_group(row: pd.Series) -> str | None:
    label = _safe_str(row.get("label")).lower()
    attack = _safe_str(row.get("attack_type")).lower()
    if label == "bonafide" or attack == "bonafide":
        return "bonafide"
    if label != "spoof":
        return None
    if attack in ATTACK_GROUPS:
        return attack
    return None


def map_old_row(row: pd.Series, split: str, row_idx: int) -> dict | None:
    group = classify_old_attack_group(row)
    if group is None:
        return None

    filepath = _safe_str(row.get("filepath"))
    if not filepath:
        return None

    filename = _safe_str(row.get("filename")) or Path(filepath).name
    file_id = _safe_str(row.get("file_id")) or Path(filepath).stem
    sample_id = file_id or f"old_{split}_{row_idx}"

    out = {c: "" for c in MANIFEST_COLUMNS}
    out.update(
        {
            "data_source": "old",
            "source_subset": "old_balanced",
            "audio_path": filepath,
            "filepath": filepath,
            "filename": filename,
            "sample_id": sample_id,
            "base_id": f"old_{sample_id}",
            "variant_id": "old_legacy",
            "speaker_id": _safe_str(row.get("speaker_id")),
            "speaker_gender": "unknown",
            "language": "unknown",
            "dataset": _safe_str(row.get("dataset")),
            "domain": _safe_str(row.get("domain")),
            "attack_type_original": _safe_str(row.get("attack_type")),
            "label_original": _safe_str(row.get("label")),
            "split": split,
            "split_group_id": f"old_{sample_id}",
            "partial_fabrication_binary": 0,
            "sample_weight": 1.0,
            "weight_reason": f"old_{group}_base",
            "use_origin_loss": True,
            "use_manipulation_loss": True,
            "use_attack_loss": True,
            "use_partial_loss": True,
            "review_status": "approved",
            "notes": "Old balanced subset for Phase 7C2 fine-tuning prep.",
        }
    )

    if group == "bonafide":
        out.update(
            {
                "source_origin": "human",
                "manipulation_type": "clean_direct",
                "origin_label": "human_likely",
                "manipulation_label": "clean_original",
                "attack_hint": "bonafide",
                "risk_level": "low",
                "origin_binary": "human",
                "manipulation_binary": "clean",
            }
        )
    elif group == "synthesis":
        out.update(
            {
                "source_origin": "ai",
                "manipulation_type": "clean_direct",
                "origin_label": "ai_likely",
                "manipulation_label": "clean_original",
                "attack_hint": "synthesis",
                "risk_level": "high",
                "origin_binary": "ai",
                "manipulation_binary": "clean",
            }
        )
    elif group == "conversion":
        out.update(
            {
                "source_origin": "ai",
                "manipulation_type": "clean_direct",
                "origin_label": "ai_likely",
                "manipulation_label": "clean_original",
                "attack_hint": "voice_conversion",
                "risk_level": "high",
                "origin_binary": "ai",
                "manipulation_binary": "clean",
            }
        )
    elif group == "replay":
        out.update(
            {
                "source_origin": "unknown",
                "manipulation_type": "ai_replay",
                "origin_label": "uncertain",
                "manipulation_label": "replayed_or_re_recorded",
                "attack_hint": "replay",
                "risk_level": "high",
                "origin_binary": "unknown",
                "manipulation_binary": "manipulated",
                "sample_weight": 0.7,
                "weight_reason": "old_replay_origin_masked",
            }
        )

    use_origin = group != "replay"
    out["use_origin_loss"] = _bool_str(use_origin)
    out["use_manipulation_loss"] = "true"
    out["use_attack_loss"] = "true"
    out["use_partial_loss"] = "true"
    return out


def _origin_binary_from_label(origin_label: str) -> str:
    m = {
        "human_likely": "human",
        "ai_likely": "ai",
        "mixed_or_partial_ai": "mixed",
        "uncertain": "unknown",
    }
    return m.get(_safe_str(origin_label).lower(), "unknown")


def _manipulation_binary_from_label(manipulation_label: str) -> str:
    ml = _safe_str(manipulation_label).lower()
    if ml == "clean_original":
        return "clean"
    if ml == "uncertain":
        return "uncertain"
    if ml:
        return "manipulated"
    return "uncertain"


def _p7c1_base_weight(manipulation_type: str, source_origin: str) -> tuple[float, str]:
    manip = _safe_str(manipulation_type).lower()
    origin = _safe_str(source_origin).lower()
    if manip == "partial_ai_insert":
        return 3.0, "p7c1_partial_fabrication"
    if manip == "clean_direct":
        key = ("clean_direct", origin if origin in {"human", "ai"} else "ai")
        return P7C1_BASE_WEIGHTS.get(key, 2.5), f"p7c1_{key[0]}_{key[1]}"
    if manip == "human_replay":
        return 2.5, "p7c1_human_replay"
    if manip == "ai_replay":
        return 2.0, "p7c1_ai_replay"
    if manip == "mixer_processed":
        key = ("mixer_processed", origin if origin in {"human", "ai"} else "human")
        return P7C1_BASE_WEIGHTS.get(key, 2.5), f"p7c1_mixer_{key[1]}"
    return 2.0, "p7c1_default"


def map_phase7c1_row(
    row: pd.Series,
    baseline_lookup: dict[str, dict],
) -> dict:
    sample_id = _safe_str(row.get("sample_id"))
    baseline = baseline_lookup.get(sample_id, {})

    manip = _safe_str(row.get("manipulation_type")).lower()
    origin = _safe_str(row.get("source_origin")).lower()
    weight, reason = _p7c1_base_weight(manip, origin)

    baseline_status = _safe_str(baseline.get("baseline_status"))
    bonus = BASELINE_WEIGHT_BONUS.get(baseline_status, 0.0)
    if bonus:
        weight = min(MAX_SAMPLE_WEIGHT, weight + bonus)
        reason = f"{reason}+baseline_{baseline_status}"

    weight = min(MAX_SAMPLE_WEIGHT, max(MIN_SAMPLE_WEIGHT, weight))

    audio_path = _safe_str(row.get("audio_path"))
    out = {c: "" for c in MANIFEST_COLUMNS}
    out.update(
        {
            "data_source": "phase7c1",
            "source_subset": "phase7c1_collection",
            "audio_path": audio_path,
            "filepath": audio_path,
            "filename": Path(audio_path.replace("\\", "/")).name if audio_path else "",
            "sample_id": sample_id,
            "base_id": _safe_str(row.get("base_id")),
            "variant_id": _safe_str(row.get("variant_id")),
            "speaker_id": _safe_str(row.get("speaker_id")),
            "speaker_gender": _safe_str(row.get("speaker_gender")),
            "language": _safe_str(row.get("language")),
            "dataset": "phase7c1",
            "domain": _safe_str(row.get("recording_condition")) or "local_forensic",
            "attack_type_original": _safe_str(row.get("attack_hint")),
            "label_original": _safe_str(row.get("origin_label")),
            "split": _safe_str(row.get("split")).lower(),
            "split_group_id": _safe_str(row.get("split_group_id")) or _safe_str(row.get("base_id")),
            "source_origin": origin,
            "manipulation_type": manip,
            "origin_label": _safe_str(row.get("origin_label")),
            "manipulation_label": _safe_str(row.get("manipulation_label")),
            "attack_hint": _safe_str(row.get("attack_hint")),
            "risk_level": _safe_str(row.get("risk_level")),
            "origin_binary": _origin_binary_from_label(_safe_str(row.get("origin_label"))),
            "manipulation_binary": _manipulation_binary_from_label(_safe_str(row.get("manipulation_label"))),
            "partial_fabrication_binary": _parse_partial_bin(row.get("partial_fabrication_binary")),
            "suspicious_start_time": row.get("suspicious_start_time", ""),
            "suspicious_end_time": row.get("suspicious_end_time", ""),
            "baseline_status": baseline_status,
            "decision_score": baseline.get("decision_score", ""),
            "max_chunk_spoof": baseline.get("max_chunk_spoof", ""),
            "suspicious_chunk_ratio": baseline.get("suspicious_chunk_ratio", ""),
            "sample_weight": round(weight, 4),
            "weight_reason": reason,
            "use_origin_loss": "true",
            "use_manipulation_loss": "true",
            "use_attack_loss": "true",
            "use_partial_loss": "true",
            "review_status": _safe_str(row.get("review_status")) or "approved",
            "notes": _safe_str(row.get("notes")),
        }
    )
    return out


def reservoir_sample_manifest(
    manifest_path: Path,
    split_name: str,
    per_attack: int,
    seed: int,
) -> tuple[pd.DataFrame, dict[str, int], list[str]]:
    """Stream large CSV and reservoir-sample per attack group."""
    rng = random.Random(seed)
    reservoirs: dict[str, list] = {g: [] for g in ATTACK_GROUPS}
    seen: dict[str, int] = {g: 0 for g in ATTACK_GROUPS}
    warnings: list[str] = []
    row_idx = 0

    if not manifest_path.is_file():
        warnings.append(f"Missing old manifest: {manifest_path}")
        return pd.DataFrame(columns=MANIFEST_COLUMNS), {g: 0 for g in ATTACK_GROUPS}, warnings

    for chunk in pd.read_csv(manifest_path, low_memory=False, chunksize=200_000):
        for _, row in chunk.iterrows():
            group = classify_old_attack_group(row)
            if group is None:
                continue
            mapped = map_old_row(row, split_name, row_idx)
            if mapped is None:
                continue
            row_idx += 1
            seen[group] += 1
            res = reservoirs[group]
            if len(res) < per_attack:
                res.append(mapped)
            else:
                j = rng.randint(0, seen[group] - 1)
                if j < per_attack:
                    res[j] = mapped

    rows = []
    counts = {}
    for g in ATTACK_GROUPS:
        counts[g] = len(reservoirs[g])
        if seen[g] < per_attack:
            warnings.append(
                f"{split_name}/{g}: only {seen[g]} available (requested {per_attack})"
            )
        rows.extend(reservoirs[g])

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df[MANIFEST_COLUMNS]
    return df, counts, warnings


def load_holdout_keys(holdout_path: Path | None) -> dict[str, set[str]]:
    keys = {"paths": set(), "basenames": set(), "ids": set()}
    if holdout_path is None or not holdout_path.is_file():
        return keys
    df = pd.read_csv(holdout_path, low_memory=False)
    for _, row in df.iterrows():
        for col in ("audio_path", "filepath"):
            p = _norm_path(row.get(col, ""))
            if p:
                keys["paths"].add(p)
                keys["basenames"].add(_basename(p))
        for col in ("test_id", "sample_id"):
            tid = _safe_str(row.get(col)).lower()
            if tid:
                keys["ids"].add(tid)
    return keys


def find_holdout_overlaps(df: pd.DataFrame, holdout_keys: dict[str, set[str]]) -> pd.DataFrame:
    if df.empty or not any(holdout_keys.values()):
        return pd.DataFrame()
    overlaps = []
    for i, row in df.iterrows():
        path = _norm_path(row.get("audio_path", ""))
        base = _basename(path)
        sid = _safe_str(row.get("sample_id")).lower()
        hit = (
            (path and path in holdout_keys["paths"])
            or (base and base in holdout_keys["basenames"])
            or (sid and sid in holdout_keys["ids"])
        )
        if hit:
            overlaps.append(
                {
                    "row_index": i,
                    "sample_id": row.get("sample_id"),
                    "audio_path": row.get("audio_path"),
                    "split": row.get("split"),
                    "data_source": row.get("data_source"),
                }
            )
    return pd.DataFrame(overlaps)


def assign_row_ids(df: pd.DataFrame, prefix: str) -> pd.DataFrame:
    out = df.copy()
    out["row_id"] = [f"{prefix}_{i:06d}" for i in range(len(out))]
    return out


def write_holdout_report(
    path: Path,
    holdout_path: Path | None,
    overlap_dfs: dict[str, pd.DataFrame],
    total_overlap: int,
) -> None:
    lines = [
        "# Phase 7C2 — Holdout Protection Report",
        "",
        "## Phase 7A controlled holdout",
        "",
    ]
    if holdout_path and holdout_path.is_file():
        lines.append(f"- Manifest: `{holdout_path}` (**found**)")
        n = len(pd.read_csv(holdout_path, low_memory=False))
        lines.append(f"- Holdout rows in manifest: **{n}**")
    else:
        lines.append(f"- Manifest: `{holdout_path}` (**missing** — overlap check limited)")

    lines.extend(["", "## Overlap scan (train + val + test combined)", ""])
    if total_overlap == 0:
        lines.append("**No overlapping rows detected.** Phase 7A holdout is protected.")
        lines.append("")
        lines.append("**Decision:** PASS — safe to proceed to validation.")
    else:
        lines.append(f"**CRITICAL: {total_overlap} overlapping row(s) found.**")
        lines.append("")
        lines.append("**Decision:** FAIL — remove overlaps before fine-tuning.")
        for split_name, odf in overlap_dfs.items():
            if not odf.empty:
                lines.append(f"### {split_name} ({len(odf)} overlaps)")
                lines.append("")
                for _, r in odf.head(20).iterrows():
                    lines.append(f"- `{r.get('sample_id')}` | `{r.get('audio_path')}`")
                lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def print_terminal_summary(
    old_counts: dict,
    p7c1_counts: dict,
    combined_counts: dict,
    holdout_overlap: int,
    origin_masked: int,
    avg_weights: dict,
    output_dir: Path,
    warnings: list[str],
) -> None:
    print("\n" + "=" * 60)
    print("Phase 7C2 training manifest build — summary")
    print("=" * 60)
    for split in ("train", "val", "test"):
        oc = old_counts.get(split, {})
        print(
            f"Old {split}: {sum(oc.values())} rows "
            f"(bonafide={oc.get('bonafide',0)}, syn={oc.get('synthesis',0)}, "
            f"conv={oc.get('conversion',0)}, replay={oc.get('replay',0)})"
        )
    for split in ("train", "val", "test"):
        print(f"Phase 7C1 {split}: {p7c1_counts.get(split, 0)} rows")
    for split in ("train", "val", "test"):
        print(f"Combined {split}: {combined_counts.get(split, 0)} rows")
    print(f"Phase 7A holdout overlaps: {holdout_overlap}")
    print(f"Old replay rows with use_origin_loss=false: {origin_masked}")
    for split, w in avg_weights.items():
        print(f"Avg sample_weight ({split}): {w:.3f}")
    print("-" * 60)
    print(f"Output dir: {output_dir}")
    if warnings:
        print(f"Warnings ({len(warnings)}):")
        for w in warnings[:15]:
            print(f"  - {w}")
        if len(warnings) > 15:
            print(f"  - ... and {len(warnings) - 15} more")
    print("\nNext: validate manifests")
    print(
        "python code/phase7/validate_phase7c2_training_manifests.py "
        "--train reports/phase7/phase7c2_training_prep/phase7c2_train_manifest.csv "
        "--val reports/phase7/phase7c2_training_prep/phase7c2_val_manifest.csv "
        "--test reports/phase7/phase7c2_training_prep/phase7c2_test_manifest.csv "
        "--phase7a_holdout reports/phase7/phase7_forensic_tests/forensic_test_manifest.csv "
        "--output_dir reports/phase7/phase7c2_training_prep/validation --allow_missing_audio --allow_warnings"
    )
    print("=" * 60 + "\n")


def build_all(args: argparse.Namespace) -> None:
    output_dir = resolve_phase7_report_path(args.output_dir, for_write=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    old_dir = Path(args.old_manifest_dir).resolve()
    seed = int(args.random_seed)

    holdout_path = resolve_phase7_report_path(args.phase7a_holdout) if args.phase7a_holdout else None
    holdout_keys = load_holdout_keys(holdout_path)

    all_warnings: list[str] = []
    old_subsets: dict[str, pd.DataFrame] = {}
    old_group_counts: dict[str, dict] = {}

    split_files = {
        "train": old_dir / "train_speaker_independent.csv",
        "val": old_dir / "val_speaker_independent.csv",
        "test": old_dir / "test_speaker_independent.csv",
    }
    per_attack = {
        "train": int(args.old_train_per_attack),
        "val": int(args.old_val_per_attack),
        "test": int(args.old_test_per_attack),
    }

    for split_name, manifest_path in split_files.items():
        df, counts, warns = reservoir_sample_manifest(
            manifest_path, split_name, per_attack[split_name], seed + hash(split_name) % 10000
        )
        all_warnings.extend(warns)
        old_subsets[split_name] = assign_row_ids(df, f"old_{split_name}")
        old_group_counts[split_name] = counts
        out_path = output_dir / f"phase7c2_old_balanced_{split_name}_subset.csv"
        old_subsets[split_name].to_csv(out_path, index=False)
        print(f"[SAVE] {out_path} ({len(df)} rows)")

    p7c1_path = resolve_phase7_report_path(args.phase7c1_manifest)
    baseline_path = resolve_phase7_report_path(args.phase7c1_baseline)
    p7c1_df = pd.read_csv(p7c1_path, low_memory=False)
    baseline_df = pd.read_csv(baseline_path, low_memory=False) if baseline_path.is_file() else pd.DataFrame()
    baseline_lookup = {}
    if not baseline_df.empty and "sample_id" in baseline_df.columns:
        for _, br in baseline_df.iterrows():
            baseline_lookup[_safe_str(br["sample_id"])] = br.to_dict()

    p7c1_rows = [map_phase7c1_row(r, baseline_lookup) for _, r in p7c1_df.iterrows()]
    p7c1_all = pd.DataFrame(p7c1_rows)
    if not p7c1_all.empty:
        p7c1_all = p7c1_all[MANIFEST_COLUMNS]

    p7c1_subsets: dict[str, pd.DataFrame] = {}
    p7c1_counts: dict[str, int] = {}
    rejected: list[dict] = []

    for split_name in ("train", "val", "test"):
        sub = p7c1_all[p7c1_all["split"].astype(str).str.lower() == split_name].copy()
        p7c1_subsets[split_name] = assign_row_ids(sub, f"p7c1_{split_name}")
        p7c1_counts[split_name] = len(sub)
        out_path = output_dir / f"phase7c2_phase7c1_{split_name}_subset.csv"
        p7c1_subsets[split_name].to_csv(out_path, index=False)
        print(f"[SAVE] {out_path} ({len(sub)} rows)")

    # Reject unassigned / holdout splits from p7c1
    other = p7c1_all[~p7c1_all["split"].isin(["train", "val", "test"])]
    for _, r in other.iterrows():
        rejected.append({**r.to_dict(), "reject_reason": "invalid_or_holdout_split"})

    combined: dict[str, pd.DataFrame] = {}
    combined_counts: dict[str, int] = {}
    overlap_by_split: dict[str, pd.DataFrame] = {}
    total_overlap = 0

    for split_name in ("train", "val", "test"):
        parts = [old_subsets[split_name], p7c1_subsets[split_name]]
        comb = pd.concat([p for p in parts if not p.empty], ignore_index=True)
        comb = assign_row_ids(comb, f"cmb_{split_name}")
        combined[split_name] = comb
        combined_counts[split_name] = len(comb)
        out_path = output_dir / f"phase7c2_{split_name}_manifest.csv"
        comb.to_csv(out_path, index=False)
        print(f"[SAVE] {out_path} ({len(comb)} rows)")

        odf = find_holdout_overlaps(comb, holdout_keys)
        overlap_by_split[split_name] = odf
        total_overlap += len(odf)

    all_combined = pd.concat([combined[s] for s in ("train", "val", "test")], ignore_index=True)
    holdout_overlap_all = find_holdout_overlaps(all_combined, holdout_keys)
    total_overlap = len(holdout_overlap_all)

    write_holdout_report(
        output_dir / "phase7c2_holdout_protection_report.md",
        holdout_path,
        {"combined": holdout_overlap_all, **overlap_by_split},
        total_overlap,
    )
    print(f"[SAVE] {output_dir / 'phase7c2_holdout_protection_report.md'}")

    if not holdout_overlap_all.empty:
        holdout_overlap_all.to_csv(output_dir / "phase7c2_holdout_overlap_rows.csv", index=False)

    rejected_df = pd.DataFrame(rejected)
    rejected_df.to_csv(output_dir / "phase7c2_rejected_rows.csv", index=False)

    origin_masked = int(
        (
            (all_combined["data_source"].astype(str) == "old")
            & (all_combined["use_origin_loss"].astype(str).str.lower() == "false")
        ).sum()
    )

    avg_weights = {}
    for split_name in ("train", "val", "test"):
        w = pd.to_numeric(combined[split_name]["sample_weight"], errors="coerce")
        avg_weights[split_name] = float(w.mean()) if len(w) else 0.0

    print_terminal_summary(
        old_group_counts,
        p7c1_counts,
        combined_counts,
        total_overlap,
        origin_masked,
        avg_weights,
        output_dir,
        all_warnings,
    )


def parse_args():
    p = argparse.ArgumentParser(description="Phase 7C2 — build fine-tuning training manifests")
    p.add_argument("--old_manifest_dir", type=str, default="data/manifests")
    p.add_argument("--phase7c1_manifest", type=str, required=True)
    p.add_argument("--phase7c1_baseline", type=str, required=True)
    p.add_argument("--phase7a_holdout", type=str, default="reports/phase7/phase7_forensic_tests/forensic_test_manifest.csv")
    p.add_argument("--output_dir", type=str, default="reports/phase7/phase7c2_training_prep")
    p.add_argument("--old_train_per_attack", type=int, default=250)
    p.add_argument("--old_val_per_attack", type=int, default=50)
    p.add_argument("--old_test_per_attack", type=int, default=50)
    p.add_argument("--random_seed", type=int, default=42)
    return p.parse_args()


def main():
    build_all(parse_args())


if __name__ == "__main__":
    main()
