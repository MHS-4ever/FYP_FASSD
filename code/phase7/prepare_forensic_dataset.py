"""
Phase 7B: Prepare forensic dataset labels and manifests from Phase 7A outputs.

Does not train models. Produces file-level labels, segment labels, training preview, and reports.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import librosa
import numpy as np
import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[2]

# Reuse timestamp helper only (no change to 7A analysis logic).
import sys

sys.path.insert(0, str(_REPO_ROOT / "code"))
from phase7.analyze_forensic_test_results import has_valid_suspicious_timestamps, parse_bool

ALLOWED_ORIGIN_LABEL = {"human_likely", "ai_likely", "mixed_or_partial_ai", "uncertain"}
ALLOWED_MANIP_LABEL = {
    "clean_original",
    "replayed_or_re_recorded",
    "channel_processed",
    "platform_compressed",
    "edited_or_spliced",
    "environment_mismatch",
    "noisy_low_quality",
    "uncertain",
}
ALLOWED_ATTACK_HINT = {"bonafide", "synthesis", "voice_conversion", "replay", "unknown"}
ALLOWED_RISK = {"low", "medium", "high", "inconclusive"}

PRODUCT_STATUSES_NEED_REVIEW = {
    "clean_human_borderline",
    "direct_ai_borderline",
    "borderline_needs_review",
    "partial_not_evaluated_missing_timestamp",
    "unknown_review_required",
}

# Phase 7A T1–T5 controlled set: diagnostic/holdout only — never main training data.
CONTROLLED_HOLDOUT_ROLE = "controlled_holdout"
CONTROLLED_HOLDOUT_READINESS = "not_ready_for_training"
CONTROLLED_HOLDOUT_WARNING = (
    "Phase 7A controlled diagnostic set only. Do not use as main training data."
)
PREVIEW_ROW_WARNING = "controlled_holdout_do_not_train"


def _to_float(value, default=None):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return default
    s = str(value).strip()
    if s == "":
        return default
    try:
        return float(s)
    except ValueError:
        return default


def _resolve_audio(audio_path: str, repo_root: Path) -> Path:
    p = Path(audio_path)
    if p.is_file():
        return p.resolve()
    c = (repo_root / audio_path).resolve()
    return c if c.is_file() else p.resolve()


def _probe_audio(path: Path) -> dict:
    out = {"duration": "", "sample_rate": "", "channels": ""}
    if not path.is_file():
        return out
    try:
        duration = float(librosa.get_duration(path=path))
        out["duration"] = round(duration, 3)
        y, sr = librosa.load(path, sr=None, mono=False, duration=0.01)
        out["sample_rate"] = int(sr)
        out["channels"] = 1 if y.ndim == 1 else int(y.shape[0])
    except Exception:
        try:
            duration = float(librosa.get_duration(path=path))
            out["duration"] = round(duration, 3)
        except Exception:
            pass
    return out


def _attack_hint_from_row(row: dict, default: str) -> str:
    hint = str(row.get("attack_hint", "") or default).strip().lower()
    if hint in {"conversion", "voice_conversion"}:
        return "voice_conversion"
    if hint in ALLOWED_ATTACK_HINT:
        return hint
    conv = _to_float(row.get("conversion_prob"), 0.0) or 0.0
    syn = _to_float(row.get("synthesis_prob"), 0.0) or 0.0
    if conv > syn + 0.1:
        return "voice_conversion"
    if syn > conv + 0.1:
        return "synthesis"
    return default if default in ALLOWED_ATTACK_HINT else "unknown"


def normalize_labels(row: dict) -> dict:
    """Map manifest + product fields to canonical forensic labels."""
    manip = str(row.get("manipulation_type", "")).strip().lower()
    gt_origin = str(row.get("ground_truth_origin", "")).strip().lower()
    gt_manip = str(row.get("ground_truth_manipulation", "")).strip().lower()
    product_status = str(row.get("product_status", "")).strip().lower()
    platform = str(row.get("platform", "")).strip().lower() or "none"

    partial_bin = 1 if manip == "partial_ai_insert" or parse_bool(row.get("partial_fabrication_detected")) else 0

    origin_label = str(row.get("origin_label", "")).strip().lower()
    manip_label = str(row.get("manipulation_label", "")).strip().lower()
    attack_hint = _attack_hint_from_row(row, "unknown")
    risk_level = str(row.get("risk_level", "")).strip().lower() or "medium"

    if manip == "clean_direct" and gt_origin == "human":
        origin_label, manip_label, attack_hint = "human_likely", "clean_original", "bonafide"
        risk_level = "inconclusive" if product_status == "clean_human_borderline" else "low"
    elif manip == "clean_direct" and gt_origin == "ai":
        origin_label, manip_label = "ai_likely", "clean_original"
        attack_hint = _attack_hint_from_row(row, "synthesis")
        if product_status in {"direct_ai_detected"}:
            risk_level = "high"
        elif product_status == "direct_ai_file_level_missed_but_segment_suspicious":
            risk_level = "medium"
        else:
            risk_level = "high" if product_status == "direct_ai_missed" else risk_level
    elif manip == "human_replay":
        origin_label, manip_label, attack_hint = "human_likely", "replayed_or_re_recorded", "replay"
        risk_level = "high" if str(row.get("prediction", "")).upper() == "FAKE" else "medium"
    elif manip == "ai_replay":
        origin_label, manip_label = "ai_likely", "replayed_or_re_recorded"
        attack_hint = _attack_hint_from_row(row, "replay")
        risk_level = "high"
    elif manip == "mixer_processed":
        if gt_origin == "human":
            origin_label, manip_label, attack_hint = "human_likely", "channel_processed", "unknown"
            risk_level = "medium"
        elif gt_origin == "ai":
            origin_label, manip_label = "ai_likely", "channel_processed"
            attack_hint = _attack_hint_from_row(row, "voice_conversion")
            risk_level = "medium"
        else:
            origin_label, manip_label, attack_hint = "uncertain", "channel_processed", "unknown"
            risk_level = "medium"
    elif manip == "whatsapp_compressed":
        origin_label = "human_likely" if gt_origin == "human" else "ai_likely" if gt_origin == "ai" else "uncertain"
        manip_label = "platform_compressed"
        platform = "whatsapp" if platform in {"", "none"} else platform
        risk_level = "medium"
    elif manip == "youtube_broadcast":
        origin_label = "human_likely" if gt_origin == "human" else "ai_likely" if gt_origin == "ai" else "uncertain"
        manip_label = "platform_compressed"
        risk_level = "medium"
    elif manip == "phone_recorded":
        origin_label = "human_likely" if gt_origin == "human" else "ai_likely" if gt_origin == "ai" else "uncertain"
        manip_label = "channel_processed"
        risk_level = "medium"
    elif manip == "edited_spliced":
        origin_label = "human_likely" if gt_origin != "mixed" else "mixed_or_partial_ai"
        manip_label = "edited_or_spliced" if gt_manip != "edited" else "edited_or_spliced"
        attack_hint = "unknown"
        risk_level = "medium"
    elif manip == "partial_ai_insert":
        origin_label = "mixed_or_partial_ai"
        manip_label = "edited_or_spliced"
        attack_hint = _attack_hint_from_row(row, "voice_conversion")
        partial_bin = 1
        risk_level = "high"
    elif manip == "noisy_room":
        origin_label = "human_likely" if gt_origin == "human" else "ai_likely" if gt_origin == "ai" else "uncertain"
        manip_label = "noisy_low_quality"
        risk_level = "medium"
    else:
        origin_label = origin_label or "uncertain"
        manip_label = manip_label or "uncertain"
        attack_hint = attack_hint if attack_hint in ALLOWED_ATTACK_HINT else "unknown"
        risk_level = risk_level if risk_level in ALLOWED_RISK else "inconclusive"

    if manip_label == "environment_mismatch" and manip == "edited_spliced":
        manip_label = "edited_or_spliced"

    origin_binary = {"human": "human", "ai": "ai", "mixed": "mixed"}.get(gt_origin, "unknown")
    if origin_label == "uncertain":
        origin_binary = "unknown"

    manip_binary = "clean" if manip_label == "clean_original" and manip == "clean_direct" else "manipulated"
    if manip_label in {"uncertain", "noisy_low_quality"} or gt_manip == "unknown":
        manip_binary = "uncertain"

    return {
        "origin_label": origin_label,
        "manipulation_label": manip_label,
        "attack_hint": attack_hint,
        "risk_level": risk_level if risk_level in ALLOWED_RISK else "inconclusive",
        "origin_binary": origin_binary,
        "manipulation_binary": manip_binary,
        "partial_fabrication_binary": partial_bin,
        "platform": platform,
    }


def _review_and_training_flags(row: dict, audio_exists: bool) -> dict:
    product_status = str(row.get("product_status", "")).strip().lower()
    manip = str(row.get("manipulation_type", "")).strip().lower()
    has_ts = has_valid_suspicious_timestamps(row.get("suspicious_start_time"), row.get("suspicious_end_time"))

    exclusion_reason = ""
    review_status = "approved"
    label_confidence = "high"

    if not audio_exists:
        review_status = "rejected"
        label_confidence = "low"
        exclusion_reason = "audio_not_found"
    elif manip == "partial_ai_insert" and not has_ts:
        review_status = "needs_review"
        label_confidence = "low"
        exclusion_reason = "missing_partial_fabrication_timestamps"
    elif product_status in PRODUCT_STATUSES_NEED_REVIEW:
        review_status = "needs_review"
        label_confidence = "medium" if product_status == "clean_human_borderline" else "low"
        if product_status == "partial_not_evaluated_missing_timestamp":
            exclusion_reason = "missing_partial_fabrication_timestamps"
    elif product_status.endswith("_missed") and not parse_bool(row.get("segment_suspicious")):
        label_confidence = "medium"
    elif str(row.get("origin_label", "")) == "uncertain":
        review_status = "needs_review"
        label_confidence = "low"

    # Phase 7A controlled set: never use for fine-tuning (holdout/diagnostic only).
    use_for_training = False
    use_for_validation = review_status == "approved"
    use_for_testing = True

    return {
        "review_status": review_status,
        "label_confidence": label_confidence,
        "use_for_training": use_for_training,
        "use_for_validation": use_for_validation,
        "use_for_testing": use_for_testing,
        "exclusion_reason": exclusion_reason,
        "dataset_role": CONTROLLED_HOLDOUT_ROLE,
        "training_readiness": CONTROLLED_HOLDOUT_READINESS,
        "training_warning": CONTROLLED_HOLDOUT_WARNING,
    }


def _segment_parent_fields(row: pd.Series | dict) -> dict:
    """File-level labels attached to each segment row."""
    return {
        "parent_origin_label": row.get("origin_label", ""),
        "parent_manipulation_label": row.get("manipulation_label", ""),
        "parent_attack_hint": row.get("attack_hint", ""),
        "parent_risk_level": row.get("risk_level", ""),
    }


def _sample_weight(row: dict) -> float:
    ps = str(row.get("product_status", "")).lower()
    if "partial_fabrication" in ps or str(row.get("manipulation_type", "")).lower() == "partial_ai_insert":
        return 2.0
    if ps == "clean_human_borderline":
        return 1.2
    if ps == "processed_human_manipulation_detected" and parse_bool(row.get("origin_confusion")):
        return 1.3
    if "segment_suspicious" in ps or parse_bool(row.get("file_level_missed_but_segment_suspicious")):
        return 1.5
    if ps in {"direct_ai_missed", "direct_ai_file_level_missed_but_segment_suspicious"}:
        return 1.5
    return 1.0


def _split_suggestion(row: dict) -> str:
    if str(row.get("review_status", "")) != "approved":
        return "test_holdout"
    if str(row.get("priority", "")).upper() == "P0":
        return "validation_candidate"
    return "test_holdout"


def build_file_level_rows(manifest: pd.DataFrame, product: pd.DataFrame, repo_root: Path) -> pd.DataFrame:
    product_idx = product.drop_duplicates(subset=["test_id"]).set_index("test_id", drop=False)

    rows = []
    for _, mrow in manifest.iterrows():
        row = mrow.to_dict()
        test_id = str(row.get("test_id", "")).strip()
        if test_id in product_idx.index:
            prow = product_idx.loc[test_id]
            if isinstance(prow, pd.DataFrame):
                prow = prow.iloc[0]
            for col in product.columns:
                if col == "test_id":
                    continue
                val = prow[col]
                if pd.notna(val):
                    row[col] = val

        audio_rel = str(row.get("audio_path", "")).strip()
        audio_path = _resolve_audio(audio_rel, repo_root)
        meta = _probe_audio(audio_path)

        labels = normalize_labels(row)
        flags = _review_and_training_flags(row, audio_path.is_file())

        filename = Path(audio_rel).name
        speaker_id = f"{row.get('speaker_type', 'unknown')}_{row.get('language', 'unknown')}"

        file_row = {
            "test_id": row.get("test_id", ""),
            "audio_path": audio_rel,
            "filename": filename,
            "duration": meta["duration"],
            "sample_rate": meta["sample_rate"],
            "channels": meta.get("channels", ""),
            "priority": row.get("priority", ""),
            "language": row.get("language", ""),
            "speaker_type": row.get("speaker_type", ""),
            "speaker_id": speaker_id,
            "device_chain": row.get("device_chain", ""),
            "platform": labels["platform"],
            "recording_condition": row.get("manipulation_type", ""),
            "source_origin": row.get("source_origin", ""),
            "manipulation_type": row.get("manipulation_type", ""),
            "ground_truth_origin": row.get("ground_truth_origin", ""),
            "ground_truth_manipulation": row.get("ground_truth_manipulation", ""),
            "origin_label": labels["origin_label"],
            "manipulation_label": labels["manipulation_label"],
            "attack_hint": labels["attack_hint"],
            "risk_level": labels["risk_level"],
            "origin_binary": labels["origin_binary"],
            "manipulation_binary": labels["manipulation_binary"],
            "partial_fabrication_binary": labels["partial_fabrication_binary"],
            "partial_fabrication_detected": parse_bool(row.get("partial_fabrication_detected")),
            "suspicious_start_time": row.get("suspicious_start_time", ""),
            "suspicious_end_time": row.get("suspicious_end_time", ""),
            "expected_forensic_result": row.get("expected_forensic_result", row.get("notes", "")),
            "notes": row.get("notes", ""),
            "prediction": row.get("prediction", ""),
            "decision_score": row.get("decision_score", ""),
            "effective_threshold": row.get("effective_threshold", ""),
            "confidence": row.get("confidence", ""),
            "attack_type": row.get("attack_type", ""),
            "attack_type_conf": row.get("attack_type_conf", ""),
            "bonafide_prob": row.get("bonafide_prob", ""),
            "synthesis_prob": row.get("synthesis_prob", ""),
            "conversion_prob": row.get("conversion_prob", ""),
            "replay_prob": row.get("replay_prob", ""),
            "product_status": row.get("product_status", ""),
            "origin_confusion": row.get("origin_confusion", ""),
            "manipulation_detected": row.get("manipulation_detected", ""),
            "segment_suspicious": row.get("segment_suspicious", ""),
            "file_level_missed_but_segment_suspicious": row.get("file_level_missed_but_segment_suspicious", ""),
            "suspicious_chunk_ratio": row.get("suspicious_chunk_ratio", ""),
            "max_chunk_spoof": row.get("max_chunk_spoof", ""),
            "inside_region_dominant_attack": row.get("inside_region_dominant_attack", ""),
            "partial_region_detected": row.get("partial_region_detected", ""),
            "final_product_interpretation": row.get("final_product_interpretation", ""),
            "label_source": "manual_phase7a",
            **flags,
            "audio_exists": audio_path.is_file(),
        }
        rows.append(file_row)

    return pd.DataFrame(rows)


def build_segment_labels(file_df: pd.DataFrame) -> pd.DataFrame:
    segments = []
    for _, row in file_df.iterrows():
        test_id = str(row["test_id"])
        audio_path = row["audio_path"]
        duration = _to_float(row.get("duration"))
        manip = str(row.get("manipulation_type", "")).lower()
        has_ts = has_valid_suspicious_timestamps(row.get("suspicious_start_time"), row.get("suspicious_end_time"))

        parent = _segment_parent_fields(row)

        if manip == "partial_ai_insert" and has_ts:
            t0 = 0.0
            t1 = _to_float(row["suspicious_start_time"])
            t2 = _to_float(row["suspicious_end_time"])
            t3 = duration if duration is not None else t2

            parent_attack = row.get("attack_hint", "synthesis")
            if parent_attack not in {"synthesis", "voice_conversion"}:
                parent_attack = "synthesis"
            insert_attack = parent_attack
            if str(row.get("inside_region_dominant_attack", "")).lower() in {"synthesis", "conversion"}:
                insert_attack = (
                    "voice_conversion"
                    if str(row.get("inside_region_dominant_attack", "")).lower() == "conversion"
                    else "synthesis"
                )

            segments.extend(
                [
                    {
                        "test_id": test_id,
                        "audio_path": audio_path,
                        "segment_id": f"{test_id}_pre_real",
                        "segment_start_time": t0,
                        "segment_end_time": t1,
                        "segment_label": "pre_real_segment",
                        "segment_origin_label": "human_likely",
                        "segment_manipulation_label": "clean_original",
                        "segment_attack_hint": "bonafide",
                        "segment_risk_level": "low",
                        **parent,
                        "source": "phase7b_rules",
                        "notes": "Real audio before inserted region",
                        "use_for_training": False,
                    },
                    {
                        "test_id": test_id,
                        "audio_path": audio_path,
                        "segment_id": f"{test_id}_inserted_ai",
                        "segment_start_time": t1,
                        "segment_end_time": t2,
                        "segment_label": "inserted_ai_segment",
                        "segment_origin_label": "ai_likely",
                        "segment_manipulation_label": "edited_or_spliced",
                        "segment_attack_hint": insert_attack,
                        "segment_risk_level": "high",
                        **parent,
                        "source": "phase7b_rules",
                        "notes": "Ground-truth inserted AI/synthetic region",
                        "use_for_training": False,
                    },
                    {
                        "test_id": test_id,
                        "audio_path": audio_path,
                        "segment_id": f"{test_id}_post_real",
                        "segment_start_time": t2,
                        "segment_end_time": t3,
                        "segment_label": "post_real_segment",
                        "segment_origin_label": "human_likely",
                        "segment_manipulation_label": "clean_original",
                        "segment_attack_hint": "bonafide",
                        "segment_risk_level": "low",
                        **parent,
                        "source": "phase7b_rules",
                        "notes": "Real audio after inserted region",
                        "use_for_training": False,
                    },
                ]
            )
        elif row.get("review_status") == "approved" and duration is not None:
            manip_label = row.get("manipulation_label", "")
            seg_manip = "full_file_manipulated" if manip_label != "clean_original" else "full_file_clean"
            segments.append(
                {
                    "test_id": test_id,
                    "audio_path": audio_path,
                    "segment_id": f"{test_id}_full",
                    "segment_start_time": 0.0,
                    "segment_end_time": duration,
                    "segment_label": seg_manip,
                    "segment_origin_label": row.get("origin_label", ""),
                    "segment_manipulation_label": manip_label,
                    "segment_attack_hint": row.get("attack_hint", ""),
                    "segment_risk_level": row.get("risk_level", ""),
                    **parent,
                    "source": "phase7b_rules",
                    "notes": "Whole-file segment for non-partial sample",
                    "use_for_training": False,
                }
            )
    return pd.DataFrame(segments)


def build_rejected_or_review(file_df: pd.DataFrame) -> pd.DataFrame:
    mask = (file_df["review_status"] != "approved") | (file_df["exclusion_reason"].astype(str).str.len() > 0)
    sub = file_df[mask].copy()
    if sub.empty:
        return pd.DataFrame(columns=["test_id", "audio_path", "review_status", "exclusion_reason", "product_status", "notes"])
    return sub[
        ["test_id", "audio_path", "review_status", "exclusion_reason", "product_status", "notes", "manipulation_type"]
    ]


def build_training_preview(file_df: pd.DataFrame, repo_root: Path) -> pd.DataFrame:
    """
    Future-format preview for Phase 7C — NOT an actual training manifest.
    All rows: use_for_training=false (controlled holdout). eligible_for_future_training
    marks rows that would qualify in a larger dataset.
    """
    rows = []
    for _, r in file_df.iterrows():
        audio_ok = _resolve_audio(str(r["audio_path"]), repo_root).is_file()
        eligible = (
            str(r.get("review_status", "")) == "approved"
            and str(r.get("label_confidence", "")) in {"high", "medium"}
            and audio_ok
        )
        rows.append(
            {
                "audio_path": r["audio_path"],
                "test_id": r["test_id"],
                "origin_binary": r["origin_binary"],
                "manipulation_binary": r["manipulation_binary"],
                "partial_fabrication_binary": r["partial_fabrication_binary"],
                "origin_label": r["origin_label"],
                "manipulation_label": r["manipulation_label"],
                "attack_hint": r["attack_hint"],
                "risk_level": r["risk_level"],
                "language": r["language"],
                "speaker_type": r["speaker_type"],
                "device_chain": r["device_chain"],
                "platform": r["platform"],
                "recording_condition": r["recording_condition"],
                "duration": r["duration"],
                "sample_rate": r["sample_rate"],
                "dataset_role": r.get("dataset_role", CONTROLLED_HOLDOUT_ROLE),
                "training_readiness": r.get("training_readiness", CONTROLLED_HOLDOUT_READINESS),
                "training_warning": r.get("training_warning", CONTROLLED_HOLDOUT_WARNING),
                "eligible_for_future_training": eligible,
                "use_for_training": False,
                "split_suggestion": _split_suggestion(r),
                "sample_weight": _sample_weight(r),
                "holdout_training_warning": PREVIEW_ROW_WARNING,
                "notes": r.get("notes", ""),
            }
        )
    return pd.DataFrame(rows)


def write_label_mapping_rules(path: Path) -> None:
    path.write_text(
        """# Forensic Label Mapping Rules — Phase 7B

