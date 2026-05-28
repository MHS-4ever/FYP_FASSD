# Phase 8C-A1 Acoustic Feature Audit Report

**Generated:** 2026-05-27 21:54:01 UTC
**Runtime:** 5.6s

> **Descriptive analysis only** — not model performance, not fake/real detection, not forensic proof.

## 1. Purpose

Sanity-check Phase 8C acoustic/channel features for internal consistency, missingness, and
descriptive differences across **known** origin/manipulation labels on Phase 7C1.

## 2. Data consistency

- File/segment IDs and row counts match Phase 8B tables.

## 3. Segment label inheritance (important)

Segment group analysis uses **file-level** `known_manipulation_labels` and `known_origin_label`
joined by `file_id` unless true per-segment ground truth exists in Phase 8B.
Do not interpret segment group shifts as localized segment truth.

## 4. Fast segment mode limitations

- Segment MFCC columns may be 100% blank (expected).
- `spectral_contrast_mean` often blank at segment level.
- `very_high_band_energy_ratio` may be blank at 16 kHz (Nyquist 8 kHz).

## 5. Missingness highlights

- exclude_for_now: 29 feature-level entries
- limited: 0 feature-level entries
- `file` `very_high_band_energy_ratio`: 100% missing
- `segment` `spectral_contrast_mean`: 100% missing
- `segment` `very_high_band_energy_ratio`: 100% missing
- `segment` `mfcc_1_mean`: 100% missing
- `segment` `mfcc_1_std`: 100% missing
- `segment` `mfcc_2_mean`: 100% missing
- `segment` `mfcc_2_std`: 100% missing
- `segment` `mfcc_3_mean`: 100% missing
- `segment` `mfcc_3_std`: 100% missing
- `segment` `mfcc_4_mean`: 100% missing
- `segment` `mfcc_4_std`: 100% missing
- `segment` `mfcc_5_mean`: 100% missing
- `segment` `mfcc_5_std`: 100% missing
- `segment` `mfcc_6_mean`: 100% missing
- `segment` `mfcc_6_std`: 100% missing

## 6. Top descriptive candidates (file-level, by comparison)

### clean_human_vs_clean_ai_synthetic
- `mfcc_1_std` effect_size=3.6523793295008256 direction=higher_in_group_b — feature shows descriptive separation — possible candidate for later modeling; not a standalone detector
- `mfcc_2_std` effect_size=2.3766034431387713 direction=higher_in_group_b — feature shows descriptive separation — possible candidate for later modeling; not a standalone detector
- `mfcc_2_mean` effect_size=2.3289550274685125 direction=higher_in_group_a — feature shows descriptive separation — possible candidate for later modeling; not a standalone detector
- `spectral_centroid_std` effect_size=2.253870693015004 direction=higher_in_group_b — feature shows descriptive separation — possible candidate for later modeling; not a standalone detector
- `zero_crossing_rate_std` effect_size=1.9206492613963229 direction=higher_in_group_b — feature shows descriptive separation — possible candidate for later modeling; not a standalone detector
- `spectral_centroid_mean` effect_size=1.8341125743636852 direction=higher_in_group_b — feature shows descriptive separation — possible candidate for later modeling; not a standalone detector
- `high_band_energy_ratio` effect_size=1.774988919053457 direction=higher_in_group_b — feature shows descriptive separation — possible candidate for later modeling; not a standalone detector
- `spectral_rolloff_std` effect_size=1.7277293917902274 direction=higher_in_group_b — feature shows descriptive separation — possible candidate for later modeling; not a standalone detector

### clean_vs_mixer_channel_processed
- `spectral_rolloff_std` effect_size=2.4252147657545273 direction=higher_in_group_a — feature shows descriptive separation — possible candidate for later modeling; not a standalone detector
- `mfcc_6_mean` effect_size=2.21653935808755 direction=higher_in_group_a — feature shows descriptive separation — possible candidate for later modeling; not a standalone detector
- `mfcc_13_mean` effect_size=2.1768240616360113 direction=higher_in_group_a — feature shows descriptive separation — possible candidate for later modeling; not a standalone detector
- `spectral_centroid_std` effect_size=2.074669110788142 direction=higher_in_group_a — feature shows descriptive separation — possible candidate for later modeling; not a standalone detector
- `spectral_bandwidth_std` effect_size=2.013819939020424 direction=higher_in_group_a — feature shows descriptive separation — possible candidate for later modeling; not a standalone detector
- `mfcc_8_mean` effect_size=1.837992169649504 direction=higher_in_group_a — feature shows descriptive separation — possible candidate for later modeling; not a standalone detector
- `mfcc_3_std` effect_size=1.797833829272808 direction=higher_in_group_a — feature shows descriptive separation — possible candidate for later modeling; not a standalone detector
- `mfcc_11_mean` effect_size=1.764576801654841 direction=higher_in_group_a — feature shows descriptive separation — possible candidate for later modeling; not a standalone detector

