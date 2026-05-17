# Phase 7 — Forensic Product Upgrade

**Status:** 🟡 **IN PROGRESS** (7A next; no training until 7A reviewed)  
**Priority:** 🔴 CRITICAL  
**Dependencies:** Phase 5 ✅, Phase 6 ✅  
**Scope:** [UPDATED_PROJECT_SCOPE.md](../UPDATED_PROJECT_SCOPE.md)

Phase 7 upgrades FASSD from binary detection to a **Forensic Voice Authenticity Analyzer** with layered reports, segment analysis, and (later) optional transformer models.

**Fixed order:** **7A → 7B → 7C → 7D → 7E → 7F → Phase 8**

---

## Phase 7A — Controlled Forensic Test Suite

**Purpose:** Run current `HybridResNetEnvironmental` on controlled test cases **before** any training.

**Training:** **None**

**Test groups:**

- clean human  
- direct AI  
- human replay  
- AI replay  
- mixer/equalizer processed  
- WhatsApp/social compressed  
- YouTube/broadcast  
- Urdu/Pakistani local audio  
- edited/spliced audio  
- partial AI insertion  

**Outputs:**

- `reports/phase7_forensic_tests/results/forensic_test_results.csv`  
- `reports/phase7_forensic_tests/results/FORENSIC_TEST_ANALYSIS.md`  
- Per-file JSON under `results/json_outputs/`

**Spec:** [PHASE7A_FORENSIC_TEST_SUITE.md](PHASE7A_FORENSIC_TEST_SUITE.md)

**Success includes:** Whether current chunking can flag **suspicious segments** when whole-file prediction is **REAL** (partial fabrication).

---

## Phase 7B — Dataset Preparation for Forensic Labels

**Purpose:** Prepare proper labels for future fine-tuning and report evaluation.

**Training:** Data preparation only

**Required labels (manifest / training CSV):**

| Label field | Description |
|-------------|-------------|
| `origin_label` | human_likely / ai_likely / mixed_or_partial_ai / uncertain |
| `manipulation_label` | clean_original, replayed, channel_processed, etc. |
| `attack_hint` | bonafide, synthesis, voice_conversion, replay, unknown |
| `risk_level` | low, medium, high, inconclusive |
| `partial_fabrication_detected` | true / false |
| `suspicious_start_time` | seconds |
| `suspicious_end_time` | seconds |
| `language` | english, urdu, … |
| `device_chain` | free text |
| `platform` | none, whatsapp, … |
| `recording_condition` | clean_direct, human_replay, … |

Maintain **speaker-independent** splits when merging with ASVspoof/RealWorld.

---

## Phase 7C — Fine-tune Current HybridResNetEnvironmental Model

**Purpose:** Improve the **current hybrid** on local forensic conditions **before** large transformer models.

**Training:** **Yes** — only after **Phase 7A** (and preferably 7B manifest) reviewed

**Focus areas:**

- Urdu/Pakistani speech  
- phone recordings  
- replayed human audio  
- replayed AI audio  
- mixer/channel processed audio  
- WhatsApp/social compression  
- partial inserted AI segments (if labeled in 7B)  

**Strategies:** Freeze branches + train fusion/heads (recommended on 12 GB VRAM); or low-LR full fine-tune with ASVspoof mix.

**Output:** `models_saved/hybrid_resnet_environmental_finetuned.pth` + before/after evaluation on 7A manifest.

---

## Phase 7D — Forensic Report Layer

**Purpose:** Convert raw model outputs into **forensic-style report** wording and structured JSON.

**Priority:** 🔴 **MANDATORY** (not optional)

**Must include:**

- Report JSON schema  
- Risk mapping logic (origin + manipulation + risk_level)  
- Suspicious timeline builder  
- Wording templates (Cases A–K)  
- Limitation wording  
- UI-ready report fields  
- Future PDF/HTML report support  

**Spec:** [PHASE7D_FORENSIC_REPORT_LAYER.md](PHASE7D_FORENSIC_REPORT_LAYER.md)  
**Also:** [FORENSIC_REPORT_OUTPUT_SPEC.md](../FORENSIC_REPORT_OUTPUT_SPEC.md)

**No training** — interpretation layer (rules first; ML optional later).

---

## Phase 7E — Transformer / Attention Model Experiments

**Purpose:** Test **additional** models only after Phase 7A–7D direction is clear and hybrid path is baselined (7A + 7C).

**Training:** Yes — experiments only; compare, do not replace blindly

**Model order (evaluate separately):**

1. **AASIST** (or AASIST-style spoof detector)  
2. **WavLM-base**  
3. **wav2vec2-base**  

**Rules:**

- Keep models **separate** at first — train/eval each standalone.  
- Compare against **7C fine-tuned hybrid** on the **same** 7A forensic manifest.  
- Use **late fusion / ensemble** only if metrics improve (Phase 7F).  
- **Do not early-fuse** everything into one monolithic model initially.  

**Hardware:** 12 GB VRAM — frozen backbone, LoRA/adapters, small-batch fine-tune practical.

**Do not start 7E** until 7A reviewed and 7D spec agreed; **do not start before 7C** hybrid fine-tune unless analysis shows rules-only path is insufficient.

---

## Phase 7F — Ensemble and Final Forensic Decision Logic

**Purpose:** Combine useful scores into **product-level** interpretation.

**Possible inputs:**

- Hybrid ResNet + Environmental score (primary)  
- AASIST score (if 7E)  
- WavLM / wav2vec score (if 7E)  
- Chunk-level suspicious regions (7D timeline)  
- Environmental inconsistency score  

**Outputs:**

- Final origin assessment  
- Manipulation risk  
- Suspicious timeline  
- Complete forensic report (Scope 6)  

**Rules:** Late fusion only after each model’s standalone 7A metrics are documented. No ensemble before 7E comparisons.

---

## Gates and immediate rules

| Gate | Rule |
|------|------|
| **Before 7C** | Complete Phase 7A; document failure patterns |
| **Before 7E** | Complete 7C hybrid fine-tune review |
| **Before 7F** | Complete 7E separate model comparisons |
| **Before any training** | No fine-tuning until 7A `FORENSIC_TEST_ANALYSIS.md` signed off |

> Do not implement transformers, ensemble, or report code in the documentation-only step. See [NEXT_ACTIONS.md](../NEXT_ACTIONS.md).

---

## Legacy note

Earlier “Phase 7 = domain adaptation only if EER > 20%” is **superseded**. RealWorld EER &lt; 20% does **not** skip forensic product work (replay, Urdu, partial fake, reports).

---

## Related

- [FORENSIC_PRODUCT_ROADMAP.md](../FORENSIC_PRODUCT_ROADMAP.md)  
- [NEXT_ACTIONS.md](../NEXT_ACTIONS.md)  
- [PROJECT_STATE_AUDIT.md](../PROJECT_STATE_AUDIT.md)  
- `code/phase7/README.md` — planned automation (not implemented)

**Last updated:** May 2026
