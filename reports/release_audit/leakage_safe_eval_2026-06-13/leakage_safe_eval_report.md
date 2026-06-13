# Leakage-Safe Split and Current-Model Diagnostic Rerun

Generated: 2026-06-12T19:53:20.138515+00:00
Seed: 42

## Important Interpretation

This run creates a leakage-safe **base-level split manifest** and reruns the **already-packaged current release models** on those partitions using cached Phase 8 features. These metrics are diagnostic only: the current packaged models were already trained on the Phase 7C1 / Phase 8 corpus, so these partitions are not an unbiased held-out evaluation for the existing artifacts. They are the split structure that should be used for the next retraining/evaluation cycle.

## Files Created

- `E:\FYP\reports\release_audit\leakage_safe_eval_2026-06-13\leakage_safe_base_split.csv`
- `E:\FYP\reports\release_audit\leakage_safe_eval_2026-06-13\leakage_safe_file_manifest.csv`
- `E:\FYP\reports\release_audit\leakage_safe_eval_2026-06-13\leakage_safe_split_condition_summary.csv`
- `E:\FYP\reports\release_audit\leakage_safe_eval_2026-06-13\current_model_artifact_inventory.csv`
- `E:\FYP\reports\release_audit\leakage_safe_eval_2026-06-13\current_model_file_predictions.csv`
- `E:\FYP\reports\release_audit\leakage_safe_eval_2026-06-13\current_model_partial_segment_predictions.csv`
- `E:\FYP\reports\release_audit\leakage_safe_eval_2026-06-13\current_model_partial_file_aggregation.csv`
- `E:\FYP\reports\release_audit\leakage_safe_eval_2026-06-13\current_model_metrics_by_split.csv`
- `E:\FYP\reports\release_audit\leakage_safe_eval_2026-06-13\current_model_metrics_by_condition.csv`

## Leakage-Safe Split Summary

Base groups: 23 | files: 184 | leakage violations: 0

| leakage_safe_split | base_count | file_count |
| ------------------ | ---------- | ---------- |
| dev                | 5          | 40         |
| test               | 5          | 40         |
| train              | 13         | 104        |

Each base group contains all eight paired variants, so every split remains condition-balanced:

| leakage_safe_split | ai_clean_direct | ai_fabricated_partial | ai_mixer_processed | ai_replayed | human_clean | human_fabricated_partial | human_mixer_processed | human_replayed |
| ------------------ | --------------- | --------------------- | ------------------ | ----------- | ----------- | ------------------------ | --------------------- | -------------- |
| dev                | 5               | 5                     | 5                  | 5           | 5           | 5                        | 5                     | 5              |
| test               | 5               | 5                     | 5                  | 5           | 5           | 5                        | 5                     | 5              |
| train              | 13              | 13                    | 13                 | 13          | 13          | 13                       | 13                    | 13             |

## Active Artifacts Rerun

| axis            | threshold | n_features_in | feature_set | phase_trained      | sha256                                                           |
| --------------- | --------- | ------------- | ----------- | ------------------ | ---------------------------------------------------------------- |
| origin          | 0.2       | 768           | ssl         | Phase 8E-1 / 8E-1A | f9ef07746a4325135f11be86e0f82d94c1e0f3a2e26834d06571d5eed86b5780 |
| replay          | 0.65      | 59            | acoustic    | Phase 8E-1 / 8E-1A | 2f3bb4661b840aed0562dcbf8bd7c0714078727425e844adb39918e17a20f7c3 |
| mixer           | 0.75      | 59            | acoustic    | Phase 8E-1 / 8E-1A | 9745c3b34390f47b35d224c96f6ec4e03146046df30806a921e96f17fd671d2e |
| partial_segment | 0.5       | 796           | combined    | Phase 8E-3         | 97cfbb8a0d280891039102641273852b70bb1316208232640d1474860a537d20 |

## Metrics By Split

