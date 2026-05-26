# Phase 7C1 — New Forensic Data Collection Plan

**Status:** **Active** — Round-1 collection design (**no training**)  
**Depends on:** Phase 7A, 7B, 7C0 signed off  
**Operational pack:** [phase7c1_collection/PHASE7C1_DATA_COLLECTION_PLAN.md](phase7c1_collection/PHASE7C1_DATA_COLLECTION_PLAN.md)

---

## 1. Goal

Phase 7C1 defines **what new data must be collected** before fine-tuning. It is **not training**. It creates a **product-aligned forensic dataset** for the first Phase 7C domain-adaptation experiment.

---

## 2. Why this phase is needed

| Prior phase | Conclusion |
|-------------|------------|
| **7A** | Manipulation-sensitive model; origin confusion on processed human; segment-level evidence required. |
| **7B** | Forensic label schema proven on T1–T5 `controlled_holdout`. |
| **7C0** | Legacy corpus technically clean but spoof/replay/studio-heavy; not product-aligned alone. |

**Do not fine-tune on the old dataset alone.** Collect Round-1 forensic data first.

---

## 3. Round-1 design (actual doable plan)

| Item | Value |
|------|--------|
| Speakers | **15+** (male and female) |
| Variants per `base_id` | **8** |
| Expected total | **~120 files** (`15 × 8`) |
| Purpose | First **domain-adaptation / fine-tuning** experiment — **not** final product-grade scale |

### Eight files per base_id

| # | Filename pattern | `variant_id` |
|---|------------------|--------------|
| 1 | `human_{id}_clean.wav` | `human_clean` |
| 2 | `human_{id}_replay_laptop_mobile.wav` | `human_replay_laptop_mobile` |
| 3 | `human_{id}_mixer_processed.wav` | `human_mixer_processed` |
| 4 | `human_{id}_fabricated.wav` | `human_fabricated` |
| 5 | `ai_{id}_direct.wav` | `ai_direct` |
| 6 | `ai_{id}_replay_laptop_mobile.wav` | `ai_replay_laptop_mobile` |
| 7 | `ai_{id}_mixer_processed.wav` | `ai_mixer_processed` |
| 8 | `ai_{id}_fabricated.wav` | `ai_fabricated` |

Details: [phase7c1_naming_convention.md](phase7c1_collection/phase7c1_naming_convention.md), [phase7c1_labeling_guide.md](phase7c1_collection/phase7c1_labeling_guide.md).

---

## 4. Recording rules (Round-1)

| Rule | Value |
|------|--------|
| Script | One paragraph per speaker — English / Urdu / mixed |
| **Recommended duration** | **30–60 seconds** per file |
| Minimum | **≥ 8 seconds** |
| Silence | **0.5–1 s** at start/end |
| Partial fabricated | Timestamps **mandatory** after editing |

Full protocol: [phase7c1_recording_protocols.md](phase7c1_collection/phase7c1_recording_protocols.md).

---

## 5. Target counts

### Round-1 (practical)

| Category | Round-1 target |
|----------|----------------|
| clean_human | 15+ |
| human_replay | 15+ |
| human_mixer_processed | 15+ |
| human_fabricated_partial_ai_insert | 15+ |
| direct_ai | 15+ |
| ai_replay | 15+ |
| ai_mixer_processed | 15+ |
| ai_fabricated_mixed | 15+ |
| **Total** | **~120** |

CSV: [phase7c1_target_counts.csv](phase7c1_collection/phase7c1_target_counts.csv)

### Future ideal (product-grade — not Round-1 gate)

| Category | Future range |
|----------|----------------|
| Clean human | 50–100 |
| Direct AI | 50–100 |
| Human / AI replay | 30–50 each |
| Mixer processed | 30–50 |
| Partial AI insertion | 20–40 |

Round-1 is **enough to start** the first 7C experiment; future counts are for stronger final product coverage.

---

## 6. Not required in Round-1

- WhatsApp mandatory  
- YouTube / TikTok / Facebook mandatory  
- Long 60–120 s evidence simulations mandatory  
- **300+ files** before first experiment  

---

## 7. Pairing and splits

