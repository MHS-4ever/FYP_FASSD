# Phase 7A — Product-Level Forensic Analysis

> **Main interpretation document** for Phase 7A review. Legacy binary view: `FORENSIC_TEST_ANALYSIS.md`.

---

## 1. Executive summary

The **legacy binary origin accuracy** is low on this 25-file controlled suite (**13/25 yes**, 12 wrong, 0 borderline). That metric treats human replay and channel-processed human audio as failures when the model outputs FAKE.

**Product-level review** shows the current hybrid model is **manipulation-sensitive** and useful beyond legacy binary accuracy:
- Human replay (T2.x) often scores **FAKE / 1.0** — manipulation alerts, not confirmed AI origin.
- **Direct AI file-level misses** (T1.3, T1.5, T3.1) still show **segment-suspicious chunks** (max spoof ≈ 1.0) — whole-file **pct_vote** hides evidence.
- **T3.5** is **file-level missed but segment suspicious** — same pooling vs chunk issue.
- **Segment-level analysis should be part of the final product** (chunk timeline + suspicious regions), not only REAL/FAKE.
- **T5_FAB_001** partial insert (**14–21 s**) detected at segment level despite whole-file REAL.
- **T4.3** not evaluable until suspicious timestamps are added.

**Main weaknesses:** direct AI file-level calibration, origin vs manipulation confusion, pct_vote vs chunk evidence.

---

## 2. Old binary accuracy summary

| Metric | Count |
|--------|------:|
| Total files | 25 |
| correct_origin_basic = yes | 13 |
| wrong | 12 |
| borderline | 0 |

| manipulation_type | yes / total |
|-------------------|------------|
| clean_direct | 3/8 |
| human_replay | 4/4 |
| ai_replay | 0/3 |
| mixer_processed | 1/2 |
| whatsapp_compressed | 0/1 |
| edited_spliced | 5/5 |
| partial_ai_insert | 0/2 |

---

## 3. Product-level usefulness summary

| Metric | Count |
|--------|------:|
| clean_human_accepted | 3 |
| clean_human_false_alarm | 0 |
| clean_human_borderline | 0 |
| direct_ai_detected | 0 |
| direct_ai_file_level_missed_but_segment_suspicious | 0 |
| direct_ai_missed (clean file-level miss) | 5 |
| direct_ai_borderline | 0 |
| processed_human_manipulation_detected | 0 |
| processed_human_missed | 10 |
| ai_replay_or_processed_detected | 0 |
| ai_replay_file_level_missed_but_segment_suspicious | 0 |
| processed_ai_file_level_missed_but_segment_suspicious | 0 |
| ai_replay_or_processed_missed (clean) | 5 |
| segment_suspicious (any file) | 0 |
| partial_fabrication_detected (evaluated) | 0 |
| partial_fabrication_missed (evaluated) | 2 |
| partial_not_evaluated_missing_timestamp | 0 |
| borderline_needs_review | 0 |

**Borderline rate** (|decision_score − threshold| ≤ 0.05): 0/25

---

## 4. Clean human performance

Focus: **T1.1**, **T1.2**, **T4.1** (clean_direct, human origin).

| Status | Count |
|--------|------:|
| clean_human_accepted | 3 |
| clean_human_borderline | 0 |
| clean_human_false_alarm | 0 |

| test_id | prediction | decision_score | effective_threshold | product_status | failure_type |
| --- | --- | --- | --- | --- | --- |
| T1.1 | REAL | 0.0 | 0.7 | clean_human_accepted |  |
| T1.2 | REAL | 0.0 | 0.7 | clean_human_accepted |  |
| T4.1 | REAL | 0.0 | 0.7 | clean_human_accepted |  |

**Notes:** **T1.1** is **borderline at the decision threshold** (FAKE, decision_score 0.700 vs threshold 0.700) — treat as **review-required**, not a confirmed clean-human false alarm. **T1.2** / **T4.1** illustrate accepted vs borderline clean human. Legacy binary metrics over-penalize borderline clean human calls.

---

## 5. Direct AI performance

