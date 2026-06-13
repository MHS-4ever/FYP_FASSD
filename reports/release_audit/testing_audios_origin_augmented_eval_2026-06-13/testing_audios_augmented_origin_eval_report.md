# Testing Audios Evaluation - Augmented Origin Model

Generated: 2026-06-12T20:17:57.264885+00:00

## Scope

Evaluated the train-only augmented origin model on the labeled Phase 7 `testing_audios` manifest. Binary metrics exclude `mixed` partial-fabrication files and report them separately.

Rows in manifest: `25` | successfully embedded: `25` | failed/missing: `0`

## Metrics

| scope                                               | n  | threshold | tp | tn | fp | fn | accuracy | balanced_accuracy | precision | recall_ai | specificity_human | fpr    | fnr | f1     | roc_auc | pr_auc |
| --------------------------------------------------- | -- | --------- | -- | -- | -- | -- | -------- | ----------------- | --------- | --------- | ----------------- | ------ | --- | ------ | ------- | ------ |
| all_binary_human_ai:aug_threshold_050               | 23 | 0.5       | 9  | 11 | 2  | 1  | 0.8696   | 0.8731            | 0.8182    | 0.9       | 0.8462            | 0.1538 | 0.1 | 0.8571 | 0.8769  | 0.7571 |
| all_binary_human_ai:aug_threshold_092               | 23 | 0.92      | 9  | 11 | 2  | 1  | 0.8696   | 0.8731            | 0.8182    | 0.9       | 0.8462            | 0.1538 | 0.1 | 0.8571 | 0.8769  | 0.7571 |
| all_binary_human_ai:current_threshold_020           | 23 | 0.2       | 7  | 11 | 2  | 3  | 0.7826   | 0.7731            | 0.7778    | 0.7       | 0.8462            | 0.1538 | 0.3 | 0.7368 | 0.9154  | 0.8771 |
| all_binary_human_ai:nonaug_threshold_050            | 23 | 0.5       | 9  | 11 | 2  | 1  | 0.8696   | 0.8731            | 0.8182    | 0.9       | 0.8462            | 0.1538 | 0.1 | 0.8571 | 0.9231  | 0.8944 |
| english_binary:aug_threshold_050                    | 12 | 0.5       | 9  | 0  | 2  | 1  | 0.75     | 0.45              | 0.8182    | 0.9       | 0.0               | 1.0    | 0.1 | 0.8571 | 0.25    | 0.7635 |
| english_binary:aug_threshold_092                    | 12 | 0.92      | 9  | 0  | 2  | 1  | 0.75     | 0.45              | 0.8182    | 0.9       | 0.0               | 1.0    | 0.1 | 0.8571 | 0.25    | 0.7635 |
| english_binary:current_threshold_020                | 12 | 0.2       | 7  | 0  | 2  | 3  | 0.5833   | 0.35              | 0.7778    | 0.7       | 0.0               | 1.0    | 0.3 | 0.7368 | 0.5     | 0.8835 |
| english_binary:nonaug_threshold_050                 | 12 | 0.5       | 9  | 0  | 2  | 1  | 0.75     | 0.45              | 0.8182    | 0.9       | 0.0               | 1.0    | 0.1 | 0.8571 | 0.5     | 0.8944 |
| clean_direct_binary:aug_threshold_050               | 8  | 0.5       | 5  | 1  | 2  | 0  | 0.75     | 0.6667            | 0.7143    | 1.0       | 0.3333            | 0.6667 | 0.0 | 0.8333 | 0.5333  | 0.6857 |
| clean_direct_binary:aug_threshold_092               | 8  | 0.92      | 5  | 1  | 2  | 0  | 0.75     | 0.6667            | 0.7143    | 1.0       | 0.3333            | 0.6667 | 0.0 | 0.8333 | 0.5333  | 0.6857 |
| clean_direct_binary:current_threshold_020           | 8  | 0.2       | 5  | 1  | 2  | 0  | 0.75     | 0.6667            | 0.7143    | 1.0       | 0.3333            | 0.6667 | 0.0 | 0.8333 | 0.8667  | 0.9333 |
| clean_direct_binary:nonaug_threshold_050            | 8  | 0.5       | 5  | 1  | 2  | 0  | 0.75     | 0.6667            | 0.7143    | 1.0       | 0.3333            | 0.6667 | 0.0 | 0.8333 | 0.8667  | 0.9333 |
| processed_replay_mixer_binary:aug_threshold_050     | 10 | 0.5       | 4  | 5  | 0  | 1  | 0.9      | 0.9               | 1.0       | 0.8       | 1.0               | 0.0    | 0.2 | 0.8889 | 0.96    | 0.9667 |
| processed_replay_mixer_binary:aug_threshold_092     | 10 | 0.92      | 4  | 5  | 0  | 1  | 0.9      | 0.9               | 1.0       | 0.8       | 1.0               | 0.0    | 0.2 | 0.8889 | 0.96    | 0.9667 |
| processed_replay_mixer_binary:current_threshold_020 | 10 | 0.2       | 2  | 5  | 0  | 3  | 0.7      | 0.7               | 1.0       | 0.4       | 1.0               | 0.0    | 0.6 | 0.5714 | 0.96    | 0.9667 |
| processed_replay_mixer_binary:nonaug_threshold_050  | 10 | 0.5       | 4  | 5  | 0  | 1  | 0.9      | 0.9               | 1.0       | 0.8       | 1.0               | 0.0    | 0.2 | 0.8889 | 1.0     | 1.0    |

