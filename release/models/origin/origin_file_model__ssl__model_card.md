# origin_file_model (experimental release card)

- status: experimental_forensic_prototype
- evidence_axis: origin_evidence
- feature_set: ssl
- threshold_candidate: 0.92
- threshold_source: leakage-safe dev split only; `testing_audios` evaluation-only
- rows packaged: 156 fit rows (78 original train rows + 78 train-only augmented rows)
- selected features: 50
- training positives: `ai_clean_direct`, `ai_mixer_processed`, `ai_replayed`
- training negatives: `human_clean`, `human_mixer_processed`, `human_replayed`

## Allowed use
origin evidence indicator for experimental review workflow

## Forbidden use
final fake/real decision; court-ready proof; production deployment without validation; replacing human forensic analyst

## Limitations
- experimental prototype only
- manual review required
- not final forensic proof
- small FYP corpus with only 13 base groups in train split
- external mixer/platform/edited manipulation cases remain documented limitations
