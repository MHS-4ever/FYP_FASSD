# Phase 7C — Final Decision Record

**Status:** Frozen (May 2026)  
**Scope:** Phase 7C1 through 7C4-v2 on controlled Phase 7C1 evaluation audio  
**Short status:** [PHASE7C_STATUS_FREEZE.md](PHASE7C_STATUS_FREEZE.md)

---

## 1. Executive Summary

Phase 7C tested whether fine-tuning `HybridResNetEnvironmental` and post-hoc calibration could become the final forensic product. **None of the fine-tuned checkpoints are accepted as standalone models.** Phase 7C4-v1 was **rejected** for excessive clean-human false alarms. **Phase 7C4-v2 is accepted only as a forensic decision-layer prototype** — it passed 8/8 Phase 7C1 v2 acceptance criteria by combining evidence sources, not by replacing the baseline checkpoint alone.

Going forward:

- **Use** the Phase 6 baseline checkpoint as one **evidence source** (replay/mixer/partial sensitivity).
- **Use** R2 checkpoints only as **optional evidence sources** inside the decision layer — not as final product models.
- **Use** Phase 7C4-v2 calibrated outputs as the **current prototype decision layer** for Phase 7D report development.
- **Do not** deploy 7C3-v1, standalone R2, or 7C4-v1 for product claims.
- **Next active work (May 2026):** Phase **7E** — AASIST candidate evidence branch (7E0 planning → 7E1+).
- **Postponed:** Phase **7D** report-layer **implementation** (specs preserved; resume after evidence improves).

This record does **not** modify any experiment CSVs or checkpoints. It documents what was tested, what failed, what was accepted, and what must not be claimed.

---

## 2. Phase 7C Timeline

### 7C1 — Dataset collection and baseline

- **184** controlled audio files collected (23 base IDs × 8 variants).
- Baseline evaluation on `models_saved/hybrid_resnet_environmental_best.pth` before fine-tuning.
- **Artifacts:** `reports/phase7/phase7c1_collection/`, `reports/phase7/phase7c1_baseline/`
- **Finding:** Baseline shows strong replay/mixer/partial sensitivity on Phase 7C1 tests but **high clean-human false alarms** (17/23).

### 7C2 — Training manifest preparation

- Balanced legacy subset + weighted Phase 7C1 manifests; Phase 7A holdout protected.
- **Artifacts:** `reports/phase7/phase7c2_training_prep/`
- **Status:** Signed off (no training in this step).

### 7C3-v1 — First fine-tuning attempt

- Fine-tuned from Phase 6 checkpoint on 7C2 manifests.
- **Status:** **REJECTED**
- **Artifacts (preserved):** `reports/phase7/phase7c3_finetune/`

### 7C3-R2 — Forensic-risk correction fine-tuning

- Risk-based label weighting; `best_product` and `best_loss` checkpoints saved.
- **Status:** Both checkpoints **REJECTED as standalone** product models.
- **Artifacts (preserved):** `reports/phase7/phase7c3_finetune_r2/`

### 7C4-v1 — First decision-layer calibration

- Fused baseline + R2 with aggressive clean-human rules.
- **Status:** **REJECTED**
- **Artifacts (preserved):** `reports/phase7/phase7c4_calibration/`

### 7C4-v2 — Corrected decision layer

- Role-based fusion: R2 for clean-human caution; baseline for replay/mixer/partial; segment evidence for direct AI.
- **Status:** **ACCEPTED AS DECISION-LAYER PROTOTYPE ONLY**
- **Artifacts:** `reports/phase7/phase7c4_calibration_v2/`
- **Script:** `code/phase7/apply_phase7c4_v2_decision_layer.py`

---

## 3. Final Status Table

| Item | Status | Use Going Forward? | Reason |
|------|--------|-------------------|--------|
| Original Phase 6 baseline checkpoint | Keep as evidence model | **Yes** — one evidence source | Strong replay/mixer/partial sensitivity but high clean-human false alarms |
| Phase 7C3-v1 checkpoint | **Rejected** | **No** | Collapsed manipulation detection; holdout behavior degraded |
| Phase 7C3-R2 `best_product` | **Rejected as standalone** | Only as decision-layer evidence if needed | Improves clean-human vs baseline but direct AI file-level 0/23; AI replay collapsed; partial dropped vs baseline |
| Phase 7C3-R2 `best_loss` | **Rejected as standalone** | Only as decision-layer evidence if needed | Slightly better partial/segment evidence than `best_product` but same direct AI / AI replay failures; not standalone-ready |
| Phase 7C4-v1 decision layer | **Rejected** | **No** | Restored replay/mixer/partial but clean-human false alarms 18/23; only 1/23 accepted |
| Phase 7C4-v2 decision layer | **Accepted prototype** | **Yes** — prototype decision layer | Passed 8/8 v2 Phase 7C1 criteria; not a final model |

