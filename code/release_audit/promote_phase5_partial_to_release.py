"""Promote Phase 5 partial segment model into release/models/partial_segment/."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import joblib

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT / "release"
PHASE5_DIR = ROOT / "reports" / "release_audit" / "phase5_partial_redesign_2026-06-13"
PHASE5_JOBLIB = PHASE5_DIR / "phase5_partial_segment_localizer.joblib"
PHASE5_META = PHASE5_DIR / "phase5_partial_segment_metadata.json"

PARTIAL_DIR = RELEASE / "models" / "partial_segment"
RELEASE_JOBLIB = PARTIAL_DIR / "partial_segment_model__combined__experimental.joblib"
RELEASE_META = PARTIAL_DIR / "partial_segment_model__combined__metadata.json"
BACKUP_DIR = PARTIAL_DIR / "backup_before_phase5_2026-06-13"

F9_REMOVED = [
    "acoustic_deviation_percentile_within_file",
    "ssl_deviation_percentile_within_file",
    "within_file_acoustic_deviation_score",
    "within_file_ssl_deviation_score",
    "combined_within_file_deviation_score",
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def selected_feature_names(pipeline, training_features: list[str]) -> list[str]:
    if hasattr(pipeline, "named_steps") and "select" in pipeline.named_steps:
        mask = pipeline.named_steps["select"].get_support()
        return [f for f, keep in zip(training_features, mask) if bool(keep)]
    if hasattr(pipeline, "feature_names_in_"):
        return [str(x) for x in pipeline.feature_names_in_]
    return list(training_features)


def main() -> int:
    args = parse_args()
    if not PHASE5_JOBLIB.is_file():
        raise FileNotFoundError(f"Phase 5 model missing: {PHASE5_JOBLIB}")

    bundle = joblib.load(PHASE5_JOBLIB)
    if isinstance(bundle, dict) and "model" in bundle:
        pipeline = bundle["model"]
        train_features = list(bundle.get("features") or [])
        threshold = float(bundle.get("segment_threshold", 0.95))
    else:
        pipeline = bundle
        train_features = []
        threshold = 0.95

    if PHASE5_META.is_file():
        phase5_meta = json.loads(PHASE5_META.read_text(encoding="utf-8"))
        threshold = float(phase5_meta.get("segment_threshold", threshold))
        if not train_features:
            train_features = list(phase5_meta.get("model_features") or [])

    selected = selected_feature_names(pipeline, train_features)
    old_meta = json.loads(RELEASE_META.read_text(encoding="utf-8")) if RELEASE_META.is_file() else {}

    new_meta = dict(old_meta)
    new_meta.update(
        {
            "artifact_schema_version": "phase9b_release_v1",
            "model_name": "partial_fabrication_segment_model",
            "task_name": "partial_fabrication_segment_model",
            "evidence_axis": "partial_fabrication_evidence",
            "phase_trained": "Phase 5 partial redesign (F9 features removed)",
            "feature_set": "combined_no_f9",
            "feature_count": len(selected),
            "feature_names": selected,
            "training_input_feature_names": train_features,
            "f9_features_removed": F9_REMOVED,
            "threshold_candidate": threshold,
            "threshold_source": "leakage_safe_dev_oracle_grid_phase5",
            "status": "experimental_forensic_prototype",
            "active_production_model": False,
            "not_final_forensic_decision": True,
            "promoted_at": utc_now(),
            "promoted_from": str(PHASE5_JOBLIB),
            "limitations": [
                "experimental prototype only",
                "manual review required",
                "not final forensic proof",
                "Phase 5 retrain without F9 within-file percentile features",
                "segment scores are uncalibrated; UI shows evidence strength bands",
                "single-segment spikes possible on non-partial files (see Phase 5 eval)",
            ],
        }
    )
    new_meta["expected_input_schema"] = {
        "type": "tabular_features",
        "feature_set": "combined_no_f9",
        "required_feature_names": train_features,
    }

    report = {
        "promoted_at": utc_now(),
        "threshold": threshold,
        "training_input_features": len(train_features),
        "selected_features": len(selected),
        "f9_removed": F9_REMOVED,
        "release_joblib": str(RELEASE_JOBLIB),
        "backup_dir": str(BACKUP_DIR),
    }

    if args.dry_run:
        print(json.dumps(report, indent=2))
        return 0

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    if RELEASE_JOBLIB.is_file():
        shutil.copy2(RELEASE_JOBLIB, BACKUP_DIR / RELEASE_JOBLIB.name)
    if RELEASE_META.is_file():
        shutil.copy2(RELEASE_META, BACKUP_DIR / RELEASE_META.name)

    joblib.dump(pipeline, RELEASE_JOBLIB)
    RELEASE_META.write_text(json.dumps(new_meta, indent=2), encoding="utf-8")
    (PHASE5_DIR / "phase5_release_promotion_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )

    # Clear inference cache if app already imported models in-process.
    try:
        import sys

        if str(RELEASE) not in sys.path:
            sys.path.insert(0, str(RELEASE))
        from src.model_loader import clear_active_model_cache

        clear_active_model_cache()
    except Exception:
        pass

    print(f"[promote] Phase 5 partial model -> {RELEASE_JOBLIB}")
    print(f"[promote] threshold={threshold}, selected_features={len(selected)}")
    print(f"[promote] backup -> {BACKUP_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
