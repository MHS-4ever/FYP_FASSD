# Post-Release Findings: Root Causes of Wrong Results and Researched Improvement Options

Date: 2026-06-12
Status: research document only — no code or model changes were made.
Scope: investigates (1) why the release shows "no AI detected" on AI audio it was nominally trained on, (2) the partial-fabrication problems, (3) whether Gradio shows hardcoded values, (4) the supervisor's resampling suggestion, and (5) all other problems found, with a ranked list of the most beneficial fixes.

---

## 1. Executive summary

The release is behaving exactly as its training data forces it to behave. The headline problems are:

1. **The origin (AI-vs-human) model has a 100% miss rate on replayed AI audio and a 22% miss rate on mixer-processed AI audio.** I re-ran the released origin model over every file in the `data/phase7c1/raw` training corpus (see Section 3). All 23 `ai_repeat` (replayed AI) files score far below the 0.2 threshold (median 0.031). This is not a one-off glitch with `ai_001_replay_laptop_mobile.wav` — it is systematic.
2. **The root cause is training data composition, not a bug.** The active origin model is a logistic regression trained on only **46 files (23 clean AI + 23 clean human)** — zero replayed or mixer-processed AI examples. Replay/mixer processing physically destroys the vocoder artifacts the model keys on, so processed AI lands in the "human" region of its feature space. This failure mode is well documented in the literature (Interspeech 2025 "Replay Attacks Against Audio Deepfake Detection": a state-of-the-art W2V2-AASIST detector's EER jumps from 4.7% to 18.2% under replay).
3. **The "good on-paper results" are an artifact of evaluating a tiny, homogeneous dataset with cross-validation.** The reported 100% accuracy / 1.0 AUC for the origin SSL model (`reports/phase8/models/phase8e1/phase8e1_metrics_summary.csv`) was measured on the same 46 clean files via 5-fold CV. No unseen speaker, no unseen TTS engine, no unseen processing chain, no unseen recording device was ever tested. Worse, the files used for manual release testing (e.g., `ai_001_replay_laptop_mobile.wav`) are literally training files for the replay/mixer axes, so even those "passing" axes have never demonstrated generalization.
4. **Gradio does not display hardcoded confidences — but several displayed numbers look hardcoded because the models are uncalibrated and saturate.** "Evidence score: 1.000" on every candidate segment, and identical scores across files, are real (saturated) logistic-regression outputs, not constants. There are, however, genuinely static displays (threshold lists, fixed wording) and a contradictory UI that makes results look wrong (Section 5).
5. **The partial-fabrication module has a structural feature design flaw**: several of its input features are within-file percentiles/max-normalized scores that by construction make some segments look anomalous in any file, even a perfectly clean one. Combined with saturation this produces the "all segments p=1.000, broad activation, then gated away" behavior seen in the case JSONs (Section 6).
6. **Changing the resampling value alone will not fix the misses.** I tested this empirically: re-encoding the same audio through 44.1 kHz and 48 kHz before analysis changes the origin score by less than 0.0001 (Section 7). The 16 kHz target is dictated by WavLM and matches training, so there is no train/inference resampling mismatch. The literature does support a *related* idea — high-frequency (>8 kHz) band features are discriminative and are currently being thrown away — but the highest-yield fixes are data-centric (augmentation + more data), not the resample constant.

The most beneficial path forward, in order: **(1) retrain the origin axis with processed-AI positives and heavy augmentation (replay/RIR, codec, RawBoost-style noise), (2) build an honest evaluation protocol (speaker/condition-disjoint, never reuse training files), (3) calibrate probabilities and fix the contradictory Gradio displays, (4) redesign the partial-fabrication features and evaluation, (5) only then consider stronger models (fine-tuned SSL + AASIST ensemble).** Details and effort estimates in Section 8.

---

## 2. How the release actually works (verified from code and artifacts)

All four active "models" are scikit-learn pipelines ending in **logistic regression** (`SimpleImputer → VarianceThreshold → StandardScaler → SelectKBest → LogisticRegression(l2, balanced, liblinear)`), confirmed by deserializing the joblib artifacts (`reports/phase9/final_release/final_active_model_classifier_types_report.md`):

| Axis | Features in | Selected | Training rows | Threshold | Training data |
|---|---|---|---|---|---|
| Origin (AI vs human) | 768 WavLM file-level dims | 50 | **46 files** | 0.20 | `phase8e0_origin_file_dataset.csv` — clean files only |
| Replay | 59 acoustic | 50 | 92 files | 0.65 | clean vs replayed (both human and AI) |
| Mixer/channel | 59 acoustic | 50 | 92 files | 0.75 | clean vs mixer-processed |
| Partial segment | 796 combined (acoustic + SSL + localization) | 75 | 1207 segments | 0.50 | phase8e2/8e3 segment tables |

Inference (`release/src/inference_pipeline.py`): audio → mono → resample to 16 kHz (`release/src/audio_io.py`, librosa) → whole-file WavLM-base-plus mean-pooled embedding (`release/src/ssl_embeddings.py` via `code/phase8/embeddings/phase8d_ssl_utils.py`) + 59 acoustic features → the three file-level axes; 4 s / 2 s-hop segments → segment features → partial model → localization gating → fusion (`release/src/fusion_rules.py` + Phase 8F rules).

Key structural observations:

- The origin model sees **one mean-pooled embedding of the entire file**. For a 56 s file, everything is averaged into a single 768-dim vector; local AI artifacts get diluted, and the global channel signature dominates.
- `SelectKBest(f_classif, k=50)` selected the 50 dims most separating 23 vs 23 *clean* files. Those dims encode whatever was easiest on that tiny set, which need not survive any processing.
- The training corpus (`data/phase7c1/raw/`) is one controlled recording protocol: 23 paired sessions reading the same 3 scripts (`data/phase7c1/Files save names.md`), one replay chain ("laptop→mobile"), one mixer chain. Every condition has exactly 23 files.

---

## 3. Empirical verification: the misclassification is systematic, not anecdotal

### 3.1 Case JSONs from the user's own Gradio runs

- `ai_001_replay_laptop_mobile.wav` (AI, replayed): origin probability **0.011** (threshold 0.2) → UI shows "AI-origin evidence: Not detected" and "Voice origin: Inconclusive under replay/channel processing" (`release/gradio_outputs/json/CASE-2F86E2E07B77_analysis.json`).
- `ai_001_mixer_processed.wav` (AI, mixer): origin probability **0.242** — barely above 0.2. A small shift in recording conditions would flip it to "no AI detected" (`CASE-DBB938B3E9FC_analysis.json`).

### 3.2 Full sweep of the released origin model over all phase7c1 conditions

I scored every `data/phase7c1/raw` file with the released origin pipeline (same code path as the app: `load_audio` → WavLM mean-pool → `origin_file_model__ssl__experimental.joblib`). Threshold = 0.2:

| Condition | n | min | median | max | flagged as AI |
|---|---|---|---|---|---|
| ai_direct (clean AI) | 23 | 0.965 | 0.999 | 1.000 | **23/23** |
| ai_fabricated | 23 | 0.875 | 0.997 | 0.999 | **23/23** |
| ai_mixer | 23 | 0.034 | 0.634 | 0.904 | **18/23** |
| ai_repeat (replayed AI) | 23 | 0.001 | 0.031 | 0.107 | **0/23** |
| human_clean | 23 | 0.000 | 0.003 | 0.042 | 0/23 |
| human_fabricated | 23 | 0.001 | 0.012 | 0.092 | 0/23 |
| human_mixer | 23 | 0.000 | 0.000 | 0.005 | 0/23 |
| human_replay | 23 | 0.000 | 0.000 | 0.007 | 0/23 |

Interpretation:

- **Replay completely defeats the origin model** (0/23). The user's observation generalizes: *any* replayed AI clip will be called "no AI" by the origin axis.
- **Mixer processing defeats it for ~1 in 4 files** (5/23 missed; median drops from 0.999 to 0.634). This matches the user's recollection of an `ai_mixer` file showing "no AI detected".
- Human files are never false-flagged — consistent with the literature finding that replay/processing pushes everything toward the "bona fide" side (it removes synthesis artifacts; it cannot add them).
- Scores on clean AI saturate at ~1.0 because these are training files; this is also why displayed scores look "hardcoded" (Section 5).

Note these are **training-distribution files** — performance on genuinely unseen audio (different TTS engine, speaker, language, device) will be *worse* than this table. The `testing_audios/old/` trials (Imran Khan / Trump real-vs-fake clips, T1–T5 sets) are the only out-of-distribution probes in the repo, and they were what originally motivated the multi-axis "evidence indicator" reframing.

### 3.3 Resampling provenance test (supervisor's hypothesis)

A plausible mechanism would have been: AI training clips are 44.1 kHz mono while human ones are 48 kHz stereo (true in `phase7c1` — `ai_direct` is 23×44.1 kHz/mono, `human_clean` is mostly 48 kHz/stereo), so the model might key on the resampling signature rather than voice origin. I tested this by re-encoding the same files through 44.1 kHz mono and 48 kHz before scoring:

| File | as-is | re-encoded 44.1k mono | re-encoded 48k |
|---|---|---|---|
| human_001_clean (human) | 0.0003 | 0.0003 | 0.0003 |
| ai_001_direct (AI clean) | 0.9990 | 0.9990 | 0.9990 |
| ai_001_replay (AI replayed) | 0.0114 | 0.0114 | 0.0114 |

The scores are unchanged to 4 decimal places. **The model is not reacting to resampling provenance, and changing the resample target will not rescue replayed/processed AI.** What the model loses under replay is the *content* above the noise floor of the replay chain (loudspeaker + room + microphone smear the spectro-temporal vocoder artifacts), which no resampling constant restores. The sample-rate confound in the training data is still worth fixing for hygiene (Section 8.2), but it is not the active failure mechanism.

---

## 4. Root causes, ranked

**RC1 — Origin training data contains zero processed AI (decisive).**
`phase8e0_origin_file_dataset.csv`: 46 rows, `known_manipulation_labels` = "clean" for all. The model has never seen what AI sounds like after a loudspeaker/microphone pass or a mixer chain. Replayed AI is out-of-distribution and falls on the human side. This single fact explains the user's complaint.

**RC2 — Dataset is far too small and homogeneous for the claimed task.**
23 paired sessions, same 3 scripts, ~1 replay chain, ~1 mixer chain, one TTS source. Logistic regression with SelectKBest can perfectly separate 46 such files (CV accuracy 1.0, AUC 1.0, Brier 0.001) without learning anything transferable. The paper-vs-practice gap the user senses is exactly this: **cross-validation on 46 homogeneous files measures memorization, not detection.**

**RC3 — Release testing reuses training files.**
`ai_001_replay_laptop_mobile.wav` and `ai_001_direct.wav` appear verbatim in `phase8e0_replay_file_dataset.csv`. The replay axis scoring 0.996 on that file is a train-set prediction, not evidence the replay detector works. There is currently no honest held-out set in the release path.

**RC4 — No augmentation anywhere in training.**
No RIR/reverb, no codec (MP3/AAC/Opus), no noise, no RawBoost-style channel simulation. Every robustness technique standard in the anti-spoofing field is absent, which is why a single WhatsApp pass or replay flips results.

**RC5 — Uncalibrated, saturated probabilities.**
Brier-optimal logistic regression on separable tiny data outputs 0.000/1.000. Hence "Evidence score: 1.000" on five segments at once, "0.011", "0.9990" — numbers that look fake/hardcoded to users and cannot express uncertainty.

**RC6 — Partial-fabrication features guarantee false structure (Section 6).**

**RC7 — Fusion wording masks failure as caution.**
When replay is detected and origin is low, `build_voice_origin_result` (`release/src/app_report_formatting.py` lines 709–721) deliberately reports "Inconclusive under replay/channel processing" instead of "likely human". That is defensible forensic wording, but the *origin axis card* still shows "Not detected", and the overall impression for an AI file is "no AI". The honesty layer cannot compensate for a detector that genuinely cannot see replayed AI.

---

## 5. The "hardcoded values" question (Gradio)

I audited `release/app_gradio.py`, `release/src/app_report_formatting.py`, `release/src/pdf_report_generator.py` and the generated HTML/JSON outputs. Findings:

**Not hardcoded (but looks like it):**
- "Evidence score: 0.011 / 0.996 / 0.106" and "Max segment score: 1.000" are live `predict_proba` outputs formatted in `app_report_formatting.py` (`score_text = f"Evidence score: {prob:.3f}"`). They *look* canned because the models saturate (RC5) — e.g., five segments all displaying exactly **1.000** in the suspicious-segments table.
- "Origin evidence score: 0.011" in the main card is the same live probability.

**Genuinely static/hardcoded displays:**
- The threshold block in "Technical details" (`file_gate_threshold: 0.5`, `segment_threshold: 0.9`, `contrast_threshold: 0.25`, `broad_limit: 0.45`) comes from the packaged `partial_report_contract.json` — fixed config echoed on every analysis, regardless of file.
- All user-facing sentences ("Replay/rerecording evidence was detected.", "Manual review recommended.", limitation lists) are fixed strings selected by branching — by design, but it contributes to the "every report looks the same" feeling.
- `evidence_sources` always lists `aasist_shadow` and `hybrid_resnet_shadow` as if they contributed, but they are **never run** in the active path ("shadow_runnable" status only). Displaying them under "ensemble_if_available" is misleading.

**Contradictory display (the real UX bug):** for the replayed-AI case the same report shows:
- "Partial replacement evidence: **Not detected**" (severity *clear*), and directly below it "Max segment score: **1.000**";
- a "Suspicious segments for review" table with five segments at 1.000, all marked "Recommended";
- "Highlighted evidence region: 00:32 – 00:36" in the main card while the partial card says nothing was detected.

This is the gating logic (broad-activation → not localized → "not detected") leaking inconsistently into the UI. A user reasonably concludes the numbers are fake or the app is broken.

---

## 6. Partial-fabrication module: why it misbehaves and what to do differently

### Observed behavior
On fully-AI replayed audio, 21/28 segments score ≥0.9 (many exactly 1.0), triggering `broad_activation_warning`, the `global_activation_not_localized` gate, and the replay/mixer arbitration block — so the axis reports "Not detected" while the table shows saturated candidates. On the P5F holdout the documented numbers are: `fabricated_20pct_recall = 0.70` (3/10 false negatives), 2 false positives on non-partial files (`release/models/partial_fabrication_experimental_p5b/partial_validation_summary.json`).

### Structural causes
1. **Relative within-file features force contrast.** `compute_live_localization_features` (`release/src/feature_extraction.py` lines 133–209) feeds the model `*_deviation_percentile_within_file` (always spans 0→1 by definition of a percentile rank) and `within_file_*_deviation_score` (always max-normalized so some segment = 1.0). In *any* file — clean, fully fake, or partial — some segments mathematically look maximally deviant. The model was trained where these features correlated with fabricated regions; at inference they fire on natural variation (pauses, emphasis) and on globally-processed audio.
2. **The model conflates "AI-sounding segment" with "fabricated region".** Trained per-segment with target `fabricated_region`, it activates on every segment of a fully-AI file — correct from its perspective, then discarded by the broad-activation gate. The gate is a patch over a target-definition problem.
3. **Saturation again**: p=1.0 on 5+ segments gives ranking no discriminative value (`topk_minus_rest` = 0.28 driven by the few low segments).
4. **4 s / 2 s hop granularity** is coarse versus the field's frame-level (~20–160 ms) localization standards.

### What the field does instead (research options)
- **Boundary/transition-centric models**: BAM (Boundary-aware Attention, Interspeech 2024) — boundary enhancement + frame-wise attention on WavLM features; best PartialSpoof results (segment EER ~3.6%, F1 0.96). BFC-Net (2025) improves with boundary-frame graph attention. TDL (Temporal Deepfake Location, wav2vec2-XLSR + contrastive embedding) transfers across datasets (11.2% EER on LAV-DF trained on PartialSpoof).
- **Segment-Aware Learning (SAL)**: models intrinsic segment characteristics with positional labels and cross-segment mixing augmentation — addresses exactly the "boundary artifacts are a shortcut" criticism.
- **Change-point detection on SSL trajectories** (lightweight, no retraining): detect discontinuities in frame-level WavLM embedding sequences (e.g., kernel change-point/CUSUM) instead of classifying absolutely-scored 4 s windows; splices show up as embedding jumps. This fits the existing frozen-WavLM design and could replace the fragile percentile features.
- **Datasets**: PartialSpoof (segment labels, standard benchmark), ADD2023 Track 2, HQ-MPSD (2025, linguistically coherent splice points — much harder and closer to real attacks). Training/evaluating on ~10 self-made `fabricated_20pct` files cannot support any reliability claim (already acknowledged in `partial_module_metadata`).

### Concrete redesign recommendation (for the doc's ranked list)
Replace per-segment absolute classification with: (a) frame-level scores from the origin-style model on short windows, (b) change-point detection on the SSL frame sequence for boundary candidates, (c) report a region only when both agree; train/evaluate on PartialSpoof + self-made splices with timestamps; remove the within-file percentile features entirely or use them only as *diagnostics*, never as model inputs.

---

## 7. The resampling question, answered thoroughly

**Current state:** everything (training Phase 8D extraction and release `audio_io.py`) targets 16 kHz mono via `librosa.resample` (soxr); no train/inference mismatch exists. WavLM-base-plus *requires* 16 kHz input, so the SSL path cannot simply run at another rate.

**Empirical result (Section 3.3):** re-encoding through 44.1/48 kHz changes origin scores by <1e-4. The resample constant is not the failure mechanism.

**What the literature says about sample rates:**
- 16 kHz processing discards everything above 8 kHz. High-frequency bands carry vocoder fingerprints, extended harmonics and breath textures that are highly discriminative; high-resolution (44.1 kHz) detectors significantly outperform 16 kHz models when artifacts live up there (2025 fullband/subband SVDD work; CVPR-W 2023 vocoder-artifact detection).
- Neural vocoders leave characteristic **upsampling/aliasing artifacts** at specific frequencies tied to their internal upsampling factors; resampling can shift/erase these — one reason detectors should not rely on them exclusively.
- Replay attacks (the actual problem here) destroy artifacts across the band; RIR-augmented retraining recovers only part of the loss (EER 18.2%→11.0% vs 4.7% baseline, Interspeech 2025). No resampling choice fixes replay.

**Where a resampling-related change genuinely could help (worth telling the supervisor):**
1. **Keep 16 kHz for WavLM, but add a parallel high-band feature branch at the native rate** (e.g., 32/44.1/48 kHz log-mel or LFCC restricted to 8–22 kHz) for the *replay and mixer axes*. Replay chains have strong high-frequency signatures (speaker rolloff, room response, device noise floor); the current 59 acoustic features are computed after 16 kHz downsampling (`extract_file_acoustic_features` receives the already-resampled signal), so `high_band_energy_ratio` etc. only see ≤8 kHz. This is the strongest version of the supervisor's idea.
2. **Record/keep originals at native rate** in any new data collection so the high-band branch is trainable.
3. **Resampling as augmentation, not as a constant**: randomly round-trip training audio through 8/22.05/32/44.1 kHz (and codecs) so models stop keying on any specific band-limiting signature (CVPR-W 2023 used exactly this and stayed robust to resampling).
4. **Fix the dataset hygiene confound**: standardize capture so AI and human classes don't differ systematically in native sample rate/channels (currently 44.1 k mono vs 48 k stereo) — even though my test shows it isn't currently driving predictions, it is a latent shortcut risk for any retrained model.

---

## 8. All other problems found

1. **Whole-file mean pooling for origin** dilutes local evidence and entangles channel with content. Field practice: score 2–4 s windows and aggregate (max/percentile/attention pooling), which also yields per-region origin evidence for free.
2. **SelectKBest(50-of-768) on 46 samples** is statistically unstable; the selected dims are noise-tailored. Any retraining should use the full embedding with proper regularization or stronger models, selected/validated on grouped splits.
3. **Origin threshold 0.2** was tuned on the same tiny CV; with saturated scores it is arbitrary. Mixer-processed AI at 0.242 sits one hair above it — the user already saw the flip side.
4. **Shadow models advertised but never run**: `evidence_sources` includes `aasist_shadow`/`hybrid_resnet_shadow` although the active path never executes them. Either run them (ensemble after validation) or remove them from the display.
5. **Replay/mixer axes are acoustic-only LRs trained on 92 files from one chain each** — they likely detect *that specific* laptop-mobile chain / mixer preset, not replay or channel processing in general. Their 0.996/0.954 outputs on training files prove nothing about new devices.
6. **Imputer hides missing-feature drift**: if feature extraction partially fails, `SimpleImputer` silently fills medians and the prediction proceeds (notes only warn above 25% missing) — predictions can quietly degrade.
7. **Fusion arbitration can suppress true positives**: replay/mixer elevation blocks partial evidence (`blocked_by_replay_or_mixer_context`) and softens origin wording; for an attacker, *adding* replay/mixer processing is therefore a reliable way to silence the system. This is the security-relevant reading of the user's complaint.
8. **Waveform/report artifacts are duplicated** into both `gradio_outputs/reports/` and `gradio_outputs/visuals/` (minor).
9. **`normalize_audio` only normalizes if peak > 1.0** — quiet recordings keep arbitrary gain; several acoustic features (rms, peak, snr proxies) are gain-sensitive, adding spurious variance the tiny training set cannot average out.

---

## 9. Ranked improvement plan (most beneficial first)

### Tier 1 — data-centric (fixes the user-visible failure; highest payoff)
1. **Add processed-AI positives to origin training.** The `ai_repeat` and `ai_mixer` recordings already exist in `data/phase7c1/raw` — they were used for the replay/mixer axes but *excluded* from origin training. Relabeling origin as "AI (any post-processing)" vs "human (any post-processing)" with all 8 conditions instantly gives 92 vs 92 and directly targets the observed miss. (Effort: small. Risk: dataset still tiny → must combine with #2/#3.)
2. **Augmentation pipeline for all axes**: RIR/reverb convolution (simulated replay), real replay re-recording where feasible, codec round-trips (MP3/AAC/Opus at multiple bitrates — WhatsApp-style), additive noise at varied SNR, RawBoost (linear/non-linear convolutive + impulsive + stationary noise; no external data needed), random resample round-trips. Literature evidence: RIR augmentation cuts replay-induced EER from 18.2%→11.0%; RawBoost gives ~27% relative improvement on ASVspoof 2021 LA; plain noise addition alone is documented as insufficient.
3. **Expand data with public corpora**: ASVspoof 2019 LA / 2021 LA+DF (codec/channel variation built in), MLAAD (multi-language, many TTS), In-the-Wild, ReplayDF (replayed deepfakes — exactly this failure mode), PartialSpoof + ADD2023 (partial axis), CodecFake (codec-based generation). Even using them only for *evaluation* would immediately give honest numbers.

### Tier 2 — evaluation honesty (cheap, removes the paper-vs-reality gap)
4. **Strict held-out protocol**: speaker-disjoint and condition-disjoint splits; never score files that appear in any training CSV; report a per-condition recall matrix like Section 3.2 in every phase report. Add an automated check that refuses to evaluate on paths present in training manifests.
5. **Probability calibration** (Platt scaling or isotonic on a held-out set; or temperature scaling): kills the fake-looking 0.000/1.000 outputs, makes thresholds meaningful, enables confidence wording. Re-derive thresholds per axis on processed/unseen data (target: fix false-negative rate, then read off the threshold).

### Tier 3 — release/UX corrections (small code changes, big credibility gain)
6. Fix the contradictory partial display: when the gate says "global activation, not localized", do not render a "Suspicious segments / Recommended" table of 1.000s; show one consistent message (and cap displayed scores, e.g., ">0.99").
7. Remove or run the shadow models — don't list `aasist_shadow`/`hybrid_resnet_shadow` as evidence sources while they are inactive.
8. Label scores honestly ("uncalibrated model score", not "confidence"), and surface the per-axis training-set sizes in the About panel; this also protects the FYP in evaluation/viva settings.

### Tier 4 — model-centric (after data/eval are fixed)
9. **Window-level origin scoring + aggregation** (replace whole-file mean pooling); reuse existing segment SSL embeddings already computed in the pipeline — near-zero extra cost.
10. **Stronger back-ends on frozen embeddings**: gradient boosting / shallow MLP / attentive pooling probe on full 768-dim (with augmented data), instead of SelectKBest-50 LR.
11. **Activate AASIST (and the W2V2/WavLM+AASIST recipe) as an ensemble member** once a fair validation set exists — the packaged reference checkpoints are already runnable (`shadow_runnable`).
12. **Partial axis redesign** per Section 6 (frame-level scoring + change-point boundaries; PartialSpoof training; drop within-file percentile features).
13. **High-band auxiliary features at native sample rate** for replay/mixer axes (the productive version of the resampling idea, Section 7).

### Explicitly *not* recommended
- Changing `target_sample_rate` from 16 kHz and retraining everything as-is: empirically does nothing for the observed failure and breaks WavLM input requirements.
- Tuning thresholds on the current 46/92-file CSVs: any threshold fitted there is noise.
- Adding more gating/arbitration rules to mask origin misses: the wording layer is already at its honest limit; further gating hides signal.

---

## 10. Reproducibility appendix

Diagnostic scripts used (research-only, since removed; re-create as needed):

- **Origin sweep** — loads `release/models/origin/origin_file_model__ssl__experimental.joblib` via `release/src/model_loader.py`, scores every wav in `data/phase7c1/raw/*` with the exact release path (`load_audio` → `extract_file_ssl_embedding` → `align_features_to_metadata` → `predict_proba`). Output table in Section 3.2.
- **Resample confound test** — same scoring function applied to `human_001_clean.wav`, `ai_001_direct.wav`, `ai_001_replay_laptop_mobile.wav` as-is and after soundfile/librosa re-encode to 44.1 kHz mono and 48 kHz. Output table in Section 3.3.

Key evidence files:

- `release/gradio_outputs/json/CASE-2F86E2E07B77_analysis.json` (replayed AI → origin 0.011)
- `release/gradio_outputs/json/CASE-DBB938B3E9FC_analysis.json` (mixer AI → origin 0.242)
- `reports/phase8/models/phase8e0/phase8e0_origin_file_dataset.csv` (46 rows, all "clean")
- `reports/phase8/models/phase8e1/phase8e1_metrics_summary.csv` (CV accuracy 1.0 / AUC 1.0 for origin-ssl)
- `reports/phase9/final_release/final_active_model_classifier_types_report.md` (classifier types, dataset sizes)
- `release/models/partial_fabrication_experimental_p5b/partial_validation_summary.json` (partial recall 0.70, 2 FPs)

External references:

- Müller et al., "Replay Attacks Against Audio Deepfake Detection", Interspeech 2025 (ReplayDF; EER 4.7→18.2%; RIR augmentation → 11.0%).
- Tak et al., "RawBoost: A Raw Data Boosting and Augmentation Method for Anti-Spoofing", ICASSP 2022 (+27% relative on ASVspoof 2021 LA).
- Sun et al., "AI-Synthesized Voice Detection Using Neural Vocoder Artifacts", CVPR-W 2023 (resampling/noise augmentation for robustness).
- Zhong et al., "Enhancing Partially Spoofed Audio Localization with Boundary-aware Attention (BAM)", Interspeech 2024; BFC-Net (Neurocomputing 2025); TDL; Segment-Aware Learning (SAL); survey "Manipulated Regions Localization For Partially Deepfake Audio" (arXiv 2506.14396).
- Fullband/subband high-resolution detection (arXiv 2604.04841): 16 kHz pipelines discard discriminative >8 kHz cues.
- Datasets: ASVspoof 2019/2021, MLAAD, In-the-Wild, ReplayDF, PartialSpoof, ADD2023 Track 2, HQ-MPSD, CodecFake.