**Source:** Phase 7A manifest + product results, normalized by `prepare_forensic_dataset.py`.  
**Schema:** [PHASE7_LABEL_SCHEMA.md](../phase7/PHASE7_LABEL_SCHEMA.md)

---

## Principles

1. **Do not train on REAL/FAKE only** — use `origin_label` + `manipulation_label` (+ optional `attack_hint`, `risk_level`).
2. **Human replay** → `origin_label=human_likely`, `manipulation_label=replayed_or_re_recorded`, `attack_hint=replay`.
3. **Direct AI** → `origin_label=ai_likely`, `manipulation_label=clean_original`.
4. **Partial AI insert** → `origin_label=mixed_or_partial_ai`, `partial_fabrication_binary=1`, segment rows for pre/insert/post.
5. **Borderline / missing partial timestamps** → `review_status=needs_review`.
6. **Phase 7A T1–T5 set** → `dataset_role=controlled_holdout`, **`use_for_training=false` always**.

---

## Condition mapping

| manipulation_type | ground_truth_origin | origin_label | manipulation_label | attack_hint (default) |
|-------------------|---------------------|--------------|----------------------|------------------------|
| clean_direct | human | human_likely | clean_original | bonafide |
| clean_direct | ai | ai_likely | clean_original | synthesis / voice_conversion |
| human_replay | human | human_likely | replayed_or_re_recorded | replay |
| ai_replay | ai | ai_likely | replayed_or_re_recorded | replay |
| mixer_processed | human | human_likely | channel_processed | **unknown** (not voice_conversion) |
| mixer_processed | ai | ai_likely | channel_processed | synthesis / voice_conversion |
| whatsapp_compressed | * | human/ai_likely | platform_compressed | context-based |
| edited_spliced | human | human_likely | edited_or_spliced | unknown |
| partial_ai_insert | mixed | mixed_or_partial_ai | edited_or_spliced | voice_conversion / synthesis |
| noisy_room | * | human/ai_likely | noisy_low_quality | unknown |

