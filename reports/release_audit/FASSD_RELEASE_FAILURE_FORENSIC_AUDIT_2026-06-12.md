# FASSD Release Failure — Forensic Audit

**Date:** 2026-06-12
**Repository:** `E:\FYP` (branch `main`, commit `c23bfe31b1de2243d4bde706bcd257351aa92847`)
**Audit type:** read-only investigation. No source code, models, thresholds, configs, datasets, labels or release bundles were modified. No packages were installed. No thresholds were tuned on any data. Temporary `python -c` diagnostics only; no diagnostic scripts were left in the repository.

> Related earlier research note: `reports/post_release_research/post_release_findings_and_improvement_research.md` (created 2026-06-12, untracked). This audit supersedes and extends it with the formal evidence standard.

---

## 1. Executive verdict

The release behaves deterministically, loads the intended artifacts, displays genuine (not hardcoded) model outputs, and has no training/inference preprocessing mismatch. **It nevertheless fails as a detector** because the active origin (AI-vs-human) model was trained on 46 clean files and has never seen processed AI audio: re-running the exact release inference path shows it misses **23/23 replayed AI files** and **5/23 mixer-processed AI files** *from its own collection corpus*. The excellent on-paper results (accuracy 1.0, ROC-AUC 1.0) come from a cross-validation in which group protection was silently disabled (each file was its own group), sibling variants of the same recording sat in opposite folds, and the evaluation set is the training distribution itself. Release acceptance testing was performed on byte-identical training-split files. The partial-fabrication module is structurally biased by within-file percentile features and is then suppressed by gating/arbitration whenever replay or mixer evidence is elevated — which is precisely when partial fabrication is most plausible.

The user-reported failure ("`ai_mixer` audio shown as No AI Detected") is **reproduced and explained** (Section 5).

## 2. Release readiness