- All 8 variants share `split_group_id=base_{id}` (e.g. `base_001`).  
- **Same `split`** for every variant in the group (70% train / 15% val / 15% test at group level).  
- **Phase 7A T1–T5** remain **`controlled_holdout`** — never in 7C1 training manifest.

[phase7c1_split_strategy.md](phase7c1_collection/phase7c1_split_strategy.md)

---

## 8. Manifest columns

Template: [phase7c1_collection_manifest_template.csv](phase7c1_collection/phase7c1_collection_manifest_template.csv)

Includes: `sample_id`, `audio_path`, `base_id`, `variant_id`, `speaker_id`, `speaker_gender`, `language`, `script_id`, labels, `partial_fabrication_binary`, timestamps, `split_group_id`, `split`, `quality_status`, `review_status`, `notes`, etc.

Example rows for **base_id=001** are pre-filled in the template.

---

## 9. Label rules (summary)

| Variant | Key labels |
|---------|------------|
| Human clean | `human_likely` + `clean_original` + `bonafide` |
| Human replay | `human_likely` + `replayed_or_re_recorded` + `replay` |
| Human mixer | `human_likely` + `channel_processed` + **`attack_hint=unknown`** (not voice_conversion) |
| Human fabricated | `mixed_or_partial_ai` + `edited_or_spliced` + timestamps |
| AI direct | `ai_likely` + `clean_original` + `synthesis` |
| AI replay | `ai_likely` + `replayed_or_re_recorded` + `replay` |
| AI mixer | `ai_likely` + `channel_processed` + `synthesis` |
| AI fabricated | `mixed_or_partial_ai` + timestamps; note `mostly_ai_with_human_insert` in `notes` if needed |

Full table: [phase7c1_labeling_guide.md](phase7c1_collection/phase7c1_labeling_guide.md)

---

## 10. Validation

```text
python code/phase7/validate_phase7c1_collection_manifest.py ^
  --input reports/phase7/phase7c1_collection/phase7c1_collection_manifest.csv ^
  --output reports/phase7/phase7c1_collection/phase7c1_validation_report.md ^
  --allow_warnings
```

Checks: required columns, 8 variants per base (warnings), split consistency, partial timestamps, human-mixer rule, duration, holdout leakage.

---

## 11. Baseline evaluation (after collection validated)

**Status:** Implemented — **no training**

Run the current hybrid checkpoint on all **184** manifest rows and save the **pre–fine-tuning** benchmark.

| Step | Script |
|------|--------|
| Inference | `code/phase7/run_phase7c1_baseline.py` |
| Analysis | `code/phase7/analyze_phase7c1_baseline.py` |

Outputs: [phase7c1_baseline/README.md](phase7c1_baseline/README.md)

Uses product-level `baseline_status` (clean human, direct AI, replay, mixer, partial fabrication region metrics). Phase 7C fine-tuning remains blocked until baseline is reviewed.

---

## 12. Success criteria (Round-1)

- [ ] Manifest template copied and collection started  
- [ ] **~120** files recorded (15+ bases × 8 variants)  
- [ ] Labels and splits validated  
- [ ] Quality checklist passed  
- [ ] Ready for Phase 7C planning (feature extract + fine-tune) — **not** in 7C1  

[phase7c1_quality_checklist.md](phase7c1_collection/phase7c1_quality_checklist.md)

---

## 13. What not to do

- Do **not** fine-tune yet.  
- Do **not** merge Phase 7A holdout into training.  
- Do **not** train REAL/FAKE only.  
- Do **not** split paired variants across train/test.  

---

## Related

| Doc | Path |
|-----|------|
| Operational plan | [PHASE7C1_DATA_COLLECTION_PLAN.md](phase7c1_collection/PHASE7C1_DATA_COLLECTION_PLAN.md) |
| Phase 7B schema | [PHASE7B_FORENSIC_DATASET_PREPARATION.md](PHASE7B_FORENSIC_DATASET_PREPARATION.md) |
| Phase 7C (blocked) | [PHASE7C_HYBRID_MODEL_FINE_TUNING.md](PHASE7C_HYBRID_MODEL_FINE_TUNING.md) |
| Baseline (pre 7C) | [phase7c1_baseline/README.md](phase7c1_baseline/README.md) |
