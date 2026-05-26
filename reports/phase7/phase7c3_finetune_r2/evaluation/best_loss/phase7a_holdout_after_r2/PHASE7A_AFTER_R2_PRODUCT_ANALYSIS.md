# Phase 7A — Product-Level Forensic Analysis

> **Main interpretation document** for Phase 7A review. Legacy binary view: `FORENSIC_TEST_ANALYSIS.md`.

---

## 1. Executive summary

The **legacy binary origin accuracy** is low on this 25-file controlled suite (**13/25 yes**, 11 wrong, 1 borderline). That metric treats human replay and channel-processed human audio as failures when the model outputs FAKE.

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
| wrong | 11 |
| borderline | 1 |

| manipulation_type | yes / total |
|-------------------|------------|
| clean_direct | 3/8 |
| human_replay | 1/4 |
| ai_replay | 1/3 |
| mixer_processed | 0/2 |
| whatsapp_compressed | 1/1 |
| edited_spliced | 5/5 |
| partial_ai_insert | 2/2 |

---

## 3. Product-level usefulness summary

| Metric | Count |
|--------|------:|
| clean_human_accepted | 3 |
| clean_human_false_alarm | 0 |
| clean_human_borderline | 0 |
| direct_ai_detected | 0 |
| direct_ai_file_level_missed_but_segment_suspicious | 3 |
| direct_ai_missed (clean file-level miss) | 2 |
| direct_ai_borderline | 0 |
| processed_human_manipulation_detected | 4 |
| processed_human_missed | 6 |
| ai_replay_or_processed_detected | 3 |
| ai_replay_file_level_missed_but_segment_suspicious | 0 |
| processed_ai_file_level_missed_but_segment_suspicious | 1 |
| ai_replay_or_processed_missed (clean) | 1 |
| segment_suspicious (any file) | 19 |
| partial_fabrication_detected (evaluated) | 2 |
| partial_fabrication_missed (evaluated) | 0 |
| partial_not_evaluated_missing_timestamp | 0 |
| borderline_needs_review | 0 |

**Borderline rate** (|decision_score − threshold| ≤ 0.05): 1/25

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
| T1.1 | REAL | 0.5 | 0.7 | clean_human_accepted |  |
| T1.2 | REAL | 0.1282051282051282 | 0.7 | clean_human_accepted |  |
| T4.1 | REAL | 0.1111111111111111 | 0.7 | clean_human_accepted |  |

**Notes:** **T1.1** is **borderline at the decision threshold** (FAKE, decision_score 0.700 vs threshold 0.700) — treat as **review-required**, not a confirmed clean-human false alarm. **T1.2** / **T4.1** illustrate accepted vs borderline clean human. Legacy binary metrics over-penalize borderline clean human calls.

---

## 5. Direct AI performance

### File-level detected

_None._

### File-level missed but segment suspicious

| test_id | prediction | decision_score | max_chunk_spoof | suspicious_chunk_ratio | segment_suspicious | product_status |
| --- | --- | --- | --- | --- | --- | --- |
| T1.3 | REAL | 0.2857142857142857 | 0.9726495146751404 | 0.2857142857142857 | True | direct_ai_file_level_missed_but_segment_suspicious |
| T1.5 | REAL | 0.2857142857142857 | 0.9724408984184265 | 0.2857142857142857 | True | direct_ai_file_level_missed_but_segment_suspicious |
| T3.1 | REAL | 0.2857142857142857 | 0.9726495146751404 | 0.2857142857142857 | True | direct_ai_file_level_missed_but_segment_suspicious |

**Notes:** **T1.3**, **T1.5**, **T3.1** — REAL at file level (~0.43 vote) but **max_chunk_spoof ≈ 1.0**. Not a clean miss; segment-level review recommended.

### File-level missed cleanly

| test_id | prediction | decision_score | max_chunk_spoof | suspicious_chunk_ratio |
| --- | --- | --- | --- | --- |
| T1.4 | REAL | 0.125 | 0.9499486684799194 | 0.125 |
| T4.2 | REAL | 0.125 | 0.9499486684799194 | 0.125 |

---

## 6. Processed / replayed human performance

T2.1–T2.5 and edited T5 files: **not simple failures** when FAKE — indicates **manipulation sensitivity** with **origin_confusion**.