## Condition Summary

| ground_truth_origin | manipulation_type   | language | n | augmented_mean_probability | augmented_detected_rate_050 | augmented_detected_rate_092 | current_mean_probability | current_detected_rate_020 |
| ------------------- | ------------------- | -------- | - | -------------------------- | --------------------------- | --------------------------- | ------------------------ | ------------------------- |
| ai                  | ai_replay           | english  | 3 | 0.9745                     | 1.0                         | 1.0                         | 0.5389                   | 0.6667                    |
| ai                  | clean_direct        | english  | 5 | 0.9734                     | 1.0                         | 1.0                         | 0.8946                   | 1.0                       |
| ai                  | mixer_processed     | english  | 1 | 0.9655                     | 1.0                         | 1.0                         | 0.169                    | 0.0                       |
| ai                  | whatsapp_compressed | english  | 1 | 0.0817                     | 0.0                         | 0.0                         | 0.1268                   | 0.0                       |
| human               | clean_direct        | english  | 2 | 0.9959                     | 1.0                         | 1.0                         | 0.822                    | 1.0                       |
| human               | clean_direct        | urdu     | 1 | 0.0045                     | 0.0                         | 0.0                         | 0.0005                   | 0.0                       |
| human               | edited_spliced      | urdu     | 5 | 0.0103                     | 0.0                         | 0.0                         | 0.0006                   | 0.0                       |
| human               | human_replay        | urdu     | 4 | 0.0279                     | 0.0                         | 0.0                         | 0.0019                   | 0.0                       |
| human               | mixer_processed     | urdu     | 1 | 0.1141                     | 0.0                         | 0.0                         | 0.0604                   | 0.0                       |
| mixed               | partial_ai_insert   | english  | 1 | 0.9918                     | 1.0                         | 1.0                         | 0.964                    | 1.0                       |
| mixed               | partial_ai_insert   | urdu     | 1 | 0.0611                     | 0.0                         | 0.0                         | 0.0133                   | 0.0                       |

## Per-File Predictions

