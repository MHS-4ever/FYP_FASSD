# Phase 7E0 — Do Not Do (AASIST Track)

**Status:** Active constraints for Phase 7E  
**Severity:** Violations invalidate experiment claims or waste GPU time

---

## Phase 7E0 (now)

| Do not | Why |
|--------|-----|
| Train or fine-tune any model | 7E0 is planning only |
| Download large pretrained weights | Wait for 7E1 scope + disk plan |
| Implement full AASIST training pipeline | Roadmap only |
| Create `code/phase7/aasist/` production code | Starts in 7E1 |
| Build report generator or website UI | 7D/UI postponed |
| Change locked benchmark metrics without version bump | Breaks comparability |
| Claim AASIST will solve forensic product gaps | Must evaluate first |

---

## Phase 7E0.5–7E2 (before pretrained eval)

| Do not | Why |
|--------|-----|
| Create `code/phase7/aasist/` before 7E0.5 path audit PASS | Wrong paths break adapters |
| Start 7E1 before filling [phase7e0_path_artifact_audit.md](phase7e0_path_artifact_audit.md) | Process gate |
| Start 7E3A/7E3B before 7E1 smoke + 7E2 holdout review | Process gate |
| Merge Phase 7A into train/val manifests | Holdout contamination |
| Use 7C4-v2 decisions as training labels | Circular / wrong supervision |
| Overwrite `hybrid_resnet_environmental_best.pth` | Baseline evidence preserved |

---

## Phase 7E3A–7E4 (pretrained eval, fine-tune, eval)

| Do not | Why |
|--------|-----|
| Start **7E3B fine-tune** before **7E3A** pretrained eval (unless documented no checkpoint) | Must know pretrained direct-AI lift first |
| Tune thresholds on 7A holdout to pass numeric gates | Overfitting holdout |
| Train WavLM/wav2vec2 in parallel on 6GB | Resource policy |
| Joint train HybridResNet + AASIST | Single-variable evaluation |
| Deploy checkpoint as “final product model” | Prototype / evidence only |
| Skip comparison to 7C4-v2 and baseline | Locked protocol |
| Say “forensic proof” or “guaranteed better” in docs or demos | Product wording rules |

---

## Phase 7E5 and product

| Do not | Why |
|--------|-----|
| Run 7E5 fusion before 7E4 sign-off | No evidence basis |
| Replace 7C4-v2 in demos without documented v3 matrix | Regression risk |
| Resume 7D mass report generation on rejected AASIST checkpoint | Weak evidence → risky reports |
| Start Phase 8 web UI before evidence sign-off | Roadmap order |

---

## Phase 7C frozen assets (unchanged)

| Do not | Why |
|--------|-----|
| Re-train 7C3-v1 or deploy standalone R2 as product scorer | [PHASE7C_FINAL_DECISION_RECORD.md](../PHASE7C_FINAL_DECISION_RECORD.md) |
| Use 7C4-v1 | Rejected |
| Change 7C4-v2 logic during 7E without explicit request | Frozen prototype reference |

---

## Environment

| Do not | Why |
|--------|-----|
| Use system `py -3` for project scripts | Missing deps |
| Assume 12GB PC without documenting which machine ran training | Reproducibility |

---

## If unsure

Stop and update [../NEXT_ACTIONS.md](../../NEXT_ACTIONS.md) after review — do not improvise training to “see what happens” without adapter + benchmark compliance.
