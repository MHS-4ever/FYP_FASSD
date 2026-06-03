# Phase 9E-P3 Release Correctness Report

Generated: 2026-06-03T20:05:20.169348+00:00
Mode: full
Discovered variant files: 184
Evaluated: 184

## Summary metrics

{
  "mode": "full",
  "total_files": 184,
  "evaluated_files": 184,
  "failed_files": 0,
  "base_audio_count": 23,
  "variant_count": 8,
  "per_variant_file_count": {
    "ai_clean": 23,
    "ai_fabricated": 23,
    "ai_mixer": 23,
    "ai_replayed": 23,
    "human_clean": 23,
    "human_fabricated": 23,
    "human_mixer": 23,
    "human_replayed": 23
  },
  "ai_clean_origin_detect_rate": 1.0,
  "ai_fabricated_origin_detect_rate": 1.0,
  "ai_mixer_mixer_detect_rate": 1.0,
  "ai_replayed_replay_detect_rate": 1.0,
  "human_clean_false_suspicious_rate": 0.0,
  "human_clean_false_ai_rate": 0.0,
  "human_fabricated_partial_candidate_or_detect_rate": 1.0,
  "human_mixer_mixer_detect_rate": 1.0,
  "human_mixer_replay_overlap_rate": 1.0,
  "human_replayed_replay_detect_rate": 0.9130434782608695,
  "partial_candidate_only_count": 46,
  "partial_full_detection_count": 0,
  "model_issue_count": 2,
  "wording_issue_count": 0,
  "release_integration_issue_count": 0,
  "acceptable_with_limitation_count": 46,
  "pass_count": 136
}

## Reference model audit

reference model present but not runnable in release app yet

## Hard gates

- human_clean_false_suspicious_rate: 0.0
- wording_issue_count: 0

## Per-file classifications

- `ai_001_direct.wav` (ai_clean): pass — Voice origin: Likely AI-generated
- `ai_002_direct.wav` (ai_clean): pass — Voice origin: Likely AI-generated
- `ai_003_direct.wav` (ai_clean): pass — Voice origin: Likely AI-generated
- `ai_004_direct.wav` (ai_clean): pass — Voice origin: Likely AI-generated
- `ai_005_direct.wav` (ai_clean): pass — Voice origin: Likely AI-generated
- `ai_006_direct.wav` (ai_clean): pass — Voice origin: Likely AI-generated
- `ai_007_direct.wav` (ai_clean): pass — Voice origin: Likely AI-generated
- `ai_008_direct.wav` (ai_clean): pass — Voice origin: Likely AI-generated
- `ai_009_direct.wav` (ai_clean): pass — Voice origin: Likely AI-generated
- `ai_010_direct.wav` (ai_clean): pass — Voice origin: Likely AI-generated
- `ai_011_direct.wav` (ai_clean): pass — Voice origin: Likely AI-generated
- `ai_012_direct.wav` (ai_clean): pass — Voice origin: Likely AI-generated
- `ai_013_direct.wav` (ai_clean): pass — Voice origin: Likely AI-generated
- `ai_014_direct.wav` (ai_clean): pass — Voice origin: Likely AI-generated
- `ai_015_direct.wav` (ai_clean): pass — Voice origin: Likely AI-generated
- `ai_016_direct.wav` (ai_clean): pass — Voice origin: Likely AI-generated
- `ai_017_direct.wav` (ai_clean): pass — Voice origin: Likely AI-generated
- `ai_018_direct.wav` (ai_clean): pass — Voice origin: Likely AI-generated
- `ai_019_direct.wav` (ai_clean): pass — Voice origin: Likely AI-generated
- `ai_020_direct.wav` (ai_clean): pass — Voice origin: Likely AI-generated
- `ai_021_direct.wav` (ai_clean): pass — Voice origin: Likely AI-generated
- `ai_022_direct.wav` (ai_clean): pass — Voice origin: Likely AI-generated
- `ai_023_direct.wav` (ai_clean): pass — Voice origin: Likely AI-generated
- `ai_001_fabricated.wav` (ai_fabricated): acceptable_with_limitation — Voice origin: Likely AI-generated
- `ai_002_fabricated.wav` (ai_fabricated): acceptable_with_limitation — Voice origin: Likely AI-generated
- `ai_003_fabricated.wav` (ai_fabricated): acceptable_with_limitation — Voice origin: Likely AI-generated
- `ai_004_fabricated.wav` (ai_fabricated): acceptable_with_limitation — Voice origin: Likely AI-generated
- `ai_005_fabricated.wav` (ai_fabricated): acceptable_with_limitation — Voice origin: Likely AI-generated
- `ai_006_fabricated.wav` (ai_fabricated): acceptable_with_limitation — Voice origin: Likely AI-generated
- `ai_007_fabricated.wav` (ai_fabricated): acceptable_with_limitation — Voice origin: Likely AI-generated
- `ai_008_fabricated.wav` (ai_fabricated): acceptable_with_limitation — Voice origin: Likely AI-generated
- `ai_009_fabricated.wav` (ai_fabricated): acceptable_with_limitation — Voice origin: Likely AI-generated
- `ai_010_fabricated.wav` (ai_fabricated): acceptable_with_limitation — Voice origin: Likely AI-generated
- `ai_011_fabricated.wav` (ai_fabricated): acceptable_with_limitation — Voice origin: Likely AI-generated
- `ai_012_fabricated.wav` (ai_fabricated): acceptable_with_limitation — Voice origin: Likely AI-generated
- `ai_013_fabricated.wav` (ai_fabricated): acceptable_with_limitation — Voice origin: Likely AI-generated
- `ai_014_fabricated.wav` (ai_fabricated): acceptable_with_limitation — Voice origin: Likely AI-generated
- `ai_015_fabricated.wav` (ai_fabricated): acceptable_with_limitation — Voice origin: Likely AI-generated
- `ai_016_fabricated.wav` (ai_fabricated): acceptable_with_limitation — Voice origin: Likely AI-generated
- `ai_017_fabricated.wav` (ai_fabricated): acceptable_with_limitation — Voice origin: Likely AI-generated
- `ai_018_fabricated.wav` (ai_fabricated): acceptable_with_limitation — Voice origin: Likely AI-generated
- `ai_019_fabricated.wav` (ai_fabricated): acceptable_with_limitation — Voice origin: Likely AI-generated
- `ai_020_fabricated.wav` (ai_fabricated): acceptable_with_limitation — Voice origin: Likely AI-generated
- `ai_021_fabricated.wav` (ai_fabricated): acceptable_with_limitation — Voice origin: Likely AI-generated
- `ai_022_fabricated.wav` (ai_fabricated): acceptable_with_limitation — Voice origin: Likely AI-generated
- `ai_023_fabricated.wav` (ai_fabricated): acceptable_with_limitation — Voice origin: Likely AI-generated
- `ai_001_mixer_processed.wav` (ai_mixer): pass — Voice origin: Likely AI-generated with processing indicators
- `ai_002_mixer_processed.wav` (ai_mixer): pass — Voice origin: Likely AI-generated with processing indicators
- `ai_003_mixer_processed.wav` (ai_mixer): pass — Voice origin: Likely AI-generated with processing indicators
- `ai_004_mixer_processed.wav` (ai_mixer): pass — Voice origin: Likely AI-generated with processing indicators
- ... and 134 more (see CSV)
