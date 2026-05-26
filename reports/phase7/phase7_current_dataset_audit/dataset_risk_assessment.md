# Dataset Risk Assessment — Phase 7C0

## class_imbalance: Class imbalance (spoof vs bonafide)

- **Severity:** high
- **Evidence:** Spoof 83.0716% vs bonafide 16.9284% (1,893,919 rows)
- **Impact:** Model may bias toward FAKE; bonafide FPR risk on deployment
- **Mitigation:** Balanced sampling or class weights in Phase 7C; add local bonafide Urdu/phone data

## attack_imbalance: Attack / PA-replay dominance

- **Severity:** high
- **Evidence:** replay=43.1%, PA dataset=49.8%
- **Impact:** Strong replay/PA cues; weak generalization to synthesis-only or non-PA replay
- **Mitigation:** Collect human/AI replay, mixer, WhatsApp chains; balance attack types in 7C

## domain_imbalance: Studio domain dominance

- **Severity:** high
- **Evidence:** studio=96.1%; social=5712; read_speech=28539
- **Impact:** Model may overfit clean studio conditions; phone/social/replay mismatch in 7A
- **Mitigation:** Collect phone, WhatsApp, room noise, local Pakistani recordings

## language_mismatch: Urdu/Pakistani / phone domain gap

- **Severity:** high
- **Evidence:** Urdu-tagged domains=none; phone domain rows=0
- **Impact:** Phase 7A Urdu clean human borderline / replay confusion
- **Mitigation:** 50–100 clean Urdu/Pakistani human + spoof conditions before fine-tuning

## speaker_leakage: Speaker leakage across splits

- **Severity:** low
- **Evidence:** train∩val=0, train∩test=0
- **Impact:** Inflated eval metrics; poor speaker-independent generalization
- **Mitigation:** Re-split if overlap > 0; keep speaker families grouped in 7C

## file_duplicate: Duplicate file paths or IDs

- **Severity:** low
- **Evidence:** duplicate_filepath_entries=0
- **Impact:** Train/val leakage or overweighted samples
- **Mitigation:** Deduplicate manifest; audit top duplicate_file_report.csv rows

## label_conflict: Label vs attack_type conflicts

- **Severity:** low
- **Evidence:** conflict_rows=0, missing_label=0
- **Impact:** Noisy supervision for attack-aware heads
- **Mitigation:** Fix label mapping; exclude conflict rows from 7C training

## missing_audio: Missing audio files (sampled)

- **Severity:** low
- **Evidence:** 0/100 missing in stratified sample (0.0%)
- **Impact:** Broken training indices; HDF5/manifest misalignment
- **Mitigation:** Repair paths or re-extract features for missing files

## product_mismatch: Product label schema mismatch

- **Severity:** high
- **Evidence:** Training uses label+attack_type; Phase 7 product uses origin+manipulation
- **Impact:** Fine-tuning only REAL/FAKE will not fix 7A origin vs manipulation confusion
- **Mitigation:** Train/calibrate separate origin and manipulation outputs in 7C

## chunk_weighting_bias: Chunk weighting bias (rows vs unique files)

- **Severity:** low
- **Evidence:** unique_files=1,893,919; avg_rows_per_file=1.0; highest=domain=studio @ 1.0 rows/file; high_risk_groups=0; medium_risk_groups=0
- **Impact:** Model may overlearn conditions with more chunks per file (long clips or heavy chunking)
- **Mitigation:** Use file-balanced or speaker-balanced sampling in Phase 7C; cap chunks per file if needed
