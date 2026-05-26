# Phase 7C Data Collection Recommendations

Based on **Phase 7C0 current-dataset audit** + **Phase 7A product analysis** + **Phase 7B gap analysis**.

---

## 1. What the old dataset already covers well

- Large-scale **ASVspoof LA / DF / PA** coverage (synthesis, conversion, replay attacks).
- **Studio** read/speech and clean-channel bonafide/spoof pairs.
- **~1.89M** chunked samples with aligned **log-mel** + **12-D environmental** features.
- Strong **spoof diversity** for academic logical-access, deepfake, and physical-access replay.

---

## 2. What the old dataset does not cover well

- **Urdu / Pakistani** speakers (not represented as a labeled domain).
- **Phone-recorded** and **room/noisy** capture (minimal vs studio).
- **WhatsApp / social compression** pipelines (very few social-domain rows vs studio).
- **Human replay** as product-level manipulation (PA replay ≠ phone human replay).
- **Mixer / equalizer** processed human chains.
- **Partial AI insertion** with segment timestamps.
- **Forensic origin + manipulation labels** (training is label + attack_type only).

---

## 3. Minimum data to collect before Phase 7C

| Category | Minimum count | Purpose | Label type |
|----------|---------------|---------|------------|
| Clean human Urdu/Pakistani | 50–100 | Reduce bonafide borderline on local speech | origin: human_likely; manipulation: clean_original |
| Direct AI Urdu/English | 50–100 | File + segment AI detection | origin: ai_likely; manipulation: clean_original |
| Human replay | 30–50 | Manipulation without implying AI origin | human_likely + replayed_or_re_recorded |
| AI replay | 30–50 | AI content through speaker/phone | ai_likely + replayed_or_re_recorded |
| Mixer/channel processed human | 30–50 | T2-style manipulation sensitivity | human_likely + channel_processed |
| Mixer/channel processed AI | 20–30 | Processed AI chains | ai_likely + channel_processed |
| WhatsApp compressed human | 30–50 | Platform robustness | human_likely + platform_compressed |
| WhatsApp compressed AI | 30–50 | Compressed AI detection | ai_likely + platform_compressed |
| Edited/spliced human | 30–50 | Editing manipulation class | human_likely + edited_or_spliced |
| Partial AI insertion (with timestamps) | 20–40 | Segment-level evaluation (T4/T5) | mixed_or_partial_ai + segment labels |
| Phone-recorded / noisy room | 30–50 | Domain gap vs studio | human_likely + noisy_low_quality / phone capture |

---

## 4. Recommended split strategy

- Keep **Phase 7A T1–T5 (25 files)** as **controlled holdout** — never merge into main training.
- New Phase 7C corpus: explicit **train / val / test** with **speaker-independent** splits where possible.
- Group **paired variants** (e.g. `human_001_clean`, `human_001_replay`, `human_001_whatsapp`) in the **same split**.
- Hold out at least one full **condition family** per manipulation type for sanity checks.

---

## 4b. Chunk vs file / utterance balance (sampler design)

The unified manifest is **chunk-level** (multiple rows per source file). Phase 7C0 audit reports both row counts and **unique-file** counts.

- **Balance by speaker/file first**, then by chunks — do not let one long file or heavily chunked domain dominate gradients.
- Keep **paired variants** in the same split (see above).
- Use a **file-balanced sampler** or **cap chunks per file** when `avg_rows_per_file` differs widely across label, attack, dataset, or domain (see `chunk_vs_file_balance_comparison.csv`).
- Review `file_level_balance_summary.csv` before finalizing batch composition.

---

## 5. Training warning

- **Do not** fine-tune on REAL/FAKE alone.
- Calibrate or train **separate origin and manipulation** outputs aligned with Phase 7D report layer.
- Keep **HybridResNetEnvironmental** baseline checkpoint for before/after comparison.
- Start Phase 7C fine-tuning only after this audit is reviewed and new local data is collected and validated (Phase 7B-style labels).

---

## 6. Rule

**No Phase 7C fine-tuning until:**

1. `CURRENT_TRAINING_DATASET_AUDIT.md` reviewed  
2. `dataset_risk_assessment.md` accepted  
3. Minimum collection table above progressed  
4. Phase 7A holdout remains untouched for evaluation