### clean_vs_non_clean
- `spectral_rolloff_std` effect_size=1.1506959966214028 direction=higher_in_group_a — feature shows descriptive separation — possible candidate for later modeling; not a standalone detector
- `spectral_bandwidth_std` effect_size=1.1231550327334554 direction=higher_in_group_a — feature shows descriptive separation — possible candidate for later modeling; not a standalone detector
- `mfcc_13_mean` effect_size=1.097849448886369 direction=higher_in_group_a — feature shows descriptive separation — possible candidate for later modeling; not a standalone detector
- `mfcc_1_mean` effect_size=1.0901454003054334 direction=higher_in_group_b — feature shows descriptive separation — possible candidate for later modeling; not a standalone detector
- `mfcc_11_mean` effect_size=1.013553264955547 direction=higher_in_group_a — feature shows descriptive separation — possible candidate for later modeling; not a standalone detector
- `noise_floor_proxy` effect_size=0.9739495425078062 direction=higher_in_group_b — feature shows descriptive separation — possible candidate for later modeling; not a standalone detector
- `mfcc_1_std` effect_size=0.9455958291131783 direction=higher_in_group_a — feature shows descriptive separation — possible candidate for later modeling; not a standalone detector
- `mfcc_3_mean` effect_size=0.9270701684779432 direction=higher_in_group_a — feature shows descriptive separation — possible candidate for later modeling; not a standalone detector

### clean_vs_partial_fabrication_combo
- `mfcc_10_std` effect_size=0.46661331852259824 direction=higher_in_group_b — weak descriptive separation — treat carefully; requires validation in later phases
- `mfcc_5_std` effect_size=0.43103390991506735 direction=higher_in_group_b — weak descriptive separation — treat carefully; requires validation in later phases
- `mfcc_13_std` effect_size=0.34707588079139906 direction=higher_in_group_b — weak descriptive separation — treat carefully; requires validation in later phases
- `mfcc_8_std` effect_size=0.29742018913116003 direction=higher_in_group_b — weak descriptive separation — treat carefully; requires validation in later phases
- `peak_amplitude` effect_size=0.2779827498504837 direction=higher_in_group_b — weak descriptive separation — treat carefully; requires validation in later phases
- `mfcc_6_std` effect_size=0.23251720422364347 direction=higher_in_group_b — weak descriptive separation — treat carefully; requires validation in later phases
- `dynamic_range_proxy` effect_size=0.22263730901939507 direction=higher_in_group_b — weak descriptive separation — treat carefully; requires validation in later phases
- `rms_max` effect_size=0.22181042447488478 direction=higher_in_group_b — weak descriptive separation — treat carefully; requires validation in later phases

### clean_vs_replay_rerecorded
- `rms_min` effect_size=4.584080891169062 direction=higher_in_group_b — feature shows descriptive separation — possible candidate for later modeling; not a standalone detector
- `spectral_contrast_std` effect_size=3.2136126674294965 direction=higher_in_group_a — feature shows descriptive separation — possible candidate for later modeling; not a standalone detector
- `mfcc_1_mean` effect_size=2.9529184270343642 direction=higher_in_group_b — feature shows descriptive separation — possible candidate for later modeling; not a standalone detector
- `noise_floor_proxy` effect_size=2.9452126215445946 direction=higher_in_group_b — feature shows descriptive separation — possible candidate for later modeling; not a standalone detector
- `mfcc_4_std` effect_size=2.8598290875551666 direction=higher_in_group_a — feature shows descriptive separation — possible candidate for later modeling; not a standalone detector
- `spectral_bandwidth_std` effect_size=2.818198548136377 direction=higher_in_group_a — feature shows descriptive separation — possible candidate for later modeling; not a standalone detector
- `low_band_energy_ratio` effect_size=2.7372613368888343 direction=higher_in_group_a — feature shows descriptive separation — possible candidate for later modeling; not a standalone detector
- `mfcc_13_std` effect_size=2.562316375751288 direction=higher_in_group_a — feature shows descriptive separation — possible candidate for later modeling; not a standalone detector

