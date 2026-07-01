# FASSD features — plain-language guide

**Audience:** supervisors, examiners, or readers without a signal-processing background.  
**Purpose:** explain what the system measures from audio before it produces evidence indicators.  
**Technical source:** `code/phase8/features/phase8c_feature_utils.py`, `code/phase8/embeddings/phase8d_ssl_utils.py`, `release/models/*/metadata.json`

---

## How to read this document

FASSD does **not** listen like a human and say “fake” or “real” in one step. It first turns audio into **numbers (features)** that describe loudness, tone, noise, recording quality, and voice character. Small **classification models** then use those numbers to support separate evidence checks:

| Evidence check | Main feature type | Plain question it helps answer |
|----------------|-------------------|--------------------------------|
| **Origin** | Voice fingerprint (SSL) | Does this sound more like a natural human voice or AI-generated speech? |
| **Replay** | Recording / acoustic cues | Does this sound like it was played and re-recorded? |
| **Mixer / channel** | Recording / acoustic cues | Does this sound like it went through a mixer, call chain, or channel processing? |
| **Partial fabrication** | Short-window fingerprint + change cues | Does one part of the recording sound different from the rest? |

None of these features alone is proof of fraud. They are **measurements** used in an experimental review workflow.

---

## 1. Voice fingerprint features (SSL / WavLM)

**Names in data:** `ssl_emb_000` … `ssl_emb_767` (768 numbers per file or per 4-second segment)  
**Model used:** Microsoft **WavLM** (`microsoft/wavlm-base-plus`), loaded frozen from Hugging Face  
**Used by:** Origin axis (whole file); Partial axis (each short segment)

**Plain explanation:**  
Think of this as a **digital fingerprint of how the voice sounds** — not the words, but the overall voice pattern. The system compresses each piece of audio into 768 measurements that capture timbre, speaking style, and speech-like qualities learned from large amounts of speech data.

**Why 768 names?**  
Each `ssl_emb_XXX` is one dimension of that fingerprint. Listing all 768 separately would not help a non-technical reader; what matters is that together they describe **voice character** for the origin and partial checks.

---

## 2. Loudness and level features

| Feature | One-line description |
|---------|----------------------|
| `rms_mean` | Average loudness of the recording. |
| `rms_std` | How much loudness varies over time. |
| `rms_min` | Quietest typical level in the recording. |
| `rms_max` | Loudest typical level in the recording. |
| `peak_amplitude` | Highest volume peak reached. |
| `mean_amplitude` | Average waveform level (related to overall volume). |
| `std_amplitude` | How uneven the waveform levels are. |
| `dc_offset` | Whether the recording is shifted above or below neutral zero (can hint at recording gear issues). |
| `dynamic_range_proxy` | How much contrast there is between quiet and loud parts. |

**Used by:** Replay and Mixer axes (whole file); Partial axis (per segment, subset).

---

## 3. Silence, activity, and distortion

| Feature | One-line description |
|---------|----------------------|
| `silence_ratio` | How much of the audio is very quiet or empty. |
| `active_audio_ratio` | How much of the audio contains actual speech or sound. |
| `zero_crossing_rate_mean` | How often the wave crosses zero — rough indicator of noisiness vs smooth tone. |
| `zero_crossing_rate_std` | How much that noisiness pattern changes over time. |
| `clipping_ratio` | How often the recording hits maximum volume and distorts (like a overloaded mic). |

**Used by:** Replay, Mixer, Partial.

---

## 4. Tone and frequency balance (“how bright or dull”)

| Feature | One-line description |
|---------|----------------------|
| `spectral_centroid_mean` | Whether the sound is overall bright (high tones) or dull (low tones). |
| `spectral_centroid_std` | How much brightness changes over time. |
| `spectral_bandwidth_mean` | How spread out the frequencies are — thin vs rich sound. |
| `spectral_bandwidth_std` | How much that frequency spread changes. |
| `spectral_rolloff_mean` | Where most of the high-frequency energy cuts off. |
| `spectral_rolloff_std` | How stable that high-frequency cutoff is. |
| `spectral_flatness_mean` | Whether the sound is more tonal (musical/voice-like) or noise-like. |
| `spectral_flatness_std` | How much that tonal vs noise-like quality varies. |
| `spectral_contrast_mean` | Difference between strong and weak frequency bands (texture of the sound). |
| `spectral_contrast_std` | How much that texture changes over time. |
| `low_band_energy_ratio` | Share of sound energy in low (bass) frequencies. |
| `mid_band_energy_ratio` | Share of energy in middle frequencies (most speech energy). |
| `high_band_energy_ratio` | Share of energy in high frequencies (clarity, hiss, artifacts). |
| `very_high_band_energy_ratio` | Share of energy in very high frequencies (can reflect compression or equipment). |
| `high_freq_rolloff_ratio` | How quickly high frequencies fall off — related to muffling or filtering. |
| `bandwidth_occupied_95` | How wide the frequency range is for most of the sound energy. |

