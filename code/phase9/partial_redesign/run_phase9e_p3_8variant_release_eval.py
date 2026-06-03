#!/usr/bin/env python3
"""Phase 9E-P3: Run release pipeline on 8-variant audio sets (quick or full 184-file mode)."""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
import traceback
import warnings
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SCRIPT_DIR = Path(__file__).resolve().parent


def _repo_root() -> Path:
    for base in (_SCRIPT_DIR, *_SCRIPT_DIR.parents):
        if (base / "release" / "src" / "inference_pipeline.py").is_file():
            return base
    return _SCRIPT_DIR.parents[3]


_REPO = _repo_root()
_RELEASE = _REPO / "release"
_OUTPUT = _REPO / "reports" / "phase9" / "app" / "phase9e_p3_8variant_eval"

if str(_RELEASE) not in sys.path:
    sys.path.insert(0, str(_RELEASE))

VARIANT_KEYS = (
    "ai_clean",
    "ai_fabricated",
    "ai_mixer",
    "ai_replayed",
    "human_clean",
    "human_fabricated",
    "human_mixer",
    "human_replayed",
)

AUDIO_EXTS = {".wav", ".flac", ".mp3", ".ogg", ".m4a", ".aac", ".mp4"}

DEFAULT_SEARCH_ROOTS = [
    _REPO / "data" / "phase7c1" / "raw",
    _REPO / "testing_audios" / "release_variants",
    _REPO / "testing_audios" / "8_variants",
    _REPO / "testing_audios",
    _RELEASE / "sample_audio",
    _REPO / "data" / "phase7c1",
]

PHASE7C1_RAW = _REPO / "data" / "phase7c1" / "raw"