**No-Go** for any forensic, operational, or demonstrative use that implies detection capability on processed audio.
**Conditional Go** only as an "experimental demo of a multi-axis evidence workflow" with the failure modes of Section 6 disclosed verbatim (the app's existing disclaimers do not disclose a 100% miss rate on replayed AI).

## 3. Repository and environment snapshot

| Item | Value |
|---|---|
| `git status --short` | `?? reports/post_release_research/` (only untracked item at audit time) |
| Branch | `main` |
| Commit | `c23bfe31b1de2243d4bde706bcd257351aa92847` (2026-06-12 22:37 +05, author MUHAMMAD HASNAIN) |
| Python | 3.10.19 (conda env `fassd`, `C:\Users\mhasn\miniconda3\envs\fassd\python.exe`) |
| torch | 2.5.1+cu121, CUDA available: True, device: NVIDIA GeForce RTX 3050 6GB Laptop GPU, CUDA 12.1 |
| transformers | 5.9.0 |
| librosa / soundfile / soxr | 0.11.0 / 0.13.1 / 1.0.0 |
| scikit-learn | 1.7.2 |
| numpy / pandas / scipy / joblib | 2.2.6 / 2.3.3 / 1.15.3 / 1.5.2 |
| gradio | 6.15.2 |

Hardware constraint for future work: RTX 3050 Laptop 6 GB VRAM, 16 GB RAM, i5-13420H, Windows 11.

## 4. Reconstructed current architecture (verified from code, not docs)

Entry points: `release/app_gradio.py` (Gradio, `analyze()` → `analyze_audio_file`), `release/app_fastapi.py` (FastAPI, → `run_inference_pipeline` → same `analyze_audio_file`, `release/src/inference_pipeline.py:633`). Both share one inference function; PDF (`release/src/pdf_report_generator.py`) and HTML/JSON reports are rendered from the same response dict.

Execution chain for an uploaded file:

| # | Stage | Function (file:line) | Input → Output | Artifact / threshold | Scope | Failure behavior |
|---|---|---|---|---|---|---|
| 1 | Load + mono + conditional peak-normalize + resample to 16 kHz | `load_audio` `release/src/audio_io.py:65-104`; `_resample` :42-54 | file → float64 mono @16 kHz | — | file | `AudioLoadError` → status `error` (not "no AI"); **silent fallback to linear-interp resampling if librosa import fails** (:49-54) |
| 2 | Segmentation | `make_segments` `release/src/segmentation.py`; config `release/config/runtime_config.yaml` | waveform → 4.0 s windows, 2.0 s hop (50% overlap) | seg_dur 4.0, hop 2.0 | segments | — |
| 3 | Acoustic features (59 file-level / segment-level) | `extract_file_acoustic_features` `release/src/feature_extraction.py:48-57` via `code/phase8/features/phase8c_feature_utils.py` | 16 kHz waveform → feature dict | — | both | NaN features → imputed silently by model pipeline |
| 4 | SSL embedding (WavLM-base-plus, last hidden state, mean pooling) | `extract_file_ssl_embedding` `release/src/ssl_embeddings.py:58-67`; `extract_ssl_embedding` `code/phase8/embeddings/phase8d_ssl_utils.py:300-323` | waveform → 768-d vector | `microsoft/wavlm-base-plus` (frozen) | both (whole file AND each 4 s segment) | RuntimeError propagates |
| 5 | Within-file localization features | `compute_live_localization_features` `release/src/feature_extraction.py:133-209` | segment table → +10 relative features (percentiles, max-normalized deviations, neighbor transitions) | — | segments | NaN |
| 6 | Origin axis | `_predict_axis` `release/src/inference_pipeline.py:71-142` (`predict_proba[0,1]`, `>=` threshold, :104-105) | 768-d → p(AI) | `origin_file_model__ssl__experimental.joblib`, th 0.20 | file | exception → `prediction_error`, axis `not_evaluated` |
| 7 | Replay axis | same | 59 acoustic → p(replay) | `replay_file_model__acoustic__experimental.joblib`, th 0.65 | file | same |
| 8 | Mixer axis | same | 59 acoustic → p(mixer) | `mixer_file_model__acoustic__experimental.joblib`, th 0.75 | file | same |
| 9 | Partial segment scoring | `_segment_candidates_from_partial` `inference_pipeline.py:412-489` | 796-d per segment → p(fabricated) per segment | `partial_segment_model__combined__experimental.joblib`, th 0.50 | segments | per-segment NaN, counted as errors |
| 10 | Partial gating | `_apply_partial_fusion_fields` `inference_pipeline.py:254-372` (broad if high-segment fraction ≥0.60, :300) | segment probs → gate label, `gated_partial_probability` | th 0.50 | file | — |
| 11 | Replay/mixer arbitration | `_apply_replay_mixer_partial_arbitration` `inference_pipeline.py:375-409`; repeated in `release/src/fusion_rules.py:80-120` | blocks partial fusion unless gate=localized AND hsf≤0.35 AND topk−rest≥0.35 AND std≥0.25 | — | file | — |
| 12 | Fusion | `fuse_live_evidence` `release/src/fusion_rules.py:201-283` + `code/phase8/fusion/phase8f_fusion_rules.py` | axis strengths → fusion status, risk | — | file | unresolved → `inconclusive_manual_review_experimental` |
| 13 | User wording | `build_voice_origin_result` `release/src/app_report_formatting.py:634-758` | origin prob + replay/mixer context → display label | origin low + processing high → "Inconclusive under replay/channel processing" (:709-721) | file | model load failure → "Inconclusive" |
| 14 | UI / PDF / JSON | `app_gradio.py:51-112`, `pdf_report_generator.py`, `save_json_report` | same response dict everywhere | — | — | waveform/PDF failures → None + error field |

There is **no P5B file gate in the active path**: `partial_module_mode = "mapped_contract"`, `file_gate_available = false` (case JSONs); the packaged `release/models/partial_fabrication_experimental_p5b/` cascade is documented as not active (`reports/phase9/final_release/final_active_model_classifier_types_report.md` §Active Path Notes). AASIST and HybridResNet are present under `release/models/reference/` as "shadow_runnable" but are **never executed** in the active analysis path.

All four active models are scikit-learn `Pipeline(imputer, variance, scaler, SelectKBest, LogisticRegression(l2, balanced, liblinear, seed 42))` — verified by deserialization (Section 10).

## 5. Exact `ai_mixer` forensic trace

### 5.1 File identity

- Release-test upload (from `release/gradio_outputs/json/CASE-DBB938B3E9FC_analysis.json`): `C:\Users\mhasn\AppData\Local\Temp\gradio\a21b8d5d...\ai_001_mixer_processed.wav` — SHA-256 `0bda38e79a864a271191c382c6f673a3c94cd18424b1aa0ba6e9494a14218746`, 11,038,798 bytes.
- Repository file `data/phase7c1/raw/ai_mixer/ai_001_mixer_processed.wav` — **identical SHA-256 and size** → the release test input is byte-identical to corpus audio. WAV PCM_16, 48 000 Hz, 2 channels, 2,759,680 frames (57.493 s).
- Manifest rows: `reports/phase7/phase7c1_collection/phase7c1_collection_manifest.csv` (speaker_001, base_001, `mixer_processed`, ground_truth_origin `ai`, split `train`); `reports/phase8/models/phase8e0/phase8e0_mixer_file_dataset.csv` (**split `train`**, `target_is_mixer_channel=1`, `target_is_ai_synthetic=1`); also in `phase8e0_file_level_master_dataset.csv` and segment master. Out-of-fold prediction exists (`phase8e1_out_of_fold_predictions.csv` rows 433/525/617, mixer task, fold 2, p=0.957–0.9995, true positive).
- **Membership conclusion (CONFIRMED):** the exact file was used in training (train split of the mixer-axis dataset; its session siblings populate origin/replay datasets). It was *not* in the origin model's training set, because the origin dataset (`phase8e0_origin_file_dataset.csv`, 46 rows) includes only `known_manipulation_labels = clean` files.

### 5.2 Release-path inference values (3 repeated runs, identical → deterministic)

Pipeline internals: loaded sample rate 16 000 (from native 48 000, librosa/soxr; stereo → mean downmix `audio_io.py:31-39`; peak-normalize only if peak>1.0, :57-62); duration 57.4934 s, 919,894 samples; 28 segments of 4.0 s at 2.0 s hop, last segment truncated (no padding); no VAD, no silence trimming.

| Axis | Raw probability (`predict_proba[:,1]`) | Threshold | Internal label | Missing features |
|---|---|---|---|---|
| Origin | **0.2423626876258826** | 0.20 (`>=`) | `elevated_ai_origin_indicator`, strength borderline | 0 |
| Replay | 0.5578262665547876 | 0.65 | `low_indicator` | 0 |
| Mixer | 0.95352623561676 | 0.75 | `elevated_mixer_channel_indicator`, strength high | 0 |
| Partial (28 segs) | max 1.0; high-segment fraction 0.3929 | 0.50 | gate `localized_pattern_supported` → **fusion-blocked** `blocked_by_replay_or_mixer_context` | 0 |

Fusion: `suspicious_mixer_channel_experimental`, risk medium. Gradio display (recorded case JSON): "Voice origin: Likely AI-generated with processing indicators", "Origin evidence score: 0.242". PDF/HTML/JSON carry the same numbers (single response dict).

Path agreement: direct estimator call (audit diagnostic) = 0.2424; shared inference function = 0.2423626876258826 (3×); recorded Gradio JSON = 0.2423626876258826. FastAPI wraps the same function. **No integration disagreement found.**

### 5.3 Was the "No AI Detected" reproduced?

Yes — at sibling-file level. Scoring every `ai_mixer` training-corpus file through the exact release origin path:

`ai_012 = 0.073`, `ai_016 = 0.125`, `ai_017 = 0.034`, `ai_018 = 0.080`, `ai_019 = 0.119` → **5/23 mixer-processed AI files score below the 0.20 threshold and display "AI-origin evidence: Not detected"**. Three more are borderline (0.211, 0.225, 0.242 — including the documented release test file, which flips to a miss under any small condition change). For replayed AI the failure is total: **0/23 above threshold** (median 0.031); full sweep:

| Condition (`data/phase7c1/raw/`) | n | min | median | max | flagged AI @0.20 |
|---|---|---|---|---|---|
| ai_direct | 23 | 0.965 | 0.999 | 1.000 | 23/23 |
| ai_fabricated | 23 | 0.875 | 0.997 | 0.999 | 23/23 |
| ai_mixer | 23 | 0.034 | 0.634 | 0.904 | **18/23** |
| ai_repeat (replayed) | 23 | 0.001 | 0.031 | 0.107 | **0/23** |
| human_clean / fabricated / mixer / replay | 4×23 | ≤0.092 max | ~0.00 | 0.092 | 0/92 |

These are *training-distribution* files; unseen-condition performance will be worse.

**The failure was internally documented before release.** `reports/phase9/app/phase9e_p4a_origin_support/phase9e_p4a_shadow_comparison_report.md` (generated 2026-06-03) records, for the **active SSL origin model**: `ai_mixer_detect_rate: 0.0`, `ai_replayed_detect_rate: 0.0`, `ai_origin_accuracy_on_ai_variants: 0.5` on the full 184-file corpus — yet `phase9g_final_release_report.md` (same date, 2026-06-03) declared **GO**. (P4A's 0.0 mixer rate is measured at the final wording-layer label and is even stricter than this audit's raw-threshold measurement of 18/23; both agree replayed AI detection is zero.) The same P4A report shows why the shadow models were rejected: AASIST flags 23/23 clean human files as AI (`human_clean_false_ai_rate: 1.0`), HybridResNet 0.957.

### 5.4 Training/inference parity for this input

- Resampling: training `code/phase8/embeddings/phase8d_ssl_utils.py:189-201` and release `release/src/audio_io.py:42-54` both use `librosa.resample` to 16 000 Hz (same env → same soxr backend). Single resample pass each.
- SSL: same module, same model name (`wavlm-base-plus`), same `pooling="mean"`, same last-hidden-state mean pooling (`phase8d_ssl_utils.py:272-283`,`300-323`).
- Feature names/order/count: enforced at inference by `align_features_to_metadata` against fit-time names (`release/src/model_loader.py`); audit run shows `missing_feature_count = 0` on all axes; pipeline `n_features_in_` (768/59/59/796) matches metadata.
- Scaling/imputation: inside the serialized pipelines (same objects as training).
- Differences found: (a) release `load_audio` casts float64 vs training float32 (numerically immaterial for LR over WavLM features; release scores reproduce the recorded Gradio scores exactly); (b) release conditionally peak-normalizes before resampling, training does not normalize — conditional triggers only when peak>1.0, i.e., effectively never for PCM input. Cached training features for this file (embedding CSVs under phase8d outputs) were not numerically diffed against fresh extraction within this audit window — **COULD NOT VERIFY numeric cache equality**, but end-to-end score equality with the recorded release run (16 decimal digits) makes a parity break implausible.

**Verdict for the primary problem:** PLAUSIBLE user recollection confirmed as a real, systematic failure class (CONFIRMED via siblings; the named test file itself is a borderline near-miss at 0.242 vs threshold 0.20).

## 6. Confirmed defects

(Full mandatory table in Section 22a; details here.)

**F1 — Origin axis blind to processed AI. CONFIRMED DEFECT, Critical.**
Evidence: Section 5.3 sweep (release code path, deterministic); `phase8e0_origin_file_dataset.csv` = 46 rows, all `known_manipulation_labels="clean"` (23 AI / 23 human). User impact: replayed or channel-processed AI shown as "AI-origin: Not detected". Root cause: training composition (no processed-AI positives) + replay/mixer chains physically attenuating vocoder artifacts. Future fix: retrain origin axis with processed-AI positives (the 46 ai_mixer/ai_repeat files already exist) + augmentation (Section 17/22). Validation: per-condition recall matrix on grouped, untouched holdout; target FNR on processed AI reported explicitly. Cost: hours (feature reuse) on this hardware.

**F2 — Cross-validation group protection silently disabled; headline metrics invalid. CONFIRMED DEFECT, Critical.**
Evidence: `phase8e1_out_of_fold_predictions.csv` has `source_group_id` unique per file (46 groups / 46 files; 92/92), so `StratifiedGroupKFold` degenerates to stratified KFold. Sibling variants of the same base recording fall in different folds: replay task 44/46 bases split across folds; mixer 44/46; origin paired same-session/script human-vs-AI 20/23. The collection manifest *defines* proper `split_group_id = base_XXX` (`phase7c1_collection_manifest.csv`) — it was not propagated. Reported metrics (`phase8e1_metrics_summary.csv`: origin-ssl accuracy 1.000, AUC 1.000; replay 0.978; mixer 0.989) therefore measure within-session memorization. User impact: "on paper good, in release wrong". Fix: group-aware splits keyed on `base_id`/speaker; recompute all metrics. Validation: leakage checker that asserts no `base_id` crosses folds/splits.

**F3 — Release acceptance testing performed on byte-identical training files. CONFIRMED DEFECT, High.**
Evidence: SHA-256 equality (Section 5.1); train-split rows; same for `ai_001_replay_laptop_mobile.wav` (in `phase8e0_replay_file_dataset.csv` train rows). No honest holdout exists in the release path. Fix: blind external test set, frozen before any further development.

**F4 — Effective sample size misrepresented by design (23 sessions, 1 device chain, 1 unknown generator). CONFIRMED DEFECT, High.**
Evidence: manifest — 184 files = 23 speakers × 8 variants; `script_id`/`language`/`generator` all "unknown"; one replay chain (`laptop_speaker_to_mobile_recording`), one mixer chain; AI native rate 44.1 kHz mono vs human mostly 48 kHz stereo (latent shortcut risk; see F9/Section 13). Origin model: 46 independent files; trained pipeline selects 50 of 768 dims via `SelectKBest` on those 46 points. Segments (1207 for partial) are correlated windows of these same recordings, not independent samples.

**F5 — Uncalibrated, saturated scores displayed as evidence. CONFIRMED DEFECT, Medium.**
Evidence: OOF probabilities outside [0.05,0.95]: origin 91%, replay 90%, mixer 84%; release UI shows "Evidence score: 1.000" on five segments at once (case JSONs, HTML report); 16-digit probabilities like 0.9999999999999625 in JSON. In-domain Brier (0.001–0.020) is meaningless under F2 leakage. User impact: numbers look fabricated; no uncertainty expression. Fix: calibration on grouped dev split + score-band wording; never display raw saturated values as "confidence".

**F6 — Contradictory partial-fabrication display. CONFIRMED DEFECT, Medium.**
Evidence: CASE-2F86E2E07B77 simultaneously shows "Partial replacement evidence: Not detected" (severity *clear*), "Max segment score: 1.000", a "Suspicious segments for review" table with five segments at 1.000 marked "Recommended", and "Highlighted evidence region: 00:32–00:36". Cause: gate/arbitration outcome (`global_activation_not_localized`, `blocked_by_replay_or_mixer_context`) is applied to the verdict but not to the candidate table/highlight. Fix: single consistent state machine for partial display.

**F7 — Inactive shadow models listed as evidence sources. CONFIRMED DEFECT, Medium.**
Evidence: `voice_origin_result.evidence_sources = ["ssl_origin_model","aasist_shadow","hybrid_resnet_shadow"]`, `evidence_source = "ensemble_if_available"` in case JSONs, generated by `app_report_formatting.py:649-666` from *registry status* ("shadow_runnable"), not from execution; the active path never runs AASIST/HybridResNet. User impact: implies ensemble corroboration that did not occur. Fix: list only executed models.

**F8 — Thresholds derived from the leaked CV on the training distribution. CONFIRMED DEFECT, Medium.**
Evidence: metadata `threshold_source: "Phase 8E-1A threshold recommendations (ssl)"` over the same `phase8e1` predictions affected by F2; origin th=0.20, replay 0.65, mixer 0.75, partial 0.50 (`*_metadata.json`, `threshold_candidate`). No untouched data informed any threshold.

**F9 — Within-file relative features structurally bias the partial localizer. CONFIRMED DEFECT (design), High.**
Evidence: `release/src/feature_extraction.py:133-209` — `*_deviation_percentile_within_file` spans 0→1 by construction in every file; `within_file_*_deviation_score` is max-normalized so some segment always equals 1.0; these are model inputs (`partial_segment_model__combined__metadata.json` feature list). Observable consequence: fully-AI replayed file → 21/28 segments ≥0.9 (broad activation), fully-AI mixer file → 11/28 high with "localized" pattern — both spurious for *partial* fabrication. Packaged holdout numbers: `fabricated_20pct_recall = 0.70`, 2 false positives (`release/models/partial_fabrication_experimental_p5b/partial_validation_summary.json`).

**F10 — Replay/mixer arbitration creates a laundering silencing vector. CONFIRMED DEFECT (design), High.**
Evidence: `inference_pipeline.py:375-409` and `fusion_rules.py:80-120`: when replay or mixer strength is moderate/high, partial evidence is fusion-blocked unless a strict localization test passes (hsf ≤0.35, topk−rest ≥0.35, std ≥0.25); both recorded cases show `blocked_by_replay_or_mixer_context`. Combined with F1, an adversary who replays or channel-processes a fake reliably reduces the system to "inconclusive / mixer detected". This is the exact attack model of ReplayDF (Section 20).

**F11 — Silent low-quality resample fallback. CONFIRMED DEFECT, Low.**
Evidence: `audio_io.py:49-54` — if librosa import/resample fails, linear `np.interp` resampling is used with no warning flag in the response (same pattern in training utils `phase8d_ssl_utils.py:196-201`). Not triggered in the audited environment; would silently change the front end elsewhere.

## 7. Strongly supported causes (not fully provable from artifacts alone)

- **S1 (STRONG EVIDENCE):** replay/mixer detectors encode the *specific* device chain (one laptop, one mobile, one mixer preset), not replay/channel processing in general — 92 files from a single chain; acoustic LR; no augmentation found anywhere in the phase 8 training path.
- **S2 (STRONG EVIDENCE):** the partial-segment model detects "AI-sounding or anomalous segment", not "fabricated region": trained target `fabricated_region` vs `outside_fabricated_region` on 1207 segments from the same corpus; it saturates on fully-AI files (Section 5.3 case data), then gating must clean up.
- **S3 (STRONG EVIDENCE):** no augmentation (noise/RIR/codec/resample) exists in the training path of the **four active release models** — none under `code/phase8/`; manifest `platform="none"` for all rows. Precision note: augmentation *does* exist in the legacy Phases 0–4 pipeline (`code/data_augmentation.py`: MUSAN noise at ~10 dB SNR 50%, RIR convolution 30%, codec simulation via 8/12/16 kHz round-trip 30%, random gain 0.8–1.2; RawBoost absent repo-wide), but that pipeline feeds only the inactive HybridResNet/AASIST lineage, not the Phase 8 sklearn axes.

## 8. Unconfirmed hypotheses

- **H1 (PLAUSIBLE HYPOTHESIS):** the sample-rate/channel class confound (AI=44.1 kHz mono, human≈48 kHz stereo) could become an active shortcut in any retrained model. Empirically it is **not** the current driver (Section 17 re-encode test), so labeled NOT SUPPORTED as a present mechanism, PLAUSIBLE as a future risk.
- **H2 (PLAUSIBLE HYPOTHESIS):** whole-file mean pooling dilutes local AI evidence on long mixed files; supported by design analysis, no controlled experiment yet.
- **H3 (COULD NOT VERIFY):** numeric equality between cached phase 8 training features and freshly extracted features for specific files (end-to-end score reproduction makes a discrepancy unlikely).
- **H4 (COULD NOT VERIFY):** identity of the TTS generator(s) used for `ai_*` recordings (manifest fields "unknown"); single-generator training is therefore likely but undocumented.

## 9. Gradio/FastAPI/PDF confidence audit

Every displayed number traces to a real model output; no constants, no `random`, no rescaling, no clamping found (searched `confidence|probability|score|placeholder|mock|fallback|round(|min(|max(|clip` across `release/`):

| Displayed field | Trace (`model output → transformation → formatting → UI`) |
|---|---|
| "Origin evidence score: 0.242" | `predict_proba[0,1]` → none → `f"...{float(prob):.3f}"` (`app_report_formatting.py:680`) → main card + PDF |
| Axis "Evidence score: x.xxx" | axis probability → none → `:497` → evidence cards |
| Segment table "Evidence score" 1.000 | per-segment `predict_proba` → none → `.3f` → table/PDF (saturation, F5 — looks hardcoded, is not) |
| "Max segment score: 1.000" | max of segment probs → none → `.3f` |
| Status texts ("Detected", "Manual review recommended", explanations) | threshold/strength branching → fixed strings (by design) |
| Technical-details thresholds 0.5/0.9/0.25/0.45 | static `partial_report_contract.json` echo — config, not a measurement |
| "evidence_sources: aasist_shadow, hybrid_resnet_shadow" | **registry status, not execution → F7 (misleading)** |

UI vs PDF vs JSON: all rendered from one response dict; recorded HTML report values match JSON values. NaN handling: axis exceptions yield `prediction_error`/"Unavailable", **not** "No AI Detected"; model-load failure yields "Inconclusive" (`app_report_formatting.py:668-678`). Threshold comparison is `>=` consistently (`inference_pipeline.py:105`, `_file_axis_strength:41-49`).

Wording audit: "Evidence score"/"Origin evidence score" are uncalibrated raw scores presented with 3-decimal precision; the term "confidence_text" appears in the schema. Recommended future wording: "uncalibrated model score" now, "calibrated probability" only after calibration; an explicit **Inconclusive / Insufficient evidence** output already partially exists (`inconclusive_under_processing`) and should be extended to OOD inputs, very short/noisy audio, and component failures.

**Verdict on the user's concern:** hardcoded/fabricated confidence — **NOT SUPPORTED**; misleading presentation (saturated scores, static threshold echo, phantom ensemble sources, contradictory partial panel) — **CONFIRMED** (F5–F7).

## 10. Model artifact and registry audit

Active artifacts (loader: `release/src/model_loader.py`, paths: `release/config/model_paths.yaml`):

| Artifact | SHA-256 | Size | mtime | classes_ | n_features_in_ | selected k | Saved th |
|---|---|---|---|---|---|---|---|
| `origin/origin_file_model__ssl__experimental.joblib` | `f9ef0774…b5780` | 56,477 | 2026-05-29 16:54:20 | [0,1] | 768 | 50 | 0.20 |
| `replay/replay_file_model__acoustic__experimental.joblib` | `2f3bb466…a20f7c3` | 7,053 | 2026-05-29 16:54:20 | [0,1] | 59 | 50 | 0.65 |
| `mixer/mixer_file_model__acoustic__experimental.joblib` | `9745c3b3…fd671d2e` | 7,053 | 2026-05-29 16:54:20 | [0,1] | 59 | 50 | 0.75 |
| `partial_segment/partial_segment_model__combined__experimental.joblib` | `97cfbb8a…a537d20` | 59,005 | 2026-05-29 16:54:23 | [0,1] | 796 | 75 | 0.50 |

- Class polarity: `classes_=[0,1]`, code reads `predict_proba[:,1]`, metadata maps 1 → positive (ai_synthetic / replay / mixer / fabricated). **Correct; no inversion or double inversion found.**
- Runtime threshold = metadata `threshold_candidate` (`get_threshold`); no source-code constant overrides found.
- No stale/duplicate active artifacts: one joblib per axis; the `partial_fabrication_experimental_p5b` package (file gate + localizer v2) exists but is intentionally **not** loaded by the active 4-model path (documented in `final_active_model_classifier_types_report.md`); the legacy `partial_segment` model is the one actually used — consistent but worth flagging as a naming/“deprecated yet active” confusion.
- Reference AASIST (`aasist_l_official_pretrained_reference.pth`, plus base variant) and HybridResNet checkpoints present, status reject_for_now/shadow; not loaded in inference.
- Exception audit: model-axis failures degrade to `prediction_error`/`not_evaluated` (no silent "human" default — NOT SUPPORTED); broad `except Exception` blocks exist around visualization/PDF (cosmetic) and resampling (F11).

## 11. Training/inference parity audit

Verified identical between phase 8 training utilities and release: 16 kHz target, librosa resample (same env/backend), mono downmix logic, WavLM-base-plus last-hidden-state mean pooling, feature schema enforcement via fit-time names, scaler/imputer embedded in the serialized pipelines. Differences: float64 (release) vs float32 (training) waveform dtype; conditional peak-normalization in release only (inert for peak≤1 input). 3× repeated full-pipeline runs byte-identical scores → deterministic. **No material parity defect.** (Cache-vs-fresh numeric diff: COULD NOT VERIFY, low risk — Section 8 H3.)

## 12. Dataset composition and effective sample size

Corpus `phase7c1` (the only training source for all active models): 184 files = 23 sessions ("speakers") × 8 conditions; per-axis training subsets: origin 46 (clean only), replay 92 (clean vs replayed), mixer 92 (clean vs mixer), partial 1207 segments (from the same recordings). Durations ~17–66 s; scripts: 3 fixed texts (English / Urdu / mixed; `data/phase7c1/Files save names.md`); generator, language, gender metadata: "unknown"; device chains: exactly one replay chain and one mixer chain; AI sources 44.1 kHz mono, human mostly 48 kHz stereo. **Effective independent units: 23 base sessions** — not 184, and certainly not 1207.

## 13. Leakage and shortcut-learning audit

- **Fold leakage (CONFIRMED, F2):** per-file group IDs; 44/46 bases (replay, mixer) and 20/23 sessions (origin) straddle folds.
- **Split reuse (CONFIRMED, F3):** release manual tests = training files (hash-proven).
- **Threshold-on-eval (CONFIRMED, F8).**
- **Shortcut candidates:** sample-rate/channel confound CONFIRMED as a dataset property; NOT SUPPORTED as the current predictive mechanism (re-encode invariance, Section 17). Same-script/same-speaker pairing across classes is structural (every AI file reads the same script as its paired human file) — mitigates content shortcuts but maximizes session leakage under F2.
- Duplicates: the audited byte-identical pair was upload-vs-corpus (expected); no intra-corpus duplicate scan was run (COULD NOT VERIFY; low value given known construction).
- Label quality: `ai_fabricated` files carry sidecar-derived `suspicious_start/end` timestamps (e.g., 18.024–27.818 s of 66.1 s ≈ 15%); units seconds; no out-of-duration values observed in sampled rows; full timestamp validation **COULD NOT VERIFY** within audit scope.

## 14. Evaluation and threshold audit (reconstructed from raw predictions)

From `phase8e1_out_of_fold_predictions.csv` at the frozen release thresholds (n behind every cell shown; leakage caveat F2 applies to all):

| Model (release feature set) | n | TP | TN | FP | FN | FNR | FPR |
|---|---|---|---|---|---|---|---|
| origin/ssl @0.20 | 46 | 23 | 23 | 0 | 0 | 0.000 | 0.000 |
| replay/acoustic @0.65 | 92 | 45 | 46 | 0 | 1 | 0.022 | 0.000 |
| mixer/acoustic @0.75 | 92 | 46 | 46 | 0 | 0 | 0.000 | 0.000 |

Versus the same released origin model on its *own corpus's processed-AI conditions* (Section 5.3): replayed-AI FNR **1.00**, mixer-AI FNR **0.22**. This is the complete quantitative explanation of "good on paper, wrong in release": the paper numbers exclude processed AI from the origin task, leak sessions across folds, and use the training distribution as the test. Confidence intervals: with 23 positives, even a true 0/23 observed FNR has a 95% upper bound ≈ 14.8% (rule of three) — the reported "100%" was never statistically meaningful.

Partial axis packaged holdout (P5F): recall 0.70 on 10 `fabricated_20pct` files, 2 false positives on 25 non-partial files, top-5 localization hit rate 1.0 when detected (`partial_validation_summary.json`) — small-n, and the 10 test fabrications mirror the training fabrication recipe. P5D and P5F reports both conclude "release packaging acceptable: NO" for the partial module (`reports/phase9/partial_redesign/phase9d_p5d/…`, `…p5f/…`), yet the demo shipped with the mapped partial contract.

Additional documented context that masked F1: the Phase 9E-P3 release regression (`phase9e_p3_release_correctness_report.md`, 184 files) reports `ai_mixer_mixer_detect_rate = 1.0` and `ai_replayed_replay_detect_rate = 1.0` — i.e., the *manipulation* axes pass on processed AI, which lets the overall report read as PASS while the *origin* axis silently scores those same files as non-AI (documented separately in P4A; see §5.3). Fusion summary across 184 files: `manual_review_required` for 164/184 (`phase8g_fusion_summary.md`) — the system routes nearly everything to manual review, which is the operational symptom of axes that cannot decide.

## 15. Calibration audit (no calibrator fitted)

- OOF Brier: origin 0.0010, replay 0.0197, mixer 0.0121; fraction of probabilities outside [0.05, 0.95]: 91% / 90% / 84%. In-domain reliability tables are uninformative (n≤92, all-but-one correct, leakage-inflated); ECE in-domain ≈ 0 by construction and should not be quoted.
- Under distribution shift the same scores collapse to confident wrongness (replayed AI median 0.031 — "confidently human"). **Calibration is required but insufficient alone**: no post-hoc map fixes a feature space where replayed AI sits inside the human cluster. Needed: calibrated probabilities on a grouped dev set + explicit OOD/inconclusive handling + band wording instead of 3-decimal scores.

## 16. Partial-fabrication root-cause analysis

Confirmed mechanics (code-level): within-file percentile/max-norm features force relative anomalies (F9); 4 s windows with 2 s hop set the localization resolution to ≥2 s, diluting sub-second edits (a 0.5 s insert is ≤12.5% of any window); aggregation is max + top-k contrast metrics with hard gates (hsf ≥0.60 → broad → suppressed; `inference_pipeline.py:300-318`); replay/mixer arbitration then blocks fusion (F10); mean-style dilution is *not* the issue — suppression-by-gating is. Training partials are a single recipe (~15–20% inserted spans, sidecar timestamps), so thresholds and gates are tuned to one easy attack family. No VAD/trimming, so timestamp drift risks are minimal (good).

Comparison of paths (from existing predictions only): localizer alone ranks true regions well when it fires (top-5 hit rate 1.0 on detected positives, P5F); current cascade loses 3/10 positives at the file gate stage and silences candidates under replay/mixer context (both recorded cases). An oracle gate would have surfaced candidates in both gradio cases; this is analysis only.

Future controlled experiment matrix (design only): fake fraction {1, 2, 5, 10, 20, 40, 60, 100}% × span length {0.1, 0.25, 0.5, 1, 2, 4, 8+} s × position {begin, middle, end, window-boundary, multiple} × segment duration {0.5, 1, 2, 4 s, multi-resolution} × overlap {0, 25, 50, 75}% × aggregator {mean, max, top-k mean, percentile, noisy-OR, MIL, attention pooling, count-above-threshold}. Aggregator expectations: mean — robust, insensitive to short spans; max — sensitive but FP-prone and saturation-fragile; top-k/percentile — best simple trade-off; noisy-OR — principled but needs calibrated per-segment probabilities; MIL/attention — best sensitivity-FPR trade-off, needs segment labels and GPU training (feasible at 6 GB with frozen SSL front end). Metrics to adopt: segment/frame precision-recall-F1, IoU, event-level F1 with declared collars (e.g., ±0.5 s), onset/offset error, and file-level detection rate stratified by fake fraction and span length.

## 17. Resampling analysis and proposed ablation

Inventory of resampling operations: exactly two code sites — training `phase8d_ssl_utils.py:189-201` and release `audio_io.py:42-54`, both single-pass `librosa.resample(native→16000)` with linear-interp silent fallback (F11); acoustic features are computed on the already-16 kHz signal; WavLM requires 16 kHz; timestamps are computed post-resample (consistent); no down-then-up chains; normalization is conditional and effectively inert.

Empirical test (release model, release code path): re-encoding `human_001_clean`, `ai_001_direct`, `ai_001_replay` through 44.1 kHz-mono and 48 kHz before analysis changes origin scores by <1e-4 (0.0003/0.9990/0.0114 in all variants). **Changing the resampling value is rejected as a fix for the observed false negatives** — the information the model loses under replay/mixer is destroyed by the acoustic channel, not by the resampler. NOT SUPPORTED: resampler-artifact shortcut as current mechanism; CONFIRMED: 16 kHz processing discards all >8 kHz content, which literature shows carries useful synthesis/channel cues.

Proposed (not executed) ablation, holding split/model/threshold/preprocessing fixed except the front end: native inspection; native→{8, 12, 16, 22.05, 24} kHz; native 44.1/48 kHz acoustic-feature branch; 8→16 upsample; 16→8→16 round-trip; librosa-soxr vs torchaudio vs scipy backends; single vs repeated resampling. Accept a change only on improved unseen-condition recall without FP inflation and with a verified absence of rate-label shortcuts. The scientifically promising variant is **dual-resolution**: keep the 16 kHz SSL branch, add a native-rate high-band acoustic branch (8–22 kHz energy/LFCC) for the replay/mixer axes, late-fuse after calibration — low VRAM cost, directly targets channel signatures.

## 18. Replay-detection analysis

Replay is genuinely trained and evaluated, but on **one** playback chain (laptop speaker → mobile mic, one room) — no diversity in speakers/devices/distances/rooms/volume/compression-after-replay; `human_replay` hard negatives are correctly included (46 replay positives = 23 AI + 23 human; replay axis detects the condition, not AI-ness — correct design). Consequences: replay axis likely fingerprints the chain (S1); origin axis has no replayed-AI representation at all (F1); the system's only response to replayed AI is the wording "Inconclusive under replay/channel processing" (`app_report_formatting.py:709-721`) — by design, but it converts the hardest attack into a shrug. ReplayDF-style evaluation (109 speaker-mic combos) is the reference protocol to adopt.

## 19. Generalization-gap analysis and open-world plan

Nothing outside `phase7c1` ever enters training; `testing_audios/` (Imran Khan/Trump real-fake clips, T1–T5, fabricated_20pct) is the only OOD probing and is not systematically scored/reported. Future evaluation must include: unseen TTS/VC/neural-codec generators, unseen speakers/languages/accents (note: corpus is English/Urdu scripted), unseen devices/rooms, telephone and social-media codecs (AMR/Opus/AAC/MP3 at multiple bitrates), 8 kHz band limiting, noise/reverb/gain/DRC/denoising/enhancement/source-separation laundering, time/pitch edits, single and multiple laundering chains, and modern partial-editing systems; protocols: grouped speaker-independent and parent-recording-independent splits, leave-one-generator-out, leave-one-dataset-out, cross-dataset, clean↔degraded, an external blind holdout, frozen thresholds, ≥3 seeds, and confidence intervals on every figure. Hard genuine negatives to add: studio, telephone, noisy, enhanced/denoised, neural-codec-passed human speech, accented/emotional/whispered speech, very short utterances, long silence, non-speech. Add OOD detection and an explicit Inconclusive state rather than forcing binary outputs.

## 20. Literature review (through 2026-06-12)

Local `research_article/` holdings reviewed (titles): Yi et al., "Audio Deepfake Detection: A Survey" (IEEE, 2023); Zhang et al., "Audio Deepfake Detection: What Has Been Achieved and What Lies Ahead" (MDPI Sensors, 2025); Khan et al., multimedia deepfake survey (Discover Computing, 2025); Li/Chen/Wei, "Where are We in Audio Deepfake Detection?" (ACM); Ahmadiadli et al., "Beyond Identity: Generalizable Deepfake Audio Detection"; Yang/Sun/Lyu/Rose, "Forensic deepfake audio detection using segmental speech features" (arXiv:2505.13847); Tahaoglu et al., spectral+ResNeXt (Knowledge-Based Systems); Kulangareth et al., speech-pause patterns (JMIR); Kawa et al., "Improved DeepFake Detection Using Whisper Features" (Interspeech 2023). None of these is integrated into the active pipeline.

External, verified this audit:

- **Müller et al., "Replay Attacks Against Audio Deepfake Detection", Interspeech 2025** (doi:10.21437/Interspeech.2025-20; ReplayDF dataset): replay makes spoofs appear bona fide; W2V2-AASIST EER 4.7%→18.2%; RIR-augmented retraining recovers to 11.0%; *plain noise augmentation does not help*. Directly explains F1. Cross-domain evidence; training feasible at 6 GB with frozen front ends. **Prioritize.**
- **Tak et al., "RawBoost", ICASSP 2022**: data-free convolutive/impulsive/stationary noise augmentation; ~27% relative gain on ASVspoof 2021 LA. CPU-cheap. **Prioritize.**
- **Sun et al., "AI-Synthesized Voice Detection Using Neural Vocoder Artifacts", CVPR-W 2023**: vocoder-artifact cues; explicit resampling/noise augmentation for robustness. **Investigate** (supports Section 17 augmentation-not-constant conclusion).
- **Zhong et al., "Boundary-aware Attention Mechanism (BAM)", Interspeech 2024** (doi:10.21437/Interspeech.2024-587): PartialSpoof frame-level SOTA (WavLM front end). **Investigate** for partial redesign; 6 GB feasible with frozen SSL.
- **BFC-Net (Neurocomputing, 2025)**: boundary-frame graph attention, improves on BAM. Investigate.
- **TDL / SAL / CFPRF / "Manipulated Regions Localization… Survey" (arXiv:2506.14396)**: temporal localization methods and survey; PartialSpoof segment EER down to ~3.6%, cross-domain transfer demonstrated (TDL 11.2% EER on LAV-DF). Investigate; the survey's warning that boundary-artifact reliance fails on artifact-free splices applies directly to FASSD's training recipe.
- **HQ-MPSD (2025)**: high-quality multilingual partial dataset with linguistically coherent splices; SOTA models drop sharply — realistic difficulty calibration for FASSD claims. Investigate for evaluation.
- **High-resolution (44.1 kHz) fullband-subband detection (arXiv 2025)**: >8 kHz subbands carry complementary forgery cues; supports the dual-resolution proposal, not a 16 kHz constant change.
- **Datasets/challenges for future evaluation:** ASVspoof 2019 LA, ASVspoof 2021 LA/DF, ASVspoof 5 (Interspeech 2024 launch; official evaluation plan at asvspoof.org), PartialSpoof, ADD 2023 Track 2, MLAAD, In-the-Wild, ReplayDF, CodecFake. **SAFE Challenge, RADAR Challenge 2026, AUDETER, "Audio Unified Deepfake Detection Benchmark Toolkit": COULD NOT VERIFY primary documentation within this audit window** — listed for follow-up, not cited as evidence.
- **Uncertainty/deployment:** temperature scaling / isotonic calibration with ECE+Brier reporting; selective prediction with risk-coverage curves; lightweight deep ensembles over frozen-embedding heads; open-set/OOD scoring (e.g., distance-based on SSL embeddings). All 6 GB-feasible; all currently absent from FASSD.

No technique above is claimed to yield a specific improvement for FASSD without a controlled experiment.

## 21. Current FASSD vs research alternatives

| Aspect | FASSD today | Field practice |
|---|---|---|
| Origin model | LR on 50/768 mean-pooled WavLM dims, 46 clean files | Fine-tuned or probed SSL (wav2vec2/WavLM/XLS-R) + AASIST-style heads, 10⁴–10⁵ utterances, heavy augmentation |
| Robustness | None (no augmentation) | RawBoost, RIR, codec, resample augmentation as default |
| Partial | 4 s window LR + relative features + gates | Frame-level boundary-aware models (BAM/TDL/SAL), PartialSpoof/ADD training, collar-based metrics |
| Replay | Single-chain acoustic LR | ReplayDF-style multi-device eval; replay treated as core threat |
| Calibration/uncertainty | None; saturated raw scores | Calibrated probabilities, selective prediction, OOD abstention |
| Evaluation | Leaked 5-fold CV on 46–92 files | Grouped, cross-dataset, leave-one-generator-out, blind holdouts, CIs |

## 22. Ranked recommendation matrix

| Priority | Recommendation | Cases addressed | Expected impact | Evidence | 6 GB feasibility | Cost | Risk | Required validation |
|---|---|---|---|---|---|---|---|---|
| P0 | Rebuild evaluation: group-aware splits on `base_id`/speaker, frozen blind holdout, per-condition recall matrix, CIs; automated leakage checker | all | High (truth recovery) | F2, F3, §14 | trivial | days | reveals worse numbers | leakage checker passes; holdout never touched until final |
| P0 | Retrain origin axis including processed-AI positives (existing ai_mixer/ai_repeat files) | complete-fake, replay | High | F1, §5.3 | yes (sklearn) | hours | still tiny data | grouped holdout FNR per condition, esp. replayed AI |
| P0 | Fix UI integrity: consistent partial state, remove phantom ensemble sources, label scores as uncalibrated | all (trust) | High (credibility) | F5–F7 | trivial | hours | none | UI/PDF/JSON consistency test on canned cases |
| P1 | Augmentation pipeline (RIR/reverb, codec round-trips, RawBoost, noise, resample round-trips) for all axes | all three | High | §20 (ReplayDF, RawBoost) | yes (CPU aug) | days | aug-domain overfit | unseen-chain replay/mixer recall; leave-one-chain-out |
| P1 | Calibration on grouped dev split + inconclusive/OOD state + band wording | all (reporting) | Medium-High | F5, §15 | trivial | days | small dev set | ECE/Brier on holdout; risk-coverage curve |
| P1 | Expand data with public corpora (ASVspoof 19/21/5, MLAAD, In-the-Wild, ReplayDF, PartialSpoof, ADD2023) at least for evaluation | all | High | §19–20 | yes | days-weeks (download/IO) | license/domain shift | cross-dataset report |
| P2 | Window-level origin scoring + top-k/MIL aggregation (reuse existing per-segment SSL embeddings) | complete + partial | Medium | H2, §16 | yes | days | FP increase | fake-fraction × span-length matrix |
| P2 | Partial redesign: drop within-file percentile features; frame/segment labels; boundary-aware or change-point method (BAM/TDL/SAL-style head on frozen WavLM) | partial | High | F9, §16, §20 | yes (frozen SSL + small head) | weeks | needs PartialSpoof access | collar-based event F1, IoU, by fake % |
| P2 | Re-derive thresholds on grouped dev data only; report operating points with CIs | all | Medium | F8 | trivial | hours | — | threshold provenance doc |
| P2 | Evaluate localizer independently of gating; redesign replay/mixer arbitration so laundering cannot silence partial evidence | partial, replay | Medium | F10 | trivial | days | FP increase | oracle-gate vs cascade comparison |
| P3 | Dual-resolution branch (16 kHz SSL + native-rate high-band acoustics) for replay/mixer | replay, mixer | Medium | §17 | yes | weeks | shortcut risk (H1) | rate-shortcut control test + ablation §17 |
| P3 | Activate AASIST / W2V2-AASIST as calibrated ensemble member after fair validation | complete-fake | Medium | §10, §20 | yes (inference); fine-tune borderline | weeks | VRAM, domain mismatch | grouped + cross-dataset eval before activation |
| P3 | OOD/anomaly branch + TRACE-style training-free trajectory analysis as auxiliary signal | all | Medium | §19–20 | yes | weeks | research maturity | selective-prediction risk-coverage |
| P3 | Larger end-to-end models | — | Low until P0–P2 done | — | borderline | high | masks root causes | only after simpler causes eliminated |

(“Use a larger model” is deliberately last.)

## 22a. Mandatory findings table

| ID | Status | Severity | Component | Evidence | Root cause | User impact | Recommended future action | Validation test |
|---|---|---|---|---|---|---|---|---|
| F1 | CONFIRMED DEFECT | Critical | origin model + training data | §5.3 sweep (0/23 replayed, 18/23 mixer); `phase8e0_origin_file_dataset.csv` all-clean | no processed-AI positives; channel destroys artifacts | replayed/processed AI shown "Not detected" | retrain with processed positives + augmentation | per-condition FNR on grouped blind holdout |
| F2 | CONFIRMED DEFECT | Critical | phase8e1 CV | per-file `source_group_id` (46/46, 92/92); 44/46 & 20/23 cross-fold siblings | group IDs not propagated from manifest | inflated "perfect" metrics | group-aware splits keyed on base_id | automated leakage assert |
| F3 | CONFIRMED DEFECT | High | release acceptance testing | SHA-256 equality upload vs train-split file (§5.1) | no holdout discipline | false sense of release readiness | blind external test set | hash audit of eval inputs vs manifests |
| F4 | CONFIRMED DEFECT | High | dataset design | manifest: 23 sessions × 8; unknown generator; single chains; rate/channel confound | scope vs collection capacity | no generalization basis | public corpora + diversified collection | dataset diversity report |
| F5 | CONFIRMED DEFECT | Medium | score reporting | 84–91% probs outside [0.05,0.95]; UI 1.000×5 | uncalibrated LR on separable tiny data | scores look fabricated | calibration + band wording | ECE/Brier + reliability on holdout |
| F6 | CONFIRMED DEFECT | Medium | Gradio/PDF partial panel | CASE-2F86E2E07B77: "Not detected" + 1.000 "Recommended" table + highlight | gate verdict not applied to table/highlight | contradictory report | single partial display state machine | snapshot consistency tests |
| F7 | CONFIRMED DEFECT | Medium | `app_report_formatting.py:649-666` | `evidence_sources` lists never-run shadow models | registry status used as execution evidence | phantom ensemble credibility | list executed models only | unit test on evidence_sources |
| F8 | CONFIRMED DEFECT | Medium | thresholds | metadata `threshold_source` = Phase 8E-1A on leaked CV | no dev/test separation | arbitrary operating points | thresholds from grouped dev only | threshold provenance doc |
| F9 | CONFIRMED DEFECT | High | partial features `feature_extraction.py:133-209` | percentile/max-norm inputs; broad activation on full-fake files | relative features force contrast | partial axis noise + gating dependence | remove relative features; frame labels | event-F1 with collars by fake % |
| F10 | CONFIRMED DEFECT | High | arbitration `inference_pipeline.py:375-409` | both recorded cases `blocked_by_replay_or_mixer_context` | hard precedence rule | laundering silences partial evidence | redesign arbitration; report both axes | oracle-gate comparison |
| F11 | CONFIRMED DEFECT | Low | `audio_io.py:49-54` | silent linear-interp resample fallback | broad except | silent front-end degradation elsewhere | surface a warning flag in response | fault-injection test |
| S1 | STRONG EVIDENCE | High | replay/mixer models | single device chain in all training data | chain fingerprinting | misses other devices/rooms | multi-chain data + augmentation | leave-one-chain-out |
| S2 | STRONG EVIDENCE | Medium | partial model target | saturation on fully-AI files | segment "fabricated" ≈ "AI-sounding" | gate dependence | redefine labels/objective | full-fake vs partial discrimination test |
| S3 | STRONG EVIDENCE | High | training pipeline | no augmentation code/manifests found | not implemented | fragility to any processing | P1 augmentation | unseen-condition recall |
| H1 | PLAUSIBLE HYPOTHESIS | Medium | dataset rates | 44.1k-mono AI vs 48k-stereo human; re-encode test negative today | collection hygiene | shortcut risk on retrain | standardize capture; control test | rate-shortcut probe |
| H2 | PLAUSIBLE HYPOTHESIS | Medium | whole-file pooling | design analysis | mean pooling dilution | weak on long mixed audio | window scoring + aggregation | fake-fraction matrix |
| H3 | COULD NOT VERIFY | Low | cached training features | not numerically diffed | — | — | optional cache diff | cosine/maxabs diff |
| H4 | COULD NOT VERIFY | Medium | generator identity | manifest "unknown" | undocumented | unknown generator coverage | document generators | metadata completion |
| N1 | NOT SUPPORTED | — | hardcoded confidence | full trace §9 | — | — | — | — |
| N2 | NOT SUPPORTED | — | train/inference preprocessing mismatch | §11 parity + exact score reproduction | — | — | — | — |
| N3 | NOT SUPPORTED | — | wrong/stale artifact loaded | §10 single-artifact registry audit | — | — | — | — |
| N4 | NOT SUPPORTED | — | exception fallback to "No AI" | §9–10 exception audit (`prediction_error`/Inconclusive) | — | — | — | — |
| N5 | NOT SUPPORTED | — | resample value causing current misses | §17 re-encode invariance | — | — | — | ablation §17 if revisited |

## 23. Mandatory root-cause tree

```
Incorrect release prediction ("No AI Detected" on AI audio)
├── Data problem  [PRIMARY — CONFIRMED]
│   ├── Origin training = 46 clean files; zero processed-AI positives (F1)
│   ├── 23 sessions, 1 replay chain, 1 mixer chain, 1 unknown generator (F4)
│   ├── No augmentation of any kind (S3)
│   └── Latent rate/channel class confound (H1)
├── Split/leakage problem  [CONFIRMED — explains "good on paper"]
│   ├── Per-file groups defeat StratifiedGroupKFold (F2)
│   ├── Release tests on byte-identical training files (F3)
│   └── Thresholds tuned on the leaked CV (F8)
├── Model problem  [CONTRIBUTING]
│   ├── LR on SelectKBest-50 of mean-pooled WavLM; memorizes tiny set
│   └── Whole-file mean pooling dilutes local evidence (H2)
├── Preprocessing problem  [RULED OUT as mismatch — N2; minor F11 fallback risk]
├── Feature/schema problem  [RULED OUT at runtime (0 missing); partial features structurally biased (F9)]
├── Threshold/calibration problem  [CONFIRMED contributing]
│   ├── Saturated uncalibrated scores (F5)
│   └── Origin th 0.20 sits inside the mixer-AI score cloud (§5.3)
├── Cascade/aggregation problem  [CONFIRMED contributing]
│   ├── Broad-activation gate discards full-file AI segment evidence
│   └── Replay/mixer arbitration silences partial axis (F10)
├── Artifact/registry problem  [RULED OUT — N3]
├── UI/report problem  [CONFIRMED presentation defects F5–F7, not score fabrication]
├── Out-of-domain input  [BY CONSTRUCTION: any processed AI is OOD for the origin model]
└── Silent exception/fallback problem  [RULED OUT for "No AI" defaults — N4; F11 latent]
```

## 24. Proposed future architecture (proposal only — not implemented)

Frozen WavLM front end (16 kHz) → per-window (1–4 s, ≥50% overlap) embeddings → (a) origin head trained with processed/augmented positives, calibrated; (b) frame/segment partial localization head with boundary-aware objective; (c) native-rate high-band acoustic branch feeding replay/mixer heads; (d) top-k/MIL file aggregation per axis; (e) calibrated late fusion that *reports* axis interactions instead of suppressing them; (f) OOD scorer on embedding space gating an explicit Inconclusive state; optional AASIST ensemble member after fair validation. All components run within 6 GB VRAM (frozen SSL inference ≈ 1–2 GB; heads are small).

## 25. Future experimental plan

1. Build leakage-safe grouped splits + blind holdout (P0) and re-baseline all current artifacts on them (expect sharp drops; publish per-condition matrix with CIs).
2. Origin retrain matrix: {clean-only vs +processed positives} × {no aug vs RIR vs codec vs RawBoost vs all} → per-condition FNR/FPR.
3. Resampling ablation per §17 (only after 1–2, since data fixes dominate).
4. Partial matrix per §16 (fake %, span, position, window, overlap, aggregator) on PartialSpoof + controlled splices; collar-based metrics.
5. Replay robustness: leave-one-chain-out with newly collected ≥3 playback chains; ReplayDF if licensable.
6. Calibration + selective prediction: reliability, ECE, Brier, risk-coverage; choose abstention operating point on dev only.
7. Final single-shot blind test on the untouched holdout; freeze and report.

## 26. Release acceptance criteria (all must hold before any future "ready" claim)

1. Release-loaded artifacts enumerated and SHA-256-hashed (done in §10; keep current).
2. Training/inference preprocessing parity verified (done §11; re-verify after changes).
3. Class mappings verified per model (done §10; re-verify).
4. No hardcoded/fabricated confidence (verified §9; keep regression test).
5. Every displayed score traceable to a model output (verified §9).
6. Scores displayed as probabilities are calibrated (currently FAILS — F5).
7. Thresholds selected on development data only (currently FAILS — F8).
8. Test data untouched during selection (currently FAILS — F3).
9. Parent recordings/augmentations cannot cross splits (currently FAILS — F2).
10. Evaluation covers complete, partial and replay cases (currently FAILS for origin axis — F1).
11. Localizer evaluated independently of gating (currently FAILS — F10/§16).
12. Results reported by file and by condition (template in §5.3/§14).
13. False-negative rates reported explicitly (currently hidden — §14).
14. Unseen generators and external data evaluated (currently FAILS — §19).
15. Genuine processed/replayed hard negatives included (partially holds — §18).
16. Partial performance reported by fake % and span duration (currently FAILS).
17. Confidence intervals reported (currently FAILS).
18. Model failures do not default to "No AI Detected" (verified holds — N4).
19. Unsupported/OOD inputs can produce "Inconclusive" (partially holds; extend per §15/§19).
20. Gradio/FastAPI/PDF labels and scores consistent (verified holds — §5.2/§9; F6 display contradiction must be fixed).
21. The `ai_mixer` failure explained with evidence (done — §5) and re-tested after fixes.
22. Final blind test completed after all fixes (pending).

## 27. Forensic wording requirements (for all future reports)

Distinguish: **detection score** (raw uncalibrated model output — everything FASSD currently shows), **calibrated probability** (does not yet exist), **decision threshold** (currently provenance-flawed, F8), **prediction** (thresholded label), **confidence** (reserve for calibrated quantities), **evidence** (axis indicators, never proof), **localization** (candidate regions with declared resolution ≥2 s), **ground-truth timestamp** (sidecar labels), **model uncertainty** (not yet measured), **OOD uncertainty** (not yet measured). The system must never claim to prove authenticity; phrases like "100% authentic", "definitely AI", or "forensically confirmed" are scientifically unjustified for this detector. The existing disclaimer wording is good; it must additionally disclose the known processed-AI miss rates until fixed.

## Evidence appendix

- Environment/commit: §3 (commands: `git status --short`, `git rev-parse`, package/CUDA probe via `python -c`).
- Artifact hashes: §10 (SHA-256 over `release/models/*/ *.joblib`).
- `ai_mixer` identity: upload temp path from CASE-DBB938B3E9FC JSON; SHA-256 `0bda38e7…8746` equals `data/phase7c1/raw/ai_mixer/ai_001_mixer_processed.wav`; soundfile info 48 kHz/2ch/57.493 s.
- Manifest membership: `phase8e0_mixer_file_dataset.csv` (split=train, targets 1/0/1); `phase7c1_collection_manifest.csv` row (speaker_001/base_001).
- Release trace: 3× `analyze_audio_file` runs — origin 0.2423626876258826, replay 0.5578262665547876, mixer 0.95352623561676, partial max 1.0/hsf 0.3929, fusion `suspicious_mixer_channel_experimental` (identical across runs).
- Sweep: release scoring loop over `data/phase7c1/raw/*` (8 conditions × 23 files) — table §5.3; mixer per-file scores listing the five sub-threshold files (ai_012/016/017/018/019).
- Re-encode test: §17 (44.1 kHz mono and 48 kHz round-trips; deltas <1e-4).
- OOF reconstruction: `phase8e1_out_of_fold_predictions.csv` → §14 confusion matrices; group cardinality (46/46, 92/92); cross-fold sibling counts (44/46, 44/46, 20/23); Brier/extremeness §15.
- Source line references: `release/src/inference_pipeline.py:104-105, 300-318, 320-337, 375-409`; `release/src/fusion_rules.py:80-120`; `release/src/feature_extraction.py:133-209`; `release/src/app_report_formatting.py:497, 634-758, 649-666, 680, 709-721`; `release/src/audio_io.py:12, 31-39, 42-54, 57-62`; `release/src/ssl_embeddings.py:14, 58-67`; `code/phase8/embeddings/phase8d_ssl_utils.py:189-201, 272-283, 300-323`; `release/config/runtime_config.yaml`; `release/models/*/ *_metadata.json` (`threshold_candidate`, `feature_names`, `target_mapping`).

## Bibliography

1. N. Müller, P. Kawa, W.-H. Choong, A. Stan, A. Tirumala Bukkapatnam, K. Pizzi, A. Wagner, P. Sperl. "Replay Attacks Against Audio Deepfake Detection." Interspeech 2025, pp. 2245–2249. doi:10.21437/Interspeech.2025-20.
2. H. Tak, M. Kamble, J. Patino, M. Todisco, N. Evans. "RawBoost: A Raw Data Boosting and Augmentation Method Applied to Automatic Speaker Verification Anti-Spoofing." ICASSP 2022.
3. C. Sun, S. Jia, S. Hou, S. Lyu. "AI-Synthesized Voice Detection Using Neural Vocoder Artifacts." CVPR Workshops 2023.
4. J. Zhong, B. Li, J. Yi. "Enhancing Partially Spoofed Audio Localization with Boundary-aware Attention Mechanism." Interspeech 2024, pp. 4838–4842. doi:10.21437/Interspeech.2024-587.
5. "BFC-Net: Boundary-Frame Cross Graph Attention Network for Partially Spoofed Audio Localization." Neurocomputing, 2025. doi:10.1016/j.neucom.2025 (S0925231225015395).
6. "Manipulated Regions Localization For Partially Deepfake Audio: A Survey." arXiv:2506.14396, 2025.
7. L. Zhang, X. Wang, E. Cooper, J. Yamagishi, et al. "PartialSpoof" database and countermeasures (IEEE/ACM TASLP 2022/2023).
8. J. Yi et al. "ADD 2023: The Second Audio Deepfake Detection Challenge" (Track 2 localization).
9. High-resolution fullband-subband singing/speech deepfake detection. arXiv:2604.04841, 2026 (44.1 kHz subband evidence).
10. J. Yi, C. Wang, J. Tao, X. Zhang, C. Y. Zhang, Y. Zhao. "Audio Deepfake Detection: A Survey." 2023. (local: research_article/1.pdf)
11. B. Zhang, H. Cui, V. Nguyen, M. Whitty. "Audio Deepfake Detection: What Has Been Achieved and What Lies Ahead." Sensors, 2025. (local: 2.pdf)
12. A. A. Khan et al. "A survey on multimedia-enabled deepfake detection…" Discover Computing 28:48, 2025. doi:10.1007/s10791-025-09550-0. (local: 3.pdf)
13. X. Li, P.-Y. Chen, W. Wei. "Where are We in Audio Deepfake Detection? A Systematic Analysis over Generative and Detection Models." ACM. (local: 4.pdf)
14. Y. Ahmadiadli, X.-P. Zhang, N. Khan. "Beyond Identity: Generalizable Deepfake Audio Detection." (local: 5.pdf)
15. T. Yang, C. Sun, S. Lyu, P. Rose. "Forensic deepfake audio detection using segmental speech features." arXiv:2505.13847, 2025. (local: 6.pdf)
16. G. Tahaoglu, D. Baracchi, D. Shullani, M. Iuliani, A. Piva. "Deepfake audio detection with spectral features and ResNeXt-based architecture." Knowledge-Based Systems. (local: 7.pdf)
17. N. V. Kulangareth, J. Kaufman, J. Oreskovic, Y. Fossat. "Investigation of Deepfake Voice Detection Using Speech Pause Patterns." JMIR. (local: 8.pdf)
18. P. Kawa, M. Plata, M. Czuba, P. Szymański, P. Syga. "Improved DeepFake Detection Using Whisper Features." Interspeech 2023. (local: 9.pdf)
19. ASVspoof consortium. ASVspoof 2019 / 2021 / ASVspoof 5 evaluation plans and summaries. https://www.asvspoof.org (ASVspoof 5: Interspeech 2024 launch; detailed review of 2025–2026 workshop material: not completed in this audit).
20. ReplayDF dataset release (with [1]); MLAAD; In-the-Wild; CodecFake — official repositories as referenced in [1] and the survey literature. (SAFE Challenge, RADAR 2026, AUDETER: primary documentation not verified in this audit window.)
