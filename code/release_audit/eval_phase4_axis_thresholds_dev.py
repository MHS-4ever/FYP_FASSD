"""Phase 4 — Re-derive replay/mixer release-model thresholds on leakage-safe dev only.

Does not retrain or overwrite release/models. Writes experimental threshold
recommendations under the Phase 4 report folder for comparison with packaged
threshold_candidate values (0.65 replay, 0.75 mixer).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / "release"
if str(RELEASE) not in sys.path:
    sys.path.insert(0, str(RELEASE))

from src.feature_extraction import align_features_to_metadata  # noqa: E402
from src.model_loader import get_model_input_feature_names, get_threshold  # noqa: E402

from retrain_mixer_channel_experimental import (  # noqa: E402
    LEAKAGE_MANIFEST,
    choose_threshold as choose_mixer_threshold,
    predict_frame as predict_mixer_frame,
)
from retrain_replay_experimental import (  # noqa: E402
    choose_threshold as choose_replay_threshold,
    extract_rows as extract_replay_rows,
    predict_frame as predict_replay_frame,
)

DEFAULT_OUT = ROOT / "reports" / "release_audit" / "phase4_two_stage_manipulation_v3_2026-06-13"
REPLAY_MODEL = RELEASE / "models" / "replay" / "replay_file_model__acoustic__experimental.joblib"
REPLAY_META = RELEASE / "models" / "replay" / "replay_file_model__acoustic__metadata.json"
MIXER_MODEL = RELEASE / "models" / "mixer" / "mixer_file_model__acoustic__experimental.joblib"
MIXER_META = RELEASE / "models" / "mixer" / "mixer_file_model__acoustic__metadata.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT))
    parser.add_argument("--features-csv", default="", help="Reuse phase7_features_base.csv from v3 train")
    parser.add_argument("--min-dev-specificity-replay", type=float, default=0.90)
    parser.add_argument("--min-dev-specificity-mixer", type=float, default=0.90)
    parser.add_argument("--progress-every", type=int, default=5)
    return parser.parse_args()


def progress(msg: str) -> None:
    print(msg, flush=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_dev_features(args: argparse.Namespace) -> pd.DataFrame:
    if args.features_csv:
        path = Path(args.features_csv)
        if not path.is_file():
            raise FileNotFoundError(f"features-csv not found: {path}")
        progress(f"[phase4-thresholds] loading cached features: {path}")
        df = pd.read_csv(path)
        if "target_is_replay" not in df.columns:
            df["target_is_replay"] = pd.to_numeric(df["audit_replay_gt"], errors="coerce").fillna(0).astype(int)
        if "target_is_mixer_channel" not in df.columns:
            df["target_is_mixer_channel"] = pd.to_numeric(df["audit_mixer_gt"], errors="coerce").fillna(0).astype(
                int
            )
        return df[df["eval_split"].eq("dev")].copy()

    manifest = pd.read_csv(LEAKAGE_MANIFEST, dtype=str, keep_default_na=False)
    replay_eligible = manifest[
        manifest["ground_truth_origin"].isin(["human", "ai"])
        & manifest["partial_fabrication_binary"].astype(str).isin(["0", "false", "False", ""])
        & manifest["manipulation_type"].isin(["clean_direct", "ai_replay", "human_replay", "mixer_processed"])
    ].copy()
    progress("[phase4-thresholds] extracting dev acoustic features (replay axis eligibility)")
    replay_df = extract_replay_rows(
        replay_eligible,
        testing=False,
        label="phase7_replay",
        max_duration_sec=None,
        progress_every=args.progress_every,
    )
    dev = replay_df[replay_df["eval_split"].eq("dev")].copy()
    dev["target_is_mixer_channel"] = pd.to_numeric(dev["audit_mixer_gt"], errors="coerce").fillna(0).astype(int)
    return dev


def predict_release_axis(
    model,
    meta: dict,
    df: pd.DataFrame,
    *,
    prob_col: str,
    pred_col: str,
    threshold: float,
) -> pd.DataFrame:
    out = df.copy()
    feature_names = get_model_input_feature_names(model, meta)
    out[prob_col] = np.nan
    out[pred_col] = np.nan
    ok = out["feature_status"].eq("ok")
    for idx in out.index[ok]:
        row = out.loc[idx].to_dict()
        x = align_features_to_metadata(row, feature_names)
        prob = float(model.predict_proba(x)[0, 1])
        out.at[idx, prob_col] = prob
        out.at[idx, pred_col] = int(prob >= threshold)
    return out


def axis_summary(
    axis: str,
    dev_pred: pd.DataFrame,
    *,
    prob_col: str,
    target_col: str,
    chosen_threshold: float,
    release_threshold: float,
    grid: pd.DataFrame,
) -> dict:
    ok = dev_pred[dev_pred["feature_status"].eq("ok")].copy()
    at_chosen = ok.copy()
    at_chosen[f"{axis}_prediction"] = (at_chosen[prob_col].astype(float) >= chosen_threshold).astype(int)
    at_release = ok.copy()
    at_release[f"{axis}_prediction"] = (at_release[prob_col].astype(float) >= release_threshold).astype(int)

    def _rates(frame: pd.DataFrame) -> dict:
        y = frame[target_col].astype(int).to_numpy()
        pred = frame[f"{axis}_prediction"].astype(int).to_numpy()
        tp = int(((y == 1) & (pred == 1)).sum())
        fn = int(((y == 1) & (pred == 0)).sum())
        tn = int(((y == 0) & (pred == 0)).sum())
        fp = int(((y == 0) & (pred == 1)).sum())
        return {
            "n": int(len(frame)),
            "tp": tp,
            "tn": tn,
            "fp": fp,
            "fn": fn,
            "recall": float(tp / max(tp + fn, 1)),
            "specificity": float(tn / max(tn + fp, 1)),
        }

    return {
        "axis": axis,
        "release_threshold_candidate": release_threshold,
        "phase4_dev_recommended_threshold": chosen_threshold,
        "dev_at_recommended": _rates(at_chosen),
        "dev_at_release_threshold": _rates(at_release),
        "grid_rows": int(len(grid)),
    }


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    features_csv = args.features_csv or str(out_dir / "phase7_features_base.csv")
    if Path(features_csv).is_file():
        args.features_csv = features_csv
    dev = load_dev_features(args)
    progress(f"[phase4-thresholds] dev rows: {len(dev)}")

    replay_model = joblib.load(REPLAY_MODEL)
    replay_meta = json.loads(REPLAY_META.read_text(encoding="utf-8"))
    mixer_model = joblib.load(MIXER_MODEL)
    mixer_meta = json.loads(MIXER_META.read_text(encoding="utf-8"))

    replay_features = get_model_input_feature_names(replay_model, replay_meta)
    mixer_features = get_model_input_feature_names(mixer_model, mixer_meta)

    dev_replay_probe = predict_release_axis(
        replay_model,
        replay_meta,
        dev,
        prob_col="replay_probability",
        pred_col="replay_prediction",
        threshold=0.5,
    )
    replay_th, replay_grid = choose_replay_threshold(dev_replay_probe, args.min_dev_specificity_replay)
    dev_replay = predict_replay_frame(replay_model, dev_replay_probe, replay_features, replay_th)

    dev_mixer_probe = predict_release_axis(
        mixer_model,
        mixer_meta,
        dev,
        prob_col="mixer_probability",
        pred_col="mixer_prediction",
        threshold=0.5,
    )
    mixer_th, mixer_grid = choose_mixer_threshold(dev_mixer_probe, args.min_dev_specificity_mixer)
    dev_mixer = predict_mixer_frame(mixer_model, dev_mixer_probe, mixer_features, mixer_th)

    dev_replay.to_csv(out_dir / "phase4_replay_dev_predictions.csv", index=False)
    dev_mixer.to_csv(out_dir / "phase4_mixer_dev_predictions.csv", index=False)
    if len(replay_grid):
        replay_grid.to_csv(out_dir / "phase4_replay_dev_threshold_grid.csv", index=False)
    if len(mixer_grid):
        mixer_grid.to_csv(out_dir / "phase4_mixer_dev_threshold_grid.csv", index=False)

    release_replay_th = float(get_threshold(replay_meta))
    release_mixer_th = float(get_threshold(mixer_meta))
    summary = {
        "created_at": utc_now(),
        "dev_split": "leakage_safe_dev",
        "does_not_overwrite_release_models": True,
        "replay": axis_summary(
            "replay",
            dev_replay_probe,
            prob_col="replay_probability",
            target_col="target_is_replay",
            chosen_threshold=replay_th,
            release_threshold=release_replay_th,
            grid=replay_grid,
        ),
        "mixer": axis_summary(
            "mixer",
            dev_mixer_probe,
            prob_col="mixer_probability",
            target_col="target_is_mixer_channel",
            chosen_threshold=mixer_th,
            release_threshold=release_mixer_th,
            grid=mixer_grid,
        ),
    }
    (out_dir / "phase4_axis_threshold_recommendations.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    report = [
        "# Phase 4 — Replay/Mixer dev threshold re-derivation",
        "",
        f"Generated: {utc_now()}",
        "",
        "Release models are **not** modified. Recommendations are experimental.",
        "",
        "## Replay",
        "",
        f"- Release `threshold_candidate`: `{release_replay_th}`",
        f"- Phase 4 dev recommendation (min specificity {args.min_dev_specificity_replay}): `{replay_th}`",
        f"- Dev recall @ recommended: `{summary['replay']['dev_at_recommended']['recall']:.4f}`",
        f"- Dev recall @ release threshold: `{summary['replay']['dev_at_release_threshold']['recall']:.4f}`",
        "",
        "## Mixer",
        "",
        f"- Release `threshold_candidate`: `{release_mixer_th}`",
        f"- Phase 4 dev recommendation (min specificity {args.min_dev_specificity_mixer}): `{mixer_th}`",
        f"- Dev recall @ recommended: `{summary['mixer']['dev_at_recommended']['recall']:.4f}`",
        f"- Dev recall @ release threshold: `{summary['mixer']['dev_at_release_threshold']['recall']:.4f}`",
    ]
    (out_dir / "phase4_axis_threshold_recommendations.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    progress(f"[phase4-thresholds] replay dev threshold: {replay_th} (release={release_replay_th})")
    progress(f"[phase4-thresholds] mixer dev threshold: {mixer_th} (release={release_mixer_th})")
    progress(f"[phase4-thresholds] complete -> {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