### Canonical paths

| Role | Path |
|------|------|
| Baseline checkpoint | `models_saved/hybrid_resnet_environmental_best.pth` |
| 7C1 baseline results | `reports/phase7/phase7c1_baseline/results/phase7c1_baseline_results.csv` |
| R2 eval (evidence only) | `reports/phase7/phase7c3_finetune_r2/evaluation/best_product/phase7c1_after_r2/` |
| **Accepted v2 outputs** | `reports/phase7/phase7c4_calibration_v2/calibration_outputs/` |
| v2 decision CSV | `phase7c4_v2_candidate_decisions.csv` |
| v2 report | `phase7c4_v2_final_recommendation.md` |

---

## 4. Key Metrics (Phase 7C4-v2 on Phase 7C1)

From v2 acceptance evaluation (controlled 7C1 suite):

| Metric | Result |
|--------|--------|
| `clean_human_false_alarm` | **7/23** |
| `clean_human_accepted` + `clean_human_borderline` | **16/23** (1 accepted + 15 borderline) |
| `direct_ai_detected` or segment-suspicious | **19/23** |
| `human_replay_detected` | **23/23** |
| `ai_replay_detected` or segment-suspicious | **23/23** |
| `human_mixer_detected` | **23/23** |
| `ai_mixer_detected` | **23/23** |
| `partial_fabrication_detected` | **44/46** |
| v2 acceptance criteria | **8/8 passed** |

### Important limitation (clean human)

| Metric | Result | Meaning |
|--------|--------|---------|
| `clean_human_accepted` | **1/23** | Only one clip gets automatic clean acceptance |
| `clean_human_borderline` | **15/23** | **Requires manual review** — not clean acceptance |
| `clean_human_false_alarm` | **7/23** | Improved vs baseline (17/23) and v1 (18/23), but not zero |

**Conclusion:** Phase 7C4-v2 is **not** a final product model. It is a **decision-layer prototype** that trades some automatic acceptance for fewer false accusations and stronger manipulation-category coverage on this controlled set.

---

## 5. Why Standalone Checkpoints Were Rejected

`HybridResNetEnvironmental` has **one binary head** and **one attack head**. Phase 7C experiments showed:

1. **7C3-v1** — Training the binary head as pure origin (`human=0`, `AI/mixed=1`) improved some clean-human scores but **collapsed** replay, mixer, partial fabrication, and Phase 7A holdout behavior relative to product needs.

2. **7C3-R2** — Risk-based weighting improved balance vs v1 (fewer clean-human false alarms, preserved mixers) but **did not** restore robust **direct AI file-level detection** (0/23) or **AI replay** behavior. Partial fabrication also **dropped** vs the original baseline on key comparisons.

3. **Neither R2 checkpoint** is acceptable as the sole scorer for a forensic product. They remain useful only as **secondary evidence** inside a fusion layer.

4. **7C4-v1** proved that naïve fusion can restore manipulation sensitivity while **worsening** clean-human outcomes (18/23 false alarms, 1/23 accepted).

5. **7C4-v2** shows that a **role-based decision layer** can meet controlled Phase 7C1 targets, but clean-human **automatic acceptance** remains minimal (1/23). Therefore the **product path** is decision-layer + report layer (7D), not a single fine-tuned weight file.

---

## 6. Accepted Prototype Behavior (Phase 7C4-v2)

Phase 7C4-v2 applies **forensic-risk evidence fusion** (analysis only; no new training):

| Role | Source | Behavior |
|------|--------|----------|
| Clean-human caution | R2 `best_product` (and loss where needed) | Low R2 spoof scores → accept or borderline; extreme baseline spoof → borderline; only high agreement → false alarm |
| Replay / mixer / partial | Original **baseline** checkpoint outputs | Preserves manipulation sensitivity from Phase 6 model |
| Direct AI suspicion | Baseline **segment** evidence + R2 scores | File-level and segment-suspicious branches |
| Conflicts | `clean_human_borderline`, review flags | **Manual review** — not silent clean pass |

Implementation: `code/phase7/apply_phase7c4_v2_decision_layer.py`  
Outputs: `reports/phase7/phase7c4_calibration_v2/` (do not overwrite when re-running historical comparisons).

---

## 7. What Must Not Be Claimed