**Used by:** Replay, Mixer, Partial.

---

## 5. Noise and clarity proxies

| Feature | One-line description |
|---------|----------------------|
| `noise_floor_proxy` | Estimated background hiss or room noise level. |
| `snr_proxy` | Rough signal-to-noise ratio — clear speech vs noisy recording. |
| `spectral_entropy_mean` | How random or complex the frequency pattern is. |
| `spectral_entropy_std` | How much that complexity changes over time. |

**Used by:** Replay, Mixer, Partial.

---

## 6. MFCC features (voice texture patterns)

**Names in data:** `mfcc_1_mean`, `mfcc_1_std`, … `mfcc_13_mean`, `mfcc_13_std` (26 values per file; similar set per segment)

**Plain explanation:**  
MFCCs are standard **voice texture** measurements — they summarize how the vocal tract and recording chain shape the sound, similar to how humans perceive timbre. Each number from 1 to 13 captures a different aspect of that texture; `_mean` is the average over the clip, `_std` is how much it changes.

**Used by:** Replay and Mixer axes (file level). On partial segments, MFCCs may be sparse in fast processing mode; the partial model relies more on SSL and localization cues.

---

## 7. “Something changed inside this file” features (partial fabrication)

These compare **one short window** (about 4 seconds) to the **rest of the same file** or to **neighbouring windows**.

| Feature | One-line description |
|---------|----------------------|
| `acoustic_distance_from_file_median` | How different this segment’s loudness/tone numbers are from the typical segment in the same file. |
| `ssl_distance_from_file_median` | How different this segment’s voice fingerprint is from the typical segment in the same file. |
| `neighbor_acoustic_transition_score` | How sharp the acoustic change is at the border with the previous/next segment. |
| `neighbor_ssl_transition_score` | How sharp the voice-fingerprint change is between neighbouring segments. |
| `combined_neighbor_transition_score` | Overall “splice-like” jump score combining acoustic and fingerprint changes. |

**Not used in the final packaged partial model (removed in release audit):**

| Feature | Why removed (plain terms) |
|---------|---------------------------|
| `within_file_acoustic_deviation_score` | Label-related within-file score — excluded to avoid training leakage. |
| `within_file_ssl_deviation_score` | Same — excluded from release model. |
| `combined_within_file_deviation_score` | Same — excluded from release model. |
| `acoustic_deviation_percentile_within_file` | Percentile rank feature (F9 group) — excluded from release model. |
| `ssl_deviation_percentile_within_file` | Percentile rank feature (F9 group) — excluded from release model. |

**Used by:** Partial fabrication axis only.

---

## 8. What each shipped model actually uses

The system **extracts many features**, but each model keeps only the most useful subset after training (typically **50–75** numbers).

| Model | Features extracted | Features used after selection | Count |
|-------|-------------------|------------------------------|-------|
| **Origin** | 768 SSL fingerprint dims | Top SSL dims (e.g. `ssl_emb_038`, `ssl_emb_199`, …) | **50** |
| **Replay** | ~59 acoustic file features | Top acoustic dims (RMS, spectral, MFCC, etc.) | **50** |
| **Mixer** | ~59 acoustic file features | Top acoustic dims (different subset than replay) | **50** |
| **Partial** | 768 SSL + segment acoustic + localization | 69 SSL + 6 localization (no F9 group) | **75** |

Exact selected names: `release/models/origin/origin_file_model__ssl__metadata.json`, `replay/...`, `mixer/...`, `partial_segment/...`.

---

## 9. Features used in older experiments (not in live four-axis release)

For context only — these appear in thesis history but are **not** the active website/release pipeline:

| Feature family | Plain description | Where it appeared |
|----------------|-------------------|-------------------|
| **LFCC / log-mel spectrograms** | Picture of how sound energy changes over time and pitch — like a heat map of the voice. | Early LCNN, ResNet, HybridResNet |
| **12 environmental features** (e.g. room echo, background level, spectral tilt) | Measurements of room, noise, and broadcast environment. | HybridResNetEnvironmental |
| **AASIST / Hybrid deep scores** | Single neural-network fake-vs-real score. | Rejected reference models |

---

## 10. Short summary for presentations

> “We convert audio into measurable traits: how loud it is, how noisy it is, how bright or muffled it sounds, and a voice fingerprint from WavLM. Separate small models read those traits to support four different review questions — AI origin, replay, mixer processing, and partial edits — instead of one black-box fake/real button.”

---

*Last aligned to release model metadata and Phase 8C feature schema. Regenerate selected-feature lists from `release/models/*/metadata.json` if models are retrained.*
