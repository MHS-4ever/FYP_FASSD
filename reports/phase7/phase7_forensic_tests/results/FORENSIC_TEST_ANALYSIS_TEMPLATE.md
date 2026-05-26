# Forensic Test Analysis — Phase 7A

**Status:** Template (fill after `forensic_test_results.csv` exists)  
**Manifest:** `../forensic_test_manifest.csv`  
**Results:** `forensic_test_results.csv`  
**Inference profile:** pct_vote, chunk_threshold=0.65, vote_threshold=0.70, VAD percentile=40

---

## Executive summary

| Metric | Value |
|--------|------:|
| Total P0 files tested | _TBD_ |
| Correct origin (basic) | _TBD_ |
| Wrong origin | _TBD_ |
| Borderline | _TBD_ |
| Top failure mode #1 | _TBD_ |
| Recommended next action | _TBD_ |

---

## Analysis by condition group

Copy this block for each group. Replace `_TBD_` after runs.

### Clean human (direct)

| Metric | Value |
|--------|------:|
| Total files | _TBD_ |
| Correct origin | _TBD_ |
| Wrong origin | _TBD_ |
| Borderline | _TBD_ |
| Avg decision_score | _TBD_ |

**Common failure pattern:** _TBD_

**Recommended next action:** _TBD_

---

### Direct AI

| Metric | Value |
|--------|------:|
| Total files | _TBD_ |
| Correct origin | _TBD_ |
| Wrong origin | _TBD_ |
| Borderline | _TBD_ |
| Avg decision_score | _TBD_ |

**Common failure pattern:** _TBD_

**Recommended next action:** _TBD_

---

### Human replay (laptop/speaker → mobile)

| Metric | Value |
|--------|------:|
| Total files | _TBD_ |
| Correct origin | _TBD_ |
| Wrong origin | _TBD_ |
| Borderline | _TBD_ |
| Avg decision_score | _TBD_ |

**Common failure pattern:** _TBD_

**Recommended next action:** _TBD_

---

### AI replay (laptop/speaker → mobile)

| Metric | Value |
|--------|------:|
| Total files | _TBD_ |
| Correct origin | _TBD_ |
| Wrong origin | _TBD_ |
| Borderline | _TBD_ |
| Avg decision_score | _TBD_ |

**Common failure pattern:** _TBD_

**Recommended next action:** _TBD_

---

### Mixer / channel processed

| Metric | Value |
|--------|------:|
| Total files | _TBD_ |
| Correct origin | _TBD_ |
| Wrong origin | _TBD_ |
| Borderline | _TBD_ |
| Avg decision_score | _TBD_ |

**Common failure pattern:** _TBD_

**Recommended next action:** _TBD_

---

### Partial fabrication (`partial_ai_insert`, e.g. `T5_FAB_001`)

| Metric | Value |
|--------|------:|
| Total files | _TBD_ |
| `partial_region_detected` matches GT | _TBD_ |
| Whole-file REAL but region detected | _TBD_ |
| Avg `inside_region_avg_spoof` | _TBD_ |
| Avg `outside_region_avg_spoof` | _TBD_ |
| Avg delta (inside − outside) | _TBD_ |

**Reference case:** `T5_FAB_001` — 34 s, fake insert **14–21 s**; do not score on whole-file alone.

**Common failure pattern:** _TBD_

**Recommended next action:** _TBD_

---

### WhatsApp / platform compressed

| Metric | Value |
|--------|------:|
| Total files | _TBD_ |
| Correct origin | _TBD_ |
| Wrong origin | _TBD_ |
| Borderline | _TBD_ |
| Avg decision_score | _TBD_ |

**Common failure pattern:** _TBD_

**Recommended next action:** _TBD_

---

### YouTube / broadcast

| Metric | Value |
|--------|------:|
| Total files | _TBD_ |
| Correct origin | _TBD_ |
| Wrong origin | _TBD_ |
| Borderline | _TBD_ |
| Avg decision_score | _TBD_ |

**Common failure pattern:** _TBD_

**Recommended next action:** _TBD_

---

### Urdu / Pakistani

| Metric | Value |
|--------|------:|
| Total files | _TBD_ |
| Correct origin | _TBD_ |
| Wrong origin | _TBD_ |
| Borderline | _TBD_ |
| Avg decision_score | _TBD_ |

**Common failure pattern:** _TBD_

**Recommended next action:** _TBD_

---

### Edited / spliced

| Metric | Value |
|--------|------:|
| Total files | _TBD_ |
| Correct origin | _TBD_ |
| Wrong origin | _TBD_ |
| Borderline | _TBD_ |
| Avg decision_score | _TBD_ |

**Common failure pattern:** _TBD_

**Recommended next action:** _TBD_

---

### Partial AI insertion

| Metric | Value |
|--------|------:|
| Total files | _TBD_ |
| Correct origin | _TBD_ |
| Wrong origin | _TBD_ |
| Borderline | _TBD_ |
| Avg decision_score | _TBD_ |

**Common failure pattern:** _TBD_

**Recommended next action:** _TBD_

---

## Gate for Phase 7C (fine-tuning)

- [ ] At least 40 P0 files tested  
- [ ] Failure patterns documented per group  
- [ ] Team agrees fine-tuning dataset priorities  

**Do not start training until this checklist is signed off.**
