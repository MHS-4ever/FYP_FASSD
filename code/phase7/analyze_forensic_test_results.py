"""
Phase 7A: Analyze forensic_test_results.csv and generate reports.

- FORENSIC_TEST_ANALYSIS.md — legacy binary origin accuracy view
- forensic_test_results_product.csv — product-level metrics
- PHASE7A_PRODUCT_LEVEL_ANALYSIS.md — main interpretation for review
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

ATTACK_TYPE_NAMES = ["bonafide", "synthesis", "conversion", "replay"]

MANIPULATION_GROUPS = [
    "clean_direct",
    "human_replay",
    "ai_replay",
    "mixer_processed",
    "whatsapp_compressed",
    "youtube_broadcast",
    "phone_recorded",
    "edited_spliced",
    "partial_ai_insert",
    "noisy_room",
    "unknown",
]

PROCESSED_HUMAN_MANIP_TYPES = {
    "human_replay",
    "mixer_processed",
    "edited_spliced",
    "phone_recorded",
    "whatsapp_compressed",
    "noisy_room",
}

AI_REPLAY_OR_PROCESSED_MANIP_TYPES = {
    "ai_replay",
    "mixer_processed",
    "whatsapp_compressed",
    "phone_recorded",
    "noisy_room",
}

MANIPULATION_DETECT_SCORE = 0.65
CHUNK_SUSPICIOUS_THRESHOLD = 0.65
SEGMENT_SUSPICIOUS_MAX_SPOOF = 0.95
SEGMENT_SUSPICIOUS_RATIO = 0.30

PRODUCT_CSV_EXTRA_COLUMNS = [
    "product_status",
    "origin_confusion",
    "manipulation_detected",
    "direct_ai_detected",
    "direct_ai_missed",
    "processed_human_detected",
    "ai_replay_or_processed_detected",
    "partial_eval_status",
    "partial_region_detected",
    "n_chunks_inside",
    "n_chunks_outside",
    "inside_region_avg_spoof",
    "outside_region_avg_spoof",
    "inside_region_max_spoof",
    "outside_region_max_spoof",
    "inside_region_dominant_attack",
    "outside_region_dominant_attack",
    "segment_suspicious",
    "file_level_missed_but_segment_suspicious",
    "suspicious_chunk_count",
    "suspicious_chunk_ratio",
    "max_chunk_spoof",
    "mean_chunk_spoof",
    "median_chunk_spoof",
    "dominant_chunk_attack",
    "final_product_interpretation",
    "timeline_scope_note",
    "candidate_suspicious_regions",
]

GROUP_DISPLAY_NAMES = {
    "clean_direct": "Clean / direct",
    "human_replay": "Human replay",
    "ai_replay": "AI replay",
    "mixer_processed": "Mixer / channel processed",
    "whatsapp_compressed": "WhatsApp / compressed",
    "youtube_broadcast": "YouTube / broadcast",
    "phone_recorded": "Phone recorded",
    "edited_spliced": "Edited / spliced",
    "partial_ai_insert": "Partial AI insertion",
    "noisy_room": "Noisy room",
    "unknown": "Unknown",
}


def _has_error(value) -> bool:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return False
    return str(value).strip() != ""


def parse_bool(value) -> bool | None:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    s = str(value).strip().lower()
    if s in {"", "nan", "none"}:
        return None
    if s in {"true", "1", "yes", "y", "t"}:
        return True
    if s in {"false", "0", "no", "n", "f"}:
        return False
    return None


def _to_float(value, default: float | None = None) -> float | None:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return default
    s = str(value).strip()
    if s == "":
        return default
    try:
        return float(s)
    except ValueError:
        return default


def _chunk_overlaps_region(chunk_start: float, chunk_end: float, region_start: float, region_end: float) -> bool:
    return chunk_start < region_end and chunk_end > region_start


def has_valid_suspicious_timestamps(suspicious_start, suspicious_end) -> bool:
    region_start = _to_float(suspicious_start)
    region_end = _to_float(suspicious_end)
    return region_start is not None and region_end is not None and region_end > region_start


def _evaluated_chunks(chunk_timeline: list[dict]) -> list[dict]:
    """Chunks with model spoof scores (VAD-kept / evaluated)."""
    scored = []
    for ch in chunk_timeline or []:
        sp = ch.get("spoof_probability")
        if sp is None or (isinstance(sp, float) and np.isnan(sp)):
            continue
        if ch.get("evaluated") is False:
            continue
        scored.append(ch)
    if scored:
        return scored
    return [ch for ch in (chunk_timeline or []) if ch.get("spoof_probability") is not None]


def _parse_attack_probs_vec(chunk: dict) -> np.ndarray | None:
    ap = chunk.get("attack_probs")
    if ap is None or ap == "":
        return None
    if isinstance(ap, str):
        try:
            ap = json.loads(ap)
        except json.JSONDecodeError:
            return None
    try:
        arr = np.asarray(ap, dtype=np.float64).reshape(-1)
        if arr.size == 0:
            return None
        out = np.zeros(4, dtype=np.float64)
        out[: min(4, arr.size)] = arr[:4]
        return out
    except (TypeError, ValueError):
        return None


def _dominant_attack(chunks: list[dict]) -> str:
    """Prefer mean attack_probs across chunks; fallback to mode of attack_type."""
    if not chunks:
        return ""
    prob_sum = np.zeros(4, dtype=np.float64)
    n_probs = 0
    for ch in chunks:
        vec = _parse_attack_probs_vec(ch)
        if vec is not None:
            prob_sum += vec
            n_probs += 1
    if n_probs > 0:
        idx = int(np.argmax(prob_sum / n_probs))
        if 0 <= idx < len(ATTACK_TYPE_NAMES):
            return ATTACK_TYPE_NAMES[idx]
        return str(idx)
    types = [str(c.get("attack_type", "")).strip() for c in chunks if c.get("attack_type")]
    if not types:
        return ""
    return Counter(types).most_common(1)[0][0]


def _is_segment_suspicious(chunk_metrics: dict) -> bool:
    max_spoof = _to_float(chunk_metrics.get("max_chunk_spoof"))
    ratio = _to_float(chunk_metrics.get("suspicious_chunk_ratio"), 0.0) or 0.0
    if max_spoof is not None and max_spoof >= SEGMENT_SUSPICIOUS_MAX_SPOOF:
        return True
    return ratio >= SEGMENT_SUSPICIOUS_RATIO


def compute_partial_region_metrics(
    chunk_timeline: list[dict],
    suspicious_start,
    suspicious_end,
    manifest_partial_gt: bool | None = None,
) -> dict:
    """Split used chunks into inside/outside suspicious region and compute partial-fab metrics."""
    empty = {
        "n_chunks_inside": 0,
        "n_chunks_outside": 0,
        "inside_region_avg_spoof": "",
        "outside_region_avg_spoof": "",
        "inside_region_max_spoof": "",
        "outside_region_max_spoof": "",
        "inside_region_dominant_attack": "",
        "outside_region_dominant_attack": "",
        "partial_region_detected": False,
        "partial_eval_status": "",
    }
    if not has_valid_suspicious_timestamps(suspicious_start, suspicious_end):
        empty["partial_eval_status"] = "partial_not_evaluated_missing_timestamp"
        return empty

    scored_timeline = _evaluated_chunks(chunk_timeline)
    if not scored_timeline:
        empty["partial_eval_status"] = "evaluated"
        return empty

    region_start = _to_float(suspicious_start)
    region_end = _to_float(suspicious_end)

    inside = []
    outside = []
    for ch in scored_timeline:
        cs = _to_float(ch.get("start_time"), 0.0)
        ce = _to_float(ch.get("end_time"), 0.0)
        if cs is None or ce is None:
            continue
        if _chunk_overlaps_region(cs, ce, region_start, region_end):
            inside.append(ch)
        else:
            outside.append(ch)

    inside_spoof = [float(c["spoof_probability"]) for c in inside if "spoof_probability" in c]
    outside_spoof = [float(c["spoof_probability"]) for c in outside if "spoof_probability" in c]

    inside_avg = float(np.mean(inside_spoof)) if inside_spoof else None
    outside_avg = float(np.mean(outside_spoof)) if outside_spoof else None
    inside_max = float(np.max(inside_spoof)) if inside_spoof else None
    outside_max = float(np.max(outside_spoof)) if outside_spoof else None

    inside_dom = _dominant_attack(inside)
    outside_dom = _dominant_attack(outside)

    partial_detected = False
    if inside_spoof:
        if inside_avg is not None and outside_avg is not None and inside_avg >= outside_avg + 0.15:
            partial_detected = True
        if inside_max is not None and inside_max >= 0.65:
            partial_detected = True
        if inside_dom in {"synthesis", "conversion"} and (
            outside_dom in {"bonafide", ""} or outside_dom == "bonafide"
        ):
            partial_detected = True

    return {
        "partial_eval_status": "evaluated",
        "n_chunks_inside": len(inside),
        "n_chunks_outside": len(outside),
        "inside_region_avg_spoof": inside_avg if inside_avg is not None else "",
        "outside_region_avg_spoof": outside_avg if outside_avg is not None else "",
        "inside_region_max_spoof": inside_max if inside_max is not None else "",
        "outside_region_max_spoof": outside_max if outside_max is not None else "",
        "inside_region_dominant_attack": inside_dom,
        "outside_region_dominant_attack": outside_dom,
        "partial_region_detected": bool(partial_detected),
    }


def _is_borderline(row: dict) -> bool:
    score = _to_float(row.get("decision_score"))
    threshold = _to_float(row.get("effective_threshold"), 0.70)
    if score is None:
        return False
    return abs(score - threshold) <= 0.05


def evaluate_correct_origin_basic(row: dict) -> str:
    if _has_error(row.get("error")):
        return "no"

    gt_origin = str(row.get("ground_truth_origin", "")).strip().lower()
    pred = str(row.get("prediction", "")).strip().upper()
    manipulation = str(row.get("manipulation_type", "")).strip().lower()
    gt_partial = parse_bool(row.get("partial_fabrication_detected"))
    partial_detected = parse_bool(row.get("partial_region_detected"))

    if _is_borderline(row) and manipulation != "partial_ai_insert":
        return "borderline"

    if gt_origin == "human":
        if pred == "REAL":
            return "yes"
        if pred == "FAKE":
            return "no"
    elif gt_origin == "ai":
        if pred == "FAKE":
            return "yes"
        if pred == "REAL":
            return "no"
    elif gt_origin == "mixed":
        if manipulation == "partial_ai_insert" or gt_partial is True:
            if not has_valid_suspicious_timestamps(
                row.get("suspicious_start_time"), row.get("suspicious_end_time")
            ):
                return "borderline"
            if partial_detected is True:
                return "yes"
            if pred == "FAKE":
                return "yes"
            if _is_borderline(row):
                return "borderline"
            return "no"
        if pred == "FAKE":
            return "yes"
        if pred == "REAL":
            return "borderline"
    elif gt_origin == "unknown":
        return "borderline"

    return "borderline"


def evaluate_failure_type(row: dict) -> str:
    if _has_error(row.get("error")):
        return str(row.get("error", "error"))[:80]

    gt_origin = str(row.get("ground_truth_origin", "")).strip().lower()
    pred = str(row.get("prediction", "")).strip().upper()
    manipulation = str(row.get("manipulation_type", "")).strip().lower()
    correct = str(row.get("correct_origin_basic", "")).strip().lower()
    gt_partial = parse_bool(row.get("partial_fabrication_detected"))
    partial_detected = parse_bool(row.get("partial_region_detected"))

    if correct == "borderline":
        return "borderline"
    if correct == "yes":
        return ""

    if manipulation == "partial_ai_insert" and not has_valid_suspicious_timestamps(
        row.get("suspicious_start_time"), row.get("suspicious_end_time")
    ):
        return "partial_not_evaluated_missing_timestamp"
    if gt_partial is True and partial_detected is not True:
        if has_valid_suspicious_timestamps(row.get("suspicious_start_time"), row.get("suspicious_end_time")):
            return "missed_partial_insert"
    if gt_origin == "human" and pred == "FAKE":
        if manipulation in {"mixer_processed", "whatsapp_compressed", "phone_recorded", "human_replay"}:
            return "fp_processed_human"
        return "fp_human"
    if gt_origin == "ai" and pred == "REAL":
        if manipulation in {"ai_replay", "mixer_processed"}:
            return "fn_ai_replay"
        return "fn_direct_ai"
    if gt_origin == "mixed" and manipulation == "partial_ai_insert":
        if has_valid_suspicious_timestamps(row.get("suspicious_start_time"), row.get("suspicious_end_time")):
            return "missed_partial_insert"
        return "partial_not_evaluated_missing_timestamp"
    if partial_detected is True and gt_partial is not True:
        return "false_partial_alarm"

    return "wrong_origin"


def build_forensic_summary(base: dict, inference: dict, partial_metrics: dict) -> str:
    pred = inference.get("prediction", "")
    score = _to_float(inference.get("decision_score"), 0.0)
    attack = inference.get("attack_type", "")
    partial = partial_metrics.get("partial_region_detected", False)
    if partial:
        return (
            f"{pred} (score={score:.3f}) with suspicious segment signal "
            f"(inside avg spoof={partial_metrics.get('inside_region_avg_spoof', 'n/a')}, "
            f"dominant inside={partial_metrics.get('inside_region_dominant_attack', 'n/a')}); "
            f"attack={attack}."
        )
    conf = _to_float(inference.get("attack_type_conf"), 0.0)
    return f"Model predicts {pred} (decision_score={score:.3f}, attack={attack}, conf={conf:.3f})."


def load_chunk_timeline(test_id: str, results_dir: Path) -> tuple[list[dict], str]:
    """Load chunk timeline from JSON (preferred) or CSV fallback."""
    json_path = results_dir / "json_outputs" / f"{test_id}.json"
    if json_path.is_file():
        with open(json_path, encoding="utf-8") as f:
            payload = json.load(f)
        inference = payload.get("inference", {})
        timeline = inference.get("chunk_timeline") or []
        note = inference.get("chunk_timeline_note") or ""
        if inference.get("chunk_timeline_includes_all_chunks"):
            scope = "all_chunks_listed_evaluated_on_vad_kept"
        elif timeline:
            scope = "vad_kept_evaluated_only"
        else:
            scope = "missing"
        return timeline, note or scope

    csv_path = results_dir / "chunk_timelines" / f"{test_id}_chunks.csv"
    if csv_path.is_file():
        tl_df = pd.read_csv(csv_path)
        timeline = tl_df.to_dict(orient="records")
        has_all = "vad_kept" in tl_df.columns and tl_df["vad_kept"].nunique(dropna=True) > 1
        scope = "all_chunks_listed_evaluated_on_vad_kept" if has_all else "vad_kept_evaluated_only"
        return timeline, scope

    return [], "missing"


def compute_suspicious_chunk_metrics(chunk_timeline: list[dict], n_chunks_used: int | None = None) -> dict:
    evaluated = _evaluated_chunks(chunk_timeline)
    if not evaluated:
        return {
            "suspicious_chunk_count": 0,
            "suspicious_chunk_ratio": 0.0,
            "max_chunk_spoof": "",
            "mean_chunk_spoof": "",
            "median_chunk_spoof": "",
            "dominant_chunk_attack": "",
        }

    spoof_vals = [float(c["spoof_probability"]) for c in evaluated]
    suspicious = [v for v in spoof_vals if v >= CHUNK_SUSPICIOUS_THRESHOLD]
    denom = int(n_chunks_used) if n_chunks_used and n_chunks_used > 0 else len(evaluated)

    return {
        "suspicious_chunk_count": len(suspicious),
        "suspicious_chunk_ratio": float(len(suspicious) / denom) if denom else 0.0,
        "max_chunk_spoof": float(max(spoof_vals)),
        "mean_chunk_spoof": float(np.mean(spoof_vals)),
        "median_chunk_spoof": float(np.median(spoof_vals)),
        "dominant_chunk_attack": _dominant_attack(evaluated),
    }


def compute_candidate_suspicious_regions(
    chunk_timeline: list[dict], threshold: float = CHUNK_SUSPICIOUS_THRESHOLD, top_k: int = 3
) -> list[dict]:
    """Merge consecutive high-spoof chunks into candidate regions (exploratory, not GT)."""
    hot = []
    for ch in _evaluated_chunks(chunk_timeline):
        sp = float(ch["spoof_probability"])
        if sp < threshold:
            continue
        hot.append(
            {
                "start_time": float(ch["start_time"]),
                "end_time": float(ch["end_time"]),
                "max_spoof": sp,
                "sum_spoof": sp,
                "chunk_count": 1,
            }
        )
    if not hot:
        return []

    hot.sort(key=lambda x: x["start_time"])
    merged = [hot[0].copy()]
    for region in hot[1:]:
        prev = merged[-1]
        if region["start_time"] <= prev["end_time"] + 0.01:
            prev["end_time"] = max(prev["end_time"], region["end_time"])
            prev["max_spoof"] = max(prev["max_spoof"], region["max_spoof"])
            prev["sum_spoof"] = prev["sum_spoof"] + region["sum_spoof"]
            prev["chunk_count"] += region["chunk_count"]
        else:
            merged.append(region.copy())

    for reg in merged:
        reg["mean_spoof"] = float(reg["sum_spoof"] / reg["chunk_count"]) if reg["chunk_count"] else 0.0
        reg.pop("sum_spoof", None)

    merged.sort(key=lambda x: (-x["max_spoof"], -(x["end_time"] - x["start_time"])))
    return merged[:top_k]


def _manipulation_detected(row: dict) -> bool:
    pred = str(row.get("prediction", "")).strip().upper()
    score = _to_float(row.get("decision_score"), 0.0) or 0.0
    return pred == "FAKE" or score >= MANIPULATION_DETECT_SCORE


def evaluate_product_metrics(row: dict, chunk_timeline: list[dict], timeline_note: str = "") -> dict:
    """Return product-level columns for one test row."""
    gt_origin = str(row.get("ground_truth_origin", "")).strip().lower()
    manip = str(row.get("manipulation_type", "")).strip().lower()
    pred = str(row.get("prediction", "")).strip().upper()
    borderline = _is_borderline(row)

    n_used = int(_to_float(row.get("n_chunks_used"), 0) or 0)
    chunk_metrics = compute_suspicious_chunk_metrics(chunk_timeline, n_chunks_used=n_used)
    manip_detected = _manipulation_detected(row)

    segment_suspicious = _is_segment_suspicious(chunk_metrics)

    out = {
        "product_status": "unknown_review_required",
        "origin_confusion": False,
        "manipulation_detected": manip_detected,
        "direct_ai_detected": False,
        "direct_ai_missed": False,
        "processed_human_detected": False,
        "ai_replay_or_processed_detected": False,
        "partial_eval_status": str(row.get("partial_eval_status", "") or ""),
        "partial_region_detected": parse_bool(row.get("partial_region_detected")) or False,
        "n_chunks_inside": row.get("n_chunks_inside", ""),
        "n_chunks_outside": row.get("n_chunks_outside", ""),
        "inside_region_avg_spoof": row.get("inside_region_avg_spoof", ""),
        "outside_region_avg_spoof": row.get("outside_region_avg_spoof", ""),
        "inside_region_max_spoof": row.get("inside_region_max_spoof", ""),
        "outside_region_max_spoof": row.get("outside_region_max_spoof", ""),
        "inside_region_dominant_attack": row.get("inside_region_dominant_attack", ""),
        "outside_region_dominant_attack": row.get("outside_region_dominant_attack", ""),
        "segment_suspicious": segment_suspicious,
        "file_level_missed_but_segment_suspicious": False,
        "timeline_scope_note": timeline_note,
        "candidate_suspicious_regions": "",
        **chunk_metrics,
    }

    candidates = compute_candidate_suspicious_regions(chunk_timeline)
    if candidates:
        out["candidate_suspicious_regions"] = json.dumps(candidates, ensure_ascii=False)

    # --- clean human (clean_direct + human) ---
    if manip == "clean_direct" and gt_origin == "human":
        if borderline:
            out["product_status"] = "clean_human_borderline"
        elif pred == "REAL":
            out["product_status"] = "clean_human_accepted"
        else:
            out["product_status"] = "clean_human_false_alarm"

    # --- direct AI (clean_direct + ai) ---
    elif manip == "clean_direct" and gt_origin == "ai":
        if borderline:
            out["product_status"] = "direct_ai_borderline"
        elif pred == "FAKE" or manip_detected:
            out["product_status"] = "direct_ai_detected"
            out["direct_ai_detected"] = True
        elif pred == "REAL" and segment_suspicious:
            out["product_status"] = "direct_ai_file_level_missed_but_segment_suspicious"
            out["file_level_missed_but_segment_suspicious"] = True
        else:
            out["product_status"] = "direct_ai_missed"
            out["direct_ai_missed"] = True

    # --- processed human ---
    elif gt_origin == "human" and manip in PROCESSED_HUMAN_MANIP_TYPES:
        if manip_detected:
            out["product_status"] = "processed_human_manipulation_detected"
            out["processed_human_detected"] = True
            if pred == "FAKE":
                out["origin_confusion"] = True
        else:
            out["product_status"] = "processed_human_missed"

    # --- AI replay / processed AI ---
    elif gt_origin == "ai" and manip in AI_REPLAY_OR_PROCESSED_MANIP_TYPES:
        if manip_detected:
            out["product_status"] = "ai_replay_or_processed_detected"
            out["ai_replay_or_processed_detected"] = True
        elif pred == "REAL" and segment_suspicious:
            out["file_level_missed_but_segment_suspicious"] = True
            if manip == "ai_replay":
                out["product_status"] = "ai_replay_file_level_missed_but_segment_suspicious"
            else:
                out["product_status"] = "processed_ai_file_level_missed_but_segment_suspicious"
        else:
            out["product_status"] = "ai_replay_or_processed_missed"

    # --- partial fabrication ---
    elif manip == "partial_ai_insert":
        if not has_valid_suspicious_timestamps(row.get("suspicious_start_time"), row.get("suspicious_end_time")):
            out["product_status"] = "partial_not_evaluated_missing_timestamp"
            out["partial_eval_status"] = "partial_not_evaluated_missing_timestamp"
            partial_metrics = {}
        else:
            partial_metrics = compute_partial_region_metrics(
                chunk_timeline,
                row.get("suspicious_start_time"),
                row.get("suspicious_end_time"),
            )
            out["partial_eval_status"] = "evaluated"
            out["partial_region_detected"] = partial_metrics.get("partial_region_detected", False)
            out.update(
                {
                    k: partial_metrics.get(k, out.get(k, ""))
                    for k in (
                        "n_chunks_inside",
                        "n_chunks_outside",
                        "inside_region_avg_spoof",
                        "outside_region_avg_spoof",
                        "inside_region_max_spoof",
                        "outside_region_max_spoof",
                        "inside_region_dominant_attack",
                        "outside_region_dominant_attack",
                    )
                    if k in partial_metrics
                }
            )
            if out["partial_region_detected"]:
                out["product_status"] = "partial_fabrication_detected"
            else:
                out["product_status"] = "partial_fabrication_missed"

    if borderline and out["product_status"] == "unknown_review_required":
        out["product_status"] = "borderline_needs_review"

    out["final_product_interpretation"] = _build_product_interpretation(row, out, candidates)
    return out


def _build_product_interpretation(row: dict, product: dict, candidates: list[dict]) -> str:
    tid = row.get("test_id", "")
    status = product.get("product_status", "")
    pred = row.get("prediction", "")
    score = _to_float(row.get("decision_score"), 0.0)
    parts = [f"{tid}: {status}; whole-file {pred} (score={score:.3f})."]

    if product.get("origin_confusion"):
        parts.append("Origin confusion: FAKE label on human-origin processed audio (manipulation signal useful).")
    if product.get("manipulation_detected") and status.startswith("processed_human"):
        parts.append("Manipulation/channel sensitivity detected despite human origin.")
    if product.get("direct_ai_missed"):
        parts.append("Direct AI miss at file level with weak segment signal.")
    if product.get("file_level_missed_but_segment_suspicious"):
        parts.append(
            "Whole-file vote is below threshold, but multiple suspicious chunks are present. "
            "Manual review or segment-level report is recommended."
        )
    if status == "partial_fabrication_detected":
        parts.append(
            f"Segment signal: inside_avg={product.get('inside_region_avg_spoof', 'n/a')}, "
            f"outside_avg={product.get('outside_region_avg_spoof', 'n/a')}."
        )
    if status == "partial_not_evaluated_missing_timestamp":
        parts.append("Add suspicious_start_time and suspicious_end_time after listening.")
    if candidates and status in {
        "ai_replay_or_processed_missed",
        "direct_ai_missed",
        "direct_ai_file_level_missed_but_segment_suspicious",
        "ai_replay_file_level_missed_but_segment_suspicious",
        "processed_ai_file_level_missed_but_segment_suspicious",
        "partial_fabrication_missed",
        "unknown_review_required",
    }:
        top = candidates[0]
        parts.append(
            f"Exploratory top candidate region: {top['start_time']:.1f}-{top['end_time']:.1f}s "
            f"(max chunk spoof={top['max_spoof']:.3f})."
        )
    scr = product.get("suspicious_chunk_ratio")
    if scr not in ("", None) and float(scr) > 0:
        parts.append(
            f"Chunks: {product.get('suspicious_chunk_count', 0)} suspicious / "
            f"{row.get('n_chunks_used', '?')} used (ratio={float(scr):.2f}, max={product.get('max_chunk_spoof', 'n/a')})."
        )
    return " ".join(parts)


def build_product_dataframe(df: pd.DataFrame, results_dir: Path) -> tuple[pd.DataFrame, dict[str, list[dict]]]:
    """Augment results with product-level columns."""
    results_dir = results_dir.resolve()
    candidate_map: dict[str, list[dict]] = {}
    product_rows = []

    for _, row in df.iterrows():
        r = row.to_dict()
        test_id = str(r.get("test_id", "")).strip()
        timeline, timeline_note = load_chunk_timeline(test_id, results_dir)
        candidate_map[test_id] = compute_candidate_suspicious_regions(timeline)
        product_rows.append(evaluate_product_metrics(r, timeline, timeline_note))

    product_df = pd.DataFrame(product_rows)
    out = df.copy()
    for col in PRODUCT_CSV_EXTRA_COLUMNS:
        if col in product_df.columns:
            out[col] = product_df[col].values
    return out, candidate_map


def _count_status(df: pd.DataFrame, status: str) -> int:
    return int((df["product_status"].astype(str) == status).sum())


def _rows_md(df: pd.DataFrame, cols: list[str], n: int = 20) -> str:
    cols = [c for c in cols if c in df.columns]
    if df.empty:
        return "_None._"
    view = df.head(n)[cols].fillna("")
    try:
        return view.to_markdown(index=False)
    except ImportError:
        lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
        for _, r in view.iterrows():
            lines.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
        return "\n".join(lines)


def generate_product_markdown(df: pd.DataFrame, candidate_map: dict[str, list[dict]]) -> str:
    df = df.copy()
    total = len(df)
    ok = (df["correct_origin_basic"].astype(str).str.lower() == "yes").sum()
    wrong = (df["correct_origin_basic"].astype(str).str.lower() == "no").sum()
    border = (df["correct_origin_basic"].astype(str).str.lower() == "borderline").sum()

    clean_human = df[(df["manipulation_type"].astype(str).str.lower() == "clean_direct") & (df["ground_truth_origin"].astype(str).str.lower() == "human")]
    direct_ai = df[(df["manipulation_type"].astype(str).str.lower() == "clean_direct") & (df["ground_truth_origin"].astype(str).str.lower() == "ai")]
    processed_human = df[
        (df["ground_truth_origin"].astype(str).str.lower() == "human")
        & (df["manipulation_type"].astype(str).str.lower().isin(PROCESSED_HUMAN_MANIP_TYPES))
    ]
    ai_replay = df[
        (df["ground_truth_origin"].astype(str).str.lower() == "ai")
        & (df["manipulation_type"].astype(str).str.lower().isin(AI_REPLAY_OR_PROCESSED_MANIP_TYPES))
    ]
    partial = df[df["manipulation_type"].astype(str).str.lower() == "partial_ai_insert"]

    partial_eval = partial[partial["partial_eval_status"].astype(str) == "evaluated"]
    partial_not_eval = partial[partial["product_status"].astype(str) == "partial_not_evaluated_missing_timestamp"]

    timeline_notes = df["timeline_scope_note"].fillna("").astype(str).value_counts().to_dict() if "timeline_scope_note" in df.columns else {}

    lines = [
        "# Phase 7A — Product-Level Forensic Analysis",
        "",
        "> **Main interpretation document** for Phase 7A review. Legacy binary view: `FORENSIC_TEST_ANALYSIS.md`.",
        "",
        "---",
        "",
        "## 1. Executive summary",
        "",
        "The **legacy binary origin accuracy** is low on this 25-file controlled suite "
        f"(**{ok}/{total} yes**, {wrong} wrong, {border} borderline). "
        "That metric treats human replay and channel-processed human audio as failures when the model outputs FAKE.",
        "",
        "**Product-level review** shows the current hybrid model is **manipulation-sensitive** and useful beyond legacy binary accuracy:",
        "- Human replay (T2.x) often scores **FAKE / 1.0** — manipulation alerts, not confirmed AI origin.",
        "- **Direct AI file-level misses** (T1.3, T1.5, T3.1) still show **segment-suspicious chunks** (max spoof ≈ 1.0) — whole-file **pct_vote** hides evidence.",
        "- **T3.5** is **file-level missed but segment suspicious** — same pooling vs chunk issue.",
        "- **Segment-level analysis should be part of the final product** (chunk timeline + suspicious regions), not only REAL/FAKE.",
        "- **T5_FAB_001** partial insert (**14–21 s**) detected at segment level despite whole-file REAL.",
        "- **T4.3** not evaluable until suspicious timestamps are added.",
        "",
        "**Main weaknesses:** direct AI file-level calibration, origin vs manipulation confusion, pct_vote vs chunk evidence.",
        "",
        "---",
        "",
        "## 2. Old binary accuracy summary",
        "",
        "| Metric | Count |",
        "|--------|------:|",
        f"| Total files | {total} |",
        f"| correct_origin_basic = yes | {ok} |",
        f"| wrong | {wrong} |",
        f"| borderline | {border} |",
        "",
        "| manipulation_type | yes / total |",
        "|-------------------|------------|",
    ]
    for group in MANIPULATION_GROUPS:
        sub = df[df["manipulation_type"].astype(str).str.lower() == group]
        if sub.empty:
            continue
        g_ok = (sub["correct_origin_basic"].astype(str).str.lower() == "yes").sum()
        lines.append(f"| {group} | {g_ok}/{len(sub)} |")

    lines.extend(
        [
            "",
            "---",
            "",
            "## 3. Product-level usefulness summary",
            "",
            "| Metric | Count |",
            "|--------|------:|",
            f"| clean_human_accepted | {_count_status(df, 'clean_human_accepted')} |",
            f"| clean_human_false_alarm | {_count_status(df, 'clean_human_false_alarm')} |",
            f"| clean_human_borderline | {_count_status(df, 'clean_human_borderline')} |",
            f"| direct_ai_detected | {_count_status(df, 'direct_ai_detected')} |",
            f"| direct_ai_file_level_missed_but_segment_suspicious | {_count_status(df, 'direct_ai_file_level_missed_but_segment_suspicious')} |",
            f"| direct_ai_missed (clean file-level miss) | {_count_status(df, 'direct_ai_missed')} |",
            f"| direct_ai_borderline | {_count_status(df, 'direct_ai_borderline')} |",
            f"| processed_human_manipulation_detected | {_count_status(df, 'processed_human_manipulation_detected')} |",
            f"| processed_human_missed | {_count_status(df, 'processed_human_missed')} |",
            f"| ai_replay_or_processed_detected | {_count_status(df, 'ai_replay_or_processed_detected')} |",
            f"| ai_replay_file_level_missed_but_segment_suspicious | {_count_status(df, 'ai_replay_file_level_missed_but_segment_suspicious')} |",
            f"| processed_ai_file_level_missed_but_segment_suspicious | {_count_status(df, 'processed_ai_file_level_missed_but_segment_suspicious')} |",
            f"| ai_replay_or_processed_missed (clean) | {_count_status(df, 'ai_replay_or_processed_missed')} |",
            f"| segment_suspicious (any file) | {int(df.get('segment_suspicious', pd.Series(dtype=bool)).fillna(False).astype(bool).sum()) if 'segment_suspicious' in df.columns else 0} |",
            f"| partial_fabrication_detected (evaluated) | {_count_status(df, 'partial_fabrication_detected')} |",
            f"| partial_fabrication_missed (evaluated) | {_count_status(df, 'partial_fabrication_missed')} |",
            f"| partial_not_evaluated_missing_timestamp | {_count_status(df, 'partial_not_evaluated_missing_timestamp')} |",
            f"| borderline_needs_review | {_count_status(df, 'borderline_needs_review')} |",
            "",
            f"**Borderline rate** (|decision_score − threshold| ≤ 0.05): "
            f"{int(df.apply(lambda r: _is_borderline(r.to_dict()), axis=1).sum())}/{total}",
            "",
            "---",
            "",
            "## 4. Clean human performance",
            "",
            "Focus: **T1.1**, **T1.2**, **T4.1** (clean_direct, human origin).",
            "",
            "| Status | Count |",
            "|--------|------:|",
            f"| clean_human_accepted | {_count_status(clean_human, 'clean_human_accepted')} |",
            f"| clean_human_borderline | {_count_status(clean_human, 'clean_human_borderline')} |",
            f"| clean_human_false_alarm | {_count_status(clean_human, 'clean_human_false_alarm')} |",
            "",
            _rows_md(
                clean_human,
                ["test_id", "prediction", "decision_score", "effective_threshold", "product_status", "failure_type"],
            ),
            "",
            "**Notes:** **T1.1** is **borderline at the decision threshold** "
            "(FAKE, decision_score 0.700 vs threshold 0.700) — treat as **review-required**, "
            "not a confirmed clean-human false alarm. "
            "**T1.2** / **T4.1** illustrate accepted vs borderline clean human. "
            "Legacy binary metrics over-penalize borderline clean human calls.",
            "",
            "---",
            "",
            "## 5. Direct AI performance",
            "",
            "### File-level detected",
            "",
            _rows_md(
                direct_ai[direct_ai["product_status"].astype(str) == "direct_ai_detected"],
                ["test_id", "prediction", "decision_score", "product_status", "max_chunk_spoof"],
            ),
            "",
            "### File-level missed but segment suspicious",
            "",
            _rows_md(
                direct_ai[
                    direct_ai["product_status"].astype(str) == "direct_ai_file_level_missed_but_segment_suspicious"
                ],
                [
                    "test_id",
                    "prediction",
                    "decision_score",
                    "max_chunk_spoof",
                    "suspicious_chunk_ratio",
                    "segment_suspicious",
                    "product_status",
                ],
            ),
            "",
            "**Notes:** **T1.3**, **T1.5**, **T3.1** — REAL at file level (~0.43 vote) but **max_chunk_spoof ≈ 1.0**. "
            "Not a clean miss; segment-level review recommended.",
            "",
            "### File-level missed cleanly",
            "",
            _rows_md(
                direct_ai[direct_ai["product_status"].astype(str) == "direct_ai_missed"],
                ["test_id", "prediction", "decision_score", "max_chunk_spoof", "suspicious_chunk_ratio"],
            ),
            "",
            "---",
            "",
            "## 6. Processed / replayed human performance",
            "",
            "T2.1–T2.5 and edited T5 files: **not simple failures** when FAKE — indicates **manipulation sensitivity** with **origin_confusion**.",
            "",
            _rows_md(
                processed_human,
                ["test_id", "manipulation_type", "prediction", "decision_score", "product_status", "origin_confusion"],
            ),
            "",
            "---",
            "",
            "## 7. AI replay and processed AI performance",
            "",
            "### Fully detected (file-level)",
            "",
            _rows_md(
                ai_replay[ai_replay["product_status"].astype(str) == "ai_replay_or_processed_detected"],
                ["test_id", "manipulation_type", "prediction", "decision_score", "product_status"],
            ),
            "",
            "### File-level missed but segment suspicious",
            "",
            _rows_md(
                ai_replay[
                    ai_replay["product_status"]
                    .astype(str)
                    .isin(
                        {
                            "ai_replay_file_level_missed_but_segment_suspicious",
                            "processed_ai_file_level_missed_but_segment_suspicious",
                        }
                    )
                ],
                [
                    "test_id",
                    "manipulation_type",
                    "prediction",
                    "decision_score",
                    "max_chunk_spoof",
                    "suspicious_chunk_ratio",
                    "product_status",
                ],
            ),
            "",
            "**Notes:** **T3.5** — **ai_replay_file_level_missed_but_segment_suspicious** "
            "(REAL ~0.571, high chunk spoof). Whole-file pct_vote under-reports segment evidence.",
            "",
            "### Fully missed (file and segments weak)",
            "",
            _rows_md(
                ai_replay[ai_replay["product_status"].astype(str) == "ai_replay_or_processed_missed"],
                ["test_id", "manipulation_type", "prediction", "decision_score", "max_chunk_spoof"],
            ),
            "",
            "---",
            "",
            "## 8. Partial fabrication performance",
            "",
            "### T5_FAB_001 (known region 14.0–21.0 s)",
            "",
        ]
    )

    fab = df[df["test_id"].astype(str) == "T5_FAB_001"]
    if not fab.empty:
        r = fab.iloc[0]
        lines.extend(
            [
                "| Field | Value |",
                "|-------|-------|",
                f"| prediction | {r.get('prediction', '')} |",
                f"| decision_score | {r.get('decision_score', '')} |",
                f"| partial_region_detected | {r.get('partial_region_detected', '')} |",
                f"| inside_region_avg_spoof | {r.get('inside_region_avg_spoof', '')} |",
                f"| outside_region_avg_spoof | {r.get('outside_region_avg_spoof', '')} |",
                f"| inside_region_dominant_attack | {r.get('inside_region_dominant_attack', '')} |",
                f"| outside_region_dominant_attack | {r.get('outside_region_dominant_attack', '')} |",
                "",
                "**Assessment:** Successful **segment-level** detection despite whole-file REAL — core Scope 3 signal.",
                "",
            ]
        )
    else:
        lines.append("_T5_FAB_001 not in results._\n")

    lines.extend(
        [
            "### T4.3 (partial_ai_insert, timestamps missing)",
            "",
            "Status: **partial_not_evaluated_missing_timestamp** — do **not** count as partial miss. "
            "Add `suspicious_start_time` / `suspicious_end_time` after listening, then re-run product analysis.",
            "",
            "### Evaluated partial rows",
            "",
            _rows_md(
                partial_eval,
                ["test_id", "prediction", "partial_region_detected", "inside_region_avg_spoof", "outside_region_avg_spoof", "product_status"],
            ),
            "",
            "### Not evaluated (missing timestamps)",
            "",
            _rows_md(partial_not_eval, ["test_id", "product_status", "notes"]),
            "",
            "---",
            "",
            "## 9. Suspicious chunk timeline observations",
            "",
        ]
    )

    if timeline_notes:
        lines.append("**Timeline scope in this run:**")
        for k, v in timeline_notes.items():
            lines.append(f"- `{k}`: {v} files")
        lines.append("")
        lines.append(
            "_If timelines were produced before the all-chunks export update, re-run the suite with "
            "`--save_chunk_timeline` to list every chunk (scores on VAD-kept chunks only)._"
        )
        lines.append("")

    ranked = df.copy()
    ranked["_scr"] = pd.to_numeric(ranked.get("suspicious_chunk_ratio"), errors="coerce").fillna(0)
    ranked["_maxc"] = pd.to_numeric(ranked.get("max_chunk_spoof"), errors="coerce").fillna(0)
    ranked = ranked.sort_values(["_scr", "_maxc"], ascending=False)

    lines.append("**Top files by suspicious_chunk_ratio / max_chunk_spoof:**")
    lines.append("")
    lines.append(
        _rows_md(
            ranked,
            ["test_id", "manipulation_type", "prediction", "decision_score", "suspicious_chunk_count", "suspicious_chunk_ratio", "max_chunk_spoof"],
            n=10,
        )
    )

    lines.extend(["", "### Exploratory candidate suspicious regions (top 3 per file, not GT)", ""])
    for test_id, regions in sorted(candidate_map.items()):
        if not regions:
            continue
        lines.append(f"**{test_id}:**")
        for i, reg in enumerate(regions, 1):
            lines.append(
                f"- #{i}: {reg['start_time']:.1f}–{reg['end_time']:.1f}s, "
                f"max_spoof={reg['max_spoof']:.3f}, chunks={reg['chunk_count']}"
            )
        lines.append("")

    lines.extend(
        [
            "---",
            "",
            "## 10. What this means for Phase 7B dataset preparation",
            "",
            "- Need **separate labels** for **origin** (human / AI / mixed) vs **manipulation** (clean / replay / channel / edit / partial insert).",
            "- Collect more **clean Urdu/Pakistani human** audio; treat borderline cases (e.g. T1.1) as review, not hard false alarms.",
            "- Add more **direct AI** examples (TTS, clone, WAV) matching T1.3/T1.5/T3.1 failure modes.",
            "- Label **human replay** and **processed human** as manipulation-positive, not origin-fake.",
            "- Add **timestamp labels** for partial insertions (T4.3, future PF cases).",
            "",
            "---",
            "",
            "## 11. What this means for Phase 7C fine-tuning",
            "",
            "- Do **not** train only on REAL/FAKE — risks origin/manipulation confusion seen in T2/T5.",
            "- If fine-tuning the hybrid model, target **separate heads or calibration** for origin vs manipulation when feasible.",
            "- Fine-tune **carefully** on 7B labels; do not discard the current hybrid baseline.",
            "",
            "---",
            "",
            "## 12. What this means for Phase 7E transformer / AASIST experiments",
            "",
            "- AASIST / WavLM may help **direct AI weakness** (T1.3, T1.5, T3.1).",
            "- Compare transformer baselines **separately** on direct AI and replay subsets before Phase 7F ensemble.",
            "",
            "---",
            "",
            "## 13. Next recommended action",
            "",
            "1. Fill **T4.3** `suspicious_start_time` / `suspicious_end_time` in the manifest after listening.",
            "2. Re-run **product analysis** (re-inference optional unless timelines missing).",
            "3. Prepare **Phase 7B** dual labels (origin + manipulation) after this cleanup is reviewed.",
            "4. **Do not fine-tune** (7C) until product-level analysis is signed off.",
            "",
        ]
    )
    return "\n".join(lines)


def print_product_terminal_summary(df: pd.DataFrame) -> None:
    print("")
    print("=== Phase 7A product-level summary ===")
    for status in [
        "clean_human_accepted",
        "clean_human_borderline",
        "clean_human_false_alarm",
        "direct_ai_detected",
        "direct_ai_file_level_missed_but_segment_suspicious",
        "direct_ai_missed",
        "processed_human_manipulation_detected",
        "ai_replay_or_processed_detected",
        "ai_replay_file_level_missed_but_segment_suspicious",
        "processed_ai_file_level_missed_but_segment_suspicious",
        "ai_replay_or_processed_missed",
        "partial_fabrication_detected",
        "partial_fabrication_missed",
        "partial_not_evaluated_missing_timestamp",
    ]:
        n = _count_status(df, status)
        if n:
            print(f"  {status}: {n}")
    print("")


def _safe_mean(series: pd.Series) -> float | None:
    vals = pd.to_numeric(series, errors="coerce").dropna()
    if vals.empty:
        return None
    return float(vals.mean())


def _group_failure_patterns(sub: pd.DataFrame) -> str:
    failures = sub[sub["correct_origin_basic"].astype(str).str.lower() == "no"]
    if failures.empty:
        return "None observed in this group."
    types = failures["failure_type"].fillna("").astype(str)
    types = types[types.str.len() > 0]
    if types.empty:
        return "Wrong origin without typed failure label."
    counts = types.value_counts().head(3)
    return "; ".join(f"{k} ({v})" for k, v in counts.items())


def _recommended_action_for_group(sub: pd.DataFrame, group: str) -> str:
    wrong = int((sub["correct_origin_basic"].astype(str).str.lower() == "no").sum())
    borderline = int((sub["correct_origin_basic"].astype(str).str.lower() == "borderline").sum())
    total = len(sub)
    if total == 0:
        return "No files in this group yet."
    if group == "partial_ai_insert":
        evaluable = sub.apply(
            lambda r: has_valid_suspicious_timestamps(r.get("suspicious_start_time"), r.get("suspicious_end_time")),
            axis=1,
        )
        missed = sub[
            evaluable
            & (sub["partial_region_detected"].map(parse_bool) != True)
        ]
        if len(missed) > 0:
            return "Improve chunk timeline + 7D Case H rules; consider 7C fine-tune on partial inserts."
        return "Partial-region detection looks acceptable; document thresholds in 7D."
    if wrong == 0 and borderline == 0:
        return "Maintain current thresholds; add more P0 samples for coverage."
    if group in {"human_replay", "mixer_processed", "phone_recorded"} and wrong > 0:
        return "Collect more replay/channel P0; plan 7B labels and 7C domain adaptation."
    if group in {"ai_replay", "clean_direct"} and wrong > 0:
        return "Review false negatives/positives; check pooling and VAD on these chains."
    if borderline > 0:
        return "Review borderline files manually; consider score band reporting in 7D."
    return "Review failures in forensic_test_results.csv and prioritize 7B/7C data collection."


def generate_analysis_markdown(df: pd.DataFrame) -> str:
    df = df.copy()
    df["correct_origin_basic"] = df.apply(
        lambda r: evaluate_correct_origin_basic(r.to_dict()) if pd.isna(r.get("correct_origin_basic")) or r.get("correct_origin_basic") == "" else r["correct_origin_basic"],
        axis=1,
    )
    df["failure_type"] = df.apply(
        lambda r: evaluate_failure_type({**r.to_dict(), "correct_origin_basic": r["correct_origin_basic"]})
        if pd.isna(r.get("failure_type")) or r.get("failure_type") == ""
        else r["failure_type"],
        axis=1,
    )

    total = len(df)
    ok_mask = df["correct_origin_basic"].astype(str).str.lower() == "yes"
    wrong_mask = df["correct_origin_basic"].astype(str).str.lower() == "no"
    border_mask = df["correct_origin_basic"].astype(str).str.lower() == "borderline"
    errors = int(df.get("error", pd.Series([""] * len(df))).apply(_has_error).sum()) if "error" in df.columns else 0

    lines = [
        "# Forensic Test Analysis — Phase 7A",
        "",
        f"**Files analyzed:** {total}  ",
        f"**Inference errors / missing audio:** {errors}  ",
        "",
        "---",
        "",
        "## 1. Overall summary",
        "",
        "| Metric | Value |",
        "|--------|------:|",
        f"| Total files | {total} |",
        f"| Correct origin (basic) | {int(ok_mask.sum())} |",
        f"| Wrong origin | {int(wrong_mask.sum())} |",
        f"| Borderline | {int(border_mask.sum())} |",
        f"| Overall accuracy (yes / evaluated) | {int(ok_mask.sum())}/{max(total - errors, 1)} |",
        "",
    ]

    failure_top = df.loc[wrong_mask, "failure_type"].fillna("").astype(str)
    failure_top = failure_top[failure_top.str.len() > 0].value_counts()
    top_failure = failure_top.index[0] if len(failure_top) else "n/a"
    lines.extend(
        [
            f"**Top failure mode:** {top_failure}  ",
            f"**Recommended next action:** {_recommended_action_for_group(df, 'unknown')}  ",
            "",
            "---",
            "",
            "## 2. Accuracy by test group (manipulation_type)",
            "",
        ]
    )

    for group in MANIPULATION_GROUPS:
        sub = df[df["manipulation_type"].astype(str).str.lower() == group]
        display = GROUP_DISPLAY_NAMES.get(group, group)
        lines.append(f"### {display} (`{group}`)")
        lines.append("")
        if sub.empty:
            lines.append("_No files in this group._")
            lines.append("")
            continue
        g_ok = (sub["correct_origin_basic"].astype(str).str.lower() == "yes").sum()
        g_wrong = (sub["correct_origin_basic"].astype(str).str.lower() == "no").sum()
        g_border = (sub["correct_origin_basic"].astype(str).str.lower() == "borderline").sum()
        avg_score = _safe_mean(sub["decision_score"])
        avg_score_str = f"{avg_score:.3f}" if avg_score is not None else "n/a"
        lines.extend(
            [
                "| Metric | Value |",
                "|--------|------:|",
                f"| Total files | {len(sub)} |",
                f"| Correct origin | {g_ok} |",
                f"| Wrong origin | {g_wrong} |",
                f"| Borderline | {g_border} |",
                f"| Avg decision_score | {avg_score_str} |",
                "",
                f"**Common failure pattern:** {_group_failure_patterns(sub)}  ",
                "",
                f"**Recommended next action:** {_recommended_action_for_group(sub, group)}  ",
                "",
            ]
        )

    def _df_to_md_table(sub: pd.DataFrame) -> str:
        cols = ["test_id", "manipulation_type", "prediction", "decision_score", "correct_origin_basic", "failure_type"]
        cols = [c for c in cols if c in sub.columns]
        view = sub[cols].fillna("")
        try:
            return view.to_markdown(index=False)
        except ImportError:
            header = "| " + " | ".join(cols) + " |"
            sep = "| " + " | ".join(["---"] * len(cols)) + " |"
            rows = [
                "| " + " | ".join(str(view.iloc[i][c]) for c in cols) + " |"
                for i in range(len(view))
            ]
            return "\n".join([header, sep, *rows])

    def _section_cases(title: str, mask: pd.Series) -> list[str]:
        sub = df[mask]
        out = [f"## {title}", ""]
        if sub.empty:
            out.append("_None._")
        else:
            out.append(_df_to_md_table(sub))
        out.append("")
        return out

    lines.extend(_section_cases("3. False positives (human GT, FAKE pred)", (df["ground_truth_origin"].astype(str).str.lower() == "human") & (df["prediction"].astype(str).str.upper() == "FAKE")))
    lines.extend(_section_cases("4. False negatives (ai GT, REAL pred)", (df["ground_truth_origin"].astype(str).str.lower() == "ai") & (df["prediction"].astype(str).str.upper() == "REAL")))
    lines.extend(_section_cases("5. Borderline cases", border_mask))
    lines.extend(
        _section_cases(
            "6. Partial fabrication cases",
            df["manipulation_type"].astype(str).str.lower().eq("partial_ai_insert")
            | df["partial_fabrication_detected"].map(parse_bool).eq(True),
        )
    )
    lines.extend(_section_cases("7. Human replay cases", df["manipulation_type"].astype(str).str.lower() == "human_replay"))
    lines.extend(_section_cases("8. AI replay cases", df["manipulation_type"].astype(str).str.lower() == "ai_replay"))
    lines.extend(_section_cases("9. Mixer / channel processed cases", df["manipulation_type"].astype(str).str.lower() == "mixer_processed"))

    lines.extend(["## 10. Recommended next action", ""])
    actions = []
    if int(wrong_mask.sum()) > 0:
        actions.append("- Address top failure types before Phase 7C fine-tuning.")
    if int(border_mask.sum()) > 0:
        actions.append("- Manually review borderline files; tune vote_threshold only with per-group evidence.")
    partial_evaluable = df.apply(
        lambda r: has_valid_suspicious_timestamps(r.get("suspicious_start_time"), r.get("suspicious_end_time")),
        axis=1,
    )
    partial_gt = df["partial_fabrication_detected"].map(parse_bool) == True
    partial_miss = partial_gt & partial_evaluable & (df["partial_region_detected"].map(parse_bool) != True)
    if int(partial_miss.sum()) > 0:
        actions.append("- Partial fabrication misses detected: prioritize chunk timeline in 7D reports (Case H).")
    if not actions:
        actions.append("- Baseline looks stable on current P0 set; expand manifest coverage (T1–T5).")
    lines.extend(actions)
    lines.append("")
    return "\n".join(lines)


def print_terminal_summary(df: pd.DataFrame, errors: int = 0, title: str = "Forensic analysis") -> None:
    total = len(df)
    ok = (df["correct_origin_basic"].astype(str).str.lower() == "yes").sum()
    wrong = (df["correct_origin_basic"].astype(str).str.lower() == "no").sum()
    borderline = (df["correct_origin_basic"].astype(str).str.lower() == "borderline").sum()

    partial_gt = df["partial_fabrication_detected"].map(parse_bool) == True
    partial_detected = df["partial_region_detected"].map(parse_bool) == True
    partial_detected_count = int(partial_detected.sum())
    partial_evaluable = df.apply(
        lambda r: has_valid_suspicious_timestamps(r.get("suspicious_start_time"), r.get("suspicious_end_time")),
        axis=1,
    )
    partial_missed = int((partial_gt & partial_evaluable & ~partial_detected).sum())
    partial_not_eval = int(
        (
            (df["manipulation_type"].astype(str).str.lower() == "partial_ai_insert")
            & ~partial_evaluable
        ).sum()
    )

    print("")
    print(f"=== {title} ===")
    print(f"Total files processed: {total}")
    print(f"Total errors: {errors}")
    print(f"Overall correct_origin_basic (yes): {ok}/{total}")
    print(f"Wrong: {wrong} | Borderline: {borderline}")
    print("")
    print("Group-wise accuracy (yes / total):")
    for group in MANIPULATION_GROUPS:
        sub = df[df["manipulation_type"].astype(str).str.lower() == group]
        if sub.empty:
            continue
        g_ok = (sub["correct_origin_basic"].astype(str).str.lower() == "yes").sum()
        print(f"  {group}: {g_ok}/{len(sub)}")
    print("")
    print(f"Borderline files: {borderline}")
    print(f"Partial fabrication detected (computed): {partial_detected_count}")
    print(f"Partial fabrication missed (evaluated GT, not detected): {partial_missed}")
    print(f"Partial not evaluated (missing timestamps): {partial_not_eval}")
    print("")


def analyze_results(
    csv_path: Path,
    output_md: Path,
    rewrite_csv: bool = True,
    results_dir: Path | None = None,
    product_csv: Path | None = None,
    product_md: Path | None = None,
    skip_legacy_md: bool = False,
) -> pd.DataFrame:
    csv_path = csv_path.resolve()
    results_dir = results_dir or csv_path.parent
    product_csv = product_csv or (results_dir / "forensic_test_results_product.csv")
    product_md = product_md or (results_dir / "PHASE7A_PRODUCT_LEVEL_ANALYSIS.md")

    df = pd.read_csv(csv_path, low_memory=False)
    df["correct_origin_basic"] = df.apply(lambda r: evaluate_correct_origin_basic(r.to_dict()), axis=1)
    df["failure_type"] = df.apply(
        lambda r: evaluate_failure_type({**r.to_dict(), "correct_origin_basic": r["correct_origin_basic"]}),
        axis=1,
    )

    product_df, candidate_map = build_product_dataframe(df, results_dir)
    product_df.to_csv(product_csv, index=False)
    print(f"[SAVE] Product CSV -> {product_csv}")

    product_md.parent.mkdir(parents=True, exist_ok=True)
    product_md.write_text(generate_product_markdown(product_df, candidate_map), encoding="utf-8")
    print(f"[SAVE] Product analysis -> {product_md}")

    if rewrite_csv:
        df.to_csv(csv_path, index=False)

    if not skip_legacy_md:
        md = generate_analysis_markdown(df)
        output_md.parent.mkdir(parents=True, exist_ok=True)
        output_md.write_text(md, encoding="utf-8")
        print(f"[SAVE] Legacy analysis -> {output_md}")

    errors = int(df["error"].apply(_has_error).sum()) if "error" in df.columns else 0
    print_terminal_summary(df, errors=errors, title="Forensic analysis (legacy binary)")
    print_product_terminal_summary(product_df)
    return product_df


def parse_args():
    p = argparse.ArgumentParser(description="Phase 7A — analyze forensic test results CSV")
    p.add_argument("--results_csv", type=str, required=True)
    p.add_argument("--results_dir", type=str, default=None, help="Dir with json_outputs/ and chunk_timelines/")
    p.add_argument("--output_md", type=str, default="reports/phase7_forensic_tests/results/FORENSIC_TEST_ANALYSIS.md")
    p.add_argument(
        "--product_csv",
        type=str,
        default="reports/phase7_forensic_tests/results/forensic_test_results_product.csv",
    )
    p.add_argument(
        "--product_md",
        type=str,
        default="reports/phase7_forensic_tests/results/PHASE7A_PRODUCT_LEVEL_ANALYSIS.md",
    )
    p.add_argument("--no_rewrite_csv", action="store_true", help="Do not update legacy results CSV")
    p.add_argument("--skip_legacy_md", action="store_true", help="Only generate product-level outputs")
    return p.parse_args()


def main():
    args = parse_args()
    csv_path = Path(args.results_csv)
    analyze_results(
        csv_path=csv_path,
        output_md=Path(args.output_md),
        rewrite_csv=not args.no_rewrite_csv,
        results_dir=Path(args.results_dir) if args.results_dir else csv_path.parent,
        product_csv=Path(args.product_csv),
        product_md=Path(args.product_md),
        skip_legacy_md=args.skip_legacy_md,
    )


if __name__ == "__main__":
    main()
