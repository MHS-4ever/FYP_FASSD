# Phase 7: Domain Adaptation & Forensic Improvement

**Status**: 🟡 **SPLIT** — Phase 7A is next; fine-tuning (7C) blocked until 7A review  
**Priority**: 🟡 CONDITIONAL (7C) / 🔴 CRITICAL (7A first)  
**Dependencies**: Phase 5 ✅, Phase 6 ✅  

---

## Phase 7 structure (updated)

Phase 7 is no longer “fine-tune if EER > 20%” only. It is a **sequence**:

| Sub-phase | Name | Training? | Document |
|-----------|------|-----------|----------|
| **7A** | Controlled forensic test suite | **No** | [PHASE7A_FORENSIC_TEST_SUITE.md](PHASE7A_FORENSIC_TEST_SUITE.md) |
| **7B** | Controlled local dataset + manifest | Prepare labels only | TBD |
| **7C** | Fine-tune current `HybridResNetEnvironmental` | **Yes** | This file (Section below) |
| **7D** | Report generation + UI labels | Optional | [FORENSIC_REPORT_OUTPUT_SPEC.md](../FORENSIC_REPORT_OUTPUT_SPEC.md) |
| **7E** | Compare SSL/transformer/AASIST-style + possible ensemble | After 7C | [FORENSIC_PRODUCT_ROADMAP.md](../FORENSIC_PRODUCT_ROADMAP.md) |

**Product direction:** [FORENSIC_PRODUCT_ROADMAP.md](../FORENSIC_PRODUCT_ROADMAP.md)

---

## Immediate rule

> **Fine-tuning (Phase 7C) starts only after Phase 7A results are created and reviewed.**

Phase 5 met RealWorld EER &lt; 20%, but **manual forensic conditions** (Urdu, replay chains, WhatsApp, mixer) still fail. Measure them in 7A before changing weights.

---

## Phase 7A (do this first)

- Fill `reports/phase7_forensic_tests/forensic_test_manifest.csv` (≥ 40 P0 clips).
- Run baseline Phase 6 inference — no training.
- Produce `forensic_test_results.csv` and `FORENSIC_TEST_ANALYSIS.md`.

See [PHASE7A_FORENSIC_TEST_SUITE.md](PHASE7A_FORENSIC_TEST_SUITE.md).

---

## Phase 7B (dataset preparation)

- Record/collect controlled audio with `ground_truth_origin` and `ground_truth_manipulation`.
- Extend manifest for training (speaker-independent splits preserved).
- Label: human vs AI origin; clean vs replayed vs processed vs compressed vs edited.

---

## Phase 7C — Fine-tuning (this document’s original scope)

### Trigger (revised)

Proceed with 7C when **Phase 7A analysis** shows:

- Clear failure modes (e.g. Urdu FP, human-replay misinterpretation), and
- A labeled dataset plan from 7B, and
- Agreement that fine-tuning is the right fix (vs report rules-only in 7D).

**Note:** Real-world EER &lt; 20% on Phase 5 **does not** skip 7A.

### Fine-tuning strategies (unchanged recommendations)

**Option 1: Full fine-tuning** — entire model, LR 1e-4–1e-5, 5–10 epochs  

**Option 2: Transfer learning (recommended)** — freeze ResNet + environmental branches; train fusion + heads  

**Option 3: Progressive unfreezing** — gradual unfreeze  

### Data mix

- Keep ASVspoof + RealWorld mix to limit catastrophic forgetting.
- Add 7B controlled clips (Urdu, phone, replay chains, WhatsApp).
- Maintain speaker-independent splits.

### Outputs

```
models_saved/
└── hybrid_resnet_environmental_finetuned.pth

reports/
├── logs/finetuning_metrics.csv
└── evaluation/finetuned_evaluation_report.md
```

### Success criteria (7C)

- [ ] 7A failure modes addressed or documented as residual
- [ ] Real-world / target domain metrics improved on held-out forensic set
- [ ] ASVspoof EER degradation &lt; ~2% vs baseline (tune per project)
- [ ] Before/after comparison saved

---

## Phase 7D — Report & UI

- Map Phase 6 JSON → layered `origin_label`, `manipulation_label`, `risk_level`
- Implement [FORENSIC_REPORT_OUTPUT_SPEC.md](../FORENSIC_REPORT_OUTPUT_SPEC.md)
- Avoid “proved fake” wording

---

## Phase 7E — SSL / transformer / AASIST comparison (after 7C)

**Start only after Phase 7A (testing) and Phase 7C (hybrid fine-tune) are reviewed.**

Phase 7E is **not** “optional because GPU is too small.” A **12 GB VRAM** PC makes these **practical** once the hybrid path is baselined:

| Approach | Notes on 12 GB VRAM |
|----------|---------------------|
| WavLM-base | Frozen backbone + head, LoRA/adapters, or careful small-batch fine-tune |
| wav2vec2-base | Same patterns as WavLM-base |
| AASIST-style front-end | Feasible as experiment or frozen-feature probe |
| Small SSL ablations | Compare against hybrid on **same** 7A forensic manifest |
| Ensemble | Only after side-by-side 7C hybrid vs 7E SSL metrics |

**Do not start 7E yet** — no transformer implementation or training in the current step.

**7E success:** Document whether SSL/transformer beats fine-tuned hybrid on priority gaps (Urdu, replay, WhatsApp, mixer); if not, keep hybrid as primary scorer.

---

## Legacy trigger note (superseded)

Previously: “Skip Phase 7 if Real-world EER &lt; 20%.”  
**Superseded by:** forensic product requirements and Phase 7A gate. EER alone does not cover replay/mixer/Urdu gaps.

---

## Related

- [NEXT_ACTIONS.md](../NEXT_ACTIONS.md)
- [PROJECT_STATE_AUDIT.md](../PROJECT_STATE_AUDIT.md)
- `code/phase7/README.md` — planned scripts

**Last Updated**: May 2026  
**Status**: 7A next; 7C pending 7A sign-off
