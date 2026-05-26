# Phase 7E0 — AASIST Experiment Plan

**Status:** Active (planning only)  
**Date:** May 2026  
**Training:** **Not allowed** in 7E0

---

## 1. Executive summary

Phase 7E0 locks the plan for adding **AASIST** (Anti-spoofing with Attention-based Spectrogram-Temporal modeling) as the **next model experiment** in FASSD. AASIST is a **candidate evidence branch**, not a replacement for the full forensic product stack.

**Goal:** Document why AASIST is next, what it should and should not do, how it will be trained and evaluated, and how results will be accepted or rejected — **before** any code integration, downloads, or training.

**Out of scope for 7E0:** Training, fine-tuning, large model downloads, full AASIST pipeline implementation, report generator, website UI.

---

## 2. Product architecture (target)

AASIST must be evaluated in the context of the intended evidence → decision → report flow:

```text
Audio
  ↓
HybridResNet evidence branch  (replay / mixer / partial / chunk spoof signals)
  ↓
AASIST evidence branch      (spoof / synthetic evidence — candidate)
  ↓
Decision fusion / calibration layer  (7C4-v2 today; 7E5 v3 after AASIST eval)
  ↓
Forensic report layer  (7D — postponed until evidence improves)
  ↓
Website / product UI  (postponed)
```

**Critical:** HybridResNet remains useful for replay, mixer, partial fabrication, and chunk-level suspicious evidence. AASIST does **not** replace that role by assumption.

---

## 3. Current model stack (context)

| Model / layer | Status | Role |
|---------------|--------|------|
| Original `HybridResNetEnvironmental` | Useful **evidence** | Binary spoof/risk; strong replay/mixer/partial in baseline; high clean-human false alarms |
| Phase 7C3-v1 | **Rejected** | Trained binary as pure origin — destroyed replay/mixer/partial |
| Phase 7C3-R2 | **Rejected** standalone | Better clean-human; weak direct AI; AI replay collapsed |
| Phase 7C4-v2 | **Accepted** prototype decision layer only | 8/8 Phase 7C1 v2 criteria; many clean cases borderline |
| Phase 7D report layer | Planning exists; **implementation postponed** | Needs stronger evidence first |

See [PHASE7C_FINAL_DECISION_RECORD.md](../PHASE7C_FINAL_DECISION_RECORD.md).

---

## 4. Why AASIST is next (not WavLM / wav2vec2 yet)

AASIST is selected **before** WavLM or wav2vec2 because:

| Reason | Detail |
|--------|--------|
| Task fit | Designed for **spoof / synthetic speech detection**, aligned with forensic-risk evidence |
| Resource fit | Lighter and more realistic on **RTX 3050 6GB** laptop and optional **12GB** PC |
| Experiment ladder | Suitable **first** transformer/attention-based experiment in this project |
| Practical fine-tune | Can run or fine-tune with conservative batch sizes on current hardware |
| Deferral | WavLM/wav2vec2 remain **later** if AASIST evaluation does not close key gaps |

**Do not oversell AASIST:**

- It **may** improve direct-AI evidence; it **must be measured**, not assumed.
- It **may still fail** on replay, mixer, or local Urdu/phone domain cases.
- It is **not** forensic proof, a final production model, or a guaranteed upgrade.

---

## 5. What AASIST should do

Evaluate AASIST in **four roles** (same checkpoint, different interpretation in reports):

1. **Standalone spoof/synthetic evidence model** — file- and chunk-level scores on locked benchmarks.
2. **Direct-AI improvement candidate** — compare direct AI detection vs HybridResNet baseline.
3. **Ensemble evidence branch** — inputs to future fusion with HybridResNet (7E5).
4. **Possible future input** to the forensic decision layer — only if 7E4 acceptance criteria are met or branch-only criteria apply.

**Initial training task:** binary **forensic-risk / spoof evidence** (see [PHASE7E0_AASIST_LABEL_STRATEGY.md](PHASE7E0_AASIST_LABEL_STRATEGY.md)), **not** full forensic category labels (origin vs manipulation vs partial taxonomy).

---

## 6. What AASIST should not do

| Do not | Why |
|--------|-----|
| Replace HybridResNet as sole product scorer | Baseline still carries replay/mixer/partial sensitivity |
| Be described as “final production model” | Product needs fusion + report + more data |
| Train on Phase 7A holdout | `controlled_holdout` — evaluation only |
| Use 7C4-v2 outputs as training labels | Comparison baseline only |
| Skip locked benchmark | Acceptance requires [PHASE7E0_LOCKED_BENCHMARK_PROTOCOL.md](PHASE7E0_LOCKED_BENCHMARK_PROTOCOL.md) |
| Block 7D forever | 7D resumes after evidence layer improvement; 7D **implementation** is postponed now |

