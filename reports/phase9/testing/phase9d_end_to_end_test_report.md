# Phase 9D End-to-End Test Report

- Generated: 2026-05-29T15:31:19.925071+00:00
- Status: **experimental architecture verification** (not production-ready, not court-ready proof)

## Purpose

Phase 9D verifies that the Phase 9C live inference pipeline runs end-to-end on controlled
testing audios, that evidence axes remain separate, and that fusion behavior is logically
consistent with expected categories before FastAPI/Gradio finalization (Phase 9E).

## Run summary

- Manifest cases: 43
- Batch rows: 43
- Successful runs (`run_status=ok`): 40
- Failed/errored runs: 3
- Expected-axis consistency (`expected`): 22
- Cases needing review: 14

## Category-wise behavior

| Category | Cases | Expected | Acceptable review | Unexpected | Pipeline error | Needs review |
|---|---:|---:|---:|---:|---:|---:|
| ai_direct | 5 | 5 | 0 | 0 | 0 | 0 |
| ai_fabricated | 5 | 0 | 0 | 0 | 0 | 5 |
| ai_mixer | 5 | 1 | 0 | 1 | 0 | 3 |
| ai_replay | 5 | 5 | 0 | 0 | 0 | 0 |
| bad_audio_invalid | 1 | 1 | 0 | 0 | 0 | 0 |
| bad_audio_short | 1 | 1 | 0 | 0 | 0 | 0 |
| bad_audio_silent | 1 | 1 | 0 | 0 | 0 | 0 |
| human_direct | 5 | 0 | 5 | 0 | 0 | 0 |
| human_fabricated | 5 | 0 | 0 | 0 | 0 | 5 |
| human_mixer | 5 | 4 | 0 | 0 | 0 | 1 |
| human_replay | 5 | 4 | 0 | 1 | 0 | 0 |

## Partial fabrication review (known limitation)

Partial fabrication localization remains a known limitation in this release verification.
On many fabricated test cases, the live partial segment model produces **broad activation**
(`global_activation_not_localized`) rather than a localized region. Fabricated cases therefore
mostly require manual review; treating broad activation as localized fabrication would
overclaim evidence. This conservative behavior is safer than overclaiming localized fabrication.
Replay/mixer context can also block `partial_fusion_eligible` under strict arbitration rules.

Phase 9E apps may proceed only after this limitation is documented in review outputs.
Optional Phase 9D-P4 can tune partial handling later; it is not required to unblock app wiring.

| Case | Category | Gate | Fusion eligible | Block reason |
|---|---|---|---|---|
| phase9d_ai_direct_001_ai_007_direct | ai_direct | global_activation_not_localized | False | global_activation_not_localized |
| phase9d_ai_direct_002_ai_008_direct | ai_direct | global_activation_not_localized | False | global_activation_not_localized |
| phase9d_ai_direct_003_ai_009_direct | ai_direct | global_activation_not_localized | False | global_activation_not_localized |
| phase9d_ai_direct_004_ai_014_direct | ai_direct | global_activation_not_localized | False | global_activation_not_localized |
| phase9d_ai_direct_005_ai_015_direct | ai_direct | global_activation_not_localized | False | global_activation_not_localized |
| phase9d_ai_fabricated_001_ai_003_fabricated | ai_fabricated | global_activation_not_localized | False | global_activation_not_localized |
| phase9d_ai_fabricated_002_ai_005_fabricated | ai_fabricated | global_activation_not_localized | False | global_activation_not_localized |
| phase9d_ai_fabricated_003_ai_008_fabricated | ai_fabricated | global_activation_not_localized | False | global_activation_not_localized |
| phase9d_ai_fabricated_004_ai_010_fabricated | ai_fabricated | global_activation_not_localized | False | global_activation_not_localized |
| phase9d_ai_fabricated_005_ai_013_fabricated | ai_fabricated | global_activation_not_localized | False | global_activation_not_localized |
| phase9d_ai_mixer_001_ai_004_mixer_processed | ai_mixer | localized_pattern_supported | True | none |
| phase9d_ai_mixer_002_ai_008_mixer_processed | ai_mixer | localized_pattern_supported | False | blocked_by_replay_or_mixer_context |
| phase9d_ai_mixer_003_ai_009_mixer_processed | ai_mixer | global_activation_not_localized | False | blocked_by_replay_or_mixer_context |
| phase9d_ai_mixer_004_ai_011_mixer_processed | ai_mixer | localized_pattern_supported | False | blocked_by_replay_or_mixer_context |
| phase9d_ai_mixer_005_ai_012_mixer_processed | ai_mixer | global_activation_not_localized | False | blocked_by_replay_or_mixer_context |
| phase9d_ai_replay_001_ai_003_replay_laptop_mobile | ai_replay | global_activation_not_localized | False | blocked_by_replay_or_mixer_context |
| phase9d_ai_replay_002_ai_007_replay_laptop_mobile | ai_replay | global_activation_not_localized | False | blocked_by_replay_or_mixer_context |
| phase9d_ai_replay_003_ai_009_replay_laptop_mobile | ai_replay | global_activation_not_localized | False | blocked_by_replay_or_mixer_context |
| phase9d_ai_replay_004_ai_011_replay_laptop_mobile | ai_replay | global_activation_not_localized | False | blocked_by_replay_or_mixer_context |
| phase9d_ai_replay_005_ai_013_replay_laptop_mobile | ai_replay | global_activation_not_localized | False | blocked_by_replay_or_mixer_context |
| ... | (23 more rows in CSV) | | | |

