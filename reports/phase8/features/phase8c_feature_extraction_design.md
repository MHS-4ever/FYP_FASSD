# Phase 8C — Acoustic / Channel Feature Extraction Design

**Status:** Phase 8C-P1 patched — progress, resume, fast/full segment modes  
**Schema version:** `phase8c_v1`  
**Code:** `code/phase8/features/extract_phase8c_acoustic_features.py`

---

## Purpose

Phase 8C extracts **measurable acoustic and channel-proxy features** from audio files and segments listed in Phase 8B evidence tables. Outputs are **separate feature CSVs** — Phase 8B tables are read-only and evidence score columns remain empty.

---

## Why features are separate from evidence scores

| Layer | Role |
|-------|------|
| **Phase 8B** | Structure + known ground-truth labels + segment windows |
| **Phase 8C** | Raw numeric descriptors (RMS, spectrum, MFCCs, band energy, quality proxies) |
| **Phase 8E** | Learned mappings from features → evidence scores (later) |
| **Phase 8F** | Fusion → calibrated labels and forensic status |

Features describe **signal properties**. Evidence scores describe **forensic inference strength** after calibrated models/rules. Mixing them in 8C would recreate binary collapse risk (e.g. one “fake probability” column).

---

## How this supports later analysis

| Forensic theme | Example Phase 8C indicators (not decisions) |
|----------------|-----------------------------------------------|
| Replay / rerecord | Band energy shifts, noise floor, SNR proxy, rolloff |
| Mixer / channel | Spectral centroid/bandwidth, contrast, band ratios |
| Compression / quality | Entropy, flatness, bandwidth_occupied_95, clipping |
| Partial / segment contrast | Per-segment features compared in 8E/8F (not 8C) |

Phase 8C does **not** label replay, mixer, or AI — it only measures signal statistics.

---

## Feature groups implemented

1. **Amplitude / time-domain** — RMS, peak, DC offset, clipping, silence/active ratios  
2. **Zero-crossing rate** — coarse high-frequency / noisiness proxy  
3. **Spectral shape** — centroid, bandwidth, rolloff, flatness, contrast  
4. **Band energy ratios** — low / mid / high / very-high bands  
5. **Quality proxies** — noise floor, SNR proxy, dynamic range, entropy, bandwidth occupancy  
6. **MFCC summaries** — means and stds for coefficients 1–13  

---

## What Phase 8C does

- Read `phase8b_file_evidence_table.csv` and `phase8b_segment_evidence_table.csv`  
- Load audio (soundfile → librosa fallback), mono, resample to `--target_sample_rate` (default 16 kHz)  
- Slice segments using `start_sec` / `end_sec`  
- Write `phase8c_file_acoustic_features.csv` and `phase8c_segment_acoustic_features.csv`  
- Write extraction and validation reports  

---

## What Phase 8C does NOT do

- Train models or run checkpoint inference  
- Modify Phase 8B evidence tables or Phase 7 outputs  
- Fill `evidence_*_score` columns  
- Emit `fake_score`, `real_score`, `ai_score`, `replay_decision`, `final_forensic_status`, or `suspicious_segment_flag`  
- Decide AI vs human or fake vs real  

---

## Protecting against fake/real collapse

- No single “spoof” or “fake” feature column  
- Known labels copied **only** for traceability (`known_origin_label`, etc.) — not used to compute features  
- Invalid/silent audio → blank features + `extraction_status` ≠ `ok` (not guessed values)  

---

## Phase 8C-P1: speed and operability

| Option | Default | Purpose |
|--------|---------|---------|
| `--segment_feature_mode` | `fast` | Skip heavy segment MFCC/contrast (blank, not fake) |
| `--resume` | off | Skip `file_id` / `segment_id` already in output CSVs |
| `--flush_every_files` | 25 | Append partial file CSV |
| `--flush_every_segments` | 500 | Append partial segment CSV |
| `--progress_every` | 100 | Fallback console progress interval |
| `--no_progress` | off | Disable tqdm/fallback progress |

**Deprecated:** `--skip_existing` → use `--resume`.

File-level features always use the **full** set. **Fast** mode applies to segments only.

## CLI (recommended full run)

```text
python code/phase8/features/extract_phase8c_acoustic_features.py ^
  --allow_missing_audio ^
  --segment_feature_mode fast ^
  --resume

python code/phase8/validation/validate_phase8c_features.py
```

Smoke test: `--max_files 5`. Deeper segment pass later: `--segment_feature_mode full` on a subset.

---

## How later phases use these features

| Phase | Use |
|-------|-----|
| **8E** | Train lightweight heads: features → evidence scores |
| **8F** | Fusion uses evidence scores, not raw MFCCs directly |
| **8G** | Reports cite fused status + summaries |

**Phase 8D** (frozen SSL embeddings) remains separate — **NOT STARTED**.

---

## Related

- [phase8c_feature_dictionary.md](phase8c_feature_dictionary.md)  
- [../roadmap/phase8c_status.md](../roadmap/phase8c_status.md)  
- [../evidence_table/phase8b_builder_design.md](../evidence_table/phase8b_builder_design.md)
