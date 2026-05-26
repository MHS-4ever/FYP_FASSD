# Phase 7E — Transformer Model Experiments

**Status:** AASIST track active at **7E0** — see [phase7e_aasist_experiment/](phase7e_aasist_experiment/README.md) and [PHASE7E_AASIST_MODEL_EXPERIMENT_PLAN.md](PHASE7E_AASIST_MODEL_EXPERIMENT_PLAN.md)  
**Training:** Yes — **after 7E1/7E2 review**; compare, do not replace blindly  
**Note:** 7D implementation postponed until evidence improves; AASIST is first in the 7E order.

---

## 1. Goal

Evaluate **additional** spoof-detection / SSL models **separately** against the Phase 7C hybrid baseline on the **same** Phase 7A forensic manifest.

---

## 2. Why this phase exists

Transformers may improve specific conditions (synthesis, conversion, noisy phone) but add cost and complexity. **Separate evaluation** avoids early fusion that hides which model helps which condition.

Process discipline: **7A metrics → 7C hybrid (frozen) → 7E AASIST evaluate → 7E5 fuse if justified → 7D report implementation → 7F**.

---

## 3. Inputs

| Input | Source |
|-------|--------|
| 7A forensic manifest | Unchanged test set |
| 7C hybrid checkpoint | Primary comparison baseline |
| Hardware | **12 GB VRAM** PC (sufficient for frozen/partial fine-tune) |
| Models (order fixed) | See below |

### Model evaluation order

1. **AASIST** (or AASIST-style anti-spoofing)  
2. **WavLM-base**  
3. **wav2vec2-base**  

Each model: train/eval **standalone** first; document metrics per T1–T5 group.

---

## 4. Outputs

| Output | Description |
|--------|-------------|
| Per-model metrics | EER, accuracy, per-condition table on 7A manifest |
| Per-file scores | CSV aligned with `test_id` |
| Comparison report | Hybrid vs AASIST vs WavLM vs wav2vec |
| Keep/drop decision | Which models proceed to 7F |

---

## 5. Tasks

### Per model

1. Set up training/inference pipeline (chunk-based where needed).  
2. Use **frozen backbone + classifier** or **partial unfreezing** first.  
3. Consider **LoRA/adapters** if available to fit 12 GB VRAM.  
4. Run full 7A manifest; same pooling/threshold documentation as hybrid.  
5. Compare **T5 partial fabrication** chunk behavior separately.  

### Rules

- **Do not early-fuse** with hybrid during 7E.  
- **Do not start 7E** before 7C review (unless analysis shows rules-only path insufficient and team agrees).  
- **Only keep** a transformer if it improves **target** conditions without unacceptable regression elsewhere.  

---

## 6. Success criteria

- [ ] All three models evaluated **standalone** on 7A manifest (or documented skip with reason).  
- [ ] Comparison table published vs 7C hybrid.  
- [ ] Clear recommendation for 7F (none / AASIST only / etc.).  
- [ ] No ensemble code required in 7E.  

---

## 7. What not to do in this phase

- Monolithic multi-model training  
- Phase 7F late fusion before standalone tables exist  
- Skip 7A baseline comparison  
- Change Phase 6 hybrid as side effect of 7E code paths without documentation  

---

## 8. Connection to next phase

**7F** combines hybrid + selected 7E model(s) + environmental evidence + chunk timeline + partial-fabrication logic into **final forensic decision** and report JSON.