- Do **not** claim final forensic-grade accuracy or court-ready proof.
- Do **not** claim market-ready fully automated judgment on real-world audio.
- Do **not** claim clean-human samples are always safely accepted (only **1/23** auto-accepted; **15/23** borderline).
- Do **not** claim direct AI is fully solved at file level (19/23 detected or segment-suspicious; not 23/23 file-level detect).
- Do **not** present R2 `best_product` or `best_loss` as the final deployed model.
- Do **not** use Phase 7C3-v1 or Phase 7C4-v1 for product demos without explicit “rejected experiment” context.

---

## 8. What Can Be Claimed

- The project has a **working forensic decision-layer prototype** on the Phase 7C1 controlled suite.
- The prototype **combines** model outputs and **segment-level evidence** rather than a single binary vote.
- On Phase 7C1 tests, it **indicates** strong replay/mixer/partial fabrication signals when baseline evidence supports them.
- It **reduces** clean-human false alarms vs the original baseline (7/23 vs 17/23) by routing many cases to **requires review** rather than false accusation.
- It **supports** Phase 7D development: mapping calibrated statuses to `origin_hint`, `manipulation_hint`, `risk_level`, and safe narrative wording.

---

## 9. Next Phase — Phase 7D Forensic Report Layer

**Next phase:** [PHASE7D_FORENSIC_REPORT_LAYER.md](PHASE7D_FORENSIC_REPORT_LAYER.md)

Phase 7D should turn Phase 7C4-v2 (and underlying evidence) into report-ready fields, for example:

- `origin_hint`
- `manipulation_hint`
- `risk_level`
- `evidence_summary`
- `suspicious_segments`
- `manual_review_required`
- Forensic wording suitable for human reviewers (suspicious / suggests / requires review)

**Do not** resume fine-tuning until after report-layer integration and/or new controlled data collection with an updated evaluation protocol.

---

## Rejected experiment detail (reference)

### Phase 7C3-v1 — REJECTED

- Clean-human false alarms improved in isolation.
- Replay, mixer, partial fabrication, and Phase 7A holdout behavior **collapsed**.
- Binary head trained as pure origin (`human=0`, `AI/mixed=1`) — not suitable for current hybrid behavior.

### Phase 7C3-R2 `best_product` — REJECTED (standalone)

- Better than v1; reduced clean-human false alarms vs baseline; mixer detection preserved.
- Direct AI file-level detection **0/23**; AI replay collapsed; partial fabrication dropped vs original baseline.

### Phase 7C3-R2 `best_loss` — REJECTED (standalone)

- Slightly better partial/segment evidence than `best_product`.
- Direct AI file-level **0/23**; AI replay collapsed; clean-human still insufficient for standalone use.

### Phase 7C4-v1 — REJECTED

- Restored replay/mixer/partial sensitivity.
- Clean-human accepted **1/23**; false alarms **18/23** — too aggressive for forensic product use.

### Phase 7C4-v2 — ACCEPTED (decision-layer prototype only)

- Passed **8/8** Phase 7C1 v2 criteria (see §4).
- Limitation: clean-human auto-accept still **1/23**; most clean clips are **borderline / requires review**.

---

## 12. After Phase 7C — next work (appendix, May 2026)

| Track | Status |
|-------|--------|
| Phase **7E** AASIST evidence branch | **Active** — 7E0 planning + locked benchmark; see [phase7e_aasist_experiment/README.md](phase7e_aasist_experiment/README.md) |
| Phase **7D** forensic report implementation | **Postponed** — planning/spec in [phase7d_report_layer/README.md](phase7d_report_layer/README.md); do not prioritize report generator or external demo over 7E |
| Phase **7C4-v2** | Remains **accepted decision-layer prototype** until 7E5 fusion v3 is evaluated |

Do **not** train AASIST until Phase **7E1** (smoke test) and **7E2** (dataset adapter) are reviewed.

---

## Related documents

| Document | Role |
|----------|------|
| [PHASE7C_STATUS_FREEZE.md](PHASE7C_STATUS_FREEZE.md) | One-page freeze summary |
| [PHASE7C_HYBRID_MODEL_FINE_TUNING.md](PHASE7C_HYBRID_MODEL_FINE_TUNING.md) | Fine-tuning plan + final decision appendix |
| [phase7c4_calibration_v2/README.md](phase7c4_calibration_v2/README.md) | v2 outputs and commands |
| [PHASE7E_AASIST_MODEL_EXPERIMENT_PLAN.md](PHASE7E_AASIST_MODEL_EXPERIMENT_PLAN.md) | **Active** next evidence phase |
| [phase7e_aasist_experiment/README.md](phase7e_aasist_experiment/README.md) | 7E0 hub |
| [PHASE7D_FORENSIC_REPORT_LAYER.md](PHASE7D_FORENSIC_REPORT_LAYER.md) | Report spec (implementation postponed) |
| [../NEXT_ACTIONS.md](../NEXT_ACTIONS.md) | Project checklist |