---

## Risk level adjustments

| Signal | risk_level |
|--------|------------|
| clean_human_borderline (product) | inconclusive |
| direct_ai_detected | high |
| direct_ai_file_level_missed_but_segment_suspicious | medium |
| partial insert region (segment) | high |
| human replay FAKE | medium–high |

---

## Review / training flags

| Condition | review_status | use_for_training | use_for_validation |
|-----------|---------------|------------------|---------------------|
| Approved (Phase 7A holdout) | approved | **false** | true |
| partial_ai_insert, no timestamps | needs_review | false | false |
| clean_human_borderline | needs_review | false | false |
| audio missing | rejected | false | false |

`forensic_training_manifest_preview.csv` is a **future CSV format example** only — not actual 7C training data.

---

## Binary preview fields

- `origin_binary`: human | ai | mixed | unknown (from ground truth)
- `manipulation_binary`: clean | manipulated | uncertain
- `partial_fabrication_binary`: 0 | 1

""",
        encoding="utf-8",
    )


def write_gap_analysis(path: Path, file_df: pd.DataFrame) -> None:
    n = len(file_df)
    path.write_text(
        f"""# Forensic Dataset Gap Analysis — Phase 7B

**Current labeled files:** {n} (Phase 7A controlled set)  
**Verdict:** Valid as **holdout / diagnostic** set and label-schema prototype — **not** sufficient for Phase 7C fine-tuning.

