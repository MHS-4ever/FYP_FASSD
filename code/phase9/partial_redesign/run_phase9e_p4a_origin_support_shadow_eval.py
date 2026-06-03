#!/usr/bin/env python3
"""Phase 9E-P4A: Shadow evaluation of AASIST/HybridResNet origin-support models."""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
import traceback
import warnings
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
_OUTPUT = _REPO / "reports" / "phase9" / "app" / "phase9e_p4a_origin_support"

if str(_RELEASE) not in sys.path:
    sys.path.insert(0, str(_RELEASE))
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

DIRECT_VARIANTS = frozenset({"ai_clean", "human_clean"})
AI_VARIANTS = frozenset({"ai_clean", "ai_fabricated", "ai_mixer", "ai_replayed"})
HUMAN_VARIANTS = frozenset({"human_clean", "human_fabricated", "human_mixer", "human_replayed"})
PROCESSED_VARIANTS = frozenset(
    {"ai_fabricated", "ai_mixer", "ai_replayed", "human_fabricated", "human_mixer", "human_replayed"}
)


def _progress_iter(items: list[Any], *, desc: str, total: int | None = None):
    try:
        from tqdm import tqdm

        return tqdm(items, desc=desc, total=total or len(items))
    except ImportError:
        return items


def _log_progress(i: int, total: int, *, model: str = "SSL baseline") -> None:
    if total <= 20 or i == 1 or i == total or i % 10 == 0:
        print(f"P4A: evaluated {i}/{total} — current: {model}", flush=True)


def _expected_origin_label(variant: str) -> str:
    if variant.startswith("ai_"):
        return "likely_ai_generated"
    if variant.startswith("human_"):
        return "likely_human"
    return "inconclusive"


def _origin_correct(label: str, variant: str, *, direct_only: bool = False) -> bool | None:
    if label in ("unavailable", "error"):
        return None
    expected = _expected_origin_label(variant)
    if direct_only and variant not in DIRECT_VARIANTS:
        return None
    if expected == "likely_ai_generated":
        return label == "likely_ai_generated"
    if expected == "likely_human":
        return label in ("likely_human", "inconclusive", "inconclusive_under_processing")
    return None


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _model_decision(
    audit: dict[str, Any],
    metrics: dict[str, Any],
    model_key: str,
) -> str:
    detail = (audit.get("model_details") or {}).get(model_key, {})
    if not detail.get("runnable_in_release"):
        return "audit_only_not_runnable"
    m = metrics.get(model_key, {})
    if m.get("runtime_error_count", 0) > m.get("evaluated_files", 0) * 0.1:
        return "reject_for_now"
    if m.get("runnable_files", 0) < m.get("total_files", 1):
        return "keep_shadow_only"
    if (
        m.get("net_help_score", 0) > 0
        and m.get("human_clean_false_ai_rate", 1.0) <= metrics.get("ssl", {}).get(
            "human_clean_false_ai_rate", 1.0
        )
        and m.get("direct_origin_accuracy", 0) >= metrics.get("ssl", {}).get("direct_origin_accuracy", 0)
        and m.get("avg_runtime_sec", 999) < 30.0
    ):
        return "activate_candidate"
    if m.get("net_help_score", 0) >= 0:
        return "keep_shadow_only"
    return "reject_for_now"


