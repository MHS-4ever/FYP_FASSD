"""Phase 6 — fit evidence strength band cutpoints on leakage-safe dev (file-level axes)."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "release" / "config" / "evidence_calibration.json"
LEAKAGE_PRED = (
    ROOT
    / "reports"
    / "release_audit"
    / "leakage_safe_eval_2026-06-13"
    / "current_model_file_predictions.csv"
)
PHASE5_PRED = ROOT / "reports" / "release_audit" / "phase5_partial_redesign_2026-06-13" / "phase5_segment_predictions.csv"
PHASE4_REPLAY = (
    ROOT / "reports" / "release_audit" / "phase4_two_stage_manipulation_v3_2026-06-13" / "phase4_replay_dev_predictions.csv"
)
PHASE4_MIXER = (
    ROOT / "reports" / "release_audit" / "phase4_two_stage_manipulation_v3_2026-06-13" / "phase4_mixer_dev_predictions.csv"
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--out", default=str(DEFAULT_OUT))
    return p.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def band_cutpoints(probs: np.ndarray, labels: np.ndarray, threshold: float) -> dict[str, float]:
    neg = probs[labels == 0]
    pos = probs[labels == 1]
    if len(neg) >= 5:
        low_max = float(np.quantile(neg, 0.90))
    else:
        low_max = max(0.33, threshold * 0.5)
    if len(pos) >= 3 and len(neg) >= 3:
        medium_max = float(np.quantile(pos, 0.25))
    else:
        medium_max = float(threshold)
    medium_max = max(low_max + 0.05, min(medium_max, 0.99))
    return {
        "low_max": round(low_max, 4),
        "medium_max": round(medium_max, 4),
        "threshold": round(float(threshold), 4),
    }


def fit_from_leakage(path: Path) -> dict[str, dict]:
    if not path.is_file():
        return {}
    df = pd.read_csv(path, low_memory=False)
    dev = df[df["leakage_safe_split"].astype(str).eq("dev")].copy()
    if dev.empty:
        return {}

    axes: dict[str, dict] = {}
    if "origin_probability" in dev.columns and "audit_origin_expected_ai" in dev.columns:
        p = pd.to_numeric(dev["origin_probability"], errors="coerce").to_numpy()
        y = pd.to_numeric(dev["audit_origin_expected_ai"], errors="coerce").fillna(0).astype(int).to_numpy()
        ok = np.isfinite(p)
        axes["origin"] = band_cutpoints(p[ok], y[ok], threshold=0.92)

    if "replay_probability" in dev.columns and "audit_replay_gt" in dev.columns:
        p = pd.to_numeric(dev["replay_probability"], errors="coerce").to_numpy()
        y = pd.to_numeric(dev["audit_replay_gt"], errors="coerce").fillna(0).astype(int).to_numpy()
        ok = np.isfinite(p)
        axes["replay"] = band_cutpoints(p[ok], y[ok], threshold=0.65)

    if "mixer_probability" in dev.columns and "audit_mixer_gt" in dev.columns:
        p = pd.to_numeric(dev["mixer_probability"], errors="coerce").to_numpy()
        y = pd.to_numeric(dev["audit_mixer_gt"], errors="coerce").fillna(0).astype(int).to_numpy()
        ok = np.isfinite(p)
        axes["mixer"] = band_cutpoints(p[ok], y[ok], threshold=0.75)
    return axes


def fit_partial_from_phase5(path: Path) -> dict[str, dict] | None:
    if not path.is_file():
        return None
    df = pd.read_csv(path, low_memory=False)
    dev = df[df["prediction_scope"].astype(str).eq("dev")].copy()
    if dev.empty or "segment_probability" not in dev.columns:
        return None
    dev["segment_probability"] = pd.to_numeric(dev["segment_probability"], errors="coerce")
    dev["target_is_fabricated_segment"] = pd.to_numeric(
        dev["target_is_fabricated_segment"], errors="coerce"
    ).fillna(0).astype(int)
    p = dev["segment_probability"].to_numpy()
    y = dev["target_is_fabricated_segment"].to_numpy()
    ok = np.isfinite(p)
    return {"partial_segment": band_cutpoints(p[ok], y[ok], threshold=0.95)}


def main() -> int:
    args = parse_args()
    axes = fit_from_leakage(LEAKAGE_PRED)

    if not axes.get("replay") and PHASE4_REPLAY.is_file():
        df = pd.read_csv(PHASE4_REPLAY, low_memory=False)
        p = pd.to_numeric(df["replay_probability"], errors="coerce").to_numpy()
        y = pd.to_numeric(df["target_is_replay"], errors="coerce").fillna(0).astype(int).to_numpy()
        ok = np.isfinite(p)
        axes["replay"] = band_cutpoints(p[ok], y[ok], threshold=0.65)

    if not axes.get("mixer") and PHASE4_MIXER.is_file():
        df = pd.read_csv(PHASE4_MIXER, low_memory=False)
        p = pd.to_numeric(df["mixer_probability"], errors="coerce").to_numpy()
        y = pd.to_numeric(df["target_is_mixer_channel"], errors="coerce").fillna(0).astype(int).to_numpy()
        ok = np.isfinite(p)
        axes["mixer"] = band_cutpoints(p[ok], y[ok], threshold=0.75)

    partial = fit_partial_from_phase5(PHASE5_PRED)
    if partial:
        axes.update(partial)

    defaults = {
        "origin": {"low_max": 0.50, "medium_max": 0.92, "threshold": 0.92},
        "replay": {"low_max": 0.40, "medium_max": 0.65, "threshold": 0.65},
        "mixer": {"low_max": 0.50, "medium_max": 0.75, "threshold": 0.75},
        "partial_segment": {"low_max": 0.50, "medium_max": 0.95, "threshold": 0.95},
    }
    for k, v in defaults.items():
        axes.setdefault(k, v)

    out = {
        "schema_version": "phase6_evidence_calibration_v1",
        "fitted_at": utc_now(),
        "fitted_on": "leakage_safe_dev",
        "sources": {
            "leakage_predictions": str(LEAKAGE_PRED),
            "phase5_segment_predictions": str(PHASE5_PRED),
        },
        "axes": axes,
        "display_note": (
            "User-facing cards show Low/Medium/High evidence bands. "
            "Raw uncalibrated probabilities appear only in technical details."
        ),
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"[phase6] calibration -> {out_path}")
    print(json.dumps(axes, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
