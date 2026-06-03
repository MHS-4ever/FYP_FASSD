# Phase 9F — API Contract

**Base URL (local):** `http://127.0.0.1:8000`  
**App:** Deepfake Audio Detector — Local Demo  
**Phase:** Phase 9E-P4B  
**Status:** Experimental forensic demo — manual review required

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | App metadata and endpoint list |
| GET | `/health` | Liveness + model load status |
| GET | `/model-info` | Inventory summary and partial module metadata |
| POST | `/analyze-audio` | Primary audio analysis endpoint |
| POST | `/analyze` | Legacy alias for `/analyze-audio` (default query flags) |

Interactive OpenAPI: `http://127.0.0.1:8000/docs`

---

## GET /

Returns app identity and available routes.

**Example response fields:**

```json
{
  "app_name": "Deepfake Audio Detector — Local Demo",
  "research_project": "Forensic Acoustic for Synthetic Speech Detection",
  "phase": "Phase 9E-P4B",
  "status": "experimental_forensic_demo",
  "endpoints": ["/", "/health", "/model-info", "/analyze-audio", "/analyze"],
  "safety": { "conclusive_authenticity_decision": "no", "...": "..." },
  "primary_app_path": "release/"
}
```

---

## GET /health

**Example response:**

```json
{
  "status": "ok",
  "phase": "Phase 9E-P4B",
  "models_loaded": true,
  "models_load_error": "",
  "partial_module_status": "experimental_manual_review_only",
  "manual_review_required": true,
  "conclusive_authenticity_decision": false
}
```

Use before batch jobs: if `models_loaded` is `false`, check `models_load_error`.

---

## GET /model-info

Returns model inventory summary and partial fabrication package metadata (thresholds, limitations, validation summary).

Key fields:

- `model_inventory_summary` — count, integration modules, warnings
- `partial_fabrication_experimental_p5b` — thresholds, metadata, validation summary
- `manual_review_required`: `true`
- `conclusive_authenticity_decision`: `false`
- `operational_deployment_claim`: `false`
- `legal_evidence_claim`: `false`

---

## POST /analyze-audio

Analyze one uploaded audio file.

### Request

**Content-Type:** `multipart/form-data`

| Field | Location | Required | Description |
|-------|----------|----------|-------------|
| `audio_file` | form (file) | Yes | Audio upload (`.wav`, etc.) |
| `case_id` | form (string) | No | Optional case identifier |

**Query parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `return_top_segments` | bool | `true` | Include top suspicious segment details in enriched payload |
| `save_report` | bool | `false` | Save JSON report under `reports/phase9/app/sample_outputs/` |
| `generate_report` | bool | `false` | Generate PDF forensic report |
| `generate_visual` | bool | `false` | Generate waveform highlight image |

### Success response (HTTP 200)

Primary user-facing fields:

| Field | Type | Description |
|-------|------|-------------|
| `request_id` | string | Unique request identifier |
| `phase` | string | App phase label (e.g. `Phase 9E-P4B`) |
| `file_name` | string | Original upload filename |
| `duration_sec` | number \| null | Audio duration in seconds |
| `processing_status` | string | `"ok"` or `"error"` |
| `case_id` | string \| null | Assigned or provided case ID |
| `voice_origin_result` | object | Origin label, display text, confidence hints |
| `forensic_indicator_summary` | string | Short multi-axis summary |
| `recommendation` | string | Human-readable recommendation text |
| `recommendation_level` | string | `none`, `optional_review`, `review_recommended`, `unavailable` |
| `evidence_axis_cards` | array | Per-axis UI cards (AI-origin, Replay, Channel/mixer, Partial) |
| `axis_interpretation` | object | Overlap and processing notes |
| `partial_fabrication` | object | Experimental partial module section |
| `partial_module_mode` | string | Typically `segment_candidate_only` |
| `origin_support_models` | object \| null | Shadow audit (AASIST/ResNet inactive) |
| `limitations` | array | File-specific limitation strings |
| `safety` | object | Safety banner (always show in UI) |
| `generated_at` | string | ISO timestamp |
| `pdf_report_path` | string \| null | Present when `generate_report=true` |
| `waveform_image_path` | string \| null | Present when `generate_visual=true` |
| `saved_report_path` | string \| null | Present when `save_report=true` |

Additional fields for advanced/debug use:

- `phase9c_report` — full Phase 9C inference payload
- `user_summary`, `evidence_summary`, `release_correctness_notes`
- `manual_review_required`: always `true`
- `conclusive_authenticity_decision`: always `false`

### Error response (models not loaded)

When models fail to load, returns JSON with `processing_status: "error"` and partial-fabrication unavailable messaging. HTTP status remains 200 with error payload (check `processing_status`).

---

## POST /analyze

Backward-compatible alias. Same multipart fields as `/analyze-audio`:

- `audio_file` (required)
- `case_id` (optional)

Uses default query parameters (`return_top_segments=true`, others `false`). For PDF/waveform/save options, call `/analyze-audio` with query flags.

---

## Safety contract (all analyze responses)

Every successful analyze response includes:

```json
{
  "manual_review_required": true,
  "conclusive_authenticity_decision": false,
  "safety": {
    "app_status": "experimental_forensic_demo",
    "partial_module_status": "experimental_manual_review_only",
    "conclusive_authenticity_decision": "no",
    "operational_deployment_claim": "no",
    "legal_evidence_claim": "no"
  }
}
```

Frontend must display safety wording prominently.

---

## Version notes

- Implemented in `release/app_fastapi.py`
- Response built by `release/src/app_report_formatting.py` → `build_api_analyze_response()`
- No AASIST/ResNet activation in this API path