| metric_scope                                     | n   | threshold | tp | tn  | fp | fn | accuracy | balanced_accuracy | precision | recall | fpr    | fnr    | f1     | roc_auc | pr_auc |
| ------------------------------------------------ | --- | --------- | -- | --- | -- | -- | -------- | ----------------- | --------- | ------ | ------ | ------ | ------ | ------- | ------ |
| all: origin_as_ai_prefix_all_8_conditions        | 184 | 0.2       | 64 | 92  | 0  | 28 | 0.8478   | 0.8478            | 1.0       | 0.6957 | 0.0    | 0.3043 | 0.8205 | 0.9571  | 0.9657 |
| all: origin_strict_clean_direct_vs_human_clean   | 46  | 0.2       | 23 | 23  | 0  | 0  | 1.0      | 1.0               | 1.0       | 1.0    | 0.0    | 0.0    | 1.0    | 1.0     | 1.0    |
| all: replay_axis_all_conditions                  | 184 | 0.65      | 46 | 131 | 7  | 0  | 0.962    | 0.9746            | 0.8679    | 1.0    | 0.0507 | 0.0    | 0.9293 | 0.9989  | 0.9969 |
| all: mixer_axis_all_conditions                   | 184 | 0.75      | 46 | 136 | 2  | 0  | 0.9891   | 0.9928            | 0.9583    | 1.0    | 0.0145 | 0.0    | 0.9787 | 0.988   | 0.9302 |
| all: partial_localizer_file_max_all_conditions   | 184 | 0.5       | 46 | 124 | 14 | 0  | 0.9239   | 0.9493            | 0.7667    | 1.0    | 0.1014 | 0.0    | 0.8679 | 1.0     | 1.0    |
| train: origin_as_ai_prefix_all_8_conditions      | 104 | 0.2       | 35 | 52  | 0  | 17 | 0.8365   | 0.8365            | 1.0       | 0.6731 | 0.0    | 0.3269 | 0.8046 | 0.9663  | 0.974  |
| train: origin_strict_clean_direct_vs_human_clean | 26  | 0.2       | 13 | 13  | 0  | 0  | 1.0      | 1.0               | 1.0       | 1.0    | 0.0    | 0.0    | 1.0    | 1.0     | 1.0    |
| train: replay_axis_all_conditions                | 104 | 0.65      | 26 | 75  | 3  | 0  | 0.9712   | 0.9808            | 0.8966    | 1.0    | 0.0385 | 0.0    | 0.9455 | 0.999   | 0.9971 |
| train: mixer_axis_all_conditions                 | 104 | 0.75      | 26 | 77  | 1  | 0  | 0.9904   | 0.9936            | 0.963     | 1.0    | 0.0128 | 0.0    | 0.9811 | 0.9906  | 0.9549 |
| train: partial_localizer_file_max_all_conditions | 104 | 0.5       | 26 | 71  | 7  | 0  | 0.9327   | 0.9551            | 0.7879    | 1.0    | 0.0897 | 0.0    | 0.8814 | 1.0     | 1.0    |
| dev: origin_as_ai_prefix_all_8_conditions        | 40  | 0.2       | 14 | 20  | 0  | 6  | 0.85     | 0.85              | 1.0       | 0.7    | 0.0    | 0.3    | 0.8235 | 0.9475  | 0.9573 |
| dev: origin_strict_clean_direct_vs_human_clean   | 10  | 0.2       | 5  | 5   | 0  | 0  | 1.0      | 1.0               | 1.0       | 1.0    | 0.0    | 0.0    | 1.0    | 1.0     | 1.0    |
| dev: replay_axis_all_conditions                  | 40  | 0.65      | 10 | 28  | 2  | 0  | 0.95     | 0.9667            | 0.8333    | 1.0    | 0.0667 | 0.0    | 0.9091 | 0.9967  | 0.9909 |
| dev: mixer_axis_all_conditions                   | 40  | 0.75      | 10 | 29  | 1  | 0  | 0.975    | 0.9833            | 0.9091    | 1.0    | 0.0333 | 0.0    | 0.9524 | 0.9667  | 0.798  |
| dev: partial_localizer_file_max_all_conditions   | 40  | 0.5       | 10 | 26  | 4  | 0  | 0.9      | 0.9333            | 0.7143    | 1.0    | 0.1333 | 0.0    | 0.8333 | 1.0     | 1.0    |
| test: origin_as_ai_prefix_all_8_conditions       | 40  | 0.2       | 15 | 20  | 0  | 5  | 0.875    | 0.875             | 1.0       | 0.75   | 0.0    | 0.25   | 0.8571 | 0.95    | 0.9587 |
| test: origin_strict_clean_direct_vs_human_clean  | 10  | 0.2       | 5  | 5   | 0  | 0  | 1.0      | 1.0               | 1.0       | 1.0    | 0.0    | 0.0    | 1.0    | 1.0     | 1.0    |
| test: replay_axis_all_conditions                 | 40  | 0.65      | 10 | 28  | 2  | 0  | 0.95     | 0.9667            | 0.8333    | 1.0    | 0.0667 | 0.0    | 0.9091 | 1.0     | 1.0    |
| test: mixer_axis_all_conditions                  | 40  | 0.75      | 10 | 30  | 0  | 0  | 1.0      | 1.0               | 1.0       | 1.0    | 0.0    | 0.0    | 1.0    | 1.0     | 1.0    |
| test: partial_localizer_file_max_all_conditions  | 40  | 0.5       | 10 | 27  | 3  | 0  | 0.925    | 0.95              | 0.7692    | 1.0    | 0.1    | 0.0    | 0.8696 | 1.0     | 1.0    |