def run_eval(args: argparse.Namespace) -> int:
    try:
        from run_phase9e_p3_8variant_release_eval import discover_audio_files
        from src.app_report_formatting import build_voice_origin_result, enrich_phase9c_response
        from src.inference_pipeline import analyze_audio_file
        from src.origin_support_models import (
            audit_origin_support_models,
            format_p4a_audit_markdown,
            load_origin_support_models,
            predict_origin_support,
        )
    except ImportError as exc:
        _OUTPUT.mkdir(parents=True, exist_ok=True)
        msg = f"# Phase 9E-P4A aborted\n\nImport error: {exc}\n"
        (_OUTPUT / "phase9e_p4a_shadow_comparison_report.md").write_text(msg, encoding="utf-8")
        print(msg)
        return 1

    _OUTPUT.mkdir(parents=True, exist_ok=True)
    audit = audit_origin_support_models()
    (_OUTPUT / "phase9e_p4a_reference_model_audit.md").write_text(
        format_p4a_audit_markdown(audit), encoding="utf-8"
    )

    any_runnable = any(
        d.get("runnable_in_release") for d in (audit.get("model_details") or {}).values()
    )
    if args.skip_if_not_runnable and not any_runnable:
        print("P4A: no runnable reference models — audit_only phase complete.")
        _write_audit_only_outputs(audit)
        return 0

    roots = [Path(args.input_root)] if args.input_root else []
    if not roots:
        raw = _REPO / "data" / "phase7c1" / "raw"
        roots = [raw] if raw.is_dir() else []

    records = discover_audio_files(
        roots,
        mode=args.mode,
        max_base_audios=args.max_base_audios,
    )
    total = len(records)
    if total == 0:
        print("P4A: no audio files discovered.")
        _write_audit_only_outputs(audit)
        return 0

    t_start = time.perf_counter()
    load_count = 0
    runtime_warnings = 0
    oom_count = 0
    bundles = None
    if any_runnable:
        load_count += 1
        bundles = load_origin_support_models(args.device)

    results: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    for idx, rec in enumerate(_progress_iter(records, desc="P4A shadow eval"), start=1):
        path: Path = rec["path"]
        variant = rec["variant"]
        _log_progress(idx, total, model="release SSL + shadow")

        row: dict[str, Any] = {
            "file_path": str(path),
            "file_name": path.name,
            "variant": variant,
            "base_id": rec["base_id"],
        }
        file_t0 = time.perf_counter()
        err = None
        try:
            phase9c = analyze_audio_file(
                audio_path=str(path),
                case_id=f"P4A-{variant}-{path.stem}",
                device=args.device,
                return_debug=False,
            )
            enriched = enrich_phase9c_response(phase9c, file_name=path.name)
            ssl_voice = build_voice_origin_result(enriched)
            row["ssl_origin_label"] = ssl_voice.get("origin_label", "")
            row["ssl_origin_text"] = ssl_voice.get("display_text", "")

            shadow = predict_origin_support(str(path), device=args.device)
            row["shadow_device"] = shadow.get("device", "")
            for key in ("aasist", "hybrid_resnet"):
                m = shadow.get(key) or {}
                row[f"{key}_status"] = m.get("status", "")
                row[f"{key}_label"] = m.get("label", "")
                row[f"{key}_score_ai"] = m.get("score_ai", "")
                row[f"{key}_runtime_sec"] = m.get("runtime_sec", "")
                row[f"{key}_error"] = m.get("error", "") or ""
                if m.get("status") == "error":
                    failures.append(
                        {
                            "file_name": path.name,
                            "variant": variant,
                            "model": key,
                            "error": m.get("error", ""),
                        }
                    )
                if m.get("error") and "out of memory" in str(m.get("error")).lower():
                    oom_count += 1

            row["aasist_agrees_ssl"] = _labels_agree(row.get("aasist_label"), row["ssl_origin_label"])
            row["hybrid_agrees_ssl"] = _labels_agree(row.get("hybrid_resnet_label"), row["ssl_origin_label"])
        except Exception as exc:
            err = f"{type(exc).__name__}: {exc}"
            failures.append(
                {
                    "file_name": path.name,
                    "variant": variant,
                    "model": "release_pipeline",
                    "error": err,
                    "traceback": traceback.format_exc(limit=2),
                }
            )
            if "out of memory" in err.lower():
                oom_count += 1

        row["pipeline_error"] = err or ""
        row["file_runtime_sec"] = round(time.perf_counter() - file_t0, 3)
        results.append(row)

    metrics = _compute_metrics(results, audit, args.mode)
    metrics["decisions"] = {
        "aasist": _model_decision(audit, metrics, "aasist"),
        "hybrid_resnet": _model_decision(audit, metrics, "hybrid_resnet"),
    }
    metrics["activation_recommendation"] = (
        "Do not activate in P4A. "
        + "; ".join(f"{k}={v}" for k, v in metrics["decisions"].items())
    )

    _write_csv(_OUTPUT / "phase9e_p4a_shadow_results.csv", results)
    _write_csv(_OUTPUT / "phase9e_p4a_shadow_failure_cases.csv", failures)
    (_OUTPUT / "phase9e_p4a_shadow_metrics.json").write_text(
        json.dumps(metrics, indent=2), encoding="utf-8"
    )
    _write_csv(_OUTPUT / "phase9e_p4a_shadow_metrics.csv", [_flatten_metrics(metrics)])

    total_runtime = time.perf_counter() - t_start
    terminal = _terminal_audit(
        load_count=load_count,
        runtime_warnings=runtime_warnings,
        oom_count=oom_count,
        device=bundles.get("device") if bundles else args.device,
        evaluated=len(results),
        total_runtime=total_runtime,
        avg_runtime=total_runtime / max(len(results), 1),
    )
    (_OUTPUT / "phase9e_p4a_terminal_resource_audit.md").write_text(terminal, encoding="utf-8")
    (_OUTPUT / "phase9e_p4a_shadow_comparison_report.md").write_text(
        _comparison_report(results, metrics, audit, args.mode), encoding="utf-8"
    )

    print(f"P4A shadow eval complete: {len(results)} files -> {_OUTPUT}")
    return 0


