# Phase 7F — Ensemble and Final Decision Logic

**Status:** Planned (after Phase 7E comparisons)  
**Training:** Optional light fusion weights; primarily **decision logic**

---

## 1. Goal

Combine the **best available signals** into a single **product-level forensic decision**: origin, manipulation risk, attack hint, risk level, suspicious timeline, and final interpretation.

Use **late fusion** only after separate models prove value in 7E.

---

## 2. Why this phase exists

No single model covers all T1–T5 conditions. A disciplined ensemble can:

- Weight hybrid + environmental inconsistency for replay/edit cases  
- Add AASIST or SSL scores only where they beat hybrid alone  
- Unify chunk timeline and partial-fabrication rules in one output  

Without 7F, users would see conflicting scores from multiple pipelines.

---

## 3. Inputs

| Input | Source |
|-------|--------|
| Hybrid score (7C) | Primary spoof / attack outputs |
| Environmental evidence | Branch features + inconsistency heuristics |
| AASIST score | If 7E shows benefit |
| WavLM / wav2vec score | If 7E shows benefit |
| Chunk suspicious timeline | 7D builder |
| Partial fabrication logic | Inside/outside region rules (T5) |
| Report templates | 7D Cases A–K |

---

## 4. Outputs

| Output | Description |
|--------|-------------|
| `origin_label` | Final fused origin assessment |
| `manipulation_label` | Final manipulation risk |
| `attack_hint` | Auxiliary fused hint |
| `risk_level` | low \| medium \| high \| inconclusive |
| `suspicious_timeline` | Merged segment list |
| `final_forensic_interpretation` | Narrative for UI/API |
| Complete forensic report JSON | Scope 6 deliverable |

---

## 5. Tasks

1. Define fusion rules (weighted vote, max spoof in region, veto rules for bonafide chunks).  
2. Document weights and when each model contributes.  
3. Run 7A manifest end-to-end through fusion + 7D report.  
4. Compare fused vs hybrid-only metrics.  
5. Lock inference profile for Phase 8 product.  

### Fusion principles

- **Late fusion** — scores at decision time, not shared backbone.  
- **Explainability** — report cites which signals drove timeline entries.  
- **Conservative wording** — fusion does not increase legal certainty language.  
- **Partial fabrication** — region rules override whole-file REAL when thresholds met.  

---

## 6. Success criteria

- [ ] Fused system **improves** agreed metrics vs 7C hybrid alone on 7A holdout.  
- [ ] No regression on critical bonafide conditions without documented tradeoff.  
- [ ] Single report JSON path for Phase 8 API.  
- [ ] Fusion weights and rules versioned in config.  

---

## 7. What not to do in this phase

- Ensemble before 7E standalone evaluation  
- End-to-end train one giant model replacing interpretable branches  
- Remove 7D wording/limitations layer  

---

## 8. Connection to next phase

**Phase 8** — product, API, authentication, upload workflow, PDF/HTML reports, and deployment use 7F + 7D as the analysis core.