---

## 1. Current dataset size and limitation

- Only **{n}** controlled files (T1–T5).
- Strong **pairing** across conditions but **no speaker-independent scale**.
- Phase 7A product analysis: manipulation-sensitive model with **origin confusion** on replay/processed human.
- **Keep this set as test_holdout** — do not use as main training corpus.

---

## 2. Direct AI gap

**7A finding:** T1.3, T1.5, T3.1 — file-level REAL (~0.43 vote) but **max_chunk_spoof ≈ 1.0** (`direct_ai_file_level_missed_but_segment_suspicious`).

**Collect next:**
- 50–100 **direct AI** clips (TTS, clone, WAV) across English + Urdu
- Include obvious and subtle synthetics
- Label: `origin_label=ai_likely`, `manipulation_label=clean_original`

---

## 3. Clean human Urdu/Pakistani gap

**7A finding:** T1.1 borderline at threshold (FAKE 0.70 vs 0.70) — review, not confirmed FP.

**Collect next:**
- 50–100 **clean direct human** Urdu/Pakistani mobile + USB recordings
- 20–30 s speech, minimal processing
- Label: `human_likely`, `clean_original`, `risk_level=low`

---

## 4. Human replay / processed human gap

**7A finding:** T2.x often FAKE (useful **manipulation** signal, not AI origin).

