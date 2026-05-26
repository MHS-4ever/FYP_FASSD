# Phase 7C4 Calibration Plan

**Phase 7C4 is calibration only — no training, no fine-tuning, no architecture changes.**

## Why Phase 7C3-v1 was rejected

- Clean human acceptance improved, but **replay**, **mixer**, and **partial fabrication** detection collapsed.
- The binary head was trained as a **pure origin proxy** (human vs AI), which is wrong for forensic product semantics.

## Why R2 checkpoints are rejected standalone

| Checkpoint | Clean human | Weakness |
|------------|-------------|----------|
| **best_product** | 14/23 accepted, 7 false alarms | Direct AI 0/23; AI replay 0/23; partial 33/46 |
| **best_loss** | 12/23 accepted, 9 false alarms | Similar; slightly worse clean-human FPs |
| **Original baseline** | 4/23 accepted, 17 false alarms | Strong segment/partial/replay signal |

R2 retargeted the binary head to **forensic-risk** (not origin) and improved clean-human false alarms, but **does not** restore baseline strength on direct AI segment evidence, AI replay, or partial fabrication.

**Standalone R2 checkpoints (`best_product`, `best_loss`) are not accepted.**

## Why calibration is needed

Product decisions require combining:

- `decision_score` (file-level risk)
- `max_chunk_spoof`, `suspicious_chunk_ratio` (segment evidence)
- Partial-region metrics (`partial_region_detected`, `inside_region_max_spoof`, `region_delta`)
- **Agreement/disagreement** between baseline and R2 checkpoints

Calibration tests **threshold sweeps** and a **rule-based decision layer** without retraining.

## What the decision layer does

1. **Clean human:** Accept when R2 product `decision_score < 0.65` and baseline `max_chunk_spoof < 0.98`; file-level FAKE → `clean_human_false_alarm`; else `clean_human_borderline` (manual review).
2. **Direct AI:** Flag suspicious via baseline segment metrics or R2 loss score — not file-level FAKE only.
3. **Human replay / mixer:** Baseline FAKE or score thresholds + R2 loss.
4. **AI replay / AI mixer:** File FAKE or high score → detected; high chunk spoof only → segment-suspicious (separate from detected).
5. **Partial fabrication:** Union of baseline/R2 partial flags and region metrics.

**Borderline is not accepted as clean; it means manual review.**

Outputs: `calibrated_status`, `calibrated_risk_level`, `origin_hint`, `manipulation_hint`, `evidence_summary`, `needs_manual_review`, `selected_model_evidence`.

Metrics report separately: `clean_human_accepted`, `clean_human_borderline`, `clean_human_false_alarm`, `clean_human_review_rate`.

## Acceptance criteria

### Phase 7C1 (decision-layer prototype)

- Clean human false alarms **lower** than original baseline (not sufficient alone).
- `clean_human_accepted + clean_human_borderline` ≥ baseline `clean_human_accepted`.
- `clean_human_accepted` reported separately from borderline.
- Direct AI suspicious/detected **higher** than R2 product alone.
- Replay/mixer detection **close** to original baseline.
- Partial fabrication detection **close** to original baseline.

Passing Phase 7C1 means **accepted for decision-layer prototype only** — not a final product model.

### Phase 7A (holdout) — required review

Run `check_phase7c4_holdout_impact.py` on:

- `reports/phase7/phase7_forensic_tests/results/forensic_test_results_product.csv`
- R2 product/loss holdout product CSVs under `reports/phase7/phase7c3_finetune_r2/evaluation/`

Holdout must be reviewed for:

- `clean_human_accepted` / `borderline` / `false_alarm`
- `direct_ai_detected` / `missed` / `segment_suspicious`
- `processed_human_manipulation_detected` / `missed`
- `ai_replay_or_processed_detected` / `missed` / `segment_suspicious`
- `partial_fabrication_detected` / `missed` / `not_evaluable`

**Decision layer is not fully accepted until Phase 7A impact is reviewed.** More external audio is still required before any market-level claim.

## Deliverables

| Item | Path |
|------|------|
| Shared helpers | `code/phase7/phase7c4_common.py` |
| Checkpoint comparison | `calibration_outputs/phase7c4_checkpoint_comparison.csv` |
| Threshold sweep | `calibration_outputs/phase7c4_threshold_sweep.csv` |
| Candidate decisions | `calibration_outputs/phase7c4_candidate_decisions.csv` |
| Error cases | `calibration_outputs/phase7c4_error_cases.csv` |
| Acceptance matrix | `calibration_outputs/phase7c4_acceptance_matrix.csv` |
| Phase 7A holdout impact | `phase7c4_phase7a_holdout_impact.md` |
| Final recommendation | `phase7c4_final_recommendation.md` |

## Next steps

1. Run Phase 7C4 scripts (see [README.md](README.md)) — use `py -3` if default `python` lacks dependencies.
2. Run `check_phase7c4_holdout_impact.py`.
3. Review acceptance matrix + `phase7c4_final_recommendation.md`.
4. If prototype accepted: wire rules into 7D product reporting; continue data collection.
5. If rejected: Phase 7C3-R3 (separate heads / targets).
