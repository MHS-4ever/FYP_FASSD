# Phase 9F — Model Registry Guide

**Inventory file:** `release/models/model_inventory.json`  
**Reference inventory:** `release/models/reference/reference_model_inventory.json`  
**Status:** Experimental forensic prototype

---

## Active models (release inference)

These models are loaded by `release/src/model_loader.py` and used in the Phase 9C/9E inference pipeline.

| Registry name | Artifact path (under `release/models/`) | Role |
|---------------|----------------------------------------|------|
| `origin_file_model` | `origin/origin_file_model__ssl__experimental.joblib` | Voice origin (SSL embeddings) |
| `replay_file_model` | `replay/replay_file_model__acoustic__experimental.joblib` | Replay / rerecording evidence |
| `mixer_file_model` | `mixer/mixer_file_model__acoustic__experimental.joblib` | Mixer / channel processing evidence |

### Partial fabrication integration module

| Item | Value |
|------|-------|
| Module name | `partial_fabrication_experimental_p5b` |
| Package path | `release/models/partial_fabrication_experimental_p5b/` |
| Status | `experimental_manual_review_only` |
| Active for Phase 9E demo | `true` |
| `final_verdict_model` (metadata flag) | `false` |
| Manual review required | `true` |

**Artifacts in package:**

- `partial_file_gate__ssl__p5b_experimental_candidate.joblib`
- `partial_segment_localizer_v2__combined__p5b_experimental_candidate.joblib`
- `partial_cascade_config__p5b_experimental_candidate.json`
- `partial_module_metadata.json`
- `partial_report_contract.json`
- `partial_validation_summary.json`

### Legacy entry (not active P5B cascade)

| Registry name | Status |
|---------------|--------|
| `partial_fabrication_segment_model` | `experimental_forensic_prototype_legacy`, `deprecated_for_p5b_cascade: true`, `active_for_phase9e_demo: false` |

The release app maps Phase 9C segment partial axis into the P6 report contract. The **full P5B file-gate cascade is not wired** as the primary demo path unless explicitly documented otherwise. Partial output is **segment candidate only** wording.

---

## Thresholds (partial module — read-only reference)

From `partial_module_metadata.json` — **do not change in Phase 9F/9G:**

| Threshold | Value |
|-----------|-------|
| `file_gate_threshold` | 0.5 |
| `segment_threshold` | 0.9 |
| `contrast_threshold` | 0.25 |
| `broad_limit` | 0.45 |

These thresholds are frozen documentation references. Changing them requires a new training/validation phase.

---

## Reference / inactive models

Stored under `release/models/reference/` for history and comparison only.

| Model | Decision | Active in fusion |
|-------|----------|------------------|
| AASIST | **`reject_for_now`** | No |
| HybridResNet / ResNet | **`reject_for_now`** | No |

Phase 9E-P4A shadow evaluation (184 files):

- Both models runnable in shadow mode
- High clean-human false-AI rates vs SSL baseline
- Negative net help score → **reject_for_now**
- **Not** listed in active `model_inventory.json` models array
- **Not** used for voice origin, replay, mixer, or partial decisions

See `release/models/reference/README_REFERENCE_MODELS.md`.

---

## Configuration files

| File | Purpose |
|------|---------|
| `release/config/model_paths.yaml` | Active model artifact paths |
| `release/config/fusion_thresholds.yaml` | Fusion rule thresholds (frozen) |
| `release/config/runtime_config.yaml` | Runtime defaults |
| `release/config/label_schema.yaml` | Label schema reference |

---

## Rules for teammates

1. **Do not** write to `models_saved/active/` or overwrite `release/models/` joblib artifacts without a packaging phase.
2. **Do not** activate AASIST/ResNet in the inference path without new validation.
3. Treat partial fabrication as **experimental manual review / segment candidate only**.
4. Voice origin remains the **SSL origin model** — the only active origin decision model.
5. Inventory changes must be reflected in validation reports before handoff.

---

## Quick inventory check

```python
import json
from pathlib import Path

inv = json.loads(Path("release/models/model_inventory.json").read_text())
active = [m["model_name"] for m in inv["models"]]
print("Active registry names:", active)
print("Integration modules:", list(inv.get("integration_modules", {}).keys()))
```

Expected active names: `origin_file_model`, `replay_file_model`, `mixer_file_model`, `partial_fabrication_segment_model` (legacy).  
Expected integration module: `partial_fabrication_experimental_p5b`.  
Must **not** include: `aasist`, `hybrid_resnet`.