| test_id | manipulation_type | prediction | decision_score | product_status | origin_confusion |
| --- | --- | --- | --- | --- | --- |
| T2.1 | human_replay | FAKE | 1.0 | processed_human_manipulation_detected | True |
| T2.2 | mixer_processed | FAKE | 0.8 | processed_human_manipulation_detected | True |
| T2.3 | human_replay | FAKE | 0.875 | processed_human_manipulation_detected | True |
| T2.4 | human_replay | FAKE | 0.9 | processed_human_manipulation_detected | True |
| T2.5 | human_replay | REAL | 0.2 | processed_human_missed | False |
| T5.1 | edited_spliced | REAL | 0.2857142857142857 | processed_human_missed | False |
| T5.2 | edited_spliced | REAL | 0.6 | processed_human_missed | False |
| T5.3 | edited_spliced | REAL | 0.125 | processed_human_missed | False |
| T5.4 | edited_spliced | REAL | 0.5 | processed_human_missed | False |
| T5.5 | edited_spliced | REAL | 0.3333333333333333 | processed_human_missed | False |

---

## 7. AI replay and processed AI performance

### Fully detected (file-level)

| test_id | manipulation_type | prediction | decision_score | product_status |
| --- | --- | --- | --- | --- |
| T3.2 | ai_replay | FAKE | 1.0 | ai_replay_or_processed_detected |
| T3.3 | ai_replay | FAKE | 0.7142857142857143 | ai_replay_or_processed_detected |
| T4.5 | whatsapp_compressed | FAKE | 0.8 | ai_replay_or_processed_detected |

### File-level missed but segment suspicious

| test_id | manipulation_type | prediction | decision_score | max_chunk_spoof | suspicious_chunk_ratio | product_status |
| --- | --- | --- | --- | --- | --- | --- |
| T3.4 | mixer_processed | REAL | 0.625 | 0.9999982118606567 | 0.625 | processed_ai_file_level_missed_but_segment_suspicious |

**Notes:** **T3.5** — **ai_replay_file_level_missed_but_segment_suspicious** (REAL ~0.571, high chunk spoof). Whole-file pct_vote under-reports segment evidence.

### Fully missed (file and segments weak)

| test_id | manipulation_type | prediction | decision_score | max_chunk_spoof |
| --- | --- | --- | --- | --- |
| T3.5 | ai_replay | REAL | 0.1428571428571428 | 0.9340951442718506 |

---

## 8. Partial fabrication performance

### T5_FAB_001 (known region 14.0–21.0 s)

| Field | Value |
|-------|-------|
| prediction | REAL |
| decision_score | 0.2 |
| partial_region_detected | True |
| inside_region_avg_spoof | 0.579963892698288 |
| outside_region_avg_spoof | 0.3527484736405313 |
| inside_region_dominant_attack | synthesis |
| outside_region_dominant_attack | synthesis |

**Assessment:** Successful **segment-level** detection despite whole-file REAL — core Scope 3 signal.

### T4.3 (partial_ai_insert, timestamps missing)

Status: **partial_not_evaluated_missing_timestamp** — do **not** count as partial miss. Add `suspicious_start_time` / `suspicious_end_time` after listening, then re-run product analysis.

### Evaluated partial rows

| test_id | prediction | partial_region_detected | inside_region_avg_spoof | outside_region_avg_spoof | product_status |
| --- | --- | --- | --- | --- | --- |
| T4.3 | REAL | True | 0.3516590491635725 | 0.1710191228868641 | partial_fabrication_detected |
| T5_FAB_001 | REAL | True | 0.579963892698288 | 0.3527484736405313 | partial_fabrication_detected |

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
| T2.1 | human_replay | FAKE | 1.0 | 9 | 1.0 | 0.9999934434890747 |
| T3.2 | ai_replay | FAKE | 1.0 | 7 | 1.0 | 0.9999117851257324 |
| T2.4 | human_replay | FAKE | 0.9 | 9 | 0.9 | 0.9999939203262329 |
| T2.3 | human_replay | FAKE | 0.875 | 7 | 0.875 | 0.9996079802513123 |
| T4.5 | whatsapp_compressed | FAKE | 0.8 | 4 | 0.8 | 0.999940037727356 |
| T2.2 | mixer_processed | FAKE | 0.8 | 8 | 0.8 | 0.9890975952148438 |
| T3.3 | ai_replay | FAKE | 0.7142857142857143 | 5 | 0.7142857142857143 | 0.9984632730484009 |
| T3.4 | mixer_processed | REAL | 0.625 | 5 | 0.625 | 0.9999982118606567 |
| T5.2 | edited_spliced | REAL | 0.6 | 6 | 0.6 | 0.915808916091919 |
| T1.1 | clean_direct | REAL | 0.5 | 5 | 0.5 | 0.9873262047767639 |

