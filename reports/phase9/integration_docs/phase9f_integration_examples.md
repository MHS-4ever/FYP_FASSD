# Phase 9F — Integration Examples

Examples for frontend/API teammates integrating with the FastAPI release app.

---

## curl — health check

```bash
curl -s http://127.0.0.1:8000/health | python -m json.tool
```

---

## curl — analyze audio (minimal)

```bash
curl -X POST "http://127.0.0.1:8000/analyze-audio" \
  -F "audio_file=@/path/to/sample.wav" \
  -F "case_id=TEAM-DEMO-001"
```

---

## curl — analyze with PDF and waveform

```bash
curl -X POST "http://127.0.0.1:8000/analyze-audio?return_top_segments=true&generate_report=true&generate_visual=true&save_report=true" \
  -F "audio_file=@/path/to/sample.wav" \
  -F "case_id=TEAM-DEMO-002"
```

On Windows CMD:

```bat
curl -X POST "http://127.0.0.1:8000/analyze-audio?generate_report=true&generate_visual=true" ^
  -F "audio_file=@E:\FYP\release\sample_audio\demo.wav" ^
  -F "case_id=WIN-DEMO-001"
```

---

## Python requests example

```python
import requests

BASE = "http://127.0.0.1:8000"
AUDIO = r"E:\FYP\release\sample_audio\demo.wav"

with open(AUDIO, "rb") as fh:
    resp = requests.post(
        f"{BASE}/analyze-audio",
        params={
            "return_top_segments": True,
            "generate_report": False,
            "generate_visual": True,
            "save_report": False,
        },
        files={"audio_file": ("demo.wav", fh, "audio/wav")},
        data={"case_id": "PY-DEMO-001"},
        timeout=120,
    )

resp.raise_for_status()
data = resp.json()

print("Voice origin:", data["voice_origin_result"]["display_text"])
print("Recommendation:", data["recommendation"])
print("Level:", data["recommendation_level"])
print("Safety:", data["safety"]["wording"])
```

---

## Expected JSON snippet (illustrative)

```json
{
  "request_id": "a1b2c3d4-...",
  "phase": "Phase 9E-P4B",
  "file_name": "demo.wav",
  "duration_sec": 12.4,
  "processing_status": "ok",
  "case_id": "CASE-...",
  "voice_origin_result": {
    "display_text": "Voice origin: Likely AI-generated",
    "origin_label": "likely_ai_generated"
  },
  "forensic_indicator_summary": "AI-origin detected",
  "recommendation": "Manual forensic review is recommended when strong indicators are present.",
  "recommendation_level": "review_recommended",
  "evidence_axis_cards": [
    {
      "axis_name": "AI-origin evidence",
      "status": "Detected",
      "user_text": "AI-origin evidence detected",
      "severity": "detected"
    }
  ],
  "partial_fabrication": {
    "module_status": "experimental_manual_review_only",
    "partial_module_mode": "segment_candidate_only"
  },
  "partial_module_mode": "segment_candidate_only",
  "limitations": [],
  "manual_review_required": true,
  "conclusive_authenticity_decision": false,
  "safety": {
    "conclusive_authenticity_decision": "no",
    "wording": "Experimental forensic evidence indicators only. Manual forensic review is recommended. Conclusive authenticity decision: no."
  },
  "generated_at": "2026-06-03T..."
}
```

Actual fields vary by file; always handle `processing_status`, `limitations`, and `safety`.

---

## Example response interpretation

| Observation | Frontend action |
|-------------|-----------------|
| `voice_origin_result.display_text` contains "Inconclusive under replay" | Show processing disclaimer; de-emphasize origin certainty |
| `recommendation_level` = `optional_review` | Soft banner — optional review, not alarm |
| `recommendation_level` = `review_recommended` | Prominent review banner |
| Partial card severity = candidate | Label "Partial replacement candidate for review" — experimental |
| `axis_interpretation.overlap_note` present | Show overlap info between replay and mixer |
| `conclusive_authenticity_decision` = false | Always show safety footer |

---

## Frontend display guidance

### Voice origin card

- **Primary text:** `voice_origin_result.display_text`
- **Secondary:** `forensic_indicator_summary`
- **Badge:** map `origin_label` to color (neutral for inconclusive)

### Evidence cards

Render `evidence_axis_cards[]`:

```javascript
data.evidence_axis_cards.forEach(card => {
  renderCard({
    title: card.axis_name,
    status: card.status,
    body: card.user_text,
    severity: card.severity, // detected | clear | candidate | unavailable
  });
});
```

### Waveform

If `waveform_image_path` is set, serve as static file from local path (demo) or proxy from your backend after upload. Gradio generates PNG under `release/gradio_outputs/visuals/`.

### PDF download

If `pdf_report_path` is set, offer download link. PDF includes same wording constraints as JSON.

### Raw JSON (advanced)

Collapse under "Advanced / developer details":

- Full response JSON
- `phase9c_report` for segment tables
- `origin_support_models` shadow audit (inactive AASIST/ResNet)

Do not expose raw JSON as the primary user view.

---

## Legacy endpoint

Older clients may POST to `/analyze` with the same multipart body. Prefer `/analyze-audio` for query-parameter control.

```python
requests.post(f"{BASE}/analyze", files={"audio_file": ...}, data={"case_id": "legacy"})
```

---

## Related docs

- [phase9f_api_contract.md](phase9f_api_contract.md)
- [phase9f_report_wording_guide.md](phase9f_report_wording_guide.md)
- Demo sample expectations: `reports/phase9/app/phase9e_p4b_demo_freeze/phase9e_p4b_final_demo_samples.csv`