**Collect next:**
- 30–50 human replay chains (laptop→phone, Bluetooth, phone-to-phone)
- 30–50 mixer/channel processed **human** clips
- Labels: `human_likely` + `replayed_or_re_recorded` or `channel_processed`

---

## 5. AI replay gap

**7A finding:** T3.2–T3.4 detected; **T3.5** file-level miss, segment suspicious.

**Collect next:**
- 30–50 AI→speaker→phone replay samples
- Label: `ai_likely`, `replayed_or_re_recorded`

---

## 6. Partial fabrication / segment-label gap

**7A finding:** **T5_FAB_001** successful segment detection (14–21 s). **T4.3** timestamps have now been filled and validated (35.0–58.0 s; `partial_eval_status=evaluated`).

**Action:**
- Continue collecting **20–40** partial AI insertion samples with **mandatory** `suspicious_start_time` / `suspicious_end_time` in the manifest
- Use T4.3 and T5_FAB_001 as reference rows for segment labeling (pre / insert / post)

---

## 7. WhatsApp / social compression gap

Current: limited rows (e.g. T4.5). Target **30–50** human + AI through WhatsApp/codec chains.

---

## 8. Phone-recorded audio gap

Add `phone_recorded` manipulation_type samples — native phone capture, 30+ files.

---

