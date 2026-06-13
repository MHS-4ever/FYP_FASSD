"""Diagnose why mixer/channel retrains fail on testing_audios.

Reads the v2 mixer retrain prediction table, compares Phase 7 mixer positives
against failed external testing-audios mixer/compression positives, and writes
feature-distance/effect-size diagnostics. This script does not train a model.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = (
    ROOT
    / "reports"
    / "release_audit"
    / "mixer_retrain_experimental_v2_2026-06-13"
    / "mixer_experimental_predictions.csv"
)
DEFAULT_OUT = ROOT / "reports" / "release_audit" / "mixer_feature_gap_diagnosis_2026-06-13"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", default=str(DEFAULT_INPUT))
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT))
    parser.add_argument("--top-k", type=int, default=30)
    return parser.parse_args()


def acoustic_feature_columns(df: pd.DataFrame) -> list[str]:
    prefixes = ("rms_", "spectral_", "mfcc_")
    exact = {
        "peak_amplitude",
        "mean_amplitude",
        "std_amplitude",
        "dc_offset",
        "zero_crossing_rate_mean",
        "zero_crossing_rate_std",
        "clipping_ratio",
        "silence_ratio",
        "active_audio_ratio",
        "low_band_energy_ratio",
        "mid_band_energy_ratio",
        "high_band_energy_ratio",
        "noise_floor_proxy",
        "snr_proxy",
        "dynamic_range_proxy",
        "high_freq_rolloff_ratio",
        "bandwidth_occupied_95",
    }
    return [c for c in df.columns if c.startswith(prefixes) or c in exact]


def numeric_frame(df: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    return df[features].apply(pd.to_numeric, errors="coerce")


def standardize(
    df: pd.DataFrame,
    features: list[str],
    ref: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    x_ref = numeric_frame(ref, features)
    center = x_ref.median(numeric_only=True)
    spread = x_ref.std(numeric_only=True).replace(0, np.nan)
    spread = spread.fillna(x_ref.mad(numeric_only=True) if hasattr(x_ref, "mad") else 1.0)
    spread = spread.replace(0, 1.0).fillna(1.0)
    x = numeric_frame(df, features).fillna(center)
    return (x - center) / spread, center, spread


def centroid_distance(z: pd.DataFrame, centroid: pd.Series) -> pd.Series:
    common = [c for c in z.columns if c in centroid.index]
    if not common:
        return pd.Series(np.nan, index=z.index)
    diff = z[common].sub(centroid[common], axis=1)
    return np.sqrt((diff**2).mean(axis=1))


def group_label(row: pd.Series) -> str:
    scope = str(row.get("prediction_scope", ""))
    manipulation = str(row.get("manipulation_type", ""))
    target = str(row.get("target_is_mixer_channel", ""))
    if scope == "testing_audios" and manipulation in {"mixer_processed", "whatsapp_compressed"}:
        return "testing_mixer_positive"
    if scope == "testing_audios" and manipulation in {"ai_replay", "human_replay"}:
        return "testing_replay_negative"
    if scope == "testing_audios" and manipulation == "clean_direct":
        return "testing_clean_negative"
    if scope in {"train_original", "dev", "test"} and target in {"1", "1.0", "True", "true"}:
        return "phase7_mixer_positive"
    if scope in {"train_original", "dev", "test"} and manipulation in {"ai_replay", "human_replay"}:
        return "phase7_replay_negative"
    if scope in {"train_original", "dev", "test"} and manipulation == "clean_direct":
        return "phase7_clean_negative"
    return "other"


def safe_mean(s: pd.Series) -> float:
    v = pd.to_numeric(s, errors="coerce")
    return float(v.mean()) if v.notna().any() else float("nan")


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.predictions, dtype=str, keep_default_na=False)
    features = acoustic_feature_columns(df)
    if not features:
        raise ValueError("No acoustic feature columns found in predictions CSV.")

    df["diagnostic_group"] = df.apply(group_label, axis=1)
    ok = df[df["feature_status"].eq("ok")].copy()

    ref = ok[ok["prediction_scope"].eq("train_original")].copy()
    if len(ref) == 0:
        raise ValueError("No train_original rows found for reference scaling.")

    z, _, _ = standardize(ok, features, ref)
    ok_z = ok.reset_index(drop=True).copy()
    z = z.reset_index(drop=True)

    phase7_pos = ok_z[ok_z["diagnostic_group"].eq("phase7_mixer_positive")]
    phase7_clean = ok_z[ok_z["diagnostic_group"].eq("phase7_clean_negative")]
    phase7_replay = ok_z[ok_z["diagnostic_group"].eq("phase7_replay_negative")]
    testing_pos = ok_z[ok_z["diagnostic_group"].eq("testing_mixer_positive")]

    z_phase7_pos = z.loc[phase7_pos.index]
    z_phase7_clean = z.loc[phase7_clean.index]
    z_phase7_replay = z.loc[phase7_replay.index]

    centroids = {
        "phase7_mixer_positive": z_phase7_pos.mean(numeric_only=True),
        "phase7_clean_negative": z_phase7_clean.mean(numeric_only=True),
        "phase7_replay_negative": z_phase7_replay.mean(numeric_only=True),
    }

    distance_rows: list[dict] = []
    for idx, row in ok_z.iterrows():
        if row["diagnostic_group"] not in {
            "testing_mixer_positive",
            "testing_replay_negative",
            "testing_clean_negative",
        }:
            continue
        z_row = z.loc[[idx]]
        item = {
            "test_id": row.get("test_id", ""),
            "audio_path": row.get("audio_path", ""),
            "ground_truth_origin": row.get("ground_truth_origin", ""),
            "manipulation_type": row.get("manipulation_type", ""),
            "diagnostic_group": row.get("diagnostic_group", ""),
            "mixer_probability": row.get("mixer_probability", ""),
            "mixer_prediction": row.get("mixer_prediction", ""),
        }
        for name, centroid in centroids.items():
            item[f"distance_to_{name}"] = float(centroid_distance(z_row, centroid).iloc[0])
        item["nearest_centroid"] = min(
            (k for k in centroids),
            key=lambda k: item[f"distance_to_{k}"],
        )
        distance_rows.append(item)
    distances = pd.DataFrame(distance_rows)
    distances.to_csv(out_dir / "mixer_testing_audio_centroid_distances.csv", index=False)

    # Feature gap table: how far testing positives are from Phase 7 positives,
    # and whether they sit closer to negative distributions.
    feature_rows: list[dict] = []
    test_pos_z = z.loc[testing_pos.index]
    for feat in features:
        row = {
            "feature": feat,
            "phase7_mixer_mean_z": safe_mean(z.loc[phase7_pos.index, feat]),
            "phase7_clean_mean_z": safe_mean(z.loc[phase7_clean.index, feat]),
            "phase7_replay_mean_z": safe_mean(z.loc[phase7_replay.index, feat]),
            "testing_mixer_mean_z": safe_mean(test_pos_z[feat]) if len(test_pos_z) else float("nan"),
        }
        row["gap_testing_vs_phase7_mixer_abs"] = abs(
            row["testing_mixer_mean_z"] - row["phase7_mixer_mean_z"]
        )
        row["closer_to_clean_than_mixer"] = abs(
            row["testing_mixer_mean_z"] - row["phase7_clean_mean_z"]
        ) < abs(row["testing_mixer_mean_z"] - row["phase7_mixer_mean_z"])
        row["closer_to_replay_than_mixer"] = abs(
            row["testing_mixer_mean_z"] - row["phase7_replay_mean_z"]
        ) < abs(row["testing_mixer_mean_z"] - row["phase7_mixer_mean_z"])
        feature_rows.append(row)
    feature_gap = pd.DataFrame(feature_rows).sort_values(
        "gap_testing_vs_phase7_mixer_abs", ascending=False
    )
    feature_gap.to_csv(out_dir / "mixer_feature_gap_ranked.csv", index=False)

    group_summary = (
        ok_z.groupby(["diagnostic_group", "manipulation_type"], dropna=False)
        .agg(
            n=("audio_path", "size"),
            mean_mixer_probability=("mixer_probability", lambda s: safe_mean(s)),
            detected_rate=("mixer_prediction", lambda s: safe_mean(s)),
        )
        .reset_index()
    )
    group_summary.to_csv(out_dir / "mixer_group_probability_summary.csv", index=False)

    top_features = feature_gap.head(args.top_k)
    testing_dist = distances[distances["diagnostic_group"].eq("testing_mixer_positive")]

    report = [
        "# Mixer Feature Gap Diagnosis",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "Purpose: explain why mixer/channel retrain v2 scores external mixer/compression examples as non-mixer.",
        "",
        "## Testing Mixer Positive Distances",
        "",
        testing_dist.round(4).to_string(index=False) if len(testing_dist) else "(none)",
        "",
        "## Top Feature Gaps",
        "",
        top_features.round(4).to_string(index=False),
        "",
        "## Group Probability Summary",
        "",
        group_summary.round(4).to_string(index=False),
        "",
        "## Interpretation Guide",
        "",
        "- If testing mixer positives are nearest to clean/replay centroids, the training mixer distribution does not match the external cases.",
        "- Large feature gaps show which acoustic dimensions differ most from Phase 7 mixer positives.",
        "- Features marked closer to clean/replay than mixer indicate likely reasons for missed detection.",
        "",
        "## Outputs",
        "",
        f"- `{out_dir / 'mixer_testing_audio_centroid_distances.csv'}`",
        f"- `{out_dir / 'mixer_feature_gap_ranked.csv'}`",
        f"- `{out_dir / 'mixer_group_probability_summary.csv'}`",
    ]
    (out_dir / "mixer_feature_gap_diagnosis_report.md").write_text(
        "\n".join(report), encoding="utf-8"
    )

    print(f"Wrote mixer feature-gap diagnosis to {out_dir}")
    print(testing_dist.round(4).to_string(index=False) if len(testing_dist) else "(no testing positives)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
