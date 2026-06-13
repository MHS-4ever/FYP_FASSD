# Origin Retrain With Train-Only Audio Augmentation

Generated: 2026-06-12T20:06:07.803637+00:00

## Scope

This is a separate experimental origin retrain. It does not replace the release model.

Training positives: `ai_clean_direct`, `ai_mixer_processed`, `ai_replayed`.
Training negatives: `human_clean`, `human_mixer_processed`, `human_replayed`.
Excluded from training: `ai_fabricated_partial`, `human_fabricated_partial` because those are mixed/partial-origin cases.

## Augmentation

Augmentation was applied only to the train split. Dev/test rows are original audio only.

Operations per training file: codec-style down/up sampling, conservative Gaussian noise, and gain jitter.

| is_augmented | negative_rows | positive_rows |
| ------------ | ------------- | ------------- |
| 0            | 39            | 39            |
| 1            | 39            | 39            |

Original evaluation split counts:

| leakage_safe_split | negative_rows | positive_rows |
| ------------------ | ------------- | ------------- |
| dev                | 15            | 15            |
| test               | 15            | 15            |
| train              | 39            | 39            |

## Model

- Pipeline: `SimpleImputer(median) -> VarianceThreshold -> StandardScaler -> SelectKBest(f_classif, k=50) -> LogisticRegression(l2, balanced)`
- Original train rows: `78`
- Augmented train rows: `78`
- Total fit rows: `156`
- Input SSL features: `768`
- Selected features: `50`
- Default threshold: `0.5`
- Dev-selected threshold: `0.92`
- Artifact: `E:\FYP\reports\release_audit\origin_retrain_processed_ai_augmented_2026-06-13\origin_processed_ai_augmented_ssl_logistic_regression.joblib`

## Metrics

| scope                                                     | n   | threshold | tp | tn | fp | fn | accuracy | balanced_accuracy | precision | recall | fpr    | fnr    | f1     | roc_auc | pr_auc | brier  |
| --------------------------------------------------------- | --- | --------- | -- | -- | -- | -- | -------- | ----------------- | --------- | ------ | ------ | ------ | ------ | ------- | ------ | ------ |
| train:threshold_050:original_eval_training_scope          | 78  | 0.5       | 39 | 39 | 0  | 0  | 1.0      | 1.0               | 1.0       | 1.0    | 0.0    | 0.0    | 1.0    | 1.0     | 1.0    | 0.0002 |
| dev:threshold_050:original_eval_training_scope            | 30  | 0.5       | 15 | 14 | 1  | 0  | 0.9667   | 0.9667            | 0.9375    | 1.0    | 0.0667 | 0.0    | 0.9677 | 1.0     | 1.0    | 0.0255 |
| test:threshold_050:original_eval_training_scope           | 30  | 0.5       | 15 | 15 | 0  | 0  | 1.0      | 1.0               | 1.0       | 1.0    | 0.0    | 0.0    | 1.0    | 1.0     | 1.0    | 0.0026 |
| all:threshold_050:original_eval_training_scope            | 138 | 0.5       | 69 | 68 | 1  | 0  | 0.9928   | 0.9928            | 0.9857    | 1.0    | 0.0145 | 0.0    | 0.9928 | 1.0     | 1.0    | 0.0062 |
| train:threshold_dev_selected:original_eval_training_scope | 78  | 0.92      | 39 | 39 | 0  | 0  | 1.0      | 1.0               | 1.0       | 1.0    | 0.0    | 0.0    | 1.0    | 1.0     | 1.0    | 0.0002 |
| dev:threshold_dev_selected:original_eval_training_scope   | 30  | 0.92      | 15 | 15 | 0  | 0  | 1.0      | 1.0               | 1.0       | 1.0    | 0.0    | 0.0    | 1.0    | 1.0     | 1.0    | 0.0255 |
| test:threshold_dev_selected:original_eval_training_scope  | 30  | 0.92      | 13 | 15 | 0  | 2  | 0.9333   | 0.9333            | 1.0       | 0.8667 | 0.0    | 0.1333 | 0.9286 | 1.0     | 1.0    | 0.0026 |
| all:threshold_dev_selected:original_eval_training_scope   | 138 | 0.92      | 67 | 69 | 0  | 2  | 0.9855   | 0.9855            | 1.0       | 0.971  | 0.0    | 0.029  | 0.9853 | 1.0     | 1.0    | 0.0062 |

## Condition-Level Comparison

