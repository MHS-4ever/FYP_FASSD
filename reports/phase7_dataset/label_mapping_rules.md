# Forensic Label Mapping Rules — Phase 7B

**Source:** Phase 7A manifest + product results, normalized by `prepare_forensic_dataset.py`.  
**Schema:** [PHASE7_LABEL_SCHEMA.md](../phase7/PHASE7_LABEL_SCHEMA.md)

---

## Principles

1. **Do not train on REAL/FAKE only** — use `origin_label` + `manipulation_label` (+ optional `attack_hint`, `risk_level`).
2. **Human replay** → `origin_label=human_likely`, `manipulation_label=replayed_or_re_recorded`, `attack_hint=replay`.
3. **Direct AI** → `origin_label=ai_likely`, `manipulation_label=clean_original`.
4. **Partial AI insert** → `origin_label=mixed_or_partial_ai`, `partial_fabrication_binary=1`, segment rows for pre/insert/post.
5. **Borderline / missing partial timestamps** → `review_status=needs_review`.
6. **Phase 7A T1–T5 set** → `dataset_role=controlled_holdout`, **`use_for_training=false` always**.

---

## Condition mapping

| manipulation_type | ground_truth_origin | origin_label | manipulation_label | attack_hint (default) |
|-------------------|---------------------|--------------|----------------------|------------------------|
| clean_direct | human | human_likely | clean_original | bonafide |
| clean_direct | ai | ai_likely | clean_original | synthesis / voice_conversion |
| human_replay | human | human_likely | replayed_or_re_recorded | replay |
| ai_replay | ai | ai_likely | replayed_or_re_recorded | replay |
| mixer_processed | human | human_likely | channel_processed | **unknown** (not voice_conversion) |
| mixer_processed | ai | ai_likely | channel_processed | synthesis / voice_conversion |
| whatsapp_compressed | * | human/ai_likely | platform_compressed | context-based |
| edited_spliced | human | human_likely | edited_or_spliced | unknown |
| partial_ai_insert | mixed | mixed_or_partial_ai | edited_or_spliced | voice_conversion / synthesis |
| noisy_room | * | human/ai_likely | noisy_low_quality | unknown |

---

## Risk level adjustments

| Signal | risk_level |
|--------|------------|
| clean_human_borderline (product) | inconclusive |
| direct_ai_detected | high |
| direct_ai_file_level_missed_but_segment_suspicious | medium |
| partial insert region (segment) | high |
| human replay FAKE | medium–high |

---

## Review / training flags

| Condition | review_status | use_for_training | use_for_validation |
|-----------|---------------|------------------|---------------------|
| Approved (Phase 7A holdout) | approved | **false** | true |
| partial_ai_insert, no timestamps | needs_review | false | false |
| clean_human_borderline | needs_review | false | false |
| audio missing | rejected | false | false |

`forensic_training_manifest_preview.csv` is a **future CSV format example** only — not actual 7C training data.

---

## Binary preview fields

- `origin_binary`: human | ai | mixed | unknown (from ground truth)
- `manipulation_binary`: clean | manipulated | uncertain
- `partial_fabrication_binary`: 0 | 1