### Exploratory candidate suspicious regions (top 3 per file, not GT)

**T1.1:**
- #1: 0.0–4.0s, max_spoof=0.987, chunks=1
- #2: 12.0–25.0s, max_spoof=0.972, chunks=4

**T1.2:**
- #1: 102.0–106.0s, max_spoof=0.981, chunks=1
- #2: 84.0–91.0s, max_spoof=0.981, chunks=2
- #3: 108.0–112.0s, max_spoof=0.958, chunks=1

**T1.3:**
- #1: 15.0–19.0s, max_spoof=0.973, chunks=1
- #2: 3.0–7.0s, max_spoof=0.929, chunks=1

**T1.4:**
- #1: 0.0–4.0s, max_spoof=0.950, chunks=1

**T1.5:**
- #1: 15.0–19.0s, max_spoof=0.972, chunks=1
- #2: 3.0–7.0s, max_spoof=0.926, chunks=1

**T2.1:**
- #1: 0.0–28.0s, max_spoof=1.000, chunks=9

**T2.2:**
- #1: 12.0–31.0s, max_spoof=0.989, chunks=6
- #2: 0.0–4.0s, max_spoof=0.841, chunks=1
- #3: 6.0–10.0s, max_spoof=0.677, chunks=1

**T2.3:**
- #1: 9.0–28.0s, max_spoof=1.000, chunks=6
- #2: 0.0–4.0s, max_spoof=0.936, chunks=1

**T2.4:**
- #1: 9.0–31.0s, max_spoof=1.000, chunks=7
- #2: 0.0–7.0s, max_spoof=0.998, chunks=2

**T2.5:**
- #1: 0.0–4.0s, max_spoof=0.996, chunks=1
- #2: 18.0–22.0s, max_spoof=0.847, chunks=1

**T3.1:**
- #1: 15.0–19.0s, max_spoof=0.973, chunks=1
- #2: 3.0–7.0s, max_spoof=0.929, chunks=1

**T3.2:**
- #1: 0.0–22.0s, max_spoof=1.000, chunks=7

**T3.3:**
- #1: 0.0–10.0s, max_spoof=0.998, chunks=3
- #2: 15.0–22.0s, max_spoof=0.990, chunks=2

**T3.4:**
- #1: 0.0–7.0s, max_spoof=1.000, chunks=2
- #2: 15.0–22.0s, max_spoof=0.985, chunks=2
- #3: 9.0–13.0s, max_spoof=0.783, chunks=1

**T3.5:**
- #1: 0.0–4.0s, max_spoof=0.934, chunks=1

**T4.1:**
- #1: 177.0–181.0s, max_spoof=0.968, chunks=1
- #2: 69.0–73.0s, max_spoof=0.959, chunks=1
- #3: 3.0–10.0s, max_spoof=0.947, chunks=2

**T4.2:**
- #1: 0.0–4.0s, max_spoof=0.950, chunks=1

**T4.3:**
- #1: 12.0–19.0s, max_spoof=1.000, chunks=2
- #2: 48.0–55.0s, max_spoof=0.910, chunks=2
- #3: 114.0–118.0s, max_spoof=0.700, chunks=1

**T4.5:**
- #1: 0.0–13.0s, max_spoof=1.000, chunks=4

**T5.1:**
- #1: 0.0–4.0s, max_spoof=0.916, chunks=1
- #2: 9.0–13.0s, max_spoof=0.858, chunks=1

**T5.2:**
- #1: 18.0–22.0s, max_spoof=0.916, chunks=1
- #2: 0.0–4.0s, max_spoof=0.907, chunks=1
- #3: 9.0–16.0s, max_spoof=0.889, chunks=2

**T5.3:**
- #1: 9.0–13.0s, max_spoof=0.870, chunks=1

**T5.4:**
- #1: 9.0–22.0s, max_spoof=0.979, chunks=4

**T5.5:**
- #1: 0.0–7.0s, max_spoof=0.970, chunks=2
- #2: 9.0–13.0s, max_spoof=0.884, chunks=1

**T5_FAB_001:**
- #1: 12.0–16.0s, max_spoof=0.803, chunks=1
- #2: 24.0–28.0s, max_spoof=0.770, chunks=1

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