## 9. YouTube / broadcast gap

Add `youtube_broadcast` chains when available — long-form + broadcast processing.

---

## 10. Minimum recommended dataset before fine-tuning (Phase 7C)

| Category | Minimum count |
|----------|---------------|
| Clean human | 50–100 |
| Direct AI | 50–100 |
| Human replay | 30–50 |
| AI replay | 30–50 |
| Mixer/channel processed | 30–50 |
| WhatsApp/social compressed | 30–50 |
| Edited/spliced | 30–50 |
| Partial AI insertion (with timestamps) | 20–40 |
| **Urdu/Pakistani speakers** | **Prioritize across all categories** |

**Holdout:** Current {n} Phase 7A files remain **controlled evaluation** — not training bulk.

---

## Next action

1. Expand manifest with gap categories above (prioritize partial inserts with timestamps).
2. Sign off Phase 7B label schema → start **7C** planning only after minimum collection counts are met.
3. Keep the current 25-file Phase 7A set as **controlled_holdout** (not training data).

""",
        encoding="utf-8",
    )


def write_dataset_readme(path: Path, file_df: pd.DataFrame, preview_df: pd.DataFrame) -> None:
    n_preview = len(preview_df)
    n_eligible = int(preview_df.get("eligible_for_future_training", pd.Series(dtype=bool)).sum()) if len(preview_df) else 0
    n_train_false = int((file_df["use_for_training"] == False).sum()) if "use_for_training" in file_df.columns else len(file_df)
    path.write_text(
        f"""# Phase 7B Forensic Dataset