| audit_condition          | n_files | included_in_training_task | target_positive_for_diagnostic | splits                | augmented_mean_probability | augmented_detected_rate_050 | augmented_detected_rate_dev_threshold | current_mean_probability | current_detected_rate_threshold_020 | nonaug_mean_probability | nonaug_detected_rate_050 |
| ------------------------ | ------- | ------------------------- | ------------------------------ | --------------------- | -------------------------- | --------------------------- | ------------------------------------- | ------------------------ | ----------------------------------- | ----------------------- | ------------------------ |
| ai_clean_direct          | 23      | True                      | 1                              | dev:5;test:5;train:13 | 0.9995                     | 1.0                         | 1.0                                   | 0.9946                   | 1.0                                 | 0.9989                  | 1.0                      |
| ai_fabricated_partial    | 23      | False                     | 1                              | dev:5;test:5;train:13 | 0.9977                     | 1.0                         | 1.0                                   | 0.979                    | 1.0                                 | 0.9972                  | 1.0                      |
| ai_mixer_processed       | 23      | True                      | 1                              | dev:5;test:5;train:13 | 0.9962                     | 1.0                         | 1.0                                   | 0.5245                   | 0.7826                              | 0.9746                  | 1.0                      |
| ai_replayed              | 23      | True                      | 1                              | dev:5;test:5;train:13 | 0.9797                     | 1.0                         | 0.913                                 | 0.0321                   | 0.0                                 | 0.9626                  | 1.0                      |
| human_clean              | 23      | True                      | 0                              | dev:5;test:5;train:13 | 0.0807                     | 0.0435                      | 0.0                                   | 0.0065                   | 0.0                                 | 0.0461                  | 0.0                      |
| human_fabricated_partial | 23      | False                     | 0                              | dev:5;test:5;train:13 | 0.2251                     | 0.087                       | 0.0                                   | 0.0184                   | 0.0                                 | 0.204                   | 0.087                    |
| human_mixer_processed    | 23      | True                      | 0                              | dev:5;test:5;train:13 | 0.0075                     | 0.0                         | 0.0                                   | 0.0011                   | 0.0                                 | 0.0041                  | 0.0                      |
| human_replayed           | 23      | True                      | 0                              | dev:5;test:5;train:13 | 0.0059                     | 0.0                         | 0.0                                   | 0.0006                   | 0.0                                 | 0.0033                  | 0.0                      |

## Top Selected Features

| selected_feature | anova_f_score |
| ---------------- | ------------- |
| ssl_emb_442      | 255.7098      |
| ssl_emb_690      | 250.4483      |
| ssl_emb_671      | 244.563       |
| ssl_emb_223      | 225.6841      |
| ssl_emb_407      | 219.0157      |
| ssl_emb_481      | 192.7131      |
| ssl_emb_324      | 189.6623      |
| ssl_emb_506      | 185.5146      |
| ssl_emb_288      | 170.6261      |
| ssl_emb_200      | 160.3483      |
| ssl_emb_246      | 159.7768      |
| ssl_emb_473      | 159.7498      |
| ssl_emb_617      | 157.036       |
| ssl_emb_719      | 155.4782      |
| ssl_emb_320      | 144.926       |

## Key Result

- Augmented origin model detects `ai_replayed` at 1.000 with threshold 0.5, compared with 0.000 for the current release origin model at threshold 0.2.
- Augmented origin model detects `ai_mixer_processed` at 1.000 with threshold 0.5, compared with 0.783 for the current release origin model.
- Human processed controls remain low at threshold 0.5: `human_replayed` detected 0.000, `human_mixer_processed` detected 0.000.
- Diagnostic mixed partial human remains a risk area: `human_fabricated_partial` detected 0.087 at threshold 0.5. It was excluded from training.
- This is still a small-corpus repair experiment, not final validation. The next necessary test is new external audio.

## Files Created

- `E:\FYP\reports\release_audit\origin_retrain_processed_ai_augmented_2026-06-13\origin_processed_ai_augmented_ssl_logistic_regression.joblib`
- `E:\FYP\reports\release_audit\origin_retrain_processed_ai_augmented_2026-06-13\origin_augmented_model_metadata.json`
- `E:\FYP\reports\release_audit\origin_retrain_processed_ai_augmented_2026-06-13\origin_processed_ai_augmentation_manifest.csv`
- `E:\FYP\reports\release_audit\origin_retrain_processed_ai_augmented_2026-06-13\origin_processed_ai_augmented_train_embeddings.csv`
- `E:\FYP\reports\release_audit\origin_retrain_processed_ai_augmented_2026-06-13\origin_processed_ai_augmented_fit_train_table.csv`
- `E:\FYP\reports\release_audit\origin_retrain_processed_ai_augmented_2026-06-13\origin_augmented_training_scope_predictions.csv`
- `E:\FYP\reports\release_audit\origin_retrain_processed_ai_augmented_2026-06-13\origin_augmented_all_condition_predictions.csv`
- `E:\FYP\reports\release_audit\origin_retrain_processed_ai_augmented_2026-06-13\origin_augmented_metrics_by_split.csv`
- `E:\FYP\reports\release_audit\origin_retrain_processed_ai_augmented_2026-06-13\origin_augmented_metrics_by_condition.csv`
- `E:\FYP\reports\release_audit\origin_retrain_processed_ai_augmented_2026-06-13\origin_augmented_dev_threshold_grid.csv`
- `E:\FYP\reports\release_audit\origin_retrain_processed_ai_augmented_2026-06-13\origin_augmented_selected_features.csv`