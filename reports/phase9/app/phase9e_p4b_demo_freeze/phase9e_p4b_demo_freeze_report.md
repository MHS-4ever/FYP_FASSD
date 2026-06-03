# Phase 9E-P4B — Demo Freeze Report

**Generated:** Phase 9E-P4B final UI/report/demo freeze  
**Decision:** **GO** — Phase 9E release demo frozen for FYP presentation. Phase 9F may start after P4B validator PASS.

## Accepted phases summary

| Phase | Status | Key outcome |
|-------|--------|-------------|
| 9E-P3 | PASS | Voice-origin-first hierarchy; 184-file regression |
| 9E-P3-P1 | PASS | Optional review wording; JSON completeness; terminal audit clean |
| 9E-P4A | PASS | AASIST/HybridResNet shadow eval (184 files); reject_for_now |
| 9E-P4B | PASS | Demo freeze — naming, reports, samples, validator |

## App location and run commands

**Primary path:** `E:\FYP\release\`

```bat
cd /d E:\FYP\release
conda activate fassd
python app_gradio.py
```

Or: `run_gradio.bat`

**FastAPI (optional API demo):**

```bat
cd /d E:\FYP\release
run_fastapi.bat
```

Then open http://127.0.0.1:8000/health and POST `/analyze-audio`.

## Product naming

| Role | Name |
|------|------|
| Product / UI title | **Deepfake Audio Detector — Local Demo** |
| Research / FYP | **Forensic Acoustic for Synthetic Speech Detection** |

The product is **not** named “Forensic Deepfake Audio Detector”.

## Active models (unchanged)

From `release/models/model_inventory.json`:

- `origin_file_model` (SSL) — **active voice origin**
- `replay_file_model`
- `mixer_file_model`
- `partial_fabrication_experimental_p5b` (segment axis mapped to P6 contract; experimental manual review only)

Legacy `partial_fabrication_segment_model` is not the active P5B cascade path.

## Inactive reference models

Under `release/models/reference/`:

| Model | P4A decision | Role in demo |
|-------|--------------|--------------|
| AASIST | **reject_for_now** | Reference/shadow only; not in fusion |
| HybridResNet | **reject_for_now** | Reference/shadow only; not in fusion |

P4A full metrics (184 files): SSL direct-origin accuracy 1.0, human_clean false-AI 0.0; AASIST/Hybrid net_help negative. **Do not activate.**

## 184 regression summary (P3 full)

- Files evaluated: **184/184**
- Inference failures: **0**
- `human_clean_false_suspicious_rate`: **0.0**
- Wording issues (human_clean optional review): **resolved**
- Validator: PASS

## UI / report freeze

- Voice origin → forensic indicators → recommendation
- Evidence cards, waveform, PDF/JSON downloads, advanced JSON collapsed
- Recommendation levels: `none`, `optional_review`, `review_recommended`, `unavailable`
- Waveform: “Highlighted evidence region” / “Candidate region for optional review” / “No highlighted evidence region”
- PDF/HTML safety: Conclusive authenticity decision: no.

## Demo sample set

Eight representative variants (speaker base 001): see `phase9e_p4b_final_demo_samples.csv`.

## Known limitations

See `phase9e_p4b_known_limitations.md`.

## Final safety wording

- Experimental forensic evidence indicators only.
- Manual forensic review is recommended when strong indicators are present.
- Optional review may be useful for sensitive cases (segment-only candidates on clean human).
- Conclusive authenticity decision: **no**.
- Not operational deployment or legal-evidence ready.

## Phase 9F go/no-go

| Criterion | Status |
|-----------|--------|
| P4B validator PASS | Required |
| No model/threshold changes in P4B | Yes |
| AASIST/ResNet inactive | Yes |
| Demo docs complete | Yes |

**Phase 9F may start** after `validate_phase9e_p4b_demo_freeze.py` reports PASS.

## No changes in P4B

- No retraining, threshold changes, or release model overwrites
- No AASIST/ResNet activation
- No Phase 9F/9G implementation in this phase