**Status:** Label preparation complete (no training in this phase).

## Critical safety rule

**All {len(file_df)} Phase 7A/T1–T5 files are `controlled_holdout`.**

- `use_for_training` = **false** on every row (`{n_train_false}/{len(file_df)}` verified in file-level CSV)
- `training_readiness` = `not_ready_for_training`
- Use for **validation / testing / label schema design** only
- **Do not fine-tune** on this set (Phase 7C needs a larger collected dataset)

## Contents

| File | Description |
|------|-------------|
| `forensic_labeled_master.csv` | Joined manifest + 7A product + normalized labels |
| `forensic_file_level_labels.csv` | One row per audio file |
| `forensic_segment_labels.csv` | Segment rows with parent_* context columns |
| `forensic_training_manifest_preview.csv` | **Format preview only** ({n_preview} rows; {n_eligible} eligible_for_future_training; **use_for_training always false**) |
| `rejected_or_needs_review.csv` | Current review-required files (e.g. T1.1, T4.1 — needs_review, not approved) |
| `forensic_dataset_validation_report.md` | Validation summary |
| `forensic_dataset_gap_analysis.md` | What to collect before 7C |
| `label_mapping_rules.md` | Mapping documentation |

## Warning

The Phase 7A set has only **{len(file_df)}** files. It is **not** enough for fine-tuning. See gap analysis for minimum counts before Phase 7C.