| test_id    | ground_truth_origin | manipulation_type   | language | expected_forensic_result                                                             | augmented_origin_probability | augmented_label_050 | augmented_label_092 | current_origin_probability | current_label_020 | nonaug_origin_probability |
| ---------- | ------------------- | ------------------- | -------- | ------------------------------------------------------------------------------------ | ---------------------------- | ------------------- | ------------------- | -------------------------- | ----------------- | ------------------------- |
| T1.1       | human               | clean_direct        | urdu     | Should not be called AI fake                                                         | 0.0045                       | HUMAN               | HUMAN               | 0.0005                     | HUMAN             | 0.0031                    |
| T1.2       | human               | clean_direct        | english  | Avoid false positive on clean audio                                                  | 0.9918                       | AI                  | AI                  | 0.9298                     | AI                | 0.9968                    |
| T1.3       | ai                  | clean_direct        | english  | Should detect as spoof                                                               | 0.9949                       | AI                  | AI                  | 0.9993                     | AI                | 0.9974                    |
| T1.4       | ai                  | clean_direct        | english  | Should detect as spoof                                                               | 0.941                        | AI                  | AI                  | 0.7376                     | AI                | 0.9963                    |
| T1.5       | ai                  | clean_direct        | english  | Should detect as spoof                                                               | 0.9949                       | AI                  | AI                  | 0.9993                     | AI                | 0.9973                    |
| T2.1       | human               | human_replay        | urdu     | Should stay human-likely (not AI fake)                                               | 0.0363                       | HUMAN               | HUMAN               | 0.0048                     | HUMAN             | 0.0202                    |
| T2.2       | human               | mixer_processed     | urdu     | Avoid false FAKE on processed human                                                  | 0.1141                       | HUMAN               | HUMAN               | 0.0604                     | HUMAN             | 0.0632                    |
| T2.3       | human               | human_replay        | urdu     | Should stay human-likely                                                             | 0.0679                       | HUMAN               | HUMAN               | 0.0012                     | HUMAN             | 0.0157                    |
| T2.4       | human               | human_replay        | urdu     | Should stay human-likely                                                             | 0.005                        | HUMAN               | HUMAN               | 0.001                      | HUMAN             | 0.003                     |
| T2.5       | human               | human_replay        | urdu     | Should stay human-likely                                                             | 0.0023                       | HUMAN               | HUMAN               | 0.0006                     | HUMAN             | 0.0022                    |
| T3.1       | ai                  | clean_direct        | english  | Should detect as spoof                                                               | 0.9949                       | AI                  | AI                  | 0.9993                     | AI                | 0.9974                    |
| T3.2       | ai                  | ai_replay           | english  | Should detect spoof + replay hints                                                   | 0.9941                       | AI                  | AI                  | 0.7562                     | AI                | 0.9976                    |
| T3.3       | ai                  | ai_replay           | english  | Should detect as spoof                                                               | 0.993                        | AI                  | AI                  | 0.8356                     | AI                | 0.9762                    |
| T3.4       | ai                  | mixer_processed     | english  | Should detect as spoof                                                               | 0.9655                       | AI                  | AI                  | 0.169                      | HUMAN             | 0.9565                    |
| T3.5       | ai                  | ai_replay           | english  | Should detect as spoof                                                               | 0.9364                       | AI                  | AI                  | 0.0248                     | HUMAN             | 0.5268                    |
| T4.1       | human               | clean_direct        | english  | Should not be called AI fake                                                         | 1.0                          | AI                  | AI                  | 0.7142                     | AI                | 0.99                      |
| T4.2       | ai                  | clean_direct        | english  | Should detect conversion/spoof                                                       | 0.941                        | AI                  | AI                  | 0.7376                     | AI                | 0.9963                    |
| T4.3       | mixed               | partial_ai_insert   | english  | Partial AI sentence in real interview — fill suspicious_start_time/end_time if known | 0.9918                       | AI                  | AI                  | 0.964                      | AI                | 0.997                     |
| T4.5       | ai                  | whatsapp_compressed | english  | Should detect spoof with compression note                                            | 0.0817                       | HUMAN               | HUMAN               | 0.1268                     | HUMAN             | 0.2805                    |
| T5.1       | human               | edited_spliced      | urdu     | Should stay human-likely (no AI insert)                                              | 0.0023                       | HUMAN               | HUMAN               | 0.0002                     | HUMAN             | 0.0015                    |
| T5.2       | human               | edited_spliced      | urdu     | Should stay human-likely                                                             | 0.0051                       | HUMAN               | HUMAN               | 0.0005                     | HUMAN             | 0.0132                    |
| T5.3       | human               | edited_spliced      | urdu     | Avoid false AI call                                                                  | 0.0058                       | HUMAN               | HUMAN               | 0.0004                     | HUMAN             | 0.0029                    |
| T5.4       | human               | edited_spliced      | urdu     | Should stay human-likely                                                             | 0.0382                       | HUMAN               | HUMAN               | 0.0018                     | HUMAN             | 0.0394                    |
| T5.5       | human               | edited_spliced      | urdu     | Should stay human-likely                                                             | 0.0004                       | HUMAN               | HUMAN               | 0.0002                     | HUMAN             | 0.0003                    |
| T5_FAB_001 | mixed               | partial_ai_insert   | urdu     | Mostly real audio with inserted AI-generated segment from 14s to 21s                 | 0.0611                       | HUMAN               | HUMAN               | 0.0133                     | HUMAN             | 0.14                      |

