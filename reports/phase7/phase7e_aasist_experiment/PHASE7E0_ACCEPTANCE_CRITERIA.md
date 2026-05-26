# Phase 7E0 — AASIST Acceptance Criteria

**Status:** Locked gates for Phase 7E4 sign-off (numeric minimums — 7E0 hardened)  
**Scope:** Standalone evidence model and branch-only roles

**Disclaimer:** Meeting criteria means **accepted for a defined role in the stack**, not forensic proof, court readiness, or a **final product model**. AASIST may be accepted for a **role**; it is never accepted as the sole forensic judge.

---

## 1. Evidence branch roles (context)

| Branch | Best expected role |
|--------|-------------------|
| **HybridResNet baseline** | Replay / mixer / partial fabrication evidence |
| **AASIST** | Direct AI / synthetic spoof evidence **candidate** |
| **Phase 7C4-v2** | Current decision-layer **prototype** |
| **Future 7E5 fusion** | Combines AASIST + HybridResNet evidence by role |

**Usefulness rule:** AASIST does **not** need to replace HybridResNet. It only needs to improve a **weak evidence axis** (especially **direct AI**) without unacceptable clean-human false alarms.

---

## 2. Evaluation prerequisite

Acceptance decisions require:

- Full [PHASE7E0_LOCKED_BENCHMARK_PROTOCOL.md](PHASE7E0_LOCKED_BENCHMARK_PROTOCOL.md) on 7C1 + 7A  
- [phase7e0_path_artifact_audit.md](phase7e0_path_artifact_audit.md) passed before 7E1/7E2 (see roadmap §7E0.5)  
- Holdout leak check passed (7E2 validation)  
- Thresholds **not** tuned on 7A holdout  
- **7E3A pretrained eval** completed before **7E3B** fine-tune (or documented impossibility)

**Metric definitions:** Counts use the same detection rules as Phase 7C1 baseline analysis unless 7E4 documents a mapping table. “Detected” = file-level detect **or** segment-suspicious per locked protocol (combined as `*_detected_or_segment_suspicious` where noted).

**Phase 7C1 denominators (locked):**

| Category | Denominator | Notes |
|----------|-------------|-------|
| clean_human_false_alarm | **23** | human clean clips |
| direct_ai_* | **23** | direct AI variants |
| ai_replay_* | **23** | AI replay variants |
| human_replay_detected | **23** | human replay variants |
| human_mixer_detected | **23** | human mixer variants |
| ai_mixer_detected | **23** | AI mixer variants |
| partial_fabrication_detected | **46** | partial-fab evaluation units (paired windows/regions per 7C1 partial analysis — confirm in 7E4 against `phase7c1_partial_fabrication_analysis.csv`) |

---

## 3. Standalone useful evidence checkpoint — numeric gates (Phase 7C1)

AASIST (pretrained **7E3A** and/or fine-tuned **7E3B**) is **accepted as standalone useful evidence** only if **all** Phase 7C1 minimums below are met on the evaluated checkpoint.

| Metric | Minimum gate | Strong (optional tag) |
|--------|--------------|-------------------------|
| `clean_human_false_alarm` | **≤ 7 / 23** | ≤ 5 / 23 |
| `direct_ai_detected_or_segment_suspicious` | **≥ 15 / 23** | **≥ 19 / 23** |
| `ai_replay_detected_or_segment_suspicious` | **≥ 15 / 23** | ≥ 18 / 23 |
| `human_replay_detected` | **≥ 20 / 23** | ≥ 22 / 23 |
| `human_mixer_detected` | **≥ 20 / 23** | ≥ 22 / 23 |
| `ai_mixer_detected` | **≥ 20 / 23** | ≥ 22 / 23 |
| `partial_fabrication_detected` | **≥ 40 / 46** | ≥ 43 / 46 |

**Phase 7A holdout (required, no numeric table in 7E0):** Must **not collapse** — document per-category regression vs HybridResNet product CSV. Catastrophic collapse → **reject** (§5).