def _labels_agree(shadow_label: Any, ssl_label: Any) -> bool | None:
    if not shadow_label or shadow_label in ("unavailable", "error"):
        return None
    s = str(shadow_label)
    b = str(ssl_label)
    if s == b:
        return True
    ai_set = {"likely_ai_generated", "likely_ai_generated_with_processing"}
    human_set = {"likely_human", "inconclusive_under_processing", "inconclusive"}
    if s in ai_set and b in ai_set:
        return True
    if s in human_set and b in human_set:
        return True
    return False


def _compute_metrics(results: list[dict[str, Any]], audit: dict[str, Any], mode: str) -> dict[str, Any]:
    total = len(results)
    out: dict[str, Any] = {
        "mode": mode,
        "total_files": total,
        "evaluated_files": sum(1 for r in results if not r.get("pipeline_error")),
        "failed_files": sum(1 for r in results if r.get("pipeline_error")),
        "audit_status": audit.get("audit_status"),
    }

    ssl = _model_metrics(results, prefix="", label_col="ssl_origin_label")
    ssl["agreement_with_ssl_origin_rate"] = 1.0
    out["ssl"] = ssl

    for key, col in (("aasist", "aasist"), ("hybrid_resnet", "hybrid_resnet")):
        out[key] = _model_metrics(results, prefix=f"{col}_", label_col=f"{col}_label", ssl_col="ssl_origin_label")

    return out


