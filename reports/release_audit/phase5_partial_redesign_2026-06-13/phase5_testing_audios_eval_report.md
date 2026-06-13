# Phase 5 — testing_audios oracle + cascade eval

Generated: 2026-06-13T13:47:16.355127+00:00

Model: `E:\FYP\reports\release_audit\phase5_partial_redesign_2026-06-13\phase5_partial_segment_localizer.joblib`
Evaluated: T4.3, T5_FAB_001, T1.1, T1.2, T1.3, T2.3, T3.2

## Partial positives

   test_id  max_segment_probability   partial_localization_gate  partial_fusion_eligible oracle_top1_overlaps_label  top_start_sec  top_end_sec
      T4.3                 0.999944 localized_pattern_supported                     True                       True           46.0         50.0
T5_FAB_001                 0.999943 localized_pattern_supported                     True                       True           18.0         22.0

## Negatives (should not broad-activate

test_id  max_segment_probability  high_segment_fraction    partial_localization_gate
   T1.1                 0.015435                    0.0 weak_or_nonlocalized_partial
   T1.2                 0.897423                    0.0  localized_pattern_supported
   T1.3                 0.691436                    0.0  localized_pattern_supported
   T2.3                 0.002315                    0.0 weak_or_nonlocalized_partial
   T3.2                 0.035147                    0.0 weak_or_nonlocalized_partial