## Metrics By Condition

| audit_condition          | n_files | splits                | origin_mean_probability | origin_detected_count | origin_detected_rate | replay_mean_probability | replay_detected_rate | mixer_mean_probability | mixer_detected_rate | partial_localizer_max_detected_rate | partial_max_probability_mean |
| ------------------------ | ------- | --------------------- | ----------------------- | --------------------- | -------------------- | ----------------------- | -------------------- | ---------------------- | ------------------- | ----------------------------------- | ---------------------------- |
| ai_clean_direct          | 23      | dev:5;test:5;train:13 | 0.9946                  | 23                    | 1.0                  | 0.0014                  | 0.0                  | 0.0061                 | 0.0                 | 0.2609                              | 0.3796                       |
| ai_fabricated_partial    | 23      | dev:5;test:5;train:13 | 0.979                   | 23                    | 1.0                  | 0.0015                  | 0.0                  | 0.0059                 | 0.0                 | 1.0                                 | 0.9952                       |
| ai_mixer_processed       | 23      | dev:5;test:5;train:13 | 0.5245                  | 18                    | 0.7826               | 0.3809                  | 0.0                  | 0.9785                 | 1.0                 | 0.0                                 | 0.0235                       |
| ai_replayed              | 23      | dev:5;test:5;train:13 | 0.0321                  | 0                     | 0.0                  | 0.998                   | 1.0                  | 0.0764                 | 0.0                 | 0.0                                 | 0.0355                       |
| human_clean              | 23      | dev:5;test:5;train:13 | 0.0065                  | 0                     | 0.0                  | 0.0356                  | 0.0                  | 0.0452                 | 0.0                 | 0.3043                              | 0.3875                       |
| human_fabricated_partial | 23      | dev:5;test:5;train:13 | 0.0184                  | 0                     | 0.0                  | 0.0119                  | 0.0                  | 0.0248                 | 0.0                 | 1.0                                 | 0.9957                       |
| human_mixer_processed    | 23      | dev:5;test:5;train:13 | 0.0011                  | 0                     | 0.0                  | 0.5569                  | 0.3043               | 0.9904                 | 1.0                 | 0.0435                              | 0.114                        |
| human_replayed           | 23      | dev:5;test:5;train:13 | 0.0006                  | 0                     | 0.0                  | 0.9737                  | 1.0                  | 0.3249                 | 0.087               | 0.0                                 | 0.0369                       |

## Key Diagnostic Findings

- Origin axis still misses replayed AI under the packaged artifact: `ai_replayed` origin detected 0/23 (rate 0.000).
- Origin axis misses a subset of mixer-processed AI: `ai_mixer_processed` origin detected 18/23 (rate 0.783).
- Clean human false-AI rate remains 0.000 in this diagnostic rerun.
- Partial localizer alone fires broadly: AI partial files max>=0.5 rate 1.000; human partial files max>=0.5 rate 1.000. This is localizer-only, not release gating.
- Because the current artifacts already saw this corpus, these numbers must not be presented as final validation. The real next step is to retrain/evaluate using the generated base-level split, then reserve a separate blind external test set.

## Recommended Next Use

1. Use `leakage_safe_file_manifest.csv` as the Phase 7C1 base-group split for the next training/evaluation cycle.
2. Retrain the origin axis with the `train` split only, tune thresholds on `dev` only, and report once on `test` only.
3. Repeat for replay, mixer and partial models; do not let variants from the same `base_id` cross split boundaries.
4. Treat the current rerun metrics as a baseline/diagnostic, not as evidence of generalization.