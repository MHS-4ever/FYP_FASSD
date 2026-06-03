# Phase 9E-P2 — User-facing UI, Waveform Visualization, and Report Export

## Product naming

| Role | Name |
|------|------|
| Product / technical app | **Deepfake Audio Detector** |
| UI title | **Deepfake Audio Detector — Local Demo** |
| Research / FYP (subtitle/footer/about only) | **Forensic Acoustic for Synthetic Speech Detection** |

Do **not** use “Forensic Deepfake Audio Detector” as the product title.

## UX goal

Present the existing Phase 9C + P6 release pipeline as a polished **local demo** for supervisors and reviewers: concise results, evidence cards, waveform/timeline visuals, and downloadable reports. Raw JSON and contract details stay under **Advanced details** (collapsed by default).

**No model behavior changes** in P2 — formatting and visualization only.

## Architecture (unchanged inference)

```
release/
  app_gradio.py              # P2 dashboard UI
  app_fastapi.py             # Stable API + optional report/visual flags
  src/
    inference_pipeline.py    # analyze_audio_file() — unchanged logic
    app_report_formatting.py # user summary, evidence cards, JSON export
    app_visualization.py     # waveform / timeline PNG
    pdf_report_generator.py  # PDF (reportlab) or HTML fallback
  models/partial_fabrication_experimental_p5b/
```

## Gradio layout

1. **Header** — product title, subtitle, research project line, safety note  
2. **Upload card** — audio, optional case ID, Analyze, Clear  
3. **Main result card** — compact status (HTML)  
4. **Audio overview** — file, duration, status, manual review, case ID  
5. **Evidence axis cards** — AI-origin, replay, channel/mixer, partial-fabrication  
6. **Waveform image** — full waveform with highlighted segment(s)  
7. **Suspicious segments table** — rank, time range, evidence score, review recommendation  
8. **Report downloads** — PDF (or HTML if reportlab missing), JSON  
9. **Advanced details** — technical markdown, partial contract JSON, raw JSON (accordions, closed by default)

## Helpers

- `build_user_result_summary(response)` — concise status/finding/segment/recommendation  
- `build_evidence_axis_cards(response)` — four axis cards with Detected / Not detected / Unavailable  
- `save_json_report(app_response, output_dir)` → `reports/phase9/app/sample_outputs/json/`  
- `generate_waveform_highlight(...)` / `generate_timeline_fallback(...)` → `sample_outputs/visuals/`  
- `generate_pdf_report(...)` → `sample_outputs/reports/`

## PDF report structure

1. Header (product + research project name)  
2. Case information  
3. Main result  
4. Evidence axis summary  
5. Waveform image (if available)  
6. Suspicious segments table  
7. Technical details (module status, thresholds, limitations)  
8. Safety note (experimental indicators; no conclusive authenticity decision)

## FastAPI

Endpoints preserved: `/`, `/health`, `/model-info`, `/analyze-audio`, `/analyze`.

`/analyze-audio` response includes optional fields: `user_summary`, `evidence_axis_cards`, `visual_summary_available`, `report_download_hint`.

Optional query params: `generate_report`, `generate_visual` (off by default).

## Dependencies

From `release/requirements_release.txt`: gradio, fastapi, matplotlib, soundfile, librosa, etc.

Optional: **reportlab** for PDF (HTML report written if import fails).

## How to run (manual)

```bat
cd release
run_gradio.bat
run_fastapi.bat
```

## Validation

```bat
python code\phase9\partial_redesign\validate_phase9e_p2_ui_report.py
```

## What is not claimed

- Operational deployment readiness  
- Legal-evidence / court readiness  
- Conclusive authenticity or final fake/real verdict  
- Partial-fabrication module as conclusive proof (experimental_manual_review_only)

## P1 relationship

Phase 9E-P1 established the release app path and P6 partial contract wiring. **P2 refines presentation only**; see `phase9e_p1_app_design.md`.

## P2-P1 clean-audio interpretation fix

The release app maps the Phase 9C **segment partial axis** into the P6 `partial_fabrication` contract. The full P5B file-gate + segment cascade is **not** running in `release/` yet.

Therefore:

- Segment-only partial candidates are shown as **Review candidate** on the partial evidence card (not **Detected**).
- They **do not** drive the main result to “Suspicious audio indicators found”.
- Main result stays **No strong manipulation indicators detected** with `clear_candidate` severity when only a segment candidate exists.
- The candidate segment remains visible in the table (titled **Candidate segments for review** unless stronger multi-axis evidence warrants “Suspicious segments for review”).
- Full suspicious main result requires stronger evidence: elevated AI/replay/mixer axis, full P5B cascade support when available, or clearly elevated fusion/risk.

Partial section adds: `source_mode`, `file_gate_available`, `full_p5b_cascade_available`, `segment_candidate_only`.

Gradio cards use explicit dark-theme colors (`#1f2937` background, `#f9fafb` primary text) for readability.