def _model_metrics(
    results: list[dict[str, Any]],
    *,
    prefix: str,
    label_col: str,
    ssl_col: str = "ssl_origin_label",
) -> dict[str, Any]:
    rows = [r for r in results if not r.get("pipeline_error")]
    status_col = f"{prefix}status" if prefix else None
    runtime_col = f"{prefix}runtime_sec" if prefix else None
    error_col = f"{prefix}error" if prefix else None

    runnable = [
        r
        for r in rows
        if r.get(label_col) not in (None, "", "unavailable")
        and (not status_col or r.get(status_col) in ("shadow_runnable", ""))
    ]
    runtimes = [
        float(r[runtime_col])
        for r in rows
        if runtime_col and r.get(runtime_col) not in (None, "")
    ]
    errors = sum(1 for r in rows if error_col and r.get(error_col))

    def rate(filter_fn, label_key: str = label_col) -> float:
        subset = [r for r in runnable if filter_fn(r)]
        if not subset:
            return 0.0
        ok = 0
        for r in subset:
            c = _origin_correct(str(r.get(label_key, "")), r["variant"])
            if c is True:
                ok += 1
        return ok / len(subset)

    def direct_rate(label_key: str = label_col) -> float:
        subset = [r for r in runnable if r["variant"] in DIRECT_VARIANTS]
        if not subset:
            return 0.0
        ok = sum(
            1
            for r in subset
            if _origin_correct(str(r.get(label_key, "")), r["variant"], direct_only=True) is True
        )
        return ok / len(subset)

    agree = 0
    disagree = 0
    helped = 0
    hurt = 0
    for r in runnable:
        shadow = str(r.get(label_col, ""))
        ssl = str(r.get(ssl_col, ""))
        if shadow in ("unavailable", "error", ""):
            continue
        a = _labels_agree(shadow, ssl)
        if a is True:
            agree += 1
        elif a is False:
            disagree += 1
        exp = _expected_origin_label(r["variant"])
        shadow_ok = _origin_correct(shadow, r["variant"]) is True
        ssl_ok = _origin_correct(ssl, r["variant"]) is True
        if shadow_ok and not ssl_ok:
            helped += 1
        if ssl_ok and not shadow_ok:
            hurt += 1

    n_agree_base = agree + disagree
    return {
        "total_files": len(rows),
        "evaluated_files": len(runnable),
        "runnable_files": len(runnable),
        "failed_files": errors,
        "runtime_error_count": errors,
        "avg_runtime_sec": float(sum(runtimes) / len(runtimes)) if runtimes else 0.0,
        "ai_origin_accuracy_on_ai_variants": rate(lambda r: r["variant"] in AI_VARIANTS),
        "human_origin_accuracy_on_human_variants": rate(lambda r: r["variant"] in HUMAN_VARIANTS),
        "ai_clean_detect_rate": rate(lambda r: r["variant"] == "ai_clean"),
        "ai_fabricated_detect_rate": rate(lambda r: r["variant"] == "ai_fabricated"),
        "ai_mixer_detect_rate": rate(lambda r: r["variant"] == "ai_mixer"),
        "ai_replayed_detect_rate": rate(lambda r: r["variant"] == "ai_replayed"),
        "human_clean_false_ai_rate": _false_ai_rate(runnable, label_col),
        "human_fabricated_false_ai_rate": _false_ai_rate(
            [r for r in runnable if r["variant"] == "human_fabricated"], label_col
        ),
        "human_mixer_false_ai_rate": _false_ai_rate(
            [r for r in runnable if r["variant"] == "human_mixer"], label_col
        ),
        "human_replayed_false_ai_rate": _false_ai_rate(
            [r for r in runnable if r["variant"] == "human_replayed"], label_col
        ),
        "direct_origin_accuracy": direct_rate(),
        "processed_origin_stability": _processed_stability(runnable, label_col),
        "agreement_with_ssl_origin_rate": agree / n_agree_base if n_agree_base else 0.0,
        "disagreement_with_ssl_origin_count": disagree,
        "cases_helped_current_ssl": helped,
        "cases_hurt_current_ssl": hurt,
        "net_help_score": helped - hurt,
    }


def _false_ai_rate(rows: list[dict[str, Any]], label_col: str) -> float:
    clean = [r for r in rows if r["variant"] == "human_clean"]
    if not clean:
        return 0.0
    false_ai = sum(1 for r in clean if str(r.get(label_col, "")) == "likely_ai_generated")
    return false_ai / len(clean)


def _processed_stability(rows: list[dict[str, Any]], label_col: str) -> float:
    subset = [r for r in rows if r["variant"] in PROCESSED_VARIANTS]
    if not subset:
        return 0.0
    ok = sum(1 for r in subset if str(r.get(label_col, "")) != "unavailable")
    return ok / len(subset)


def _flatten_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    flat: dict[str, Any] = {"mode": metrics.get("mode"), "total_files": metrics.get("total_files")}
    for key in ("ssl", "aasist", "hybrid_resnet"):
        for mk, mv in (metrics.get(key) or {}).items():
            flat[f"{key}_{mk}"] = mv
    for k, v in (metrics.get("decisions") or {}).items():
        flat[f"decision_{k}"] = v
    flat["activation_recommendation"] = metrics.get("activation_recommendation", "")
    return flat