## Regenerate

```text
python code/phase7/prepare_forensic_dataset.py ^
  --manifest reports/phase7/phase7_forensic_tests/forensic_test_manifest.csv ^
  --product_results reports/phase7/phase7_forensic_tests/results/forensic_test_results_product.csv ^
  --output_dir reports/phase7/phase7_dataset
```

```text
python code/phase7/validate_forensic_labels.py ^
  --input reports/phase7/phase7_dataset/forensic_labeled_master.csv ^
  --output reports/phase7/phase7_dataset/forensic_dataset_validation_report.md ^
  --allow_warnings
```

""",
        encoding="utf-8",
    )


def prepare_dataset(manifest_path: Path, product_path: Path, output_dir: Path, repo_root: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = pd.read_csv(manifest_path, low_memory=False)
    product = pd.read_csv(product_path, low_memory=False)

    file_df = build_file_level_rows(manifest, product, repo_root)
    if "audio_exists" in file_df.columns:
        file_df = file_df.drop(columns=["audio_exists"])

    segment_df = build_segment_labels(file_df)
    rejected_df = build_rejected_or_review(file_df)
    preview_df = build_training_preview(file_df, repo_root)

    master_df = file_df.copy()

    file_df.to_csv(output_dir / "forensic_file_level_labels.csv", index=False)
    segment_df.to_csv(output_dir / "forensic_segment_labels.csv", index=False)
    master_df.to_csv(output_dir / "forensic_labeled_master.csv", index=False)
    preview_df.to_csv(output_dir / "forensic_training_manifest_preview.csv", index=False)
    rejected_df.to_csv(output_dir / "rejected_or_needs_review.csv", index=False)

    write_label_mapping_rules(output_dir / "label_mapping_rules.md")
    write_gap_analysis(output_dir / "forensic_dataset_gap_analysis.md", file_df)
    write_dataset_readme(output_dir / "README.md", file_df, preview_df)

    return {
        "file_df": file_df,
        "segment_df": segment_df,
        "preview_df": preview_df,
        "rejected_df": rejected_df,
    }


def print_summary(stats: dict) -> None:
    file_df = stats["file_df"]
    preview_df = stats["preview_df"]
    print("")
    print("=== Phase 7B dataset preparation ===")
    print(f"Total files: {len(file_df)}")
    print(f"Approved: {(file_df['review_status'] == 'approved').sum()}")
    print(f"Needs review: {(file_df['review_status'] == 'needs_review').sum()}")
    print(f"Rejected: {(file_df['review_status'] == 'rejected').sum()}")
    print(f"Format preview rows: {len(preview_df)} (use_for_training=false on all)")
    print(f"use_for_training=true rows: {(file_df['use_for_training'] == True).sum()} (must be 0)")
    if "eligible_for_future_training" in preview_df.columns:
        print(f"eligible_for_future_training: {preview_df['eligible_for_future_training'].sum()}")
    missing_audio = int((~file_df['audio_path'].apply(lambda p: _resolve_audio(str(p), _REPO_ROOT).is_file())).sum())
    print(f"Missing audio: {missing_audio}")
    partial_missing_ts = int(
        (
            (file_df["manipulation_type"].astype(str).str.lower() == "partial_ai_insert")
            & ~file_df.apply(
                lambda r: has_valid_suspicious_timestamps(r.get("suspicious_start_time"), r.get("suspicious_end_time")),
                axis=1,
            )
        ).sum()
    )
    print(f"Partial rows missing timestamps: {partial_missing_ts}")
    print("")
    print("Recommended next action:")
    print("  1. Run validate_forensic_labels.py")
    print("  2. Collect gap data per forensic_dataset_gap_analysis.md before Phase 7C.")
    print("  3. Keep Phase 7A set as controlled_holdout (use_for_training=false).")
    print("")


def parse_args():
    p = argparse.ArgumentParser(description="Phase 7B — prepare forensic dataset labels")
    p.add_argument("--manifest", type=str, required=True)
    p.add_argument("--product_results", type=str, required=True)
    p.add_argument("--output_dir", type=str, default="reports/phase7/phase7_dataset")
    p.add_argument("--repo_root", type=str, default=str(_REPO_ROOT))
    return p.parse_args()


def main():
    args = parse_args()
    stats = prepare_dataset(
        Path(args.manifest),
        Path(args.product_results),
        Path(args.output_dir),
        Path(args.repo_root),
    )
    print_summary(stats)


if __name__ == "__main__":
    main()
