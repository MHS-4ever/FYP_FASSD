# Current Training Dataset Audit — Phase 7C0

**Generated:** 2026-05-17 22:36 UTC

**Model:** HybridResNetEnvironmental (`hybrid_resnet_environmental_best.pth`)

**Scope:** Audit only — no training, no fine-tuning, no Phase 6/7A/7B changes.

---

## 1. Executive summary

- **Unified samples:** 1,893,919 rows; **speakers:** 73,421
- **Bonafide / spoof:** 16.9% / 83.1%
- **Dominant datasets:** PA (943,110), DF (611,829), LA (181,566)
- **Dominant domains:** studio (1,819,660), read_speech (28,539), broadcast (17,994)
- **Main imbalance risks:** spoof-heavy (~83%); PA + replay dominate; studio domain >96% of rows.
- **Main domain gaps:** Urdu/Pakistani, phone capture, WhatsApp/social compression underrepresented vs Phase 7A needs.

## 2. Manifest files found/missing

| File | Status |
|------|--------|
| `unified_manifest.csv` | found |
| `train_speaker_independent.csv` | found |
| `val_speaker_independent.csv` | found |
| `test_speaker_independent.csv` | found |

---

## 3. Full dataset distribution

### Labels

- **spoof:** 1,573,308 (83.07%)
- **bonafide:** 320,611 (16.93%)

### Attack types

- **replay:** 816,480 (43.11%)
- **conversion:** 589,212 (31.11%)
- **bonafide:** 320,611 (16.93%)
- **synthesis:** 167,616 (8.85%)

### Datasets

- **PA:** 943,110 (49.80%)
- **DF:** 611,829 (32.30%)
- **LA:** 181,566 (9.59%)
- **RealWorld:** 157,414 (8.31%)

### Domains

- **studio:** 1,819,660 (96.08%)
- **read_speech:** 28,539 (1.51%)
- **broadcast:** 17,994 (0.95%)
- **podcast:** 17,512 (0.92%)
- **social:** 5,712 (0.30%)
- **synthetic:** 4,502 (0.24%)

## 4. Train/val/test split distribution

- **train:** 1,483,741 rows; 58,734 speakers; bonafide 16.9% / spoof 83.1%
- **val:** 155,604 rows; 7,338 speakers; bonafide 19.0% / spoof 81.0%
- **test:** 254,574 rows; 7,349 speakers; bonafide 15.6% / spoof 84.4%

See `split_balance_summary.csv` for detail.

## 5. Speaker independence check

- train ∩ val speakers: **0**
- train ∩ test speakers: **0**
- val ∩ test speakers: **0**
- Duplicate filepaths across splits: train/val=0, train/test=0

Full matrix: `speaker_split_integrity.csv`

## 6. Duration analysis

- Rows with duration value: 157,414 (8.3% of unified; primarily **RealWorld** clips)
- Mean / median: 6.2544 / 4.65 sec
- Min / max: 1.41 / 10.0 sec
- ASVspoof LA/DF/PA rows typically have **empty** duration in manifest (clip-length fixed in feature pipeline).

Buckets: `duration_distribution.csv`

## 7. Missing audio check

- Stratified sample checked: **5000** files
- Missing on disk: **0**

Detail: `missing_audio_report.csv`

## 8. Duplicate / leakage check

- Duplicate filepath reports: **0** (see `duplicate_file_report.csv`)

## 9. Label conflict check

- Conflict rows captured: **0**

Detail: `label_conflict_report.csv`

## 10. Feature HDF5 summary

HDF5 audit completed — see `feature_hdf5_audit.md` and `feature_shape_summary.csv`.

## 11. Phase 7 risks

- **Class imbalance (spoof vs bonafide)** (high): Spoof 83.0716% vs bonafide 16.9284% (1,893,919 rows)
- **Attack / PA-replay dominance** (high): replay=43.1%, PA dataset=49.8%
- **Studio domain dominance** (high): studio=96.1%; social=5712; read_speech=28539
- **Urdu/Pakistani / phone domain gap** (high): Urdu-tagged domains=none; phone domain rows=0
- **Product label schema mismatch** (high): Training uses label+attack_type; Phase 7 product uses origin+manipulation

## 12. What this means for Phase 7C

- **Do not fine-tune blindly** on the legacy unified corpus without addressing imbalance and domain gaps.
- **Collect controlled forensic labels** (origin + manipulation) per Phase 7B schema.
- **Balance local Urdu/phone/social/replay data** before training.
- **Phase 7A T1–T5 (25 files)** remain **holdout**, not training data.

See also: `dataset_risk_assessment.md`, `phase7c_data_collection_recommendations.md`.