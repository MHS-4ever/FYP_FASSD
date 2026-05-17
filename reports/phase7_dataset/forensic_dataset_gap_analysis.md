# Forensic Dataset Gap Analysis — Phase 7B

**Current labeled files:** 25 (Phase 7A controlled set)  
**Verdict:** Valid as **holdout / diagnostic** set and label-schema prototype — **not** sufficient for Phase 7C fine-tuning.

---

## 1. Current dataset size and limitation

- Only **25** controlled files (T1–T5).
- Strong **pairing** across conditions but **no speaker-independent scale**.
- Phase 7A product analysis: manipulation-sensitive model with **origin confusion** on replay/processed human.
- **Keep this set as test_holdout** — do not use as main training corpus.

---

## 2. Direct AI gap

**7A finding:** T1.3, T1.5, T3.1 — file-level REAL (~0.43 vote) but **max_chunk_spoof ≈ 1.0** (`direct_ai_file_level_missed_but_segment_suspicious`).

**Collect next:**
- 50–100 **direct AI** clips (TTS, clone, WAV) across English + Urdu
- Include obvious and subtle synthetics
- Label: `origin_label=ai_likely`, `manipulation_label=clean_original`

---

## 3. Clean human Urdu/Pakistani gap

**7A finding:** T1.1 borderline at threshold (FAKE 0.70 vs 0.70) — review, not confirmed FP.

**Collect next:**
- 50–100 **clean direct human** Urdu/Pakistani mobile + USB recordings
- 20–30 s speech, minimal processing
- Label: `human_likely`, `clean_original`, `risk_level=low`

---

## 4. Human replay / processed human gap

**7A finding:** T2.x often FAKE (useful **manipulation** signal, not AI origin).

**Collect next:**
- 30–50 human replay chains (laptop→phone, Bluetooth, phone-to-phone)
- 30–50 mixer/channel processed **human** clips
- Labels: `human_likely` + `replayed_or_re_recorded` or `channel_processed`

---

## 5. AI replay gap

**7A finding:** T3.2–T3.4 detected; **T3.5** file-level miss, segment suspicious.

**Collect next:**
- 30–50 AI→speaker→phone replay samples
- Label: `ai_likely`, `replayed_or_re_recorded`

---

## 6. Partial fabrication / segment-label gap

**7A finding:** **T5_FAB_001** successful segment detection (14–21 s). **T4.3** timestamps have now been filled and validated (35.0–58.0 s; `partial_eval_status=evaluated`).

**Action:**
- Continue collecting **20–40** partial AI insertion samples with **mandatory** `suspicious_start_time` / `suspicious_end_time` in the manifest
- Use T4.3 and T5_FAB_001 as reference rows for segment labeling (pre / insert / post)

---

## 7. WhatsApp / social compression gap

Current: limited rows (e.g. T4.5). Target **30–50** human + AI through WhatsApp/codec chains.

---

## 8. Phone-recorded audio gap

Add `phone_recorded` manipulation_type samples — native phone capture, 30+ files.

---

## 9. YouTube / broadcast gap

Add `youtube_broadcast` chains when available — long-form + broadcast processing.

---

## 10. Minimum recommended dataset before fine-tuning (Phase 7C)

| Category | Minimum count |
|----------|---------------|
| Clean human | 50–100 |
| Direct AI | 50–100 |
| Human replay | 30–50 |
| AI replay | 30–50 |
| Mixer/channel processed | 30–50 |
| WhatsApp/social compressed | 30–50 |
| Edited/spliced | 30–50 |
| Partial AI insertion (with timestamps) | 20–40 |
| **Urdu/Pakistani speakers** | **Prioritize across all categories** |

**Holdout:** Current 25 Phase 7A files remain **controlled evaluation** — not training bulk.

---

## Next action

1. Expand manifest with gap categories above (prioritize partial inserts with timestamps).
2. Sign off Phase 7B label schema → start **7C** planning only after minimum collection counts are met.
3. Keep the current 25-file Phase 7A set as **controlled_holdout** (not training data).

