# Phase 7A — Product-Level Forensic Analysis

> **Main interpretation document** for Phase 7A review. Legacy binary view: `FORENSIC_TEST_ANALYSIS.md`.

---

## 1. Executive summary

The **legacy binary origin accuracy** is low on this 25-file controlled suite (**9/25 yes**, 13 wrong, 3 borderline). That metric treats human replay and channel-processed human audio as failures when the model outputs FAKE.

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
| correct_origin_basic = yes | 9 |
| wrong | 13 |
| borderline | 3 |

| manipulation_type | yes / total |
|-------------------|------------|
| clean_direct | 3/8 |
| human_replay | 0/4 |
| ai_replay | 2/3 |
| mixer_processed | 1/2 |
| whatsapp_compressed | 1/1 |
| edited_spliced | 1/5 |
| partial_ai_insert | 1/2 |

---

## 3. Product-level usefulness summary

| Metric | Count |
|--------|------:|
| clean_human_accepted | 1 |
| clean_human_false_alarm | 0 |
| clean_human_borderline | 2 |
| direct_ai_detected | 2 |
| direct_ai_file_level_missed_but_segment_suspicious | 3 |
| direct_ai_missed (clean file-level miss) | 0 |
| direct_ai_borderline | 0 |
| processed_human_manipulation_detected | 9 |
| processed_human_missed | 1 |
| ai_replay_or_processed_detected | 4 |
| ai_replay_file_level_missed_but_segment_suspicious | 1 |
| processed_ai_file_level_missed_but_segment_suspicious | 0 |
| ai_replay_or_processed_missed (clean) | 0 |
| segment_suspicious (any file) | 25 |
| partial_fabrication_detected (evaluated) | 2 |
| partial_fabrication_missed (evaluated) | 0 |
| partial_not_evaluated_missing_timestamp | 0 |
| borderline_needs_review | 0 |

**Borderline rate** (|decision_score − threshold| ≤ 0.05): 3/25

---

## 4. Clean human performance

Focus: **T1.1**, **T1.2**, **T4.1** (clean_direct, human origin).

| Status | Count |
|--------|------:|
| clean_human_accepted | 1 |
| clean_human_borderline | 2 |
| clean_human_false_alarm | 0 |

| test_id | prediction | decision_score | effective_threshold | product_status | failure_type |
| --- | --- | --- | --- | --- | --- |
| T1.1 | FAKE | 0.7 | 0.7 | clean_human_borderline | borderline |
| T1.2 | REAL | 0.6153846153846154 | 0.7 | clean_human_accepted |  |
| T4.1 | REAL | 0.6666666666666666 | 0.7 | clean_human_borderline | borderline |

**Notes:** **T1.1** is **borderline at the decision threshold** (FAKE, decision_score 0.700 vs threshold 0.700) — treat as **review-required**, not a confirmed clean-human false alarm. **T1.2** / **T4.1** illustrate accepted vs borderline clean human. Legacy binary metrics over-penalize borderline clean human calls.

---

## 5. Direct AI performance

### File-level detected

| test_id | prediction | decision_score | product_status | max_chunk_spoof |
| --- | --- | --- | --- | --- |
| T1.4 | FAKE | 0.875 | direct_ai_detected | 1.0 |
| T4.2 | FAKE | 0.875 | direct_ai_detected | 1.0 |

### File-level missed but segment suspicious

| test_id | prediction | decision_score | max_chunk_spoof | suspicious_chunk_ratio | segment_suspicious | product_status |
| --- | --- | --- | --- | --- | --- | --- |
| T1.3 | REAL | 0.4285714285714285 | 1.0 | 0.42857142857142855 | True | direct_ai_file_level_missed_but_segment_suspicious |
| T1.5 | REAL | 0.4285714285714285 | 1.0 | 0.42857142857142855 | True | direct_ai_file_level_missed_but_segment_suspicious |
| T3.1 | REAL | 0.4285714285714285 | 1.0 | 0.42857142857142855 | True | direct_ai_file_level_missed_but_segment_suspicious |

**Notes:** **T1.3**, **T1.5**, **T3.1** — REAL at file level (~0.43 vote) but **max_chunk_spoof ≈ 1.0**. Not a clean miss; segment-level review recommended.

### File-level missed cleanly

_None._

---

## 6. Processed / replayed human performance

T2.1–T2.5 and edited T5 files: **not simple failures** when FAKE — indicates **manipulation sensitivity** with **origin_confusion**.

