# Phase 7C1 Collection Status

**Total manifest rows:** 184
**Unique base_id:** 23
**Unique variant_id:** 8
**Expected (23 × 8):** 184

## By split

- `train`: 128
- `test`: 32
- `val`: 24

## By source_origin

- `ai`: 69
- `human`: 69
- `mixed`: 46

## By manipulation_type

- `clean_direct`: 46
- `partial_ai_insert`: 46
- `mixer_processed`: 46
- `ai_replay`: 23
- `human_replay`: 23

## By origin_label

- `ai_likely`: 69
- `human_likely`: 69
- `mixed_or_partial_ai`: 46

## By manipulation_label

- `clean_original`: 46
- `edited_or_spliced`: 46
- `channel_processed`: 46
- `replayed_or_re_recorded`: 46

## By review_status

- `approved`: 184

## By quality_status

- `approved`: 184

## Missing variants per base_id

- None

## Fabricated files missing timestamps

- Total fabricated rows: 46
- Missing timestamps: 0

## Rows with review_status=needs_review: 0

## Next required actions

4. Run `validate_phase7c1_collection_manifest.py` with `--allow_missing_audio` if paths differ.
5. After validation passes, plan Phase 7C feature extraction (not in this step).

Target counts reference: `phase7c1_target_counts.csv`
