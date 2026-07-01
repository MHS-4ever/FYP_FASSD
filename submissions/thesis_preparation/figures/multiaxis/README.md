# Multi-axis confusion matrices

Generated from official release-audit metrics on **testing_audios** (evaluation-only).

Source: `reports/release_audit/phase7_final_release_2026-06-13/phase7_final_testing_audios_metrics.csv`

| Figure | Axis | n | TP | TN | FP | FN |
|--------|------|---|----|----|----|-----|
| `multiaxis_origin_confusion_matrix.png` | origin | 18 | 9 | 6 | 2 | 1 |
| `multiaxis_replay_confusion_matrix.png` | replay | 25 | 5 | 15 | 3 | 2 |
| `multiaxis_mixer_confusion_matrix.png` | mixer | 25 | 0 | 22 | 1 | 2 |
| `multiaxis_partial_confusion_matrix.png` | partial | 25 | 2 | 23 | 0 | 0 |

Combined 4-panel: `multiaxis_all_axes_confusion_matrices.png`

Regenerate:
```bash
python code/generate_multiaxis_confusion_matrices.py
```
