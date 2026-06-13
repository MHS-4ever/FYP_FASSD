# Phase 5 — F9 feature audit

## Removed from model inputs (audit F9)

- `acoustic_deviation_percentile_within_file`
- `combined_within_file_deviation_score`
- `ssl_deviation_percentile_within_file`
- `within_file_acoustic_deviation_score`
- `within_file_ssl_deviation_score`

## Kept localization features

- `acoustic_distance_from_file_median`
- `ssl_distance_from_file_median`
- `neighbor_acoustic_transition_score`
- `neighbor_ssl_transition_score`
- `combined_neighbor_transition_score`

Total model features: **819**