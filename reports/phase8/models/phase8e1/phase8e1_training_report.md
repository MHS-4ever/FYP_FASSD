# Phase 8E-1 Training Report

**Generated:** 2026-05-28 10:41:32 UTC

> Experimental cross-validated evidence modeling only. No final forensic decisions.

## Dataset Counts

- origin_file_model: 46
- replay_file_model: 92
- mixer_file_model: 92

## Class Counts

- origin_file_model__acoustic: {'1': 23, '0': 23}
- origin_file_model__ssl: {'1': 23, '0': 23}
- origin_file_model__combined: {'1': 23, '0': 23}
- replay_file_model__acoustic: {'0': 46, '1': 46}
- replay_file_model__ssl: {'0': 46, '1': 46}
- replay_file_model__combined: {'0': 46, '1': 46}
- mixer_file_model__acoustic: {'0': 46, '1': 46}
- mixer_file_model__ssl: {'0': 46, '1': 46}
- mixer_file_model__combined: {'0': 46, '1': 46}

## Feature Set Sizes

- mixer_file_model / acoustic: input=59, mean_selected=50.0
- mixer_file_model / combined: input=827, mean_selected=50.0
- mixer_file_model / ssl: input=768, mean_selected=50.0
- origin_file_model / acoustic: input=59, mean_selected=50.0
- origin_file_model / combined: input=827, mean_selected=50.0
- origin_file_model / ssl: input=768, mean_selected=50.0
- replay_file_model / acoustic: input=59, mean_selected=50.0
- replay_file_model / combined: input=827, mean_selected=50.0
- replay_file_model / ssl: input=768, mean_selected=50.0

## Cross-Validated Experimental Metrics

- origin_file_model / acoustic | split=StratifiedGroupKFold | acc=0.9356 | bal_acc=0.93 | f1=0.9442
- origin_file_model / ssl | split=StratifiedGroupKFold | acc=1.0 | bal_acc=1.0 | f1=1.0
- origin_file_model / combined | split=StratifiedGroupKFold | acc=1.0 | bal_acc=1.0 | f1=1.0
- replay_file_model / acoustic | split=StratifiedGroupKFold | acc=0.9673 | bal_acc=0.9693 | f1=0.9616
- replay_file_model / ssl | split=StratifiedGroupKFold | acc=0.9784 | bal_acc=0.9784 | f1=0.9749
- replay_file_model / combined | split=StratifiedGroupKFold | acc=0.9673 | bal_acc=0.9693 | f1=0.9616
- mixer_file_model / acoustic | split=StratifiedGroupKFold | acc=0.9889 | bal_acc=0.9909 | f1=0.9867
- mixer_file_model / ssl | split=StratifiedGroupKFold | acc=0.9673 | bal_acc=0.9718 | f1=0.9631
- mixer_file_model / combined | split=StratifiedGroupKFold | acc=0.9895 | bal_acc=0.9909 | f1=0.9882

## Confusion Matrices (OOF Aggregated)

- mixer_file_model / acoustic: tn=45, fp=1, fn=0, tp=46
- mixer_file_model / combined: tn=45, fp=1, fn=0, tp=46
- mixer_file_model / ssl: tn=43, fp=3, fn=0, tp=46
- origin_file_model / acoustic: tn=20, fp=3, fn=0, tp=23
- origin_file_model / combined: tn=23, fp=0, fn=0, tp=23
- origin_file_model / ssl: tn=23, fp=0, fn=0, tp=23
- replay_file_model / acoustic: tn=44, fp=2, fn=1, tp=45
- replay_file_model / combined: tn=44, fp=2, fn=1, tp=45
- replay_file_model / ssl: tn=45, fp=1, fn=1, tp=45

## Known Limitations

- Small dataset sizes; metrics are unstable across folds.
- Group-aware splitting may reduce effective training data.
- No segment-level modeling in this phase.
- No partial fabrication training in this phase.
- No final forensic decisions are produced.

## Recommendation

- Review experimental metrics and failure patterns before Phase 8E-2 or Phase 8F planning.