### File-level detected

_None._

### File-level missed but segment suspicious

_None._

**Notes:** **T1.3**, **T1.5**, **T3.1** — REAL at file level (~0.43 vote) but **max_chunk_spoof ≈ 1.0**. Not a clean miss; segment-level review recommended.

### File-level missed cleanly

| test_id | prediction | decision_score | max_chunk_spoof | suspicious_chunk_ratio |
| --- | --- | --- | --- | --- |
| T1.3 | REAL | 0.0 | 0.15591201186180115 | 0.0 |
| T1.4 | REAL | 0.0 | 0.36545664072036743 | 0.0 |
| T1.5 | REAL | 0.0 | 0.1557193398475647 | 0.0 |
| T3.1 | REAL | 0.0 | 0.15591201186180115 | 0.0 |
| T4.2 | REAL | 0.0 | 0.36545664072036743 | 0.0 |

---

## 6. Processed / replayed human performance

T2.1–T2.5 and edited T5 files: **not simple failures** when FAKE — indicates **manipulation sensitivity** with **origin_confusion**.

| test_id | manipulation_type | prediction | decision_score | product_status | origin_confusion |
| --- | --- | --- | --- | --- | --- |
| T2.1 | human_replay | REAL | 0.0 | processed_human_missed | False |
| T2.2 | mixer_processed | REAL | 0.0 | processed_human_missed | False |
| T2.3 | human_replay | REAL | 0.125 | processed_human_missed | False |
| T2.4 | human_replay | REAL | 0.0 | processed_human_missed | False |
| T2.5 | human_replay | REAL | 0.0 | processed_human_missed | False |
| T5.1 | edited_spliced | REAL | 0.0 | processed_human_missed | False |
| T5.2 | edited_spliced | REAL | 0.0 | processed_human_missed | False |
| T5.3 | edited_spliced | REAL | 0.0 | processed_human_missed | False |
| T5.4 | edited_spliced | REAL | 0.0 | processed_human_missed | False |
| T5.5 | edited_spliced | REAL | 0.0 | processed_human_missed | False |

---

## 7. AI replay and processed AI performance

### Fully detected (file-level)

_None._

### File-level missed but segment suspicious

_None._

**Notes:** **T3.5** — **ai_replay_file_level_missed_but_segment_suspicious** (REAL ~0.571, high chunk spoof). Whole-file pct_vote under-reports segment evidence.

### Fully missed (file and segments weak)

| test_id | manipulation_type | prediction | decision_score | max_chunk_spoof |
| --- | --- | --- | --- | --- |
| T3.2 | ai_replay | REAL | 0.0 | 0.3122127056121826 |
| T3.3 | ai_replay | REAL | 0.0 | 0.5195822715759277 |
| T3.4 | mixer_processed | REAL | 0.125 | 0.8604864478111267 |
| T3.5 | ai_replay | REAL | 0.0 | 0.12199921905994415 |
| T4.5 | whatsapp_compressed | REAL | 0.2 | 0.8653948307037354 |

---

## 8. Partial fabrication performance

### T5_FAB_001 (known region 14.0–21.0 s)

| Field | Value |
|-------|-------|
| prediction | REAL |
| decision_score | 0.0 |
| partial_region_detected | False |
| inside_region_avg_spoof | 0.022575633600354195 |
| outside_region_avg_spoof | 0.006310137498076074 |
| inside_region_dominant_attack | bonafide |
| outside_region_dominant_attack | bonafide |

**Assessment:** Successful **segment-level** detection despite whole-file REAL — core Scope 3 signal.

### T4.3 (partial_ai_insert, timestamps missing)

Status: **partial_not_evaluated_missing_timestamp** — do **not** count as partial miss. Add `suspicious_start_time` / `suspicious_end_time` after listening, then re-run product analysis.

### Evaluated partial rows

| test_id | prediction | partial_region_detected | inside_region_avg_spoof | outside_region_avg_spoof | product_status |
| --- | --- | --- | --- | --- | --- |
| T4.3 | REAL | False | 0.024580690107427472 | 0.03208830604164022 | partial_fabrication_missed |
| T5_FAB_001 | REAL | False | 0.022575633600354195 | 0.006310137498076074 | partial_fabrication_missed |

