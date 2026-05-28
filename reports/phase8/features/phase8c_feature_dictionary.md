# Phase 8C — Feature Dictionary

**Schema version:** `phase8c_v1`  
**Wording:** All entries are **indicators** or **proxies** — not proof of replay, AI, or manipulation.

---

## Identity / provenance columns

| Column | Type | Meaning |
|--------|------|---------|
| `schema_version` | string | `phase8c_v1` |
| `file_id` | string | Join key to Phase 8B file table |
| `segment_id` | string | Join key to Phase 8B segment table (segment rows only) |
| `audio_path` | string | Source audio path |
| `source_dataset` | string | e.g. `phase7c1` (file rows) |
| `split` | string | train/val/test/etc. (file rows) |
| `known_origin_label` | string | **Ground truth context only** — not a model prediction |
| `known_manipulation_labels` | string | **Ground truth context only** |
| `duration_sec` | string/float | File duration from 8B |
| `sample_rate` | int string | Sample rate used for feature extraction |
| `start_sec` / `end_sec` | float | Segment window (segment rows) |
| `segment_duration_sec` | float | Window length |
| `feature_source` | string | `phase8c_acoustic_librosa` or numpy fallback |
| `extraction_status` | enum | `ok`, `missing_audio`, `unreadable_audio`, `too_short`, `silent_or_invalid`, `error` |
| `warning_message` | string | Non-fatal issues during extraction |

---

## Amplitude / time-domain indicators

| Column | Type | Meaning | Why useful | Limitations |
|--------|------|---------|------------|-------------|
| `rms_mean` | float | Mean frame RMS energy | Overall loudness level | Mic gain dependent |
| `rms_std` | float | Std of frame RMS | Dynamics / pumping | Not replay-specific alone |
| `rms_min` | float | Minimum frame RMS | Quiet passages | |
| `rms_max` | float | Maximum frame RMS | Peaks | |
| `peak_amplitude` | float | Max absolute sample | Clipping/near-clip proxy | |
| `mean_amplitude` | float | Mean absolute value | DC-free level proxy | |
| `std_amplitude` | float | Sample std | Spread of waveform | |
| `dc_offset` | float | Mean sample value | Channel offset indicator | |
| `zero_crossing_rate_mean` | float | Mean ZCR | Noisiness / high-frequency proxy | Not speech content |
| `zero_crossing_rate_std` | float | ZCR variability | | |
| `clipping_ratio` | float | Fraction near full scale | Distortion proxy | |
| `silence_ratio` | float | Fraction of quiet frames | Active speech ratio inverse | Threshold-based |
| `active_audio_ratio` | float | 1 − silence_ratio | How much signal is active | |

---

## Spectral shape indicators

| Column | Type | Meaning | Why useful | Limitations |
|--------|------|---------|------------|-------------|
| `spectral_centroid_mean` | float | Brightness proxy | Channel/mic coloration | |
| `spectral_centroid_std` | float | Centroid variability | | |
| `spectral_bandwidth_mean` | float | Spectral spread | Mixer EQ proxy | |
| `spectral_bandwidth_std` | float | | | |
| `spectral_rolloff_mean` | float | High-frequency energy roll-off | Playback chain hint | |
| `spectral_rolloff_std` | float | | | |
| `spectral_flatness_mean` | float | Tonality vs noise-like | Compression artifact hint | |
| `spectral_flatness_std` | float | | | |
| `spectral_contrast_mean` | float | Peak vs valley bands | Channel processing | |
| `spectral_contrast_std` | float | | | |

---

## Band energy ratio indicators

| Column | Type | Meaning | Why useful | Limitations |
|--------|------|---------|------------|-------------|
| `low_band_energy_ratio` | float | Share of energy below ~300 Hz | Room/rumble | Band edges fixed |
| `mid_band_energy_ratio` | float | ~300 Hz–3 kHz | Speech band emphasis | |
| `high_band_energy_ratio` | float | ~3–8 kHz | Presence / playback | |
| `very_high_band_energy_ratio` | float | ~8 kHz–Nyquist | HF loss / resampling | |

---

## Quality / compression proxy indicators

| Column | Type | Meaning | Why useful | Limitations |
|--------|------|---------|------------|-------------|
| `noise_floor_proxy` | float | Low percentile frame RMS | Background noise | Not true dB SNR |
| `snr_proxy` | float | High vs low RMS ratio | Quality degradation hint | Crude proxy |
| `dynamic_range_proxy` | float | Max − min frame RMS | Compression crushing | |
| `spectral_entropy_mean` | float | Mean spectral entropy | Codec/artifact complexity | |
| `spectral_entropy_std` | float | Entropy variability | | |
| `high_freq_rolloff_ratio` | float | Rolloff / Nyquist | HF cutoff proxy | |
| `bandwidth_occupied_95` | float | Frequency below 95% energy | Band-limiting hint | |

---

## MFCC summary indicators (coefficients 1–13)

| Column | Type | Meaning | Why useful | Limitations |
|--------|------|---------|------------|-------------|
| `mfcc_N_mean` | float | Mean of MFCC N over time | Timbral envelope | Not speaker ID |
| `mfcc_N_std` | float | Std of MFCC N | Temporal variability | |

N = 1 … 13. File table includes all 13 means/stds; segment table includes same set.

---

## Segment-only note

Segment rows omit some file-only aggregates (`rms_min`/`max` file-level extras, some std pairs) per Phase 8C schema — see `SEGMENT_TABLE_COLUMNS` in `phase8c_feature_utils.py`.

---

## Placeholder policy

When audio is missing, too short, or silent: numeric features are **blank** (empty CSV cell), `extraction_status` ≠ `ok`. **No imputation** with zeros that look like measurements.

### Fast segment mode (`--segment_feature_mode fast`, default)

These segment columns remain **blank** (not approximated):

- `spectral_contrast_mean`
- All `mfcc_*_mean` and `mfcc_*_std`

Blank heavy features are **not** forensic decisions. Use `--segment_feature_mode full` later for complete segment MFCC/contrast on selected files.

## Progress and resume (8C-P1)

- Progress: tqdm if installed, else console every N items.
- `--resume`: skip IDs already in output CSVs; safe for interrupted runs.
- Periodic flush writes partial CSVs without corrupting column order.

---

## Forbidden outputs (must not appear)

`fake_score`, `real_score`, `ai_score`, `replay_decision`, `mixer_decision`, `evidence_origin_score`, `origin_score`, `final_forensic_status`, `suspicious_segment_flag`
