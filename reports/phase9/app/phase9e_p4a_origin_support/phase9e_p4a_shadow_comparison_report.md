# Phase 9E-P4A Shadow Origin-Support Comparison Report

Generated: 2026-06-03T20:38:35.600925+00:00
Mode: full
Audit: one or more reference origin-support models runnable for shadow eval

## SSL baseline (active release origin model)

{
  "total_files": 184,
  "evaluated_files": 184,
  "runnable_files": 184,
  "failed_files": 0,
  "runtime_error_count": 0,
  "avg_runtime_sec": 0.0,
  "ai_origin_accuracy_on_ai_variants": 0.5,
  "human_origin_accuracy_on_human_variants": 1.0,
  "ai_clean_detect_rate": 1.0,
  "ai_fabricated_detect_rate": 1.0,
  "ai_mixer_detect_rate": 0.0,
  "ai_replayed_detect_rate": 0.0,
  "human_clean_false_ai_rate": 0.0,
  "human_fabricated_false_ai_rate": 0.0,
  "human_mixer_false_ai_rate": 0.0,
  "human_replayed_false_ai_rate": 0.0,
  "direct_origin_accuracy": 1.0,
  "processed_origin_stability": 1.0,
  "agreement_with_ssl_origin_rate": 1.0,
  "disagreement_with_ssl_origin_count": 0,
  "cases_helped_current_ssl": 0,
  "cases_hurt_current_ssl": 0,
  "net_help_score": 0
}

## AASIST shadow

{
  "total_files": 184,
  "evaluated_files": 184,
  "runnable_files": 184,
  "failed_files": 0,
  "runtime_error_count": 0,
  "avg_runtime_sec": 0.37676973315252404,
  "ai_origin_accuracy_on_ai_variants": 1.0,
  "human_origin_accuracy_on_human_variants": 0.0,
  "ai_clean_detect_rate": 1.0,
  "ai_fabricated_detect_rate": 1.0,
  "ai_mixer_detect_rate": 1.0,
  "ai_replayed_detect_rate": 1.0,
  "human_clean_false_ai_rate": 1.0,
  "human_fabricated_false_ai_rate": 0.0,
  "human_mixer_false_ai_rate": 0.0,
  "human_replayed_false_ai_rate": 0.0,
  "direct_origin_accuracy": 0.5,
  "processed_origin_stability": 1.0,
  "agreement_with_ssl_origin_rate": 0.34782608695652173,
  "disagreement_with_ssl_origin_count": 120,
  "cases_helped_current_ssl": 46,
  "cases_hurt_current_ssl": 92,
  "net_help_score": -46
}

**Decision:** reject_for_now

## HybridResNet shadow

{
  "total_files": 184,
  "evaluated_files": 184,
  "runnable_files": 184,
  "failed_files": 0,
  "runtime_error_count": 0,
  "avg_runtime_sec": 0.4155412907608163,
  "ai_origin_accuracy_on_ai_variants": 0.6195652173913043,
  "human_origin_accuracy_on_human_variants": 0.043478260869565216,
  "ai_clean_detect_rate": 0.17391304347826086,
  "ai_fabricated_detect_rate": 0.34782608695652173,
  "ai_mixer_detect_rate": 1.0,
  "ai_replayed_detect_rate": 0.9565217391304348,
  "human_clean_false_ai_rate": 0.9565217391304348,
  "human_fabricated_false_ai_rate": 0.0,
  "human_mixer_false_ai_rate": 0.0,
  "human_replayed_false_ai_rate": 0.0,
  "direct_origin_accuracy": 0.10869565217391304,
  "processed_origin_stability": 1.0,
  "agreement_with_ssl_origin_rate": 0.19021739130434784,
  "disagreement_with_ssl_origin_count": 149,
  "cases_helped_current_ssl": 45,
  "cases_hurt_current_ssl": 122,
  "net_help_score": -77
}

**Decision:** reject_for_now

## Activation recommendation (P4A — report only)

Do not activate in P4A. aasist=reject_for_now; hybrid_resnet=reject_for_now

Replay, mixer, and partial axes were **not** modified. Shadow scores are origin-support only.

## Sample rows

- `ai_001_direct.wav` (ai_clean): SSL=likely_ai_generated | AASIST=likely_ai_generated | Hybrid=likely_human
- `ai_002_direct.wav` (ai_clean): SSL=likely_ai_generated | AASIST=likely_ai_generated | Hybrid=likely_human
- `ai_003_direct.wav` (ai_clean): SSL=likely_ai_generated | AASIST=likely_ai_generated | Hybrid=inconclusive
- `ai_004_direct.wav` (ai_clean): SSL=likely_ai_generated | AASIST=likely_ai_generated | Hybrid=likely_human
- `ai_005_direct.wav` (ai_clean): SSL=likely_ai_generated | AASIST=likely_ai_generated | Hybrid=likely_human
- `ai_006_direct.wav` (ai_clean): SSL=likely_ai_generated | AASIST=likely_ai_generated | Hybrid=likely_human
- `ai_007_direct.wav` (ai_clean): SSL=likely_ai_generated | AASIST=likely_ai_generated | Hybrid=likely_ai_generated
- `ai_008_direct.wav` (ai_clean): SSL=likely_ai_generated | AASIST=likely_ai_generated | Hybrid=likely_human
- `ai_009_direct.wav` (ai_clean): SSL=likely_ai_generated | AASIST=likely_ai_generated | Hybrid=likely_human
- `ai_010_direct.wav` (ai_clean): SSL=likely_ai_generated | AASIST=likely_ai_generated | Hybrid=likely_human
- `ai_011_direct.wav` (ai_clean): SSL=likely_ai_generated | AASIST=likely_ai_generated | Hybrid=likely_human
- `ai_012_direct.wav` (ai_clean): SSL=likely_ai_generated | AASIST=likely_ai_generated | Hybrid=likely_human
- ... and 172 more (see CSV)