### Not evaluated (missing timestamps)

_None._

---

## 9. Suspicious chunk timeline observations

**Timeline scope in this run:**
- `All file chunks listed; model scores only on vad_kept/evaluated chunks.`: 25 files

_If timelines were produced before the all-chunks export update, re-run the suite with `--save_chunk_timeline` to list every chunk (scores on VAD-kept chunks only)._

**Top files by suspicious_chunk_ratio / max_chunk_spoof:**

| test_id | manipulation_type | prediction | decision_score | suspicious_chunk_count | suspicious_chunk_ratio | max_chunk_spoof |
| --- | --- | --- | --- | --- | --- | --- |
| T4.5 | whatsapp_compressed | REAL | 0.2 | 1 | 0.2 | 0.8653948307037354 |
| T3.4 | mixer_processed | REAL | 0.125 | 1 | 0.125 | 0.8604864478111267 |
| T2.3 | human_replay | REAL | 0.125 | 1 | 0.125 | 0.7766229510307312 |
| T4.3 | partial_ai_insert | REAL | 0.0227272727272727 | 1 | 0.022727272727272728 | 0.8125700354576111 |
| T1.2 | clean_direct | REAL | 0.0 | 0 | 0.0 | 0.6181467175483704 |
| T2.5 | human_replay | REAL | 0.0 | 0 | 0.0 | 0.528198778629303 |
| T3.3 | ai_replay | REAL | 0.0 | 0 | 0.0 | 0.5195822715759277 |
| T2.4 | human_replay | REAL | 0.0 | 0 | 0.0 | 0.49133387207984924 |
| T2.1 | human_replay | REAL | 0.0 | 0 | 0.0 | 0.3765658140182495 |
| T1.4 | clean_direct | REAL | 0.0 | 0 | 0.0 | 0.36545664072036743 |

### Exploratory candidate suspicious regions (top 3 per file, not GT)

**T2.3:**
- #1: 24.0–28.0s, max_spoof=0.777, chunks=1

**T3.4:**
- #1: 0.0–4.0s, max_spoof=0.860, chunks=1

**T4.3:**
- #1: 15.0–19.0s, max_spoof=0.813, chunks=1

**T4.5:**
- #1: 0.0–4.0s, max_spoof=0.865, chunks=1

---

## 10. What this means for Phase 7B dataset preparation

- Need **separate labels** for **origin** (human / AI / mixed) vs **manipulation** (clean / replay / channel / edit / partial insert).
- Collect more **clean Urdu/Pakistani human** audio; treat borderline cases (e.g. T1.1) as review, not hard false alarms.
- Add more **direct AI** examples (TTS, clone, WAV) matching T1.3/T1.5/T3.1 failure modes.
- Label **human replay** and **processed human** as manipulation-positive, not origin-fake.
- Add **timestamp labels** for partial insertions (T4.3, future PF cases).

---

## 11. What this means for Phase 7C fine-tuning

- Do **not** train only on REAL/FAKE — risks origin/manipulation confusion seen in T2/T5.
- If fine-tuning the hybrid model, target **separate heads or calibration** for origin vs manipulation when feasible.
- Fine-tune **carefully** on 7B labels; do not discard the current hybrid baseline.

---

## 12. What this means for Phase 7E transformer / AASIST experiments

- AASIST / WavLM may help **direct AI weakness** (T1.3, T1.5, T3.1).
- Compare transformer baselines **separately** on direct AI and replay subsets before Phase 7F ensemble.

---

## 13. Next recommended action

1. Fill **T4.3** `suspicious_start_time` / `suspicious_end_time` in the manifest after listening.
2. Re-run **product analysis** (re-inference optional unless timelines missing).
3. Prepare **Phase 7B** dual labels (origin + manipulation) after this cleanup is reviewed.
4. **Do not fine-tune** (7C) until product-level analysis is signed off.
