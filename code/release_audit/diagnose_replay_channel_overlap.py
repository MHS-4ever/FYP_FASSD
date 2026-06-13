"""Diagnose replay-vs-channel overlap on testing_audios.

Reads the experimental replay retrain predictions and compares external
testing failures against Phase 7 replay, mixer/channel, and clean groups.
This script does not train a model.
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
    / "replay_retrain_experimental_2026-06-13"
    / "replay_experimental_predictions.csv"
)
DEFAULT_OUT = ROOT / "reports" / "release_audit" / "replay_channel_overlap_diagnosis_2026-06-13"


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


def safe_mean(s: pd.Series) -> float:
    values = pd.to_numeric(s, errors="coerce")
    return float(values.mean()) if values.notna().any() else float("nan")


def numeric_frame(df: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    return df[features].apply(pd.to_numeric, errors="coerce")


def standardize(df: pd.DataFrame, features: list[str], ref: pd.DataFrame) -> pd.DataFrame:
    x_ref = numeric_frame(ref, features)
    center = x_ref.median(numeric_only=True)
    spread = x_ref.std(numeric_only=True).replace(0, np.nan).fillna(1.0)
    x = numeric_frame(df, features).fillna(center)
    return (x - center) / spread


def centroid_distance(z: pd.DataFrame, centroid: pd.Series) -> pd.Series:
    cols = [c for c in z.columns if c in centroid.index]
    diff = z[cols].sub(centroid[cols], axis=1)
    return np.sqrt((diff**2).mean(axis=1))


def diagnostic_group(row: pd.Series) -> str:
    scope = str(row.get("prediction_scope", ""))
    manipulation = str(row.get("manipulation_type", ""))
    target = str(row.get("target_is_replay", ""))
    if scope == "testing_audios":
        if manipulation in {"human_replay", "ai_replay"}:
            return "testing_replay_positive"
        if manipulation == "mixer_processed":
            return "testing_mixer_negative"
        if manipulation == "edited_spliced":
            return "testing_edited_negative"
        if manipulation == "clean_direct":
            return "testing_clean_negative"
        return "testing_other"
    if scope in {"train_original", "dev", "test"}:
        if target in {"1", "1.0", "True", "true"}:
            return "phase7_replay_positive"
        if manipulation == "mixer_processed":
            return "phase7_mixer_negative"
        if manipulation == "clean_direct":
            return "phase7_clean_negative"
    return "other"


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.predictions, dtype=str, keep_default_na=False)
    features = acoustic_feature_columns(df)
    if not features:
        raise ValueError("No acoustic feature columns found.")

    df["diagnostic_group"] = df.apply(diagnostic_group, axis=1)
    ok = df[df["feature_status"].eq("ok")].copy().reset_index(drop=True)
    ref = ok[ok["prediction_scope"].eq("train_original")].copy()
    if len(ref) == 0:
        raise ValueError("No train_original rows found for reference scaling.")

    z = standardize(ok, features, ref).reset_index(drop=True)
    centroids: dict[str, pd.Series] = {}
    for group in ["phase7_replay_positive", "phase7_mixer_negative", "phase7_clean_negative"]:
        idx = ok.index[ok["diagnostic_group"].eq(group)]
        centroids[group] = z.loc[idx].mean(numeric_only=True)

    distance_rows: list[dict] = []
    for idx, row in ok.iterrows():
        if not str(row["diagnostic_group"]).startswith("testing_"):
            continue
        item = {
            "test_id": row.get("test_id", ""),
            "audio_path": row.get("audio_path", ""),
            "ground_truth_origin": row.get("ground_truth_origin", ""),
            "manipulation_type": row.get("manipulation_type", ""),
            "diagnostic_group": row.get("diagnostic_group", ""),
            "replay_probability": row.get("replay_probability", ""),
            "replay_prediction": row.get("replay_prediction", ""),
            "target_is_replay": row.get("target_is_replay", ""),
        }
        z_row = z.loc[[idx]]
        for group, centroid in centroids.items():
            item[f"distance_to_{group}"] = float(centroid_distance(z_row, centroid).iloc[0])
        item["nearest_centroid"] = min(
            centroids,
            key=lambda g: item[f"distance_to_{g}"],
        )
        distance_rows.append(item)
    distances = pd.DataFrame(distance_rows)
    distances.to_csv(out_dir / "replay_testing_audio_centroid_distances.csv", index=False)

    focus = ok[
        ok["test_id"].isin(["T2.2", "T3.2", "T3.4", "T4.1", "T5.5"])
    ].copy()
    focus.to_csv(out_dir / "replay_focus_failure_rows.csv", index=False)

    # Feature gaps for false replay positives against true Phase 7 replay positives.
    false_positive_ids = {"T2.2", "T3.4", "T5.5"}
    false_pos = ok[ok["test_id"].isin(false_positive_ids)].copy()
    phase7_replay = ok[ok["diagnostic_group"].eq("phase7_replay_positive")]
    phase7_mixer = ok[ok["diagnostic_group"].eq("phase7_mixer_negative")]
    phase7_clean = ok[ok["diagnostic_group"].eq("phase7_clean_negative")]

    feature_rows: list[dict] = []
    for feature in features:
        row = {
            "feature": feature,
            "false_positive_mean_z": safe_mean(z.loc[false_pos.index, feature]),
            "phase7_replay_mean_z": safe_mean(z.loc[phase7_replay.index, feature]),
            "phase7_mixer_mean_z": safe_mean(z.loc[phase7_mixer.index, feature]),
            "phase7_clean_mean_z": safe_mean(z.loc[phase7_clean.index, feature]),
        }
        row["gap_false_positive_vs_phase7_replay_abs"] = abs(
            row["false_positive_mean_z"] - row["phase7_replay_mean_z"]
        )
        row["closer_to_replay_than_mixer"] = abs(
            row["false_positive_mean_z"] - row["phase7_replay_mean_z"]
        ) < abs(row["false_positive_mean_z"] - row["phase7_mixer_mean_z"])
        row["closer_to_replay_than_clean"] = abs(
            row["false_positive_mean_z"] - row["phase7_replay_mean_z"]
        ) < abs(row["false_positive_mean_z"] - row["phase7_clean_mean_z"])
        feature_rows.append(row)
    feature_gap = pd.DataFrame(feature_rows).sort_values(
        "gap_false_positive_vs_phase7_replay_abs", ascending=False
    )
    feature_gap.to_csv(out_dir / "replay_false_positive_feature_gap_ranked.csv", index=False)

    group_summary = (
        ok.groupby(["diagnostic_group", "manipulation_type"], dropna=False)
        .agg(
            n=("audio_path", "size"),
            mean_replay_probability=("replay_probability", lambda s: safe_mean(s)),
            detected_rate=("replay_prediction", lambda s: safe_mean(s)),
        )
        .reset_index()
    )
    group_summary.to_csv(out_dir / "replay_group_probability_summary.csv", index=False)

    testing_focus_distances = distances[
        distances["test_id"].isin(["T2.2", "T3.2", "T3.4", "T4.1", "T5.5"])
    ]
    top_features = feature_gap.head(args.top_k)

    report = [
        "# Replay vs Channel Overlap Diagnosis",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "Purpose: explain why replay retrain still confuses mixer/edited/channel cases with replay.",
        "",
        "## Focus Testing Rows",
        "",
        testing_focus_distances.round(4).to_string(index=False),
        "",
        "## Top False-Positive Feature Gaps",
        "",
        top_features.round(4).to_string(index=False),
        "",
        "## Group Probability Summary",
        "",
        group_summary.round(4).to_string(index=False),
        "",
        "## Interpretation",
        "",
        "- If mixer/edited false positives are nearest to the replay centroid, replay and channel artifacts overlap in the current acoustic feature space.",
        "- If the missed AI replay is near replay but below threshold, threshold/calibration is part of the issue.",
        "- If clean/mixer/edited negatives have high replay probabilities, a two-stage manipulation design is more appropriate than independent replay and mixer binaries.",
        "",
        "## Outputs",
        "",
        f"- `{out_dir / 'replay_testing_audio_centroid_distances.csv'}`",
        f"- `{out_dir / 'replay_focus_failure_rows.csv'}`",
        f"- `{out_dir / 'replay_false_positive_feature_gap_ranked.csv'}`",
        f"- `{out_dir / 'replay_group_probability_summary.csv'}`",
    ]
    (out_dir / "replay_channel_overlap_diagnosis_report.md").write_text(
        "\n".join(report), encoding="utf-8"
    )

    print(f"Wrote replay/channel overlap diagnosis to {out_dir}")
    print(testing_focus_distances.round(4).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
