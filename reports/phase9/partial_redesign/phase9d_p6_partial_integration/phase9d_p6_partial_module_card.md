# Partial fabrication experimental module card (P5B / P5F)

| Field | Value |
|-------|--------|
| module_name | `partial_fabrication_experimental_p5b` |
| status | experimental_manual_review_only |
| production_ready | false |
| court_ready | false |
| final_verdict_model | false |
| manual_review_required | true |

## Thresholds (unchanged P5B-P2)

- file_gate_threshold = 0.5
- segment_threshold = 0.9
- contrast_threshold = 0.25
- broad_limit = 0.45

## Validation snapshot (P5F)

- total_files: 35
- fabricated_20pct_recall: 0.7
- fabricated_20pct_false_negative_count: 3
- false_partial_count: 2

## Integration tags

`experimental_partial_fabrication_evidence`, `manual_review_required`, `no_conclusive_authenticity_decision`,
`no_operational_deployment_claim`, `no_legal_evidence_claim`

## Claim flags (JSON booleans in metadata)

- production_ready: false
- court_ready: false
- final_verdict_model: false