| test_id | manipulation_type | prediction | decision_score | product_status | origin_confusion |
| --- | --- | --- | --- | --- | --- |
| T2.1 | human_replay | FAKE | 1.0 | processed_human_manipulation_detected | True |
| T2.2 | mixer_processed | FAKE | 0.9 | processed_human_manipulation_detected | True |
| T2.3 | human_replay | FAKE | 1.0 | processed_human_manipulation_detected | True |
| T2.4 | human_replay | FAKE | 1.0 | processed_human_manipulation_detected | True |
| T2.5 | human_replay | FAKE | 1.0 | processed_human_manipulation_detected | True |
| T5.1 | edited_spliced | FAKE | 0.8571428571428571 | processed_human_manipulation_detected | True |
| T5.2 | edited_spliced | FAKE | 0.9 | processed_human_manipulation_detected | True |
| T5.3 | edited_spliced | REAL | 0.625 | processed_human_missed | False |
| T5.4 | edited_spliced | FAKE | 0.75 | processed_human_manipulation_detected | True |
| T5.5 | edited_spliced | REAL | 0.6666666666666666 | processed_human_manipulation_detected | False |

---

## 7. AI replay and processed AI performance

### Fully detected (file-level)

| test_id | manipulation_type | prediction | decision_score | product_status |
| --- | --- | --- | --- | --- |
| T3.2 | ai_replay | FAKE | 1.0 | ai_replay_or_processed_detected |
| T3.3 | ai_replay | FAKE | 1.0 | ai_replay_or_processed_detected |
| T3.4 | mixer_processed | FAKE | 1.0 | ai_replay_or_processed_detected |
| T4.5 | whatsapp_compressed | FAKE | 1.0 | ai_replay_or_processed_detected |

### File-level missed but segment suspicious

| test_id | manipulation_type | prediction | decision_score | max_chunk_spoof | suspicious_chunk_ratio | product_status |
| --- | --- | --- | --- | --- | --- | --- |
| T3.5 | ai_replay | REAL | 0.5714285714285714 | 0.9946358799934387 | 0.5714285714285714 | ai_replay_file_level_missed_but_segment_suspicious |

**Notes:** **T3.5** — **ai_replay_file_level_missed_but_segment_suspicious** (REAL ~0.571, high chunk spoof). Whole-file pct_vote under-reports segment evidence.

### Fully missed (file and segments weak)

_None._

---

## 8. Partial fabrication performance

### T5_FAB_001 (known region 14.0–21.0 s)

| Field | Value |
|-------|-------|
| prediction | REAL |
| decision_score | 0.6 |
| partial_region_detected | True |
| inside_region_avg_spoof | 0.9513935446739197 |
| outside_region_avg_spoof | 0.6248397068120539 |
| inside_region_dominant_attack | conversion |
| outside_region_dominant_attack | bonafide |

**Assessment:** Successful **segment-level** detection despite whole-file REAL — core Scope 3 signal.

### T4.3 (partial_ai_insert, timestamps missing)

Status: **partial_not_evaluated_missing_timestamp** — do **not** count as partial miss. Add `suspicious_start_time` / `suspicious_end_time` after listening, then re-run product analysis.

### Evaluated partial rows

| test_id | prediction | partial_region_detected | inside_region_avg_spoof | outside_region_avg_spoof | product_status |
| --- | --- | --- | --- | --- | --- |
| T4.3 | REAL | True | 0.5220973361938377 | 0.5507127796587257 | partial_fabrication_detected |
| T5_FAB_001 | REAL | True | 0.9513935446739197 | 0.6248397068120539 | partial_fabrication_detected |

### Not evaluated (missing timestamps)

_None._

---

## 9. Suspicious chunk timeline observations

**Timeline scope in this run:**
- `vad_kept_evaluated_only`: 25 files

_If timelines were produced before the all-chunks export update, re-run the suite with `--save_chunk_timeline` to list every chunk (scores on VAD-kept chunks only)._

**Top files by suspicious_chunk_ratio / max_chunk_spoof:**

| test_id | manipulation_type | prediction | decision_score | suspicious_chunk_count | suspicious_chunk_ratio | max_chunk_spoof |
| --- | --- | --- | --- | --- | --- | --- |
| T2.1 | human_replay | FAKE | 1.0 | 9 | 1.0 | 1.0 |
| T2.3 | human_replay | FAKE | 1.0 | 8 | 1.0 | 1.0 |
| T2.4 | human_replay | FAKE | 1.0 | 10 | 1.0 | 1.0 |
| T3.2 | ai_replay | FAKE | 1.0 | 7 | 1.0 | 1.0 |
| T3.4 | mixer_processed | FAKE | 1.0 | 8 | 1.0 | 1.0 |
| T4.5 | whatsapp_compressed | FAKE | 1.0 | 5 | 1.0 | 1.0 |
| T2.5 | human_replay | FAKE | 1.0 | 10 | 1.0 | 0.9999998807907104 |
| T3.3 | ai_replay | FAKE | 1.0 | 7 | 1.0 | 0.9999997615814209 |
| T2.2 | mixer_processed | FAKE | 0.9 | 9 | 0.9 | 0.9999985694885254 |
| T5.2 | edited_spliced | FAKE | 0.9 | 9 | 0.9 | 0.9999984502792358 |