**Not sufficient alone:** Beating baseline on one metric while failing other rows in this table → **branch-only** (§4) or **reject** (§5).

---

## 4. Branch-only acceptance — direct-AI / synthetic evidence specialist

Use when standalone §3 fails on replay/mixer/partial but AASIST still improves the **direct-AI axis**.

| Metric | Branch-only gate |
|--------|------------------|
| `direct_ai_detected_or_segment_suspicious` | **≥ 15 / 23** |
| `clean_human_false_alarm` | **≤ 10 / 23** |

| Condition | Decision |
|-----------|----------|
| Direct-AI gates met; replay/mixer/partial below §3 | **Branch-only accepted** — direct-AI / synthetic evidence branch only |
| Direct-AI gates met; clean-human false alarms **> 10 / 23** | **Reject** branch-only (too noisy for fusion) |
| **Do not** replace HybridResNet | Baseline remains replay/mixer/partial evidence |
| **Proceed to 7E5** | Fusion v3: AASIST → direct AI / synthetic signal; baseline → manipulation |

Record in `AASIST_BASELINE_COMPARISON.md` with `acceptance_level=branch_only_direct_ai`.

**Explicit:** Branch-only AASIST is **not** a general forensic scorer and **not** a final product model.

---

## 5. Reject or postpone

| Condition | Decision |
|-----------|----------|
| `direct_ai_detected_or_segment_suspicious` only **1–3 / 23** (trivial improvement) | **Reject** or **postpone** |
| `clean_human_false_alarm` **≥ baseline** (typically near **17 / 23** on HybridResNet) with no branch-only path | **Reject** or **postpone** |
| Fails branch-only §4 and standalone §3 | **Reject** |
| Phase **7A holdout collapses** (mass clean false alarm, replay/mixer/partial largely lost vs baseline) | **Reject** |
| Training holdout leak detected | **Invalid run** — discard checkpoint |
| 7E3B run before 7E3A without documented “no suitable pretrained checkpoint” | **Invalid process** — redo 7E3A first |
| Path/artifact audit failed (7E0.5) | **Block** 7E1+ until fixed |

Rejected checkpoints must **not** be wired into 7E5 fusion, product demos, or 7D reports as primary evidence.

---

## 6. Comparison to 7C3-R2 and 7C4-v2

| Comparator | Use |
|------------|-----|
| 7C3-R2 `best_product` / `best_loss` | Reference for clean-human vs direct-AI tradeoff; R2 **not** standalone accepted |
| 7C4-v2 | Whether 7E5 fusion could beat v2 on 8/8-style matrix |

**7C4-v2 remains accepted** as current prototype until 7E5 v3 is evaluated and explicitly supersedes it.

---

## 7. Sign-off levels

| Level | Meaning |
|-------|---------|
| **Standalone accepted** | §3 all numeric gates met — general spoof-risk evidence input (still not final product model) |
| **Branch-only accepted** | §4 — direct-AI/synthetic evidence only; fusion mandatory |
| **Rejected** | §5 |
| **Postponed** | Failed 7E0.5, 7E1 smoke, or insufficient pretrained/fine-tune signal |

---

## 8. 7E5 fusion gate (preview)

7E5 may start only if:

- 7E4 sign-off is **standalone accepted** or **branch-only accepted**, and  
- Fusion plan assigns scores by branch role (§1 table).

7E5 does **not** require AASIST to beat 7C4-v2 on every metric — it requires **documented** improvement on weak axes without holdout collapse.

---

## 9. Related

- [PHASE7E0_LOCKED_BENCHMARK_PROTOCOL.md](PHASE7E0_LOCKED_BENCHMARK_PROTOCOL.md)  
- [PHASE7E0_IMPLEMENTATION_ROADMAP.md](PHASE7E0_IMPLEMENTATION_ROADMAP.md) (7E3A / 7E3B)  
- [PHASE7C_FINAL_DECISION_RECORD.md](../PHASE7C_FINAL_DECISION_RECORD.md)