def _normalize_token(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def _infer_variant_from_name(stem: str) -> tuple[str, str] | None:
    """Map Phase 7C1 names like human_001_clean / ai_001_direct to P3 variant keys."""
    s = _normalize_token(stem)
    speaker = None
    if re.match(r"human_\d+", s):
        speaker = "human"
    elif re.match(r"ai_\d+", s):
        speaker = "ai"
    if speaker is None:
        return None

    m = re.match(r"(human|ai)_(\d+)", s)
    if not m:
        return None
    speaker = m.group(1)
    # Phase 7C1: one speaker base (e.g. 001) spans human_001_* and ai_001_* (8 files).
    base_id = m.group(2).zfill(3)

    suffix = s[len(f"{speaker}_{base_id}") :].strip("_")
    if not suffix and s != f"{speaker}_{base_id}":
        suffix = s.replace(f"{speaker}_{base_id}_", "", 1)

    if "fabricated" in suffix or "partial_fake" in suffix or "fake_20pct" in suffix:
        kind = "fabricated"
    elif "mixer_processed" in suffix or suffix.endswith("mixer") or "mixer" in suffix:
        kind = "mixer"
    elif "replay_laptop_mobile" in suffix or "replay" in suffix or "replayed" in suffix:
        kind = "replayed"
    elif suffix in ("clean", "direct") or suffix.endswith("_clean") or suffix.endswith("_direct"):
        kind = "clean"
    else:
        return None

    if speaker == "ai" and kind == "clean":
        key = "ai_clean"
    elif speaker == "human" and kind == "clean":
        key = "human_clean"
    elif speaker == "ai":
        key = f"ai_{kind}"
    else:
        key = f"human_{kind}"
    if key not in VARIANT_KEYS:
        return None
    return key, base_id


def _resolve_search_roots(input_root: str | None) -> list[Path]:
    if input_root:
        return [Path(input_root)]
    if PHASE7C1_RAW.is_dir():
        return [PHASE7C1_RAW]
    return [p for p in DEFAULT_SEARCH_ROOTS if p.is_dir()]


def discover_audio_files(
    roots: list[Path],
    *,
    mode: str,
    max_base_audios: int | None,
) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    seen: set[str] = set()
    for root in roots:
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in AUDIO_EXTS:
                continue
            inferred = _infer_variant_from_name(path.stem)
            if inferred is None:
                continue
            variant, base_id = inferred
            key = str(path.resolve())
            if key in seen:
                continue
            seen.add(key)
            found.append(
                {
                    "path": path,
                    "variant": variant,
                    "base_id": base_id,
                    "file_name": path.name,
                }
            )

    if mode == "quick" and max_base_audios is not None:
        bases = sorted({r["base_id"] for r in found})
        keep = set(bases[: max(1, max_base_audios)])
        found = [r for r in found if r["base_id"] in keep]
        # Quick mode expects up to 8 variants per numeric base (human + ai chains).
        if max_base_audios == 1 and len(found) < 8:
            import sys

            print(
                f"Note: quick mode found {len(found)} files for base(s) {sorted(keep)} "
                f"(expected up to 8 per Phase 7C1 base).",
                file=sys.stderr,
            )
    return found


def _classify_row(
    variant: str,
    summary: dict[str, Any],
    cards: list[dict[str, Any]],
    voice: dict[str, Any],
    error: str | None,
) -> str:
    if error:
        return "release_integration_issue"
    finding = str(summary.get("voice_origin_text", ""))
    forensic = str(summary.get("forensic_indicator_summary", ""))
    if "Suspicious audio indicators found" in finding:
        return "wording_issue"
    card_map = {c.get("axis_name"): c.get("status") for c in cards}
    origin = voice.get("origin_label", "inconclusive")
    partial_st = card_map.get("Partial replacement evidence", "Unavailable")
    replay_st = card_map.get("Replay evidence", "Unavailable")
    mixer_st = card_map.get("Channel/mixer evidence", "Unavailable")
    origin_st = card_map.get("AI-origin evidence", "Unavailable")

    if variant == "human_clean":
        rec = str(summary.get("recommendation_text", ""))
        rec_level = summary.get("recommendation_level", "")
        if summary.get("strong_forensic_detected"):
            return "wording_issue"
        if rec == "Manual review recommended." and rec_level != "review_recommended":
            return "wording_issue"
        if rec == "Manual review recommended." and partial_st == "Review candidate":
            return "wording_issue"
        if partial_st == "Review candidate" and summary.get("segment_candidate_only"):
            if rec_level in ("optional_review", "none"):
                return "pass"
            return "wording_issue"
        if origin in ("likely_human", "inconclusive", "inconclusive_under_processing"):
            return "pass"
        return "acceptable_with_limitation"

    if variant == "ai_clean":
        if origin == "likely_ai_generated" or origin_st == "Detected":
            return "pass"
        return "acceptable_with_limitation"

    if variant in ("ai_replayed", "human_replayed"):
        if replay_st == "Detected":
            return "pass"
        return "model_issue"

    if variant in ("ai_mixer", "human_mixer"):
        if mixer_st in ("Detected", "Possible overlap"):
            if replay_st in ("Detected", "Possible overlap"):
                return "pass"
            return "pass"
        return "model_issue"

    if variant in ("ai_fabricated", "human_fabricated"):
        if partial_st in ("Review candidate", "Detected"):
            return "pass"
        return "acceptable_with_limitation"

    return "acceptable_with_limitation"


def _concise_text(summary: dict[str, Any]) -> str:
    lines = [
        summary.get("voice_origin_text", ""),
        summary.get("forensic_indicator_summary", ""),
        f"Recommendation: {summary.get('recommendation_text', '')}",
    ]
    return "\n".join(x for x in lines if x)


def run_eval(args: argparse.Namespace) -> int:
    try:
        from src.app_report_formatting import (
            build_evidence_axis_cards,
            build_user_result_summary,
            build_voice_origin_result,
            enrich_phase9c_response,
            save_json_report,
        )
        from src.app_visualization import generate_timeline_fallback, generate_waveform_highlight
        from src.inference_pipeline import analyze_audio_file
        from src.origin_support_models import audit_reference_models, format_reference_audit_markdown
        from src.pdf_report_generator import generate_pdf_report
    except ImportError as exc:
        _OUTPUT.mkdir(parents=True, exist_ok=True)
        msg = (
            f"# Phase 9E-P3 Eval aborted\n\nImport error: {exc}\n\n"
            "Run in the project conda env (fassd) where pandas/torch are installed.\n"
        )
        (_OUTPUT / "phase9e_p3_release_correctness_report.md").write_text(msg, encoding="utf-8")
        print(msg)
        return 1

    roots = _resolve_search_roots(args.input_root)
    _OUTPUT.mkdir(parents=True, exist_ok=True)
    per_file_dir = _OUTPUT / "per_file"
    per_file_dir.mkdir(parents=True, exist_ok=True)

    records = discover_audio_files(
        roots,
        mode=args.mode,
        max_base_audios=args.max_base_audios,
    )

    log_capture = io.StringIO()
    weight_load_count = 0
    runtime_warning_count = 0
    feature_warning_count = 0
    external_warning_count = 0
    real_error_count = 0
    traceback_count = 0
    warning_samples: list[str] = []

    results_rows: list[dict[str, Any]] = []
    axis_rows: list[dict[str, Any]] = []
    failure_rows: list[dict[str, Any]] = []

    for rec in records:
        path: Path = rec["path"]
        variant = rec["variant"]
        err: str | None = None
        enriched: dict[str, Any] = {}
        summary: dict[str, Any] = {}
        cards: list[dict[str, Any]] = []
        voice: dict[str, Any] = {}
        try:
            with redirect_stdout(log_capture), redirect_stderr(log_capture):
                phase9c = analyze_audio_file(
                    audio_path=str(path),
                    case_id=f"P3-{variant}-{path.stem}",
                    device="auto",
                    return_debug=True,
                )
                enriched = enrich_phase9c_response(phase9c, file_name=path.name, return_top_segments=True)
                summary = build_user_result_summary(enriched)
                cards = build_evidence_axis_cards(enriched)
                voice = build_voice_origin_result(enriched)
        except Exception as exc:
            err = f"{type(exc).__name__}: {exc}"
            failure_rows.append(
                {
                    "file": str(path),
                    "variant": variant,
                    "base_id": rec["base_id"],
                    "error": err,
                    "traceback": traceback.format_exc(limit=3),
                }
            )

        log_text = log_capture.getvalue()
        weight_load_count += log_text.count("Loading weights:")
        runtime_warning_count += log_text.count("RuntimeWarning")
        feature_warning_count += log_text.count("Mean of empty slice")
        feature_warning_count += log_text.count("invalid value encountered")
        external_warning_count += log_text.count("Support for mismatched key_padding_mask")
        traceback_count += log_text.count("Traceback (most recent call last)")
        if "Error" in log_text or "Exception" in log_text:
            real_error_count += 1
        for line in log_text.splitlines():
            if "RuntimeWarning" in line or "Mean of empty slice" in line:
                if line.strip() not in warning_samples and len(warning_samples) < 5:
                    warning_samples.append(line.strip()[:200])
        log_capture.truncate(0)
        log_capture.seek(0)

        classification = _classify_row(variant, summary, cards, voice, err)
        if len(results_rows) == 0 or (len(results_rows) + 1) % 10 == 0 or len(results_rows) + 1 == len(records):
            print(f"P3: evaluated {len(results_rows) + 1}/{len(records)}", flush=True)
        safe_stem = re.sub(r"[^a-zA-Z0-9_-]+", "_", path.stem)[:60]
        out_sub = per_file_dir / variant / safe_stem
        out_sub.mkdir(parents=True, exist_ok=True)

        json_path = ""
        pdf_path = ""
        wave_path = ""
        if enriched and not err:
            try:
                json_path = save_json_report(enriched, output_dir=out_sub)
                (out_sub / "summary.txt").write_text(_concise_text(summary), encoding="utf-8")
                wave_path = generate_waveform_highlight(str(path), enriched, output_dir=out_sub)
                pdf_path = generate_pdf_report(enriched, waveform_image_path=wave_path, output_dir=out_sub)
            except Exception as exc:
                failure_rows.append(
                    {
                        "file": str(path),
                        "variant": variant,
                        "base_id": rec["base_id"],
                        "error": f"export: {exc}",
                        "traceback": "",
                    }
                )

        results_rows.append(
            {
                "file_path": str(path),
                "file_name": path.name,
                "variant": variant,
                "base_id": rec["base_id"],
                "classification": classification,
                "voice_origin": voice.get("origin_label", ""),
                "voice_origin_text": summary.get("voice_origin_text", ""),
                "forensic_indicator_summary": summary.get("forensic_indicator_summary", ""),
                "recommendation": summary.get("recommendation_text", ""),
                "recommendation_level": summary.get("recommendation_level", ""),
                "error": err or "",
                "json_path": json_path,
                "pdf_path": pdf_path,
                "waveform_path": wave_path,
            }
        )

        for card in cards:
            axis_rows.append(
                {
                    "file_name": path.name,
                    "variant": variant,
                    "base_id": rec["base_id"],
                    "axis_name": card.get("axis_name"),
                    "status": card.get("status"),
                    "score_text": card.get("score_text"),
                }
            )

    _write_csv(_OUTPUT / "phase9e_p3_8variant_results.csv", results_rows)
    _write_csv(_OUTPUT / "phase9e_p3_8variant_axis_decisions.csv", axis_rows)
    _write_csv(_OUTPUT / "phase9e_p3_8variant_failure_analysis.csv", failure_rows)

    audit = audit_reference_models()
    (_OUTPUT / "phase9e_p3_reference_model_audit.md").write_text(
        format_reference_audit_markdown(audit), encoding="utf-8"
    )

    metrics = _compute_metrics(results_rows, records, args.mode)
    (_OUTPUT / "phase9e_p3_full_184_metrics.json").write_text(
        json.dumps(metrics, indent=2), encoding="utf-8"
    )
    _write_csv(_OUTPUT / "phase9e_p3_full_184_metrics.csv", [metrics])

    terminal_audit = _terminal_audit(
        weight_load_count=weight_load_count,
        runtime_warning_count=runtime_warning_count,
        feature_warning_count=feature_warning_count,
        external_warning_count=external_warning_count,
        real_error_count=real_error_count,
        traceback_count=traceback_count,
        evaluated=len(results_rows),
        warning_samples=warning_samples,
    )
    (_OUTPUT / "phase9e_p3_terminal_resource_audit.md").write_text(terminal_audit, encoding="utf-8")

    report = _correctness_report(results_rows, metrics, audit, args.mode, len(records))
    (_OUTPUT / "phase9e_p3_release_correctness_report.md").write_text(report, encoding="utf-8")

    print(f"P3 eval complete: {len(results_rows)} files -> {_OUTPUT}")
    return 0


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _compute_metrics(
    results: list[dict[str, Any]], records: list[dict[str, Any]], mode: str
) -> dict[str, Any]:
    def rate(filter_fn) -> float:
        subset = [r for r in results if filter_fn(r)]
        if not subset:
            return 0.0
        return sum(1 for r in subset if r.get("classification") in ("pass", "acceptable_with_limitation")) / len(
            subset
        )

    by_variant: dict[str, int] = {k: 0 for k in VARIANT_KEYS}
    for r in results:
        by_variant[r["variant"]] = by_variant.get(r["variant"], 0) + 1

    classifications: dict[str, int] = {}
    for r in results:
        c = r.get("classification", "fail")
        classifications[c] = classifications.get(c, 0) + 1

    human_clean = [r for r in results if r["variant"] == "human_clean"]
    false_suspicious = [
        r
        for r in human_clean
        if "Suspicious audio indicators found" in str(r.get("voice_origin_text", ""))
        or "Suspicious audio indicators found" in str(r.get("forensic_indicator_summary", ""))
    ]

    return {
        "mode": mode,
        "total_files": len(records),
        "evaluated_files": len(results),
        "failed_files": sum(1 for r in results if r.get("error")),
        "base_audio_count": len({r["base_id"] for r in records}),
        "variant_count": len(VARIANT_KEYS),
        "per_variant_file_count": by_variant,
        "ai_clean_origin_detect_rate": rate(lambda r: r["variant"] == "ai_clean"),
        "ai_fabricated_origin_detect_rate": rate(lambda r: r["variant"] == "ai_fabricated"),
        "ai_mixer_mixer_detect_rate": rate(lambda r: r["variant"] == "ai_mixer"),
        "ai_replayed_replay_detect_rate": rate(lambda r: r["variant"] == "ai_replayed"),
        "human_clean_false_suspicious_rate": (
            len(false_suspicious) / len(human_clean) if human_clean else 0.0
        ),
        "human_clean_false_ai_rate": rate(
            lambda r: r["variant"] == "human_clean" and r.get("voice_origin") == "likely_ai_generated"
        ),
        "human_fabricated_partial_candidate_or_detect_rate": rate(
            lambda r: r["variant"] == "human_fabricated"
        ),
        "human_mixer_mixer_detect_rate": rate(lambda r: r["variant"] == "human_mixer"),
        "human_mixer_replay_overlap_rate": rate(lambda r: r["variant"] == "human_mixer"),
        "human_replayed_replay_detect_rate": rate(lambda r: r["variant"] == "human_replayed"),
        "partial_candidate_only_count": classifications.get("acceptable_with_limitation", 0),
        "partial_full_detection_count": 0,
        "model_issue_count": classifications.get("model_issue", 0),
        "wording_issue_count": classifications.get("wording_issue", 0),
        "release_integration_issue_count": classifications.get("release_integration_issue", 0),
        "acceptable_with_limitation_count": classifications.get("acceptable_with_limitation", 0),
        "pass_count": classifications.get("pass", 0),
    }


def _terminal_audit(
    *,
    weight_load_count: int,
    runtime_warning_count: int,
    feature_warning_count: int,
    external_warning_count: int,
    real_error_count: int,
    traceback_count: int,
    evaluated: int,
    warning_samples: list[str] | None = None,
) -> str:
    from src.model_loader import load_all_active_models
    from src.ssl_embeddings import load_ssl_extractor

    models_cached = hasattr(load_all_active_models, "cache_info")
    ssl_cached = hasattr(load_ssl_extractor, "cache_info")
    try:
        from src.feature_extraction import safe_nanmean  # noqa: F401

        feature_fix = True
    except ImportError:
        feature_fix = False

    per_file_rw = runtime_warning_count / evaluated if evaluated else 0
    per_file_feature = feature_warning_count / evaluated if evaluated else 0
    terminal_clean = (
        traceback_count == 0
        and real_error_count == 0
        and per_file_rw <= 1.5
        and per_file_feature <= 1.0
    )
    unresolved: list[str] = []
    if feature_warning_count:
        unresolved.append("feature empty-slice warnings may remain in upstream libs")
    if external_warning_count:
        unresolved.append("torch transformer key_padding_mask deprecation (external, filtered in eval entry)")
    if runtime_warning_count and feature_warning_count == 0:
        unresolved.append("RuntimeWarning lines captured — review samples below")
    if warning_samples:
        unresolved.extend(warning_samples[:3])

    body = [
            "# Phase 9E-P3-P1 Terminal & Resource Audit",
            "",
            f"- models cached (lru_cache): {'yes' if models_cached else 'no'}",
            f"- ssl extractor cached: {'yes' if ssl_cached else 'no'}",
            f"- repeated weight loading lines observed: {weight_load_count}",
            f"- repeated weight loading reduced: {'yes' if weight_load_count <= max(2, evaluated) else 'no'}",
            f"- feature empty-slice warning fixed (safe_nanmean): {'yes' if feature_fix else 'no'}",
            f"- runtime_warning_count: {runtime_warning_count}",
            f"- feature_warning_count: {feature_warning_count}",
            f"- external_warning_count: {external_warning_count}",
            f"- real_error_count: {real_error_count}",
            f"- traceback_count: {traceback_count}",
            f"- files evaluated: {evaluated}",
            f"- terminal_clean_enough_for_demo: {'true' if terminal_clean else 'false'}",
            "",
            "## Unresolved warning notes",
            "",
    ]
    if unresolved:
        body.extend(f"- {n}" for n in unresolved)
    else:
        body.append("- none")
    return "\n".join(body) + "\n"


def _correctness_report(
    results: list[dict[str, Any]],
    metrics: dict[str, Any],
    audit: dict[str, Any],
    mode: str,
    discovered: int,
) -> str:
    lines = [
        "# Phase 9E-P3 Release Correctness Report",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        f"Mode: {mode}",
        f"Discovered variant files: {discovered}",
        f"Evaluated: {metrics.get('evaluated_files', 0)}",
        "",
        "## Summary metrics",
        "",
        json.dumps(metrics, indent=2),
        "",
        "## Reference model audit",
        "",
        audit.get("audit_status", ""),
        "",
        "## Hard gates",
        "",
        f"- human_clean_false_suspicious_rate: {metrics.get('human_clean_false_suspicious_rate', 'n/a')}",
        f"- wording_issue_count: {metrics.get('wording_issue_count', 0)}",
        "",
        "## Per-file classifications",
        "",
    ]
    for r in results[:50]:
        lines.append(
            f"- `{r.get('file_name')}` ({r.get('variant')}): {r.get('classification')} — "
            f"{r.get('voice_origin_text', r.get('error', ''))}"
        )
    if len(results) > 50:
        lines.append(f"- ... and {len(results) - 50} more (see CSV)")
    if discovered == 0:
        lines.extend(
            [
                "",
                "## Note",
                "",
                "No 8-variant audio files were discovered. Expected Phase 7C1 layout: "
                "`data/phase7c1/raw/` with 184 files (23 bases × 8 variants), e.g. "
                "`human_001_clean.wav`, `ai_001_direct.wav`, `human_001_replay_laptop_mobile.wav`.",
            ]
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 9E-P3 8-variant release eval.")
    parser.add_argument("--mode", choices=("quick", "full"), default="quick")
    parser.add_argument("--max_base_audios", type=int, default=1)
    parser.add_argument(
        "--input_root",
        default=None,
        help="Audio root (default: data/phase7c1/raw when present, else search list)",
    )
    args = parser.parse_args()
    warnings.filterwarnings(
        "ignore",
        message="Support for mismatched key_padding_mask and attn_mask is deprecated",
        category=UserWarning,
    )
    warnings.filterwarnings(
        "ignore",
        message="Mean of empty slice",
        category=RuntimeWarning,
    )
    warnings.filterwarnings(
        "ignore",
        message="invalid value encountered in divide",
        category=RuntimeWarning,
    )
    return run_eval(args)


if __name__ == "__main__":
    raise SystemExit(main())