## Examples of expected behavior

- `phase9d_ai_direct_001_ai_007_direct` (ai_direct): fusion `suspicious_origin_experimental`
- `phase9d_ai_direct_002_ai_008_direct` (ai_direct): fusion `suspicious_origin_experimental`
- `phase9d_ai_direct_003_ai_009_direct` (ai_direct): fusion `suspicious_origin_experimental`
- `phase9d_ai_direct_004_ai_014_direct` (ai_direct): fusion `suspicious_origin_experimental`
- `phase9d_ai_direct_005_ai_015_direct` (ai_direct): fusion `suspicious_origin_experimental`

## Examples needing review

- `phase9d_ai_fabricated_001_ai_003_fabricated` (ai_fabricated): fusion `suspicious_origin_experimental`, consistency `needs_review`
- `phase9d_ai_fabricated_002_ai_005_fabricated` (ai_fabricated): fusion `suspicious_origin_experimental`, consistency `needs_review`
- `phase9d_ai_fabricated_003_ai_008_fabricated` (ai_fabricated): fusion `suspicious_origin_experimental`, consistency `needs_review`
- `phase9d_ai_fabricated_004_ai_010_fabricated` (ai_fabricated): fusion `suspicious_origin_experimental`, consistency `needs_review`
- `phase9d_ai_fabricated_005_ai_013_fabricated` (ai_fabricated): fusion `suspicious_origin_experimental`, consistency `needs_review`

## Limitations

- No single binary authenticity score was produced; evidence axes remain separate.
- No single fake/real decision field is emitted.
- AASIST/HybridResNet reference models remain inactive.
- Partial localization is experimental; broad activation is documented, not proof of a localized region.
- Category-to-fusion mappings are behavior checks, not validated forensic accuracy.

## Recommendation before Phase 9E

1. Review `phase9d_failure_cases.csv` and `phase9d_partial_behavior_review.csv`.
2. Confirm mixer/replay cases do not become `suspicious_mixed` solely due to partial overfire.
3. Confirm fabricated cases are flagged for review when partial gates show broad activation.
4. Re-run batch inference after limitation wording fixes so JSON/Markdown outputs pass validation.
5. Proceed to FastAPI/Gradio only after manual review of this report and validation PASS.

## Failure / unexpected cases

- `phase9d_ai_mixer_001_ai_004_mixer_processed`: run_status=ok, fusion=suspicious_mixed_evidence_experimental, consistency=unexpected_axis
- `phase9d_bad_audio_invalid_001_bad_invalid`: run_status=pipeline_error, fusion=not_evaluated, consistency=expected
- `phase9d_bad_audio_short_001_bad_short_0_3sec`: run_status=pipeline_error, fusion=not_evaluated, consistency=expected
- `phase9d_bad_audio_silent_001_bad_silent_3sec`: run_status=pipeline_error, fusion=not_evaluated, consistency=expected
- `phase9d_human_replay_003_human_009_replay_laptop_mobile`: run_status=ok, fusion=suspicious_mixed_evidence_experimental, consistency=unexpected_axis