## Errors at Threshold 0.5

| test_id | ground_truth_origin | manipulation_type   | language | expected_forensic_result                  | augmented_origin_probability | augmented_label_050 | augmented_label_092 | current_origin_probability | current_label_020 | nonaug_origin_probability |
| ------- | ------------------- | ------------------- | -------- | ----------------------------------------- | ---------------------------- | ------------------- | ------------------- | -------------------------- | ----------------- | ------------------------- |
| T1.2    | human               | clean_direct        | english  | Avoid false positive on clean audio       | 0.9918                       | AI                  | AI                  | 0.9298                     | AI                | 0.9968                    |
| T4.5    | ai                  | whatsapp_compressed | english  | Should detect spoof with compression note | 0.0817                       | HUMAN               | HUMAN               | 0.1268                     | HUMAN             | 0.2805                    |
| T4.1    | human               | clean_direct        | english  | Should not be called AI fake              | 1.0                          | AI                  | AI                  | 0.7142                     | AI                | 0.99                      |

## Errors at Threshold 0.92

| test_id | ground_truth_origin | manipulation_type   | language | expected_forensic_result                  | augmented_origin_probability | augmented_label_050 | augmented_label_092 | current_origin_probability | current_label_020 | nonaug_origin_probability |
| ------- | ------------------- | ------------------- | -------- | ----------------------------------------- | ---------------------------- | ------------------- | ------------------- | -------------------------- | ----------------- | ------------------------- |
| T1.2    | human               | clean_direct        | english  | Avoid false positive on clean audio       | 0.9918                       | AI                  | AI                  | 0.9298                     | AI                | 0.9968                    |
| T4.5    | ai                  | whatsapp_compressed | english  | Should detect spoof with compression note | 0.0817                       | HUMAN               | HUMAN               | 0.1268                     | HUMAN             | 0.2805                    |
| T4.1    | human               | clean_direct        | english  | Should not be called AI fake              | 1.0                          | AI                  | AI                  | 0.7142                     | AI                | 0.99                      |

## Mixed Partial Diagnostic Rows

| test_id    | ground_truth_origin | manipulation_type | language | expected_forensic_result                                                             | augmented_origin_probability | augmented_label_050 | augmented_label_092 | current_origin_probability | current_label_020 | nonaug_origin_probability |
| ---------- | ------------------- | ----------------- | -------- | ------------------------------------------------------------------------------------ | ---------------------------- | ------------------- | ------------------- | -------------------------- | ----------------- | ------------------------- |
| T4.3       | mixed               | partial_ai_insert | english  | Partial AI sentence in real interview — fill suspicious_start_time/end_time if known | 0.9918                       | AI                  | AI                  | 0.964                      | AI                | 0.997                     |
| T5_FAB_001 | mixed               | partial_ai_insert | urdu     | Mostly real audio with inserted AI-generated segment from 14s to 21s                 | 0.0611                       | HUMAN               | HUMAN               | 0.0133                     | HUMAN             | 0.14                      |

## Interpretation

- This is a stronger external-style check than the Phase 7C1 grouped split, because these files were marked as controlled holdout / not ready for training in Phase 7 metadata.
- Results still evaluate only the origin axis. Replay, mixer, and partial localization axes must be tested separately before changing release behavior.
- Threshold `0.5` is included for recall-oriented origin screening; threshold `0.92` is the earlier dev-selected threshold and is stricter.