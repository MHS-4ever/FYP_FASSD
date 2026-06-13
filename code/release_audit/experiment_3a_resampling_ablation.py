"""Phase 3A — Resampling ablation for origin SSL front-end.

Holds model, threshold, and leakage-safe split fixed; varies only the
resampling chain before WavLM (always ending at 16 kHz).

Decision rule: if no chain beats ssl_16k_direct on leakage-safe test AND
testing_audios balanced accuracy, close the resampling question.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from phase3_common import (
    LEAKAGE_MANIFEST,
    ORIGIN_THRESHOLD,
    PHASE3_OUT,
    RESAMPLE_VARIANTS,
    ROOT,
    TESTING_MANIFEST,
    apply_resample_chain,
    beats_baseline,
    load_native_audio_mono,
    load_origin_model,
    metric_row,
    normalized_path,
    phase7_origin_eval_frame,
    predict_origin_probability,
    resolve_audio,
    ssl_columns,
    testing_origin_eval_frame,
    tqdm_iter,
    variant_outputs_complete,
)

ROOT_STR = str(ROOT)
if str(ROOT / "release") not in sys.path:
    sys.path.insert(0, str(ROOT / "release"))

from src.ssl_embeddings import extract_file_ssl_embedding, load_ssl_extractor  # noqa: E402

DEFAULT_OUT = PHASE3_OUT / "experiment_3a_resampling_ablation"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT))
    parser.add_argument(
        "--device",
        default="cuda",
        help="cuda (recommended), cpu, or auto",
    )
    parser.add_argument(
        "--force-rerun",
        action="store_true",
        help="Re-run all variants even if prediction CSVs already exist",
    )
    parser.add_argument(
        "--variants",
        default=",".join(RESAMPLE_VARIANTS.keys()),
        help="Comma-separated variant ids",
    )
    parser.add_argument("--progress-every", type=int, default=10)
    parser.add_argument(
        "--use-cached-baseline",
        action="store_true",
        default=True,
        help="Use cached Phase 8 file SSL for ssl_16k_direct on Phase 7",
    )
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def progress(msg: str) -> None:
    print(msg, flush=True)


def extract_ssl_for_chain(
    audio_path: Path,
    chain_hz: list[int],
    model,
    processor,
    device,
) -> dict[str, float]:
    y, sr = load_native_audio_mono(audio_path)
    y16, sr16 = apply_resample_chain(y, sr, chain_hz)
    return extract_file_ssl_embedding(y16, sr16, model, processor, device)


def eval_variant_predictions(
    variant: str,
    phase7_probs: pd.DataFrame,
    testing_probs: pd.DataFrame,
    threshold: float,
) -> tuple[pd.DataFrame, dict[str, float]]:
    metrics_rows: list[dict] = []
    summary: dict[str, float] = {"variant": variant, "threshold": threshold}

    for label, df in [("phase7", phase7_probs), ("testing_audios", testing_probs)]:
        ok = df[df["eval_status"].eq("ok")].copy()
        ok["pred"] = (ok["probability"] >= threshold).astype(int)
        for split in sorted(ok.get("leakage_safe_split", pd.Series(["all"])).dropna().unique()) if label == "phase7" else ["all"]:
            scope_name = f"{label}_{split}" if label == "phase7" else label
            scope_df = ok if split == "all" else ok[ok["leakage_safe_split"].eq(split)]
            metrics_rows.append(
                metric_row(scope_name, scope_df, extra={"variant": variant, "dataset": label, "split": split})
            )
            if label == "phase7" and split == "test":
                summary["phase7_test_balanced_accuracy"] = float(
                    metrics_rows[-1].get("balanced_accuracy", float("nan"))
                )
                summary["phase7_test_recall"] = float(metrics_rows[-1].get("recall", float("nan")))
                summary["phase7_test_fpr"] = float(metrics_rows[-1].get("fpr", float("nan")))
            if label == "testing_audios" and split == "all":
                summary["testing_audios_balanced_accuracy"] = float(
                    metrics_rows[-1].get("balanced_accuracy", float("nan"))
                )
                summary["testing_audios_recall"] = float(metrics_rows[-1].get("recall", float("nan")))
                summary["testing_audios_fpr"] = float(metrics_rows[-1].get("fpr", float("nan")))

        if label == "phase7":
            train_scope = ok[ok.get("origin_training_scope", False).astype(bool)]
            metrics_rows.append(
                metric_row(
                    "phase7_all_origin_training_scope",
                    train_scope,
                    extra={"variant": variant, "dataset": label, "split": "origin_training_scope"},
                )
            )

    return pd.DataFrame(metrics_rows), summary


def run_variant(
    variant: str,
    chain_hz: list[int],
    *,
    device: str,
    use_cached_baseline: bool,
    progress_every: int,
    out_dir: Path,
    origin_model,
    origin_meta,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, float]]:
    cache_path = out_dir / f"embeddings_{variant}.csv"
    threshold = float(ORIGIN_THRESHOLD)
    ssl_model = ssl_processor = ssl_device = None
    if cache_path.is_file():
        cached = pd.read_csv(cache_path)
    else:
        cached = None

    if cached is None or variant != "ssl_16k_direct" or not use_cached_baseline:
        ssl_model, ssl_processor, ssl_device = load_ssl_extractor(device=device)

    phase7 = phase7_origin_eval_frame()
    testing = testing_origin_eval_frame()

    # Baseline Phase 7: reuse cached Phase 8 file SSL when available.
    if variant == "ssl_16k_direct" and use_cached_baseline:
        file_ssl = pd.read_csv(ROOT / "reports" / "phase8" / "embeddings" / "phase8d_file_ssl_embeddings.csv")
        file_ssl["_join_audio_path"] = file_ssl["audio_path"].map(normalized_path)
        phase7 = phase7.merge(file_ssl[["_join_audio_path"] + ssl_columns()], on="_join_audio_path", how="left")

    rows_p7: list[dict] = []
    phase7_iter = list(phase7.iterrows())
    for _, row in tqdm_iter(phase7_iter, desc=f"3A {variant} phase7", unit="file"):
        out = {
            "variant": variant,
            "sample_id": row.get("sample_id"),
            "audio_path": row.get("audio_path"),
            "leakage_safe_split": row.get("leakage_safe_split"),
            "audit_condition": row.get("audit_condition"),
            "target": row.get("target"),
            "origin_training_scope": row.get("origin_training_scope"),
            "eval_status": "ok",
        }
        feats: dict[str, float] | None = None
        if variant == "ssl_16k_direct" and use_cached_baseline:
            cols = ssl_columns()
            if any(pd.isna(row.get(c)) for c in cols):
                out["eval_status"] = "missing_cached_ssl"
            else:
                feats = {c: float(row[c]) for c in cols}
        else:
            audio = resolve_audio(str(row["audio_path"]))
            if audio is None:
                out["eval_status"] = "missing_audio"
            else:
                try:
                    feats = extract_ssl_for_chain(audio, chain_hz, ssl_model, ssl_processor, ssl_device)
                except Exception as exc:
                    out["eval_status"] = f"ssl_error: {exc}"
        if feats is not None:
            out["probability"] = predict_origin_probability(origin_model, origin_meta, feats)
        rows_p7.append(out)

    rows_ta: list[dict] = []
    testing_iter = list(testing.iterrows())
    for _, row in tqdm_iter(testing_iter, desc=f"3A {variant} testing", unit="file"):
        out = {
            "variant": variant,
            "test_id": row.get("test_id"),
            "audio_path": row.get("audio_path"),
            "manipulation_type": row.get("manipulation_type"),
            "target": row.get("target"),
            "leakage_safe_split": "all",
            "eval_status": "ok",
        }
        audio = resolve_audio(str(row["audio_path"]))
        if audio is None:
            out["eval_status"] = "missing_audio"
        else:
            try:
                feats = extract_ssl_for_chain(audio, chain_hz, ssl_model, ssl_processor, ssl_device)
                out["probability"] = predict_origin_probability(origin_model, origin_meta, feats)
            except Exception as exc:
                out["eval_status"] = f"ssl_error: {exc}"
        rows_ta.append(out)

    pred_p7 = pd.DataFrame(rows_p7)
    pred_ta = pd.DataFrame(rows_ta)
    metrics, summary = eval_variant_predictions(variant, pred_p7, pred_ta, threshold)
    pred_p7.to_csv(out_dir / f"predictions_phase7_{variant}.csv", index=False)
    pred_ta.to_csv(out_dir / f"predictions_testing_audios_{variant}.csv", index=False)
    return metrics, pred_p7, pred_ta, summary


def write_decision_report(
    summaries: list[dict],
    out_dir: Path,
    *,
    started_at: str,
    finished_at: str,
) -> None:
    baseline = next((s for s in summaries if s["variant"] == "ssl_16k_direct"), summaries[0])
    winners = [s for s in summaries if s["variant"] != "ssl_16k_direct" and beats_baseline(s, baseline)]
    close_question = len(winners) == 0

    lines = [
        "# Phase 3A — Resampling ablation decision",
        "",
        f"- Started: {started_at}",
        f"- Finished: {finished_at}",
        f"- Fixed model: promoted Phase 2 origin (`threshold={ORIGIN_THRESHOLD}`)",
        f"- Fixed split: leakage-safe `base_id` manifest",
        f"- Variable: SSL front-end resampling chain (WavLM input always 16 kHz)",
        "",
        "## Summary table",
        "",
        "| Variant | Phase7 test bal-acc | Testing bal-acc | Phase7 test FPR | Beats 16 kHz? |",
        "|---|---:|---:|---:|---|",
    ]
    for s in summaries:
        beat = "yes" if s["variant"] != "ssl_16k_direct" and beats_baseline(s, baseline) else (
            "baseline" if s["variant"] == "ssl_16k_direct" else "no"
        )
        lines.append(
            f"| {s['variant']} | {s.get('phase7_test_balanced_accuracy', float('nan')):.4f} | "
            f"{s.get('testing_audios_balanced_accuracy', float('nan')):.4f} | "
            f"{s.get('phase7_test_fpr', float('nan')):.4f} | {beat} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
        ]
    )
    if close_question:
        lines.append(
            "**CLOSE resampling question permanently in thesis.** "
            "No alternative chain beat `ssl_16k_direct` on both leakage-safe test and testing_audios."
        )
    else:
        lines.append(
            f"**Do not close yet.** Winners on both metrics: "
            + ", ".join(s["variant"] for s in winners)
            + ". Pursue only after confirming no FP inflation on dev."
        )
    (out_dir / "experiment_3a_decision.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_summary_from_predictions(variant: str, out_dir: Path, threshold: float) -> dict:
    p7 = pd.read_csv(out_dir / f"predictions_phase7_{variant}.csv")
    ta = pd.read_csv(out_dir / f"predictions_testing_audios_{variant}.csv")
    _, summary = eval_variant_predictions(variant, p7, ta, threshold)
    summary["variant"] = variant
    summary["resumed_from_disk"] = True
    return summary


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    variants = [v.strip() for v in args.variants.split(",") if v.strip()]
    started = utc_now()
    skip_completed = not args.force_rerun
    progress(f"[3A] start variants={variants} device={args.device} resume={skip_completed}")

    origin_model, origin_meta = load_origin_model()
    all_metrics: list[pd.DataFrame] = []
    summaries: list[dict] = []

    variant_bar = tqdm_iter(variants, desc="3A variants", unit="variant")
    for variant in variant_bar:
        if variant not in RESAMPLE_VARIANTS:
            raise SystemExit(f"Unknown variant: {variant}")
        if skip_completed and variant_outputs_complete(out_dir, variant):
            progress(f"[3A] skip {variant} (outputs exist)")
            summaries.append(load_summary_from_predictions(variant, out_dir, ORIGIN_THRESHOLD))
            continue
        t0 = time.time()
        progress(f"[3A] running {variant} ...")
        metrics, _, _, summary = run_variant(
            variant,
            RESAMPLE_VARIANTS[variant],
            device=args.device,
            use_cached_baseline=args.use_cached_baseline,
            progress_every=args.progress_every,
            out_dir=out_dir,
            origin_model=origin_model,
            origin_meta=origin_meta,
        )
        summary["elapsed_sec"] = round(time.time() - t0, 2)
        summaries.append(summary)
        all_metrics.append(metrics)
        progress(f"[3A] done {variant} in {summary['elapsed_sec']}s")

    # Rebuild metrics from all variant prediction files (resume-safe).
    all_metrics = []
    for variant in variants:
        if not variant_outputs_complete(out_dir, variant):
            continue
        p7 = pd.read_csv(out_dir / f"predictions_phase7_{variant}.csv")
        ta = pd.read_csv(out_dir / f"predictions_testing_audios_{variant}.csv")
        m, _ = eval_variant_predictions(variant, p7, ta, ORIGIN_THRESHOLD)
        all_metrics.append(m)

    # Keep summaries in the requested variant order.
    summary_by_variant = {s["variant"]: s for s in summaries}
    summaries = [summary_by_variant[v] for v in variants if v in summary_by_variant]

    metrics_df = pd.concat(all_metrics, ignore_index=True) if all_metrics else pd.DataFrame()
    metrics_df.to_csv(out_dir / "experiment_3a_metrics_by_variant.csv", index=False)
    pd.DataFrame(summaries).to_csv(out_dir / "experiment_3a_summary.csv", index=False)
    finished = utc_now()
    write_decision_report(summaries, out_dir, started_at=started, finished_at=finished)
    with open(out_dir / "experiment_3a_metadata.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "started_at": started,
                "finished_at": finished,
                "variants": variants,
                "device": args.device,
                "origin_threshold": ORIGIN_THRESHOLD,
                "manifests": {
                    "leakage_safe": str(LEAKAGE_MANIFEST),
                    "testing_audios": str(TESTING_MANIFEST),
                },
            },
            f,
            indent=2,
        )
    progress(f"[3A] complete -> {out_dir}")


if __name__ == "__main__":
    main()
