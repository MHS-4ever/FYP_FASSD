"""Phase 3B — Window-level origin aggregation (segment SSL + top-k/MIL).

Reuses cached Phase 8 segment SSL embeddings. Holds model and threshold fixed;
varies only file-level aggregation over segment probabilities.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from phase3_common import (
    ORIGIN_THRESHOLD,
    PHASE3_OUT,
    PHASE8_SEGMENT_SSL,
    ROOT,
    beats_baseline,
    load_origin_model,
    metric_row,
    normalized_path,
    phase7_origin_eval_frame,
    predict_origin_probability,
    ssl_columns,
    testing_origin_eval_frame,
    tqdm_iter,
)

DEFAULT_OUT = PHASE3_OUT / "experiment_3b_window_origin"

AGGREGATORS = {
    "file_mean_ssl": "mean_embedding_then_score",
    "segment_max_prob": "max_segment_probability",
    "segment_top3_mean_prob": "top3_segment_probability_mean",
    "segment_noisy_or_max": "noisy_or_max_probability",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT))
    parser.add_argument(
        "--aggregators",
        default=",".join(AGGREGATORS.keys()),
        help="Comma-separated aggregator ids",
    )
    parser.add_argument("--top-k", type=int, default=3)
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def progress(msg: str) -> None:
    print(msg, flush=True)


def segment_probabilities(
    seg_df: pd.DataFrame,
    origin_model,
    origin_meta,
) -> pd.DataFrame:
    cols = ssl_columns()
    rows: list[dict] = []
    seg_rows = list(seg_df.iterrows())
    for _, row in tqdm_iter(seg_rows, desc="3B segment SSL scoring", unit="seg"):
        feats = {c: float(row[c]) for c in cols if c in row.index and pd.notna(row[c])}
        if len(feats) != len(cols):
            continue
        prob = predict_origin_probability(origin_model, origin_meta, feats)
        rows.append(
            {
                "file_id": row["file_id"],
                "segment_id": row["segment_id"],
                "audio_path": row["audio_path"],
                "segment_probability": prob,
            }
        )
    return pd.DataFrame(rows)


def aggregate_file_probability(seg_probs: pd.DataFrame, method: str, top_k: int) -> pd.DataFrame:
    grouped = []
    for file_id, group in seg_probs.groupby("file_id", sort=False):
        probs = group["segment_probability"].to_numpy(dtype=float)
        audio_path = group["audio_path"].iloc[0]
        if method == "max_segment_probability":
            file_prob = float(np.max(probs))
        elif method == "top3_segment_probability_mean":
            k = min(top_k, len(probs))
            file_prob = float(np.mean(np.sort(probs)[-k:]))
        elif method == "noisy_or_max_probability":
            # MIL-style noisy-OR over segment posteriors (cap at 1.0).
            file_prob = float(1.0 - np.prod(1.0 - np.clip(probs, 0.0, 1.0)))
        else:
            raise ValueError(method)
        grouped.append(
            {
                "file_id": file_id,
                "audio_path": audio_path,
                "probability": file_prob,
                "n_segments": len(probs),
            }
        )
    return pd.DataFrame(grouped)


def file_mean_from_cached_file_ssl(
    manifest: pd.DataFrame,
    file_ssl: pd.DataFrame,
    origin_model,
    origin_meta,
) -> pd.DataFrame:
    file_ssl = file_ssl.copy()
    file_ssl["_join_audio_path"] = file_ssl["audio_path"].map(normalized_path)
    merged = manifest.merge(file_ssl[["_join_audio_path"] + ssl_columns()], on="_join_audio_path", how="left")
    rows = []
    cols = ssl_columns()
    for _, row in merged.iterrows():
        out = {
            "audio_path": row["audio_path"],
            "eval_status": "ok",
        }
        if any(pd.isna(row.get(c)) for c in cols):
            out["eval_status"] = "missing_cached_ssl"
        else:
            feats = {c: float(row[c]) for c in cols}
            out["probability"] = predict_origin_probability(origin_model, origin_meta, feats)
        for col in manifest.columns:
            if col not in out:
                out[col] = row[col]
        rows.append(out)
    return pd.DataFrame(rows)


def eval_predictions(
    aggregator: str,
    phase7: pd.DataFrame,
    testing: pd.DataFrame,
    threshold: float,
) -> tuple[pd.DataFrame, dict]:
    metrics_rows: list[dict] = []
    summary = {"aggregator": aggregator, "threshold": threshold}

    for label, df in [("phase7", phase7), ("testing_audios", testing)]:
        ok = df[df["eval_status"].eq("ok")].copy()
        ok["pred"] = (ok["probability"] >= threshold).astype(int)
        if label == "phase7":
            for split in ["train", "dev", "test", "all"]:
                scope_df = ok if split == "all" else ok[ok["leakage_safe_split"].eq(split)]
                metrics_rows.append(
                    metric_row(
                        f"phase7_{split}",
                        scope_df,
                        extra={"aggregator": aggregator, "dataset": label, "split": split},
                    )
                )
                if split == "test":
                    summary["phase7_test_balanced_accuracy"] = float(
                        metrics_rows[-1].get("balanced_accuracy", float("nan"))
                    )
                    summary["phase7_test_fpr"] = float(metrics_rows[-1].get("fpr", float("nan")))
        else:
            metrics_rows.append(
                metric_row(
                    "testing_audios",
                    ok,
                    extra={"aggregator": aggregator, "dataset": label, "split": "all"},
                )
            )
            summary["testing_audios_balanced_accuracy"] = float(
                metrics_rows[-1].get("balanced_accuracy", float("nan"))
            )
            summary["testing_audios_fpr"] = float(metrics_rows[-1].get("fpr", float("nan")))

    return pd.DataFrame(metrics_rows), summary


def write_decision_report(summaries: list[dict], out_dir: Path, started: str, finished: str) -> None:
    baseline = next((s for s in summaries if s["aggregator"] == "file_mean_ssl"), summaries[0])
    winners = [
        s for s in summaries if s["aggregator"] != "file_mean_ssl" and beats_baseline(s, baseline)
    ]
    pursue = len(winners) > 0
    lines = [
        "# Phase 3B — Window-level origin decision",
        "",
        f"- Started: {started}",
        f"- Finished: {finished}",
        f"- Fixed: promoted origin model, threshold={ORIGIN_THRESHOLD}, cached segment SSL",
        f"- Variable: segment-to-file aggregation",
        "",
        "| Aggregator | Phase7 test bal-acc | Testing bal-acc | Beats file mean? |",
        "|---|---:|---:|---|",
    ]
    for s in summaries:
        beat = (
            "baseline"
            if s["aggregator"] == "file_mean_ssl"
            else ("yes" if beats_baseline(s, baseline) else "no")
        )
        lines.append(
            f"| {s['aggregator']} | {s.get('phase7_test_balanced_accuracy', float('nan')):.4f} | "
            f"{s.get('testing_audios_balanced_accuracy', float('nan')):.4f} | {beat} |"
        )
    lines.extend(["", "## Decision", ""])
    if pursue:
        lines.append(
            "**Pursue to Phase 4:** "
            + ", ".join(s["aggregator"] for s in winners)
            + " beat whole-file mean on both leakage-safe test and testing_audios."
        )
    else:
        lines.append(
            "**Do not pursue window-level origin into Phase 4.** "
            "No aggregator beat file-mean SSL on both decision metrics."
        )
    (out_dir / "experiment_3b_decision.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    aggregators = [a.strip() for a in args.aggregators.split(",") if a.strip()]
    started = utc_now()
    progress(f"[3B] start aggregators={aggregators}")

    origin_model, origin_meta = load_origin_model()
    seg_raw = pd.read_csv(PHASE8_SEGMENT_SSL)
    seg_raw["_join_audio_path"] = seg_raw["audio_path"].map(normalized_path)
    progress(f"[3B] segment rows={len(seg_raw)} files={seg_raw['file_id'].nunique()}")

    seg_probs = segment_probabilities(seg_raw, origin_model, origin_meta)
    seg_probs.to_csv(out_dir / "segment_origin_probabilities.csv", index=False)

    file_ssl = pd.read_csv(ROOT / "reports" / "phase8" / "embeddings" / "phase8d_file_ssl_embeddings.csv")
    phase7_manifest = phase7_origin_eval_frame()
    testing_manifest = testing_origin_eval_frame()

    all_metrics: list[pd.DataFrame] = []
    summaries: list[dict] = []

    for agg in aggregators:
        if agg not in AGGREGATORS:
            raise SystemExit(f"Unknown aggregator: {agg}")
        method = AGGREGATORS[agg]
        if agg == "file_mean_ssl":
            p7 = file_mean_from_cached_file_ssl(phase7_manifest, file_ssl, origin_model, origin_meta)
            # testing_audios has no cached file SSL — use segment max as proxy unavailable; extract from segments if any
            ta_seg = seg_probs.merge(
                testing_manifest.assign(_join_audio_path=testing_manifest["audio_path"].map(normalized_path)),
                left_on="audio_path",
                right_on="_join_audio_path",
                how="inner",
            )
            if ta_seg.empty:
                ta = testing_manifest.copy()
                ta["eval_status"] = "no_cached_segments_for_testing_audios"
                ta["probability"] = np.nan
            else:
                ta_file = aggregate_file_probability(
                    ta_seg.rename(columns={"segment_probability": "segment_probability"}),
                    "max_segment_probability",
                    args.top_k,
                )
                ta = testing_manifest.copy()
                ta["_join_audio_path"] = ta["audio_path"].map(normalized_path)
                ta_file["_join_audio_path"] = ta_file["audio_path"].map(normalized_path)
                ta = ta.merge(ta_file[["_join_audio_path", "probability"]], on="_join_audio_path", how="left")
                ta["eval_status"] = np.where(ta["probability"].notna(), "ok", "missing_segments")
        else:
            file_probs = aggregate_file_probability(seg_probs, method, args.top_k)
            file_probs["_join_audio_path"] = file_probs["audio_path"].map(normalized_path)
            p7 = phase7_manifest.merge(
                file_probs[["_join_audio_path", "probability", "n_segments"]],
                on="_join_audio_path",
                how="left",
            )
            p7["eval_status"] = np.where(p7["probability"].notna(), "ok", "missing_segments")
            ta = testing_manifest.copy()
            ta["_join_audio_path"] = ta["audio_path"].map(normalized_path)
            ta = ta.merge(file_probs[["_join_audio_path", "probability", "n_segments"]], on="_join_audio_path", how="left")
            ta["eval_status"] = np.where(ta["probability"].notna(), "ok", "missing_segments")

        p7.to_csv(out_dir / f"predictions_phase7_{agg}.csv", index=False)
        ta.to_csv(out_dir / f"predictions_testing_audios_{agg}.csv", index=False)
        metrics, summary = eval_predictions(agg, p7, ta, ORIGIN_THRESHOLD)
        all_metrics.append(metrics)
        summaries.append(summary)
        progress(f"[3B] done {agg}")

    pd.concat(all_metrics, ignore_index=True).to_csv(out_dir / "experiment_3b_metrics_by_aggregator.csv", index=False)
    pd.DataFrame(summaries).to_csv(out_dir / "experiment_3b_summary.csv", index=False)
    finished = utc_now()
    write_decision_report(summaries, out_dir, started, finished)
    with open(out_dir / "experiment_3b_metadata.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "started_at": started,
                "finished_at": finished,
                "aggregators": aggregators,
                "top_k": args.top_k,
                "segment_ssl": str(PHASE8_SEGMENT_SSL),
            },
            f,
            indent=2,
        )
    progress(f"[3B] complete -> {out_dir}")


if __name__ == "__main__":
    main()
