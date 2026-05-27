# Phase 8A — Success and Rejection Criteria (Frozen)

**Status:** FROZEN for Phase 8A  
**Version:** 8A.1  
**Primary benchmark:** Phase 7C1 controlled set (locked file IDs and roles)  
**Holdout:** Phase 7A — sanity check only; no threshold tuning for product claims  

---

## 1. Purpose

Define when the Phase 8 forensic architecture **succeeds** on controlled evaluation and when a candidate system or design **must be rejected**. These criteria apply at Phase 8H validation; 8A freezes the targets for implementation alignment.

---

## 2. Controlled Phase 7C1 acceptance targets

Counts are on the **locked Phase 7C1** role inventory (same definitions as Phase 7 closure and [../PHASE8_ACCEPTANCE_CRITERIA.md](../PHASE8_ACCEPTANCE_CRITERIA.md)).

| Metric | Target | Notes |
|--------|--------|-------|
| `clean_human_accepted` | **≥ 15 / 23** | `final_forensic_status` = `accept_human_clean` on clean human role |
| `clean_human_false_alarm` | **≤ 5 / 23** | Strong suspicious origin/manipulation on clean human without acceptable abstention |
| `direct_ai_detected_or_suspicious` | **≥ 18 / 23** | `suspicious_origin`, `suspicious_mixed`, or acceptable segment-flagged AI |
| `human_replay_detected` | **≥ 20 / 23** | `replay_rerecorded` in calibrated manipulation (origin remains human-capable) |
| `ai_replay_detected_or_suspicious` | **≥ 20 / 23** | Replay + AI-origin or suspicious combined pattern |
| `human_mixer_detected` | **≥ 20 / 23** | `mixer_channel_processed` without falsely forcing AI origin |
| `ai_mixer_detected` | **≥ 20 / 23** | Mixer + AI-origin evidence both represented |
| `partial_fabrication_detected` | **≥ 40 / 46** | Segment-supported partial role detection |

### Additional success requirements (architecture semantics)

| Requirement | Pass condition |
|-------------|----------------|
| Forensic-safe wording | Reports never equate risk-positive with “AI-generated” without origin evidence |
| Manual review path | `inconclusive_manual_review` used when evidence insufficient — not forced verdict |
| Axis population | Every evaluated file has origin + manipulation fields populated in evidence table |
| Holdout stability | No catastrophic regression on Phase 7A vs Hybrid baseline (qualitative note in 8H) |
| Segment use | Partial and direct-AI roles use segment axis in evaluation, not file mean only |

### Hard failure thresholds (candidate rejection during 8H)

| Metric | Reject if |
|--------|-----------|
| `clean_human_false_alarm` | **> 10 / 23** (same ceiling as Phase 7E fine-tune rejection) |
| `direct_ai_detected_or_suspicious` | **< 15 / 23** |
| `partial_fabrication_detected` | **< 35 / 46** |

---

## 3. Architecture-level rejection criteria

Reject the Phase 8 **design or implementation** (stop and redesign) if any of the following occur:

| # | Rejection condition | Why |
|---|---------------------|-----|
| R1 | Architecture collapses back to **binary fake/real** as sole output | Repeats Phase 7 failure mode |
| R2 | **Replay** treated as proof of AI generation | Violates human-replay semantics |
| R3 | **Mixer/channel** processing treated as proof of AI generation | Violates human-mixer semantics |
| R4 | **No** manual-review / inconclusive state | Forces false certainty |
| R5 | **Clean-human** false alarms remain uncontrolled (above targets and hard ceiling) | Unacceptable for witness audio |
| R6 | **Segment evidence ignored** for partial fabrication and direct-AI | Loses 19/23 segment rescue finding |
| R7 | Report wording makes **absolute claims** (“proven fake”, “definitely AI”) | Violates decision-support scope |
| R8 | Holdout used to **optimize thresholds** then reported as unbiased performance | Invalidates generalization claims |
| R9 | Rejected checkpoints (AASIST 7E, 7C3-R2 standalone) drive **product** decisions | Registry policy violation |
| R10 | `risk_positive` displayed or exported as **fake** | Label semantic violation |

---

## 4. Phase 8A documentation success criteria (this task)

Phase 8A is **accepted** when:

- [x] Origin, manipulation, and segment evidence are clearly separated in architecture freeze  
- [x] Binary fake/real collapse explicitly rejected  
- [x] Clean-human protection included in fusion rules  
- [x] Replay/mixer not treated as AI proof in label schema and fusion  
- [x] Manual-review / inconclusive logic defined  
- [x] Evidence table schema frozen for 8B  
- [x] 8B readiness checklist exists  
- [x] Scope update draft created (not overwriting original scope file)  

---

## 5. Comparison baselines (must match or beat with better semantics)

| Baseline | Role |
|----------|------|
| HybridResNet Phase 7C1 | Manipulation evidence floor |
| Phase 7C4-v2 | Fusion prototype floor |
| AASIST (archived) | Optional — not required to beat as classifier |

Phase 8 must **beat or match** detection counts **while** improving semantic correctness (origin vs manipulation separation and false-alarm control).

---

## 6. Sign-off artifacts (Phase 8H — future)

1. Metrics table vs Section 2 targets  
2. Holdout qualitative note  
3. Architecture diagram + evidence table sample rows  
4. Report template samples with forensic-safe wording  

---

## Related

- [phase8a_fusion_and_abstention_rules.md](../fusion/phase8a_fusion_and_abstention_rules.md)  
- [phase8a_to_phase8b_readiness_review.md](../roadmap/phase8a_to_phase8b_readiness_review.md)  
- [../../phase7/PHASE7_FINAL_CLOSURE_REPORT.md](../../phase7/PHASE7_FINAL_CLOSURE_REPORT.md)

**Phase 8B:** NOT STARTED