### Exploratory candidate suspicious regions (top 3 per file, not GT)

**T1.1:**
- #1: 0.0–4.0s, max_spoof=1.000, chunks=1
- #2: 12.0–25.0s, max_spoof=1.000, chunks=4
- #3: 6.0–10.0s, max_spoof=1.000, chunks=1

**T1.2:**
- #1: 72.0–97.0s, max_spoof=1.000, chunks=8
- #2: 99.0–115.0s, max_spoof=1.000, chunks=5
- #3: 0.0–4.0s, max_spoof=1.000, chunks=1

**T1.3:**
- #1: 12.0–19.0s, max_spoof=1.000, chunks=2
- #2: 0.0–4.0s, max_spoof=0.983, chunks=1

**T1.4:**
- #1: 9.0–25.0s, max_spoof=1.000, chunks=5
- #2: 0.0–7.0s, max_spoof=1.000, chunks=2

**T1.5:**
- #1: 12.0–19.0s, max_spoof=1.000, chunks=2
- #2: 0.0–4.0s, max_spoof=0.982, chunks=1

**T2.1:**
- #1: 0.0–28.0s, max_spoof=1.000, chunks=9

**T2.2:**
- #1: 6.0–31.0s, max_spoof=1.000, chunks=8
- #2: 0.0–4.0s, max_spoof=0.999, chunks=1

**T2.3:**
- #1: 6.0–28.0s, max_spoof=1.000, chunks=7
- #2: 0.0–4.0s, max_spoof=1.000, chunks=1

**T2.4:**
- #1: 0.0–31.0s, max_spoof=1.000, chunks=10

**T2.5:**
- #1: 0.0–31.0s, max_spoof=1.000, chunks=10

**T3.1:**
- #1: 12.0–19.0s, max_spoof=1.000, chunks=2
- #2: 0.0–4.0s, max_spoof=0.983, chunks=1

**T3.2:**
- #1: 0.0–22.0s, max_spoof=1.000, chunks=7

**T3.3:**
- #1: 0.0–22.0s, max_spoof=1.000, chunks=7

**T3.4:**
- #1: 0.0–25.0s, max_spoof=1.000, chunks=8

**T3.5:**
- #1: 0.0–4.0s, max_spoof=0.995, chunks=1
- #2: 15.0–22.0s, max_spoof=0.992, chunks=2
- #3: 9.0–13.0s, max_spoof=0.940, chunks=1

**T4.1:**
- #1: 0.0–13.0s, max_spoof=1.000, chunks=4
- #2: 66.0–79.0s, max_spoof=1.000, chunks=4
- #3: 177.0–181.0s, max_spoof=1.000, chunks=1

**T4.2:**
- #1: 9.0–25.0s, max_spoof=1.000, chunks=5
- #2: 0.0–7.0s, max_spoof=1.000, chunks=2

**T4.3:**
- #1: 105.0–118.0s, max_spoof=1.000, chunks=4
- #2: 12.0–19.0s, max_spoof=1.000, chunks=2
- #3: 120.0–130.0s, max_spoof=1.000, chunks=3

**T4.5:**
- #1: 0.0–16.0s, max_spoof=1.000, chunks=5

**T5.1:**
- #1: 0.0–19.0s, max_spoof=1.000, chunks=6

**T5.2:**
- #1: 0.0–16.0s, max_spoof=1.000, chunks=5
- #2: 18.0–31.0s, max_spoof=1.000, chunks=4

**T5.3:**
- #1: 3.0–16.0s, max_spoof=1.000, chunks=4
- #2: 24.0–28.0s, max_spoof=0.665, chunks=1

**T5.4:**
- #1: 3.0–22.0s, max_spoof=1.000, chunks=6

**T5.5:**
- #1: 0.0–7.0s, max_spoof=1.000, chunks=2
- #2: 9.0–16.0s, max_spoof=0.998, chunks=2
- #3: 18.0–25.0s, max_spoof=0.979, chunks=2

**T5_FAB_001:**
- #1: 9.0–19.0s, max_spoof=0.998, chunks=3
- #2: 21.0–28.0s, max_spoof=0.996, chunks=2
- #3: 0.0–4.0s, max_spoof=0.987, chunks=1

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