### human_vs_ai_synthetic
- `spectral_flatness_std` effect_size=1.4489534443495597 direction=higher_in_group_b — feature shows descriptive separation — possible candidate for later modeling; not a standalone detector
- `zero_crossing_rate_std` effect_size=1.3519643758936508 direction=higher_in_group_b — feature shows descriptive separation — possible candidate for later modeling; not a standalone detector
- `spectral_centroid_std` effect_size=1.267245357785824 direction=higher_in_group_b — feature shows descriptive separation — possible candidate for later modeling; not a standalone detector
- `mfcc_2_std` effect_size=1.227138246862998 direction=higher_in_group_b — feature shows descriptive separation — possible candidate for later modeling; not a standalone detector
- `mfcc_11_std` effect_size=1.1831897004406784 direction=higher_in_group_b — feature shows descriptive separation — possible candidate for later modeling; not a standalone detector
- `mfcc_2_mean` effect_size=1.1830969905372826 direction=higher_in_group_a — feature shows descriptive separation — possible candidate for later modeling; not a standalone detector
- `zero_crossing_rate_mean` effect_size=1.1524180257964423 direction=higher_in_group_b — feature shows descriptive separation — possible candidate for later modeling; not a standalone detector
- `spectral_flatness_mean` effect_size=1.0672282257956416 direction=higher_in_group_b — feature shows descriptive separation — possible candidate for later modeling; not a standalone detector

### seg_clean_vs_mixer_inherited
- `rms_mean` effect_size=0.8300385432739373 direction=higher_in_group_b — feature shows descriptive separation — possible candidate for later modeling; not a standalone detector
- `spectral_flatness_mean` effect_size=0.7318677533407748 direction=higher_in_group_a — moderate descriptive separation — possible candidate for later modeling; requires validation in later phases
- `noise_floor_proxy` effect_size=0.6758672994680408 direction=higher_in_group_b — moderate descriptive separation — possible candidate for later modeling; requires validation in later phases
- `spectral_centroid_mean` effect_size=0.6466172625761962 direction=higher_in_group_a — moderate descriptive separation — possible candidate for later modeling; requires validation in later phases
- `spectral_rolloff_mean` effect_size=0.6457710918932765 direction=higher_in_group_a — moderate descriptive separation — possible candidate for later modeling; requires validation in later phases
- `snr_proxy` effect_size=0.6012233492634922 direction=higher_in_group_a — moderate descriptive separation — possible candidate for later modeling; requires validation in later phases
- `rms_std` effect_size=0.5043687363617199 direction=higher_in_group_b — moderate descriptive separation — possible candidate for later modeling; requires validation in later phases
- `silence_ratio` effect_size=0.5000958367698873 direction=higher_in_group_a — moderate descriptive separation — possible candidate for later modeling; requires validation in later phases

### seg_clean_vs_partial_inherited
- `clipping_ratio` effect_size=0.08609799867561191 direction=higher_in_group_a — weak descriptive separation — treat carefully; requires validation in later phases
- `rms_std` effect_size=0.0507382068094855 direction=higher_in_group_a — weak descriptive separation — treat carefully; requires validation in later phases
- `rms_mean` effect_size=0.048690042710050084 direction=higher_in_group_a — weak descriptive separation — treat carefully; requires validation in later phases
- `snr_proxy` effect_size=0.03953739315764672 direction=higher_in_group_a — weak descriptive separation — treat carefully; requires validation in later phases
- `peak_amplitude` effect_size=0.03863391877307698 direction=higher_in_group_a — weak descriptive separation — treat carefully; requires validation in later phases
- `dynamic_range_proxy` effect_size=0.03751498805316323 direction=higher_in_group_a — weak descriptive separation — treat carefully; requires validation in later phases
- `spectral_centroid_mean` effect_size=0.0242519099923749 direction=higher_in_group_a — weak descriptive separation — treat carefully; requires validation in later phases
- `zero_crossing_rate_mean` effect_size=0.022304327940000673 direction=higher_in_group_a — weak descriptive separation — treat carefully; requires validation in later phases

## 7. Safe use for Phase 8E (indicators only)

- Prefer features marked **usable** with effect_size ≥ 0.5 on replay/mixer/partial comparisons.
- Exclude 100% missing or zero-variance features.
- Do not use a single feature as spoof/AI proof.

## 8. Outputs

- Directory: `reports/phase8/features/audit`

## 9. What this audit did NOT do

- No classifier training or inference
- No predictions or forensic decisions
- No modification of Phase 8B/8C CSVs

