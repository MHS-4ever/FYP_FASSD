# Origin Retrain With Processed AI Included

Generated: 2026-06-12T19:56:31.198095+00:00

## Scope

This is a separate experimental retrain of the origin axis. It does not replace `release/models/origin/origin_file_model__ssl__experimental.joblib`.

Training positives: `ai_clean_direct`, `ai_mixer_processed`, `ai_replayed`.
Training negatives: `human_clean`, `human_mixer_processed`, `human_replayed`.
Excluded from training: `ai_fabricated_partial`, `human_fabricated_partial` because those are mixed/partial-origin cases.

## Leakage-Safe Split

| leakage_safe_split | negative_rows | positive_rows |
| ------------------ | ------------- | ------------- |
| dev                | 15            | 15            |
| test               | 15            | 15            |
| train              | 39            | 39            |

## Model

- Pipeline: `SimpleImputer(median) -> VarianceThreshold -> StandardScaler -> SelectKBest(f_classif, k=50) -> LogisticRegression(l2, balanced)`
- Input SSL features: `768`
- Selected features: `50`
- Default threshold: `0.5`
- Dev-selected threshold: `0.73`
- Artifact: `E:\FYP\reports\release_audit\origin_retrain_processed_ai_2026-06-13\origin_processed_ai_ssl_logistic_regression.joblib`

## Metrics

| scope                                                          | n   | threshold | tp | tn | fp | fn | accuracy | balanced_accuracy | precision | recall | fpr | fnr    | f1     | roc_auc | pr_auc | brier  |
| -------------------------------------------------------------- | --- | --------- | -- | -- | -- | -- | -------- | ----------------- | --------- | ------ | --- | ------ | ------ | ------- | ------ | ------ |
| train:threshold_050:training_scope_clean_replay_mixer          | 78  | 0.5       | 39 | 39 | 0  | 0  | 1.0      | 1.0               | 1.0       | 1.0    | 0.0 | 0.0    | 1.0    | 1.0     | 1.0    | 0.0008 |
| dev:threshold_050:training_scope_clean_replay_mixer            | 30  | 0.5       | 15 | 15 | 0  | 0  | 1.0      | 1.0               | 1.0       | 1.0    | 0.0 | 0.0    | 1.0    | 1.0     | 1.0    | 0.0068 |
| test:threshold_050:training_scope_clean_replay_mixer           | 30  | 0.5       | 15 | 15 | 0  | 0  | 1.0      | 1.0               | 1.0       | 1.0    | 0.0 | 0.0    | 1.0    | 1.0     | 1.0    | 0.0056 |
| all:threshold_050:training_scope_clean_replay_mixer            | 138 | 0.5       | 69 | 69 | 0  | 0  | 1.0      | 1.0               | 1.0       | 1.0    | 0.0 | 0.0    | 1.0    | 1.0     | 1.0    | 0.0032 |
| train:threshold_dev_selected:training_scope_clean_replay_mixer | 78  | 0.73      | 39 | 39 | 0  | 0  | 1.0      | 1.0               | 1.0       | 1.0    | 0.0 | 0.0    | 1.0    | 1.0     | 1.0    | 0.0008 |
| dev:threshold_dev_selected:training_scope_clean_replay_mixer   | 30  | 0.73      | 15 | 15 | 0  | 0  | 1.0      | 1.0               | 1.0       | 1.0    | 0.0 | 0.0    | 1.0    | 1.0     | 1.0    | 0.0068 |
| test:threshold_dev_selected:training_scope_clean_replay_mixer  | 30  | 0.73      | 14 | 15 | 0  | 1  | 0.9667   | 0.9667            | 1.0       | 0.9333 | 0.0 | 0.0667 | 0.9655 | 1.0     | 1.0    | 0.0056 |
| all:threshold_dev_selected:training_scope_clean_replay_mixer   | 138 | 0.73      | 68 | 69 | 0  | 1  | 0.9928   | 0.9928            | 1.0       | 0.9855 | 0.0 | 0.0145 | 0.9927 | 1.0     | 1.0    | 0.0032 |

## Condition-Level Comparison

