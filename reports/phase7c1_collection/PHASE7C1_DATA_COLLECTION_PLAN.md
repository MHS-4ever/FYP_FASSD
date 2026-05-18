# Phase 7C1 — Data Collection Plan (Round-1 operational)

**Status:** Active — collection design  
**Training:** None in this phase  
**Canonical summary:** [PHASE7C1_NEW_FORENSIC_DATA_COLLECTION_PLAN.md](../phase7/PHASE7C1_NEW_FORENSIC_DATA_COLLECTION_PLAN.md)

---

## Round-1 design (doable now)

| Item | Value |
|------|--------|
| Speakers | **15+** (male and female) |
| Variants per `base_id` | **8** |
| Expected files | **~120** (`15 × 8`) |
| Purpose | First **domain-adaptation / fine-tuning** experiment — not final product dataset |

### Eight variants per base_id

1. `human_{id}_clean.wav`  
2. `human_{id}_replay_laptop_mobile.wav`  
3. `human_{id}_mixer_processed.wav`  
4. `human_{id}_fabricated.wav` (partial AI insert + timestamps)  
5. `ai_{id}_direct.wav`  
6. `ai_{id}_replay_laptop_mobile.wav`  
7. `ai_{id}_mixer_processed.wav`  
8. `ai_{id}_fabricated.wav` (partial insert + timestamps)  

---

## Folder layout

```text
reports/phase7c1_collection/
  phase7c1_collection_manifest_template.csv   # 8 example rows (base 001)
  phase7c1_collection_manifest.csv          # filled during collection
  phase7c1_target_counts.csv
  phase7c1_recording_protocols.md
  phase7c1_labeling_guide.md
  phase7c1_naming_convention.md
  phase7c1_split_strategy.md
  phase7c1_quality_checklist.md
  phase7c1_validation_report.md               # after validate script

data/phase7c1/raw/                           # audio files (gitignored recommended)
```

---

## Target counts

See [phase7c1_target_counts.csv](phase7c1_target_counts.csv):

- **Round-1:** 15+ per category (8 categories) → ~120 total  
- **Future ideal:** 50–100 / 30–50 per category for product-grade coverage  

---

## Workflow

1. Assign `speaker_id`, `script_id`, language (English / Urdu / mixed).  
2. Record 8 variants per `base_id` (30–60 s target).  
3. Edit fabricated files; fill `suspicious_start_time` / `suspicious_end_time`.  
4. Copy template → `phase7c1_collection_manifest.csv`; fill paths and metadata.  
5. Assign `split_group_id=base_{id}` and `split` (70/15/15 at group level).  
6. Run validation script.  
7. After approval → Phase 7C feature extraction / fine-tuning planning (not in 7C1).

---

## Not in Round-1

- WhatsApp mandatory  
- YouTube / TikTok / Facebook mandatory  
- Long 60–120 s evidence mandatory  
- 300+ files before first experiment  

---

## Related code

| Script | Role |
|--------|------|
| [validate_phase7c1_collection_manifest.py](../../code/phase7/validate_phase7c1_collection_manifest.py) | Manifest QA |
| [validate_forensic_labels.py](../../code/phase7/validate_forensic_labels.py) | Phase 7B schema (after merge to labeled master) |
