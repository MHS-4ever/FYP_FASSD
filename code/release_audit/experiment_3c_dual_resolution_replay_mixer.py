"""Phase 3C — Dual-resolution replay/mixer branch evaluation.

Compares baseline 16 kHz acoustic features vs dual-resolution features:
16 kHz acoustic (59 dims) + native-rate high-band ratios (2 dims).

Trains lightweight leakage-safe logistic models per axis (replay, mixer);
does not overwrite release models. No new audio collection.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from phase3_common import (
    LEAKAGE_MANIFEST,
    PHASE3_OUT,
    ROOT,
    beats_baseline,
    load_native_audio_mono,
    metric_row,
    normalized_path,
    resolve_audio,
    tqdm_iter,
)

ROOT_RELEASE = ROOT / "release"
if str(ROOT_RELEASE) not in sys.path:
    sys.path.insert(0, str(ROOT_RELEASE))

from src.audio_io import load_audio  # noqa: E402
from src.feature_extraction import extract_file_acoustic_features  # noqa: E402

# Native high-band extraction (same band edges as phase8c, computed at native SR).
PHASE8_FEAT = ROOT / "code" / "phase8" / "features"
if str(PHASE8_FEAT) not in sys.path:
    sys.path.insert(0, str(PHASE8_FEAT))
import phase8c_feature_utils as p8c  # noqa: E402

DEFAULT_OUT = PHASE3_OUT / "experiment_3c_dual_resolution_replay_mixer"
TESTING_MANIFEST = (
    ROOT
    / "reports"
    / "phase7"
    / "phase7_forensic_tests"
    / "forensic_test_manifest_backup_before_T4_3_timestamp.csv"
)

ACOUSTIC_16K_COLS = list(p8c.FILE_FEATURE_NAMES)
NATIVE_HIGHBAND_COLS = ["native_high_band_energy_ratio", "native_very_high_band_energy_ratio"]
FEATURE_MODES = {
    "baseline_16k_acoustic": "baseline",
    "dual_16k_plus_native_highband": "dual",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT))
    parser.add_argument("--random-seed", type=int, default=42)
    parser.add_argument("--max-selected-features", type=int, default=50)
    parser.add_argument("--progress-every", type=int, default=20)
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def progress(msg: str) -> None:
    print(msg, flush=True)


def native_highband_features(audio_path: Path) -> dict[str, float]:
    y, sr = load_native_audio_mono(audio_path)
    bands = p8c.compute_band_energy_features(y, sr)
    return {
        "native_high_band_energy_ratio": float(bands.get("high_band_energy_ratio", np.nan)),
        "native_very_high_band_energy_ratio": float(bands.get("very_high_band_energy_ratio", np.nan)),
    }


def extract_feature_row(audio_path: Path, mode: str) -> dict[str, float]:
    y16, sr16 = load_audio(str(audio_path), target_sample_rate=16000)
    feats = extract_file_acoustic_features(y16, sr16)
    if mode == "dual":
        feats.update(native_highband_features(audio_path))
    return feats


def feature_columns(mode: str) -> list[str]:
    if mode == "baseline":
        return ACOUSTIC_16K_COLS
    return ACOUSTIC_16K_COLS + NATIVE_HIGHBAND_COLS


def build_manifest_frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    phase7 = pd.read_csv(LEAKAGE_MANIFEST)
    phase7["target_is_replay"] = pd.to_numeric(phase7["audit_replay_gt"], errors="coerce").fillna(0).astype(int)
    phase7["target_is_mixer"] = pd.to_numeric(phase7["audit_mixer_gt"], errors="coerce").fillna(0).astype(int)
    testing = pd.read_csv(TESTING_MANIFEST, dtype=str, keep_default_na=False)
    testing["target_is_replay"] = testing["manipulation_type"].isin(["human_replay", "ai_replay"]).astype(int)
    testing["target_is_mixer"] = testing["manipulation_type"].eq("mixer_processed").astype(int)
    testing["leakage_safe_split"] = "testing_audios"
    return phase7, testing


def extract_dataset(
    manifest: pd.DataFrame,
    mode: str,
    *,
    label: str,
    progress_every: int,
) -> pd.DataFrame:
    rows: list[dict] = []
    total = len(manifest)
    manifest_rows = list(manifest.iterrows())
    for idx, (_, row) in enumerate(
        tqdm_iter(manifest_rows, desc=f"3C {mode}:{label}", unit="file"),
        start=1,
    ):
        out = row.to_dict()
        out["feature_mode"] = mode
        out["feature_status"] = "ok"
        audio = resolve_audio(str(row["audio_path"]))
        if audio is None:
            out["feature_status"] = "missing_audio"
            rows.append(out)
            continue
        try:
            out.update(extract_feature_row(audio, mode))
        except Exception as exc:
            out["feature_status"] = f"error: {exc}"
        rows.append(out)

    return pd.DataFrame(rows)


def train_and_eval_axis(
    train_df: pd.DataFrame,
    eval_frames: dict[str, pd.DataFrame],
    *,
    axis: str,
    target_col: str,
    mode: str,
    seed: int,
    max_k: int,
    out_dir: Path,
) -> tuple[pd.DataFrame, dict, Pipeline]:
    cols = feature_columns(mode)
    train_ok = train_df[train_df["feature_status"].eq("ok")].copy()
    train_ok = train_ok[train_ok["leakage_safe_split"].isin(["train", "dev"])]
    x_train = train_ok[cols].apply(pd.to_numeric, errors="coerce")
    y_train = train_ok[target_col].astype(int).to_numpy()
    usable = [c for c in x_train.columns if x_train[c].notna().any()]
    x_train = x_train[usable].fillna(x_train[usable].median())

    k = min(max_k, len(usable), max(1, len(np.unique(y_train)) * 10))
    pipe = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            (
                "select",
                SelectKBest(score_func=f_classif, k=k),
            ),
            (
                "clf",
                LogisticRegression(
                    max_iter=3000,
                    class_weight="balanced",
                    random_state=seed,
                ),
            ),
        ]
    )
    pipe.fit(x_train, y_train)

    metrics_rows: list[dict] = []
    summary = {
        "axis": axis,
        "feature_mode": mode,
        "n_train": int(len(train_ok)),
        "n_features": len(usable),
        "selected_k": int(k),
    }

    for scope, df in eval_frames.items():
        ok = df[df["feature_status"].eq("ok")].copy()
        x = ok[usable].apply(pd.to_numeric, errors="coerce").fillna(x_train[usable].median())
        prob = pipe.predict_proba(x)[:, 1]
        ok["probability"] = prob
        ok["pred"] = (prob >= 0.5).astype(int)
        ok["target"] = ok[target_col].astype(int)
        metrics_rows.append(
            metric_row(
                scope,
                ok,
                extra={"axis": axis, "feature_mode": mode},
            )
        )
        if scope == "phase7_test":
            summary["phase7_test_balanced_accuracy"] = float(metrics_rows[-1]["balanced_accuracy"])
            summary["phase7_test_fpr"] = float(metrics_rows[-1]["fpr"])
        if scope == "testing_audios":
            summary["testing_audios_balanced_accuracy"] = float(metrics_rows[-1]["balanced_accuracy"])
            summary["testing_audios_fpr"] = float(metrics_rows[-1]["fpr"])
        ok.to_csv(
            out_dir / f"predictions_{axis}_{mode}_{scope}.csv",
            index=False,
        )

    return pd.DataFrame(metrics_rows), summary, pipe


def write_decision_report(summaries: list[dict], out_dir: Path, started: str, finished: str) -> None:
    lines = [
        "# Phase 3C — Dual-resolution replay/mixer decision",
        "",
        f"- Started: {started}",
        f"- Finished: {finished}",
        "- Fixed: leakage-safe split, sklearn LR pipeline, no release model overwrite",
        "- Variable: 16 kHz acoustic only vs 16 kHz + native high-band ratios",
        "",
        "| Axis | Feature mode | Phase7 test bal-acc | Testing bal-acc | Beats baseline? |",
        "|---|---|---:|---:|---|",
    ]
    for axis in ["replay", "mixer"]:
        base = next(
            (s for s in summaries if s["axis"] == axis and s["feature_mode"] == "baseline_16k_acoustic"),
            None,
        )
        for s in summaries:
            if s["axis"] != axis:
                continue
            beat = "baseline"
            if s["feature_mode"] != "baseline_16k_acoustic" and base is not None:
                beat = "yes" if beats_baseline(s, base) else "no"
            lines.append(
                f"| {axis} | {s['feature_mode']} | {s.get('phase7_test_balanced_accuracy', float('nan')):.4f} | "
                f"{s.get('testing_audios_balanced_accuracy', float('nan')):.4f} | {beat} |"
            )
    winners = []
    for axis in ["replay", "mixer"]:
        base = next(
            (s for s in summaries if s["axis"] == axis and s["feature_mode"] == "baseline_16k_acoustic"),
            None,
        )
        dual = next(
            (s for s in summaries if s["axis"] == axis and s["feature_mode"] == "dual_16k_plus_native_highband"),
            None,
        )
        if base and dual and beats_baseline(dual, base):
            winners.append(f"{axis}:dual_16k_plus_native_highband")
    lines.extend(["", "## Decision", ""])
    if winners:
        lines.append(
            "**Pursue to Phase 4:** dual-resolution features won on both metrics for: "
            + ", ".join(winners)
        )
    else:
        lines.append(
            "**Do not pursue dual-resolution replay/mixer into Phase 4.** "
            "Native high-band add-on did not beat 16 kHz-only acoustics on both decision metrics."
        )
    (out_dir / "experiment_3c_decision.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    started = utc_now()
    progress("[3C] extracting features for phase7 + testing_audios")

    phase7, testing = build_manifest_frames()
    all_metrics: list[pd.DataFrame] = []
    summaries: list[dict] = []

    for mode_name, mode in FEATURE_MODES.items():
        p7 = extract_dataset(phase7, mode, label="phase7", progress_every=args.progress_every)
        ta = extract_dataset(testing, mode, label="testing", progress_every=args.progress_every)
        p7.to_csv(out_dir / f"features_phase7_{mode_name}.csv", index=False)
        ta.to_csv(out_dir / f"features_testing_audios_{mode_name}.csv", index=False)

        for axis, target in [("replay", "target_is_replay"), ("mixer", "target_is_mixer")]:
            eval_frames = {
                "phase7_test": p7[p7["leakage_safe_split"].eq("test")],
                "testing_audios": ta,
            }
            metrics, summary, pipe = train_and_eval_axis(
                p7,
                eval_frames,
                axis=axis,
                target_col=target,
                mode=mode,
                seed=args.random_seed,
                max_k=args.max_selected_features,
                out_dir=out_dir,
            )
            all_metrics.append(metrics)
            summaries.append(summary)
            joblib.dump(pipe, out_dir / f"model_{axis}_{mode_name}.joblib")
            progress(f"[3C] trained {axis}/{mode_name}")

    pd.concat(all_metrics, ignore_index=True).to_csv(out_dir / "experiment_3c_metrics.csv", index=False)
    pd.DataFrame(summaries).to_csv(out_dir / "experiment_3c_summary.csv", index=False)
    finished = utc_now()
    write_decision_report(summaries, out_dir, started, finished)
    with open(out_dir / "experiment_3c_metadata.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "started_at": started,
                "finished_at": finished,
                "feature_modes": list(FEATURE_MODES.keys()),
                "native_highband_cols": NATIVE_HIGHBAND_COLS,
            },
            f,
            indent=2,
        )
    progress(f"[3C] complete -> {out_dir}")


if __name__ == "__main__":
    main()
