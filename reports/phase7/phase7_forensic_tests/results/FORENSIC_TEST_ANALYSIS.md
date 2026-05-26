# Forensic Test Analysis — Phase 7A

**Files analyzed:** 25  
**Inference errors / missing audio:** 0  

---

## 1. Overall summary

| Metric | Value |
|--------|------:|
| Total files | 25 |
| Correct origin (basic) | 9 |
| Wrong origin | 12 |
| Borderline | 4 |
| Overall accuracy (yes / evaluated) | 9/25 |

**Top failure mode:** fp_processed_human  
**Recommended next action:** Review borderline files manually; consider score band reporting in 7D.  

---

## 2. Accuracy by test group (manipulation_type)

### Clean / direct (`clean_direct`)

| Metric | Value |
|--------|------:|
| Total files | 8 |
| Correct origin | 3 |
| Wrong origin | 3 |
| Borderline | 2 |
| Avg decision_score | 0.627 |

**Common failure pattern:** fn_direct_ai (3)  

**Recommended next action:** Review false negatives/positives; check pooling and VAD on these chains.  

### Human replay (`human_replay`)

| Metric | Value |
|--------|------:|
| Total files | 4 |
| Correct origin | 0 |
| Wrong origin | 4 |
| Borderline | 0 |
| Avg decision_score | 1.000 |

**Common failure pattern:** fp_processed_human (4)  

**Recommended next action:** Collect more replay/channel P0; plan 7B labels and 7C domain adaptation.  

### AI replay (`ai_replay`)

| Metric | Value |
|--------|------:|
| Total files | 3 |
| Correct origin | 2 |
| Wrong origin | 1 |
| Borderline | 0 |
| Avg decision_score | 0.857 |

**Common failure pattern:** fn_ai_replay (1)  

**Recommended next action:** Review false negatives/positives; check pooling and VAD on these chains.  

### Mixer / channel processed (`mixer_processed`)

| Metric | Value |
|--------|------:|
| Total files | 2 |
| Correct origin | 1 |
| Wrong origin | 1 |
| Borderline | 0 |
| Avg decision_score | 0.950 |

**Common failure pattern:** fp_processed_human (1)  

**Recommended next action:** Collect more replay/channel P0; plan 7B labels and 7C domain adaptation.  

### WhatsApp / compressed (`whatsapp_compressed`)

| Metric | Value |
|--------|------:|
| Total files | 1 |
| Correct origin | 1 |
| Wrong origin | 0 |
| Borderline | 0 |
| Avg decision_score | 1.000 |

**Common failure pattern:** None observed in this group.  

**Recommended next action:** Maintain current thresholds; add more P0 samples for coverage.  

### YouTube / broadcast (`youtube_broadcast`)

_No files in this group._

### Phone recorded (`phone_recorded`)

_No files in this group._

### Edited / spliced (`edited_spliced`)

| Metric | Value |
|--------|------:|
| Total files | 5 |
| Correct origin | 1 |
| Wrong origin | 3 |
| Borderline | 1 |
| Avg decision_score | 0.760 |

**Common failure pattern:** fp_human (3)  

**Recommended next action:** Review borderline files manually; consider score band reporting in 7D.  

### Partial AI insertion (`partial_ai_insert`)

| Metric | Value |
|--------|------:|
| Total files | 2 |
| Correct origin | 1 |
| Wrong origin | 0 |
| Borderline | 1 |
| Avg decision_score | 0.573 |

**Common failure pattern:** None observed in this group.  

**Recommended next action:** Partial-region detection looks acceptable; document thresholds in 7D.  

### Noisy room (`noisy_room`)

_No files in this group._

### Unknown (`unknown`)

_No files in this group._

## 3. False positives (human GT, FAKE pred)

| test_id | manipulation_type | prediction | decision_score | correct_origin_basic | failure_type |
| --- | --- | --- | --- | --- | --- |
| T1.1 | clean_direct | FAKE | 0.7 | borderline | borderline |
| T2.1 | human_replay | FAKE | 1.0 | no | fp_processed_human |
| T2.2 | mixer_processed | FAKE | 0.9 | no | fp_processed_human |
| T2.3 | human_replay | FAKE | 1.0 | no | fp_processed_human |
| T2.4 | human_replay | FAKE | 1.0 | no | fp_processed_human |
| T2.5 | human_replay | FAKE | 1.0 | no | fp_processed_human |
| T5.1 | edited_spliced | FAKE | 0.8571428571428571 | no | fp_human |
| T5.2 | edited_spliced | FAKE | 0.9 | no | fp_human |
| T5.4 | edited_spliced | FAKE | 0.75 | no | fp_human |

## 4. False negatives (ai GT, REAL pred)

| test_id | manipulation_type | prediction | decision_score | correct_origin_basic | failure_type |
| --- | --- | --- | --- | --- | --- |
| T1.3 | clean_direct | REAL | 0.4285714285714285 | no | fn_direct_ai |
| T1.5 | clean_direct | REAL | 0.4285714285714285 | no | fn_direct_ai |
| T3.1 | clean_direct | REAL | 0.4285714285714285 | no | fn_direct_ai |
| T3.5 | ai_replay | REAL | 0.5714285714285714 | no | fn_ai_replay |

## 5. Borderline cases

| test_id | manipulation_type | prediction | decision_score | correct_origin_basic | failure_type |
| --- | --- | --- | --- | --- | --- |
| T1.1 | clean_direct | FAKE | 0.7 | borderline | borderline |
| T4.1 | clean_direct | REAL | 0.6666666666666666 | borderline | borderline |
| T4.3 | partial_ai_insert | REAL | 0.5454545454545454 | borderline | borderline |
| T5.5 | edited_spliced | REAL | 0.6666666666666666 | borderline | borderline |

## 6. Partial fabrication cases

| test_id | manipulation_type | prediction | decision_score | correct_origin_basic | failure_type |
| --- | --- | --- | --- | --- | --- |
| T4.3 | partial_ai_insert | REAL | 0.5454545454545454 | borderline | borderline |
| T5_FAB_001 | partial_ai_insert | REAL | 0.6 | yes |  |

## 7. Human replay cases

| test_id | manipulation_type | prediction | decision_score | correct_origin_basic | failure_type |
| --- | --- | --- | --- | --- | --- |
| T2.1 | human_replay | FAKE | 1.0 | no | fp_processed_human |
| T2.3 | human_replay | FAKE | 1.0 | no | fp_processed_human |
| T2.4 | human_replay | FAKE | 1.0 | no | fp_processed_human |
| T2.5 | human_replay | FAKE | 1.0 | no | fp_processed_human |

## 8. AI replay cases

| test_id | manipulation_type | prediction | decision_score | correct_origin_basic | failure_type |
| --- | --- | --- | --- | --- | --- |
| T3.2 | ai_replay | FAKE | 1.0 | yes |  |
| T3.3 | ai_replay | FAKE | 1.0 | yes |  |
| T3.5 | ai_replay | REAL | 0.5714285714285714 | no | fn_ai_replay |

## 9. Mixer / channel processed cases

| test_id | manipulation_type | prediction | decision_score | correct_origin_basic | failure_type |
| --- | --- | --- | --- | --- | --- |
| T2.2 | mixer_processed | FAKE | 0.9 | no | fp_processed_human |
| T3.4 | mixer_processed | FAKE | 1.0 | yes |  |

## 10. Recommended next action

- Address top failure types before Phase 7C fine-tuning.
- Manually review borderline files; tune vote_threshold only with per-group evidence.