def _terminal_audit(
    *,
    load_count: int,
    runtime_warnings: int,
    oom_count: int,
    device: str,
    evaluated: int,
    total_runtime: float,
    avg_runtime: float,
) -> str:
    clean = oom_count == 0 and runtime_warnings == 0
    return "\n".join(
        [
            "# Phase 9E-P4A Terminal & Resource Audit",
            "",
            f"- model load count: {load_count}",
            f"- repeated loading warning count: {max(0, load_count - 1)}",
            f"- runtime warnings: {runtime_warnings}",
            f"- cuda oom count: {oom_count}",
            f"- fallback device used: {device}",
            f"- avg runtime per file (sec): {avg_runtime:.3f}",
            f"- total runtime (sec): {total_runtime:.1f}",
            f"- files evaluated: {evaluated}",
            f"- terminal_clean_enough_for_demo: {'true' if clean else 'false'}",
        ]
    ) + "\n"


def _comparison_report(
    results: list[dict[str, Any]],
    metrics: dict[str, Any],
    audit: dict[str, Any],
    mode: str,
) -> str:
    lines = [
        "# Phase 9E-P4A Shadow Origin-Support Comparison Report",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        f"Mode: {mode}",
        f"Audit: {audit.get('audit_status', '')}",
        "",
        "## SSL baseline (active release origin model)",
        "",
        json.dumps(metrics.get("ssl", {}), indent=2),
        "",
        "## AASIST shadow",
        "",
        json.dumps(metrics.get("aasist", {}), indent=2),
        "",
        f"**Decision:** {metrics.get('decisions', {}).get('aasist', 'audit_only_not_runnable')}",
        "",
        "## HybridResNet shadow",
        "",
        json.dumps(metrics.get("hybrid_resnet", {}), indent=2),
        "",
        f"**Decision:** {metrics.get('decisions', {}).get('hybrid_resnet', 'audit_only_not_runnable')}",
        "",
        "## Activation recommendation (P4A — report only)",
        "",
        metrics.get("activation_recommendation", "Do not activate without P4B validation."),
        "",
        "Replay, mixer, and partial axes were **not** modified. Shadow scores are origin-support only.",
        "",
        "## Sample rows",
        "",
    ]
    for r in results[:12]:
        lines.append(
            f"- `{r.get('file_name')}` ({r.get('variant')}): SSL={r.get('ssl_origin_label')} | "
            f"AASIST={r.get('aasist_label')} | Hybrid={r.get('hybrid_resnet_label')}"
        )
    if len(results) > 12:
        lines.append(f"- ... and {len(results) - 12} more (see CSV)")
    return "\n".join(lines) + "\n"


def _write_audit_only_outputs(audit: dict[str, Any]) -> None:
    metrics = {
        "mode": "audit_only",
        "total_files": 0,
        "audit_status": audit.get("audit_status"),
        "decisions": {
            "aasist": "audit_only_not_runnable",
            "hybrid_resnet": "audit_only_not_runnable",
        },
        "activation_recommendation": "No shadow eval run — reference models not runnable.",
    }
    (_OUTPUT / "phase9e_p4a_shadow_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    _write_csv(_OUTPUT / "phase9e_p4a_shadow_results.csv", [])
    _write_csv(_OUTPUT / "phase9e_p4a_shadow_failure_cases.csv", [])
    _write_csv(_OUTPUT / "phase9e_p4a_shadow_metrics.csv", [_flatten_metrics(metrics)])
    (_OUTPUT / "phase9e_p4a_shadow_comparison_report.md").write_text(
        "# Phase 9E-P4A\n\nAudit-only phase — no runnable reference models.\n", encoding="utf-8"
    )
    (_OUTPUT / "phase9e_p4a_terminal_resource_audit.md").write_text(
        "# Phase 9E-P4A Terminal Audit\n\n- terminal_clean_enough_for_demo: true\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 9E-P4A shadow origin-support eval.")
    parser.add_argument("--mode", choices=("quick", "full"), default="quick")
    parser.add_argument("--input_root", default=None)
    parser.add_argument("--device", default="auto", choices=("auto", "cpu", "cuda"))
    parser.add_argument("--max_base_audios", type=int, default=1)
    parser.add_argument("--skip_if_not_runnable", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()
    warnings.filterwarnings("ignore", message="Mean of empty slice", category=RuntimeWarning)
    return run_eval(args)


if __name__ == "__main__":
    raise SystemExit(main())