---

## 7. Datasets

| Dataset | Purpose | Training? |
|---------|---------|-----------|
| Old balanced / ASVspoof-derived | General spoof knowledge; bonafide / synthesis / conversion / replay | Yes (7E3+, via 7C2-style manifests) |
| Phase 7C1 local forensic dataset | Human/AI/replay/mixer/partial; paired variants; Urdu/English/mixed; phone/laptop/mixer | Yes (weighted in manifests) |
| Phase 7A controlled holdout | Final generalization check | **Never** — holdout only |
| Phase 7C4-v2 decision outputs | Compare fusion baseline | **No** — not labels |

**Manifest sources:**

- Training prep: `reports/phase7/phase7c2_training_prep/` (holdout protection in [phase7c2_holdout_protection_report.md](../phase7c2_training_prep/phase7c2_holdout_protection_report.md))
- 7C1 collection: `reports/phase7/phase7c1_collection/`
- 7A: `reports/phase7/phase7_forensic_tests/forensic_test_manifest.csv`

---

## 8. Evaluation modes (locked in separate doc)

| Mode | Description |
|------|-------------|
| Standalone AASIST | Thresholded scores on 7C1 + 7A |
| vs HybridResNet baseline | `phase7c1_baseline_results.csv` path |
| vs 7C3-R2 `best_product` / `best_loss` | Evidence reference only |
| vs 7C4-v2 | `phase7c4_v2_candidate_decisions.csv` — decision-layer comparison |

Full metrics: [PHASE7E0_LOCKED_BENCHMARK_PROTOCOL.md](PHASE7E0_LOCKED_BENCHMARK_PROTOCOL.md).  
Acceptance: [PHASE7E0_ACCEPTANCE_CRITERIA.md](PHASE7E0_ACCEPTANCE_CRITERIA.md).

---

## 9. Resource context

| Machine | GPU | RAM | Notes |
|---------|-----|-----|-------|
| Laptop (primary dev) | NVIDIA RTX 3050 **6GB** | 16GB | Windows, miniconda `(fassd)`, PyTorch CUDA |
| Optional PC | **12GB** VRAM | — | Larger batch / faster cache builds |

Policy: conservative first runs, small batch, careful audio/feature streaming — [PHASE7E0_RESOURCE_AND_TRAINING_CONSTRAINTS.md](PHASE7E0_RESOURCE_AND_TRAINING_CONSTRAINTS.md).

---

## 10. Implementation phases (summary)

| Phase | Deliverable |
|-------|-------------|
| **7E0** | This plan + locked benchmark (current) |
| **7E1** | `code/phase7/aasist/` smoke test — imports, forward pass, VRAM |
| **7E2** | Manifest adapter — 7C1/7C2 → AASIST lists; holdout guard |
| **7E3** | Train/fine-tune on balanced data; separate checkpoints |
| **7E4** | 7C1 + 7A eval vs baselines |
| **7E5** | Fusion decision layer v3 (HybridResNet + AASIST) |

Detail: [PHASE7E0_IMPLEMENTATION_ROADMAP.md](PHASE7E0_IMPLEMENTATION_ROADMAP.md).

---

## 11. Phase 7D postponement

Phase 7D **planning and specs** exist under `reports/phase7/phase7d_report_layer/`. **Report generator implementation and product demo** are postponed because:

- 7C4-v2 still leaves most clean-human cases as **borderline / manual review**.
- Direct AI and AI replay evidence remain weak at the model layer.
- Reports built on weak evidence risk **over-confident wording** even with lint rules.

7D resumes when Phase 7E (or successor evidence) shows measurable improvement on locked benchmarks.

---

## 12. Related documents

| Doc | Role |
|-----|------|
| [PHASE7E0_LOCKED_BENCHMARK_PROTOCOL.md](PHASE7E0_LOCKED_BENCHMARK_PROTOCOL.md) | Metrics and comparison baselines |
| [PHASE7E0_AASIST_LABEL_STRATEGY.md](PHASE7E0_AASIST_LABEL_STRATEGY.md) | Label 0/1 mapping |
| [PHASE7E0_ACCEPTANCE_CRITERIA.md](PHASE7E0_ACCEPTANCE_CRITERIA.md) | Accept / reject / branch-only |
| [PHASE7E0_DO_NOT_DO.md](PHASE7E0_DO_NOT_DO.md) | Hard stops |
| [../PHASE7E_AASIST_MODEL_EXPERIMENT_PLAN.md](../PHASE7E_AASIST_MODEL_EXPERIMENT_PLAN.md) | Parent summary |
