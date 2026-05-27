# Phase 8 Acceptance Criteria

**Benchmark:** Phase 7C1 controlled set (primary) · Phase 7A holdout (sanity, no threshold tuning for claims)

**Status:** Targets for Phase 8H — not guarantees

---

## Phase 8 controlled targets (Phase 7C1)

| Metric | Target |
|--------|--------|
| clean_human_accepted | **≥ 15/23** |
| clean_human_false_alarm | **≤ 5/23** |
| direct_ai_detected_or_suspicious | **≥ 18/23** |
| human_replay_detected | **≥ 20/23** |
| ai_replay_detected_or_suspicious | **≥ 20/23** |
| human_mixer_detected | **≥ 20/23** |
| ai_mixer_detected | **≥ 20/23** |
| partial_fabrication_detected | **≥ 40/46** |

---

## Additional requirements

| Requirement | Description |
|-------------|-------------|
| Holdout stability | No catastrophic regression on Phase 7A vs Hybrid baseline |
| Forensic-safe wording | Reports distinguish AI-generation vs manipulation/channel evidence |
| Manual review path | System must flag uncertainty — not force binary verdict |
| No holdout tuning | Phase 7A not used to optimize thresholds for product claims |
| Architecture compliance | Origin and manipulation axes both populated in evidence table |

---

## Comparison baselines (must beat or match with better semantics)

| Baseline | Role |
|----------|------|
| HybridResNet Phase 7C1 | Manipulation evidence floor |
| Phase 7C4-v2 | Fusion prototype floor |
| AASIST (archived) | Optional — not required to beat as classifier |

---

## Rejection conditions

Phase 8 candidate is **rejected** if:

- clean_human_false_alarm **> 10/23** on 7C1 (same hard ceiling as Phase 7E fine-tune)  
- direct_ai_detected_or_suspicious **< 15/23**  
- partial_fabrication_detected **< 35/46**  
- Reports equate risk-positive with “AI-generated” without origin evidence  

---

## Sign-off

Phase 8H requires:

1. Metrics table vs targets above  
2. Holdout note (qualitative)  
3. Architecture diagram + evidence table sample  
4. Updated report templates  

See [PHASE8_IMPLEMENTATION_ROADMAP.md](PHASE8_IMPLEMENTATION_ROADMAP.md).