| audit_condition          | n_files | included_in_training_task | target_positive_for_diagnostic | splits                | new_mean_probability | new_detected_rate_050 | new_detected_rate_dev_threshold | current_mean_probability | current_detected_rate_threshold_020 |
| ------------------------ | ------- | ------------------------- | ------------------------------ | --------------------- | -------------------- | --------------------- | ------------------------------- | ------------------------ | ----------------------------------- |
| ai_clean_direct          | 23      | True                      | 1                              | dev:5;test:5;train:13 | 0.9989               | 1.0                   | 1.0                             | 0.9946                   | 1.0                                 |
| ai_fabricated_partial    | 23      | False                     | 1                              | dev:5;test:5;train:13 | 0.9972               | 1.0                   | 1.0                             | 0.979                    | 1.0                                 |
| ai_mixer_processed       | 23      | True                      | 1                              | dev:5;test:5;train:13 | 0.9746               | 1.0                   | 1.0                             | 0.5245                   | 0.7826                              |
| ai_replayed              | 23      | True                      | 1                              | dev:5;test:5;train:13 | 0.9626               | 1.0                   | 0.9565                          | 0.0321                   | 0.0                                 |
| human_clean              | 23      | True                      | 0                              | dev:5;test:5;train:13 | 0.0461               | 0.0                   | 0.0                             | 0.0065                   | 0.0                                 |
| human_fabricated_partial | 23      | False                     | 0                              | dev:5;test:5;train:13 | 0.204                | 0.087                 | 0.0                             | 0.0184                   | 0.0                                 |
| human_mixer_processed    | 23      | True                      | 0                              | dev:5;test:5;train:13 | 0.0041               | 0.0                   | 0.0                             | 0.0011                   | 0.0                                 |
| human_replayed           | 23      | True                      | 0                              | dev:5;test:5;train:13 | 0.0033               | 0.0                   | 0.0                             | 0.0006                   | 0.0                                 |

## Top Selected Features

| selected_feature | anova_f_score |
| ---------------- | ------------- |
| ssl_emb_690      | 158.0661      |
| ssl_emb_671      | 146.1501      |
| ssl_emb_442      | 136.418       |
| ssl_emb_506      | 126.859       |
| ssl_emb_617      | 106.1654      |
| ssl_emb_407      | 104.6414      |
| ssl_emb_481      | 104.2449      |
| ssl_emb_324      | 103.2628      |
| ssl_emb_288      | 99.0594       |
| ssl_emb_223      | 98.2532       |
| ssl_emb_473      | 87.0409       |
| ssl_emb_719      | 82.92         |
| ssl_emb_206      | 79.1421       |
| ssl_emb_598      | 79.0337       |
| ssl_emb_246      | 78.6065       |

## Key Result

- New origin model detects `ai_replayed` at 1.000 with threshold 0.5, compared with 0.000 for the current release origin model at threshold 0.2.
- New origin model detects `ai_mixer_processed` at 1.000 with threshold 0.5, compared with 0.783 for the current release origin model.
- Human processed controls remain low at threshold 0.5: `human_replayed` detected 0.000, `human_mixer_processed` detected 0.000.
- Because only 13 base groups are used for training, this is a first repair experiment, not final validation.

## Files Created

- `E:\FYP\reports\release_audit\origin_retrain_processed_ai_2026-06-13\origin_processed_ai_ssl_logistic_regression.joblib`
- `E:\FYP\reports\release_audit\origin_retrain_processed_ai_2026-06-13\origin_processed_ai_model_metadata.json`
- `E:\FYP\reports\release_audit\origin_retrain_processed_ai_2026-06-13\origin_processed_ai_training_scope_predictions.csv`
- `E:\FYP\reports\release_audit\origin_retrain_processed_ai_2026-06-13\origin_processed_ai_all_condition_predictions.csv`
- `E:\FYP\reports\release_audit\origin_retrain_processed_ai_2026-06-13\origin_processed_ai_metrics_by_split.csv`
- `E:\FYP\reports\release_audit\origin_retrain_processed_ai_2026-06-13\origin_processed_ai_metrics_by_condition.csv`
- `E:\FYP\reports\release_audit\origin_retrain_processed_ai_2026-06-13\origin_processed_ai_dev_threshold_grid.csv`
- `E:\FYP\reports\release_audit\origin_retrain_processed_ai_2026-06-13\origin_processed_ai_selected_features.csv`