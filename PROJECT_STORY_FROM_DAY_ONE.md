# FASSD Project Story From Day One

**Project:** FASSD - Forensic Acoustics for Synthetic Speech Detection  
**Product-facing name (public):** deepfakedetection.dev — Forensic Acoustics voice integrity web platform  
**Backend package name (FYP repo):** Deepfake Audio Detector - Local Demo (Phase 9G release folder label)  
**Document purpose:** Complete story of the project evolution, scope changes, datasets, architectures, results, limitations, and final forensic product direction.  
**Status at the end of the project:** Phase 9G local demo/handoff package passed, then a release-audit cycle (Phases 0–7) repaired the origin axis, promoted the Phase 5 partial localizer, added Phase 6 evidence-band wording, and produced the final Phase 7 release matrix. A live Next.js web platform was then built and deployed at [https://www.deepfakedetection.dev/](https://www.deepfakedetection.dev/) with the Phase 9 FastAPI backend on DigitalOcean (full story: `thesis_working_notes/FRONTEND_AND_DEPLOYMENT_STORY.md`). The project is complete as an experimental forensic decision-support prototype, not a court-ready proof system.

---

## 1. The Whole Story in One Paragraph

This project started as a deepfake audio detection model. At the beginning, the work followed the usual anti-spoofing path: extract LFCC and MFCC/log-mel spectrogram-style features from ASVspoof audio, train CNN models, compare EER values, and improve the architecture. That produced strong numbers, especially after moving to a ResNet-style CNN. But that success exposed a deeper problem: the original point of the project was not only to detect synthetic artifacts; it was to use environmental and acoustic evidence as well. ASVspoof alone could not represent broadcast, YouTube, replay, mixer, phone, and real-world conditions, so the project expanded into custom real-world data and a hybrid ResNet + environmental-feature model. That model improved the project scientifically, but then the product goal changed again: the final system could not be just a binary real/fake classifier. It had to behave like a forensic tool that explains origin, replay, mixer/channel effects, partial fabrication, suspicious segments, and limitations. HybridResNet fine-tuning and AASIST were both tested and both showed the same core limitation: binary anti-spoof models cannot represent forensic authenticity. The final architecture therefore became a multi-axis forensic audio intelligence system with separate origin, replay, mixer/channel, partial-fabrication, segment, fusion, report, and UI layers. The release-audit cycle then repaired the most serious shipped failure: origin was retrained with processed-AI positives and train-only augmentation, partial fabrication was redesigned without F9 within-file percentile/max-normalized features, and Gradio/PDF/JSON wording was changed from raw scores to evidence bands. The main remaining limitations are external replay/mixer generalization, WhatsApp/platform-compressed AI, and the fact that all axes remain experimental manual-review evidence rather than legal proof.

---

## 2. Why the Project Changed So Many Times

The project did not change direction randomly. Every shift happened because the previous approach answered only part of the real problem.

At first, a good EER looked like success. The CNN and ResNet models could separate bona fide and spoofed ASVspoof samples very well. But the project goal was forensic acoustics, not leaderboard anti-spoofing. A model that detects vocoder traces in controlled data does not automatically detect environmental inconsistency in real evidence.

Then environmental features were added. That was closer to the original idea, but the dataset problem became obvious. ASVspoof data is large, but it is not enough by itself for broadcast, YouTube, podcast, phone, replay, mixer, and platform-compressed audio. A huge dataset can still be narrow if its recording conditions are not the conditions the product must handle.

Then the project became a forensic product. This was the biggest change. A forensic user does not only ask "is this fake?" They ask whether the speech origin is human or AI, whether it was replayed, whether it went through a mixer or platform, whether only one part was replaced, and whether the system is confident enough or should recommend manual review. A binary model cannot express those cases.

Finally, the architecture changed from a single model to a multi-axis evidence system. That final shift was based on experimental failure modes, not preference. HybridResNet and AASIST both produced useful evidence, but neither could be trusted as the final forensic judge. The final system therefore separates evidence axes and fuses them carefully with safe wording.

---

## 3. Original Scope

The original FASSD scope had three core goals:

1. **AI vs human voice detection** - determine whether a complete recording is natural human speech or AI-generated speech.
2. **Detection of AI-replaced voices in real recordings** - identify cases where a real recording has been manipulated by replacing or swapping the original voice.
3. **Replay detection of AI voices** - detect AI-generated speech played through a speaker or device and then re-recorded.

The early technical approach was model-centric and binary:

- extract spectral features from audio,
- train a CNN classifier,
- classify samples as bona fide/real or spoof/fake,
- improve EER and accuracy.

This was a reasonable starting point, but it was incomplete for the original forensic idea because the early pipeline mostly learned speech/synthesis artifacts, not environmental consistency.

---

## 4. Phase 1: ASVspoof Foundation and Feature Extraction

The first major technical foundation was ASVspoof 2021.

Early dataset scale:

- ASVspoof data size: more than 400 GB.
- ASVspoof LA: 181,566 audio files.
- ASVspoof DF: 611,829 audio files.
- Early total: around 800,000 audio files.
- Early missing coverage: PA/replay was not properly included in the first pipeline.

The first features were:

- **LFCC**: 20 Linear Frequency Cepstral Coefficients.
- **Log-Mel / MFCC-style spectrogram features**: 64 frequency bins.
- Features were saved as NumPy arrays and later packed into HDF5 for efficient loading.

The first important lesson was that the feature pipeline worked. The project could process large-scale audio, extract repeatable features, train models, and evaluate them.

But this phase was still mostly an anti-spoofing setup. It did not yet solve environmental audio forensics.

---

## 5. Phase 2: Data Augmentation

The next step was robustness. The project added augmentation because clean studio-style data is not enough for realistic audio.

Augmentation included:

- MUSAN background noise,
- RIR room impulse response / reverberation,
- codec-style downsample/upsample simulation,
- random gain,
- clipping.

The augmentation pipeline created **611,829 additional augmented samples**.

The purpose was correct: real-world audio has noise, reverb, compression, device effects, and platform processing. But the later results showed that augmentation alone cannot replace real target-domain data. It can improve robustness inside a related domain, but it does not fully solve broadcast/YouTube/phone/domain mismatch.

---

## 6. Phase 3: Baseline CNN With LFCC

The first trained detector was a lightweight CNN/LCNN baseline.

Baseline details:

- Architecture: small CNN/LCNN.
- Approximate size: around 5,000 parameters.
- Main input: LFCC features.
- Goal: establish a baseline before using deeper models.

Important fixes during this phase:

- class weight bug,
- Unicode console issues,
- data loading issues.

Results:

| Model / setting | Result |
|---|---:|
| LFCC CNN on clean data | 9.68% EER |
| LFCC CNN on augmented data | 15.71% EER |

Interpretation:

The baseline worked, but it was not strong enough. It proved the training pipeline, but the EER was still high for a final detector.

---

## 7. Phase 4.1: LFCC vs Log-Mel / MFCC-Style Spectrogram Features

After the LFCC baseline, the project compared LFCC with log-mel spectrogram features.

Key comparison:

| Feature / model | Clean test EER | Augmented test EER |
|---|---:|---:|
| LFCC robust baseline | not the best clean result | 15.71% |
| Log-Mel clean model | 8.57% | 36.33% |
| Log-Mel robust model | 9.69% | 15.25% |

Important finding:

- Log-Mel robust training slightly outperformed LFCC robust training on augmented data: **15.25% vs 15.71% EER**.
- Clean-only training looked good on clean data but failed badly under augmentation.
- Robust training was necessary.

This phase moved the project away from LFCC-only features and toward log-mel spectrogram features for advanced CNN models.

---

## 8. Phase 4.2: Deep ResNet CNN Success

The next architecture was a deeper ResNet-style CNN.

Architecture:

- 8 residual blocks with skip connections.
- Around 2.8 million parameters.
- Batch normalization.
- Mixed precision / FP16 training.
- TF32 acceleration on supported NVIDIA GPU.
- Class weighting for imbalance.

Results:

| Evaluation | Result |
|---|---:|
| Clean test | 0.57% EER |
| Augmented test | 2.61% EER |

This was the first major success. Compared with the baseline, the ResNet CNN was a huge improvement. On ASVspoof-style data, the model looked very strong.

But this success created a false sense of completion. The model was excellent for the ASVspoof domain, but it was still mostly a synthetic-artifact detector. It was not yet the environmental forensic system the project was supposed to become.

---

## 9. The First Major Wall: Real-World Broadcast Failure

The turning point came when the strong ResNet model was tested on real-world broadcast-style audio, including Trump audio examples.

Observed behavior:

- 6 real audio files.
- 2 fake audio files.
- All 8 were predicted as fake.
- This created 100% false positives on the real examples in that small test.

Why this happened:

- The model was trained on ASVspoof-style controlled/studio data.
- The test audio was broadcast/processed audio.
- Broadcast audio contains compression, EQ, noise reduction, transmission artifacts, and channel effects.
- These artifacts can look "synthetic" to a model trained mostly on controlled anti-spoof data.

This was the first clear proof that a low EER on ASVspoof did not mean the system solved the real forensic problem.

The practical lesson:

> A model can be very good at detecting dataset-specific synthetic artifacts and still fail as a real-world forensic detector.

---

## 10. Phase 4.3: Environmental Feature Classifier

After the broadcast failure, the project returned to the original environmental-acoustics idea.

The environmental feature extractor used 12 features, including:

- RT60 / reverberation-related evidence,
- SNR,
- spectral tilt,
- spectral flatness,
- spectral rolloff,
- background noise analysis,
- "too clean" indicators.

Two approaches were tested.

### 10.1 Anomaly Detection

Approach:

- Train an Isolation Forest on bona fide/real samples only.
- Learn normal environmental patterns.
- Flag environmental anomalies as fake.

Result:

- Around **24.5% to 25% accuracy**.

Decision:

- Rejected. It did not work well enough.

### 10.2 Supervised Environmental Classifier

Approach:

- Train a supervised classifier, such as Random Forest, on both real and fake samples.
- Learn differences between environmental features of the two classes.

Result:

- **81.69% accuracy** on ASVspoof-style test data.

Decision:

- Useful, but not enough.

The environmental classifier worked inside the training domain, but still failed to generalize cleanly to broadcast/processed real-world audio. On Trump/broadcast examples, real and fake environmental scores overlapped:

- real audio scores: 0.500 to 0.746, mean around 0.660,
- fake audio scores: 0.669 to 0.674, mean around 0.672.

This showed that environmental features also need target-domain data. Real broadcast audio and AI/broadcast-style audio can become very similar after processing.

---

## 11. Why ASVspoof Alone Was Not Enough

ASVspoof is valuable, but the project outgrew it.

The limitations were:

- early work used LA and DF but missed proper PA/replay coverage,
- ASVspoof alone did not represent broadcast, YouTube, podcast, phone, mixer, WhatsApp, social-media, and local recording chains,
- environmental features learned from clean/studio-like data did not transfer reliably,
- random or non-speaker-controlled splitting did not represent true generalization,
- binary labels did not represent forensic situations such as human replay or partial fabrication.

This is why the dataset design changed.

---

## 12. Phase 0 to Phase 6 Rebuild: Real-World + Unified Dataset

The project then moved into a more complete pipeline. This pipeline rebuilt the dataset around ASVspoof plus real-world audio.

Collected and integrated sources:

- ASVspoof LA,
- ASVspoof DF,
- ASVspoof PA,
- LibriSpeech,
- VCTK,
- optional VoxCeleb-style public material,
- YouTube broadcast,
- YouTube podcast,
- YouTube social audio,
- synthetic/generated audio,
- processed local real-world material.

Important real-world domains:

- broadcast,
- podcast,
- social,
- read speech,
- synthetic,
- studio.

Unified dataset statistics:

| Dataset / group | Samples |
|---|---:|
| PA | 943,110 |
| DF | 611,829 |
| LA | 181,566 |
| RealWorld | 157,414 |
| **Total** | **1,893,919** |

Label distribution:

| Label | Samples |
|---|---:|
| spoof | 1,573,308 |
| bona fide | 320,611 |

Attack-type distribution:

| Attack type | Samples |
|---|---:|
| replay | 816,480 |
| conversion | 589,212 |
| bona fide | 320,611 |
| synthesis | 167,616 |

Domain distribution:

| Domain | Samples |
|---|---:|
| studio | 1,819,660 |
| read_speech | 28,539 |
| broadcast | 17,994 |
| podcast | 17,512 |
| social | 5,712 |
| synthetic | 4,502 |

Other important facts:

- Total speakers: 73,421.
- Real/fake ratio: about 16.9% bona fide and 83.1% spoof.
- Mean duration: about 6.25 seconds.
- Median duration: about 4.65 seconds.
- Duration range: 1.41 to 10.0 seconds.
- Speaker-independent splits were created.
- Speaker overlap in final test evaluation: 0.

This was the first dataset design that matched the real project goal more closely.

---

## 13. Phase 3 to Phase 5 HybridResNetEnvironmental Architecture

The major hybrid model was `HybridResNetEnvironmental`.

Purpose:

Combine spectrogram evidence with environmental evidence.

Inputs:

- Log-mel spectrogram: `[64, 400]` per 4-second chunk.
- Environmental feature vector: 12 features per chunk.

Architecture:

- ResNet branch for log-mel spectrograms.
- Environmental MLP branch for 12 environmental features.
- Fusion layer by concatenation and fully connected layers.
- Binary head: bona fide vs spoof.
- Multiclass head: bona fide, synthesis, conversion, replay.

Model size:

- **2,902,822 parameters**.
- Around 12 MB.

Training:

- 20 epochs.
- Mixed ASVspoof + RealWorld data.
- Speaker-independent train/validation/test.
- Fast HDF5 feature loader after fixing a gzip bottleneck.
- HDF5 sample access improved from around 470 ms to around 2 ms per sample.

Best checkpoint:

- `models_saved/hybrid_resnet_environmental_best.pth`
- Best validation binary EER: **20.17%** at epoch 17.

---

## 14. Phase 5 Hybrid Evaluation

The formal Phase 5 evaluation tested the hybrid model on a speaker-independent test set.

Test set:

- 254,574 test segments.
- Speaker overlap: 0.

Overall test results:

| Metric | Value |
|---|---:|
| Binary EER | 16.21% / 16.22% reported across docs |
| Binary AUC | 0.9167 |
| Binary accuracy at 0.5 | 89.78% |
| Multiclass accuracy | 64.36% |

Domain-specific results:

| Subset | Samples | Binary EER | Binary AUC |
|---|---:|---:|---:|
| ASVspoof test | 237,490 | 18.15% | 0.8947 |
| RealWorld test | 17,084 | 16.14% | 0.9236 |

Threshold sweep:

| Threshold | Accuracy | Bona fide FPR |
|---|---:|---:|
| 0.50 | 89.78% | 41.28% |
| 0.65 | 89.61% | 39.28% |
| 0.70 | 89.52% | 38.43% |

Multiclass classification:

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| bona fide | 0.6983 | 0.6105 | 0.6515 | 39,737 |
| synthesis | 0.1631 | 0.5160 | 0.2479 | 22,192 |
| conversion | 0.7992 | 0.8851 | 0.8399 | 90,585 |
| replay | 0.9727 | 0.4698 | 0.6336 | 102,060 |

Interpretation:

The hybrid model was a major improvement over the earlier narrow ASVspoof-only pipeline. It met the RealWorld EER MVP target of less than 20%, but it did not meet every product requirement:

- overall EER target below 10% was not met,
- multiclass attack typing was only 64.36%,
- bona fide false positive rate remained high,
- binary output still did not represent forensic meaning.

---

## 15. Phase 6: Raw Audio Explanation System

The project then moved from model metrics to usable inference.

Phase 6 added:

- raw audio chunking,
- VAD-aware processing,
- log-mel + environmental feature extraction,
- chunk-level inference,
- pooling and voting,
- JSON outputs,
- CSV outputs,
- human-readable explanations,
- suspicious chunk timelines.

Important script:

- `code/phase6/explain_prediction.py`

Tuned Phase 6 result:

- Trump test audios: **8/8** after tuning.
- All custom test audios: **12/17**, or **70.6%**.
- Weak area: Pakistani / Urdu domain.

This phase moved the project toward explainability, but the output was still too close to a binary detector.

---

## 16. The Second Major Scope Change: From Model to Forensic Product

After Phase 6, the project direction changed from "train the best binary detector" to "build a forensic voice authenticity analyzer."

The reason was practical:

Real forensic cases are not binary.

Examples:

- Human speech replayed through a speaker and recorded on a phone is not AI-generated, but it is not an original clean recording either.
- AI speech replayed through a speaker contains both AI-origin evidence and replay/channel evidence.
- Mixer-processed human speech can look suspicious to an anti-spoof model without being AI-generated.
- YouTube/WhatsApp compression can shift scores.
- A long recording may be mostly human with one inserted AI segment.

This required the project to separate:

- **origin evidence**: human, AI, mixed, unknown,
- **manipulation evidence**: replay, mixer/channel, compression, edit/splice, partial fabrication,
- **segment evidence**: suspicious timestamps and inside/outside region differences,
- **final report wording**: safe, limited, manual-review oriented.

This is where the project became a forensic product rather than only a detector.

---

## 17. Phase 7: Controlled Forensic Evaluation

Phase 7 was the phase that proved the binary-model strategy was not enough.

Phase 7 included:

- 7A: controlled forensic test suite,
- 7B: forensic label preparation,
- 7C0: dataset audit,
- 7C1: local forensic dataset + baseline evaluation,
- 7C2: training manifest preparation,
- 7C3: HybridResNet fine-tuning,
- 7C4: decision-layer calibration,
- 7D: report layer planning,
- 7E: AASIST experiment.

Controlled local forensic roles included:

- clean human,
- human replay,
- human mixer/channel processed,
- human partial fabrication,
- direct AI,
- AI replay,
- AI mixer/channel processed,
- AI partial fabrication.

This dataset and test suite were necessary because ASVspoof-style labels could not answer the product questions.

---

## 18. Phase 7C1: HybridResNet Baseline on Controlled Forensic Data

The HybridResNet baseline was evaluated on local controlled forensic data.

Results:

| Metric | Count |
|---|---:|
| clean_human_accepted | 4/23 |
| clean_human_false_alarm | 17/23 |
| direct_ai_detected at file level | 0/23 |
| direct_ai_file_missed_but_segment_suspicious | 19/23 |
| human_replay_detected | 23/23 |
| ai_replay_detected_or_segment_suspicious | 23/23 |
| human_mixer_detected | 23/23 |
| ai_mixer_detected | 23/23 |
| partial_fabrication_detected | 43/46 |

Interpretation:

HybridResNet was very useful for replay, mixer/channel, and partial-region sensitivity. But it was not acceptable as a single final model because it over-flagged clean human files and missed direct AI at file level unless segment evidence was considered.

This was one of the most important findings of the project:

> The model had useful forensic evidence, but the evidence could not be collapsed into one real/fake score.

---

## 19. Phase 7C3: HybridResNet Fine-Tuning Attempts

The next idea was to tune the HybridResNet model so it could meet the forensic product requirements.

Experiments:

- 7C3-v1 fine-tuning.
- 7C3-R2 risk-tuned checkpoints.
- `best_product` and `best_loss` style checkpoint comparisons.

Decision:

- 7C3-v1 was rejected because manipulation sensitivity collapsed.
- 7C3-R2 improved balance in some areas but was rejected as a standalone product scorer.

Main lesson:

Fine-tuning a binary-style model did not solve the semantic problem. The product did not only need better thresholds; it needed a different architecture.

---

## 20. Phase 7C4: Decision-Layer Fusion Prototype

The project then tested a decision-layer approach.

Phase 7C4-v1:

- Rejected because clean-human false alarms remained too high.

Phase 7C4-v2:

- Accepted as a **prototype only**.
- It improved clean-human behavior compared with raw HybridResNet.
- It preserved most replay/mixer/partial detection.
- It was not considered a final product model.

Phase 7C4-v2 controlled results:

| Metric | Count |
|---|---:|
| clean_human_false_alarm | 7/23 |
| clean_human_accepted | 1/23 |
| clean_human_borderline | 15/23 |
| clean_human accepted + borderline | 16/23 |
| direct_ai_detected_or_segment_suspicious | 19/23 |
| human_replay_detected | 23/23 |
| ai_replay_detected_or_segment_suspicious | 23/23 |
| human_mixer_detected | 23/23 |
| ai_mixer_detected | 23/23 |
| partial_fabrication_detected | 44/46 |

Interpretation:

The decision layer showed the direction was correct: use evidence streams and interpretation rules, not one raw score. But it was still only a prototype because it depended on the older model outputs and did not yet implement the final multi-axis architecture.

---

## 21. Phase 7E: AASIST Experiment

After HybridResNet tuning did not solve the product problem, the project tried AASIST.

Reason:

AASIST is an anti-spoofing architecture designed for audio spoof detection. It was a reasonable candidate to test because it might capture artifacts that the ResNet missed.

Pretrained AASIST-L results on Phase 7C1:

| Metric | Count |
|---|---:|
| clean_human_false_alarm | 22/23 |
| clean_human_accepted | 1/23 |
| direct_ai_detected_or_segment_suspicious | 18/23 |
| partial_fabrication_detected | 45/46 |

Fine-tuned AASIST:

- `best_product`: rejected because clean-human false alarms remained unacceptable.
- `best_loss`: rejected because it did not meet the product goal.

Decision:

- AASIST was rejected as the current standalone solution.
- AASIST was also rejected as a branch-only current solution.
- It remained archived/reference evidence only.

Key lesson:

AASIST was also anti-spoof biased. It detected many suspicious patterns, but it did not solve the clean-human/product semantics problem. This confirmed that the issue was not simply "use a better binary model."

---

## 22. Phase 7 Final Conclusion

Phase 7 was closed with a stable conclusion:

> A single binary real/fake, spoof/bonafide, or origin-first classifier cannot represent the forensic product goal.

Accepted:

- Phase 7A controlled testing.
- Phase 7B forensic labels.
- Phase 7C0 dataset audit.
- Phase 7C1 local forensic dataset.
- Phase 7C2 manifests.
- Phase 7C4-v2 as decision-layer prototype only.

Rejected as final/current product solutions:

- Phase 7C3-v1.
- Phase 7C3-R2 standalone.
- Phase 7C4-v1.
- AASIST pretrained.
- AASIST fine-tuned `best_product`.
- AASIST fine-tuned `best_loss`.

Postponed:

- Phase 7D report implementation, later moved into Phase 8/9 product work.

Phase 7 was not a failure. It was the phase that proved the correct final architecture.

---

## 23. Phase 8: Final Architecture Direction

Phase 8 defined the final architecture as **Multi-Axis Forensic Audio Intelligence**.

The final architecture rule:

> Origin and manipulation must be inferred in parallel. Do not use a hard AI/human first-stage routing gate as final logic.

Final processing flow:

```text
Audio input
  |
  v
Preprocessing and segmentation
  |
  v
Evidence extraction
  |
  +--> Origin evidence axis
  |       - human
  |       - ai_synthetic
  |       - mixed
  |       - unknown
  |
  +--> Manipulation evidence axes
  |       - clean
  |       - replay_rerecorded
  |       - mixer_channel_processed
  |       - partial_fabrication
  |       - edited_spliced
  |       - compressed_low_quality
  |       - unknown_manipulation
  |
  +--> Segment evidence axis
          - per-window scores
          - suspicious flags
          - timestamps
          - region deltas
  |
  v
Fusion and abstention
  |
  v
Forensic-safe report and UI
```

Non-negotiable rules:

- No binary fake/real collapse as final truth.
- No hard AI/human routing gate.
- Replay evidence does not mean AI-generated.
- Mixer/channel evidence does not mean AI-generated.
- Partial fabrication requires segment evidence.
- File-level averages must not hide suspicious inserted regions.
- Output must support manual review and abstention.
- Reports must not claim legal proof.

Phase 8 allowed claims:

- the system extracts multi-axis forensic evidence,
- the system produces experimental evidence indicators,
- the system can localize timestamp-aligned partial fabrication candidates,
- the system avoids binary fake/real collapse,
- the system uses manual-review and abstention logic.

Phase 8 forbidden claims:

- detects all deepfakes perfectly,
- proves audio is fake,
- court-ready forensic proof,
- detects every manipulation type,
- robust on all real-world audio,
- final production system.

Phase 8 evidence-table and model results:

- Phase 8B evidence table: 184 files and 4,189 segment rows.
- Phase 8F fusion output: 184 file rows, 1,207 segment rows, and 164 manual-review triggers.
- Origin model using SSL features: balanced accuracy 1.0, F1 1.0, clean-human false-AI rate 0/23, AI detected 23/23.
- Replay model using acoustic features: balanced accuracy about 0.97, clean false positives 2/46, replay manipulation detected 45/46.
- Mixer/channel model using acoustic features: balanced accuracy about 0.99, clean false positives 1/46, mixer manipulation detected 46/46.
- Phase 8E-3 combined partial segment model: balanced accuracy about 0.88, ROC-AUC about 0.956, fabricated segment recall 190/224 or 84.8%, outside false-fabricated rate 86/983 or 8.7%.

---

## 24. Phase 9: Local Forensic Product / Demo

Phase 9 packaged the project as a local demo and integration prototype.

Phase 9 purpose:

- convert the research/evidence engine into a teammate-usable local release,
- provide a Gradio UI,
- provide a FastAPI API,
- package active experimental models,
- generate JSON/PDF/HTML-style forensic outputs,
- preserve safety wording and known limitations.

Release identity:

- Release name: `phase9g_deepfake_audio_detector_demo_handoff`.
- Product name: **Deepfake Audio Detector - Local Demo**.
- Research/FYP name: **Forensic Acoustic for Synthetic Speech Detection**.
- Important naming constraint from the release chats: do not present the demo product as **Forensic Deepfake Audio Detector**; keep that idea as research/scope context, not the UI product title.

Phase 9G result:

- Status: **PASS**.
- Final go/no-go: **GO** for local demo/handoff.
- Files in package manifest: 71.
- Total uncompressed bytes: 37,248,295.
- Package path: `release_packages/phase9g_deepfake_audio_detector_demo_handoff.zip`.

Active release models:

- `origin_file_model`,
- `replay_file_model`,
- `mixer_file_model`,
- `partial_fabrication_segment_model`.

Inactive reference models:

- AASIST: `reject_for_now`.
- HybridResNet/ResNet: `reject_for_now`.

Important: the final release does not activate AASIST or HybridResNet as decision models. They remain historical/reference/shadow artifacts.

---

## 25. Final Release Architecture

The active release folder contains:

- `release/app_gradio.py` - Gradio UI.
- `release/app_fastapi.py` - FastAPI REST API.
- `release/src/inference_pipeline.py` - Phase 9C analysis pipeline.
- `release/src/model_loader.py` - active packaged model loading.
- `release/src/fusion_rules.py` - multi-axis fusion rules.
- `release/src/feature_extraction.py` - acoustic/SSL features.
- `release/src/ssl_embeddings.py` - SSL embedding extraction.
- `release/src/segmentation.py` - audio segmentation.
- `release/src/report_generator.py` - Markdown report helpers.
- `release/src/pdf_report_generator.py` - PDF export.
- `release/src/app_visualization.py` - waveform/timeline image generation.
- `release/src/origin_support_models.py` - AASIST/ResNet shadow wrappers, inactive.

The UI/report shows:

- voice origin first,
- forensic indicators second,
- recommendation level,
- evidence cards,
- waveform/timeline visualization,
- JSON/PDF downloads,
- limitations and safety text.

The API documents:

- `/`,
- `/health`,
- `/model-info`,
- `/analyze-audio`,
- `/analyze`.

Response fields include:

- request ID,
- file name,
- duration,
- processing status,
- case ID,
- voice origin result,
- forensic indicator summary,
- recommendation,
- evidence axis cards,
- axis interpretation,
- partial fabrication details,
- safety and limitations,
- generated report paths.

---

## 26. Final Active Model Cards

### Origin model

- Evidence axis: origin evidence.
- Feature set: SSL.
- Threshold candidate: 0.2.
- Rows packaged: 46.
- Selected features: 50.
- Allowed use: origin evidence indicator for experimental review workflow.
- Forbidden use: final fake/real decision, court-ready proof, production deployment without validation, replacing a human forensic analyst.

### Replay model

- Evidence axis: replay/rerecording evidence.
- Feature set: acoustic.
- Threshold candidate: 0.65.
- Rows packaged: 92.
- Selected features: 50.
- Important rule: replay evidence does not mean AI-generated.

### Mixer/channel model

- Evidence axis: mixer/channel evidence.
- Feature set: acoustic.
- Threshold candidate: 0.75.
- Rows packaged: 92.
- Selected features: 50.
- Important rule: mixer/channel evidence does not mean AI-generated.

### Partial fabrication module

- Status: experimental/manual-review only.
- Thresholds:
  - file gate threshold: 0.5,
  - segment threshold: 0.9,
  - contrast threshold: 0.25,
  - broad activation limit: 0.45.
- Output: candidate segment(s) for manual review.
- Not a conclusive authenticity decision.

---

## 27. Phase 9 Validation Results

### Demo freeze validation

Phase 9E-P4B demo freeze validation:

- Overall: PASS.
- Required Gradio/FastAPI/report/visualization files present.
- P3 full 184-file evaluation present.
- 184/184 files evaluated with 0 inference failures.
- Pass count: 136/184.
- Acceptable-with-limitation count: 46/184, mainly partial-fabrication candidate-only cases.
- Human clean false suspicious rate: 0.0.
- Human clean false AI rate: 0.0.
- AI clean origin detect rate: 1.0.
- AI fabricated origin detect rate: 1.0.
- Human replay replay-detection rate: about 0.913.
- Partial full-detection count in release regression: 0; partial cases were treated as candidate/limited evidence rather than conclusive detection.
- AASIST decision: reject_for_now.
- HybridResNet decision: reject_for_now.
- No AASIST/ResNet in active inventory.
- Demo sample variants verified:
  - `ai_clean`,
  - `ai_fabricated`,
  - `ai_mixer`,
  - `ai_replayed`,
  - `human_clean`,
  - `human_fabricated`,
  - `human_mixer`,
  - `human_replayed`.

### Origin-support shadow comparison

The active SSL baseline was compared against AASIST and HybridResNet as shadow origin-support models on 184 files.

SSL baseline:

- total files: 184,
- evaluated files: 184,
- failed files: 0,
- AI-origin accuracy on AI variants: 0.5,
- human-origin accuracy on human variants: 1.0,
- AI clean detect rate: 1.0,
- AI fabricated detect rate: 1.0,
- AI mixer detect rate: 0.0,
- AI replayed detect rate: 0.0,
- human clean false AI rate: 0.0,
- human fabricated false AI rate: 0.0,
- human mixer false AI rate: 0.0,
- human replayed false AI rate: 0.0.

AASIST shadow:

- AI-origin accuracy on AI variants: 1.0,
- human-origin accuracy on human variants: 0.0,
- human clean false AI rate: 1.0,
- cases helped current SSL: 46,
- cases hurt current SSL: 92,
- net help score: -46,
- decision: reject_for_now.

HybridResNet shadow:

- AI-origin accuracy on AI variants: 0.6196,
- human-origin accuracy on human variants: 0.0435,
- human clean false AI rate: 0.9565,
- cases helped current SSL: 45,
- cases hurt current SSL: 122,
- net help score: -77,
- decision: reject_for_now.

Interpretation:

AASIST and HybridResNet could detect some AI/processed cases, but both hurt clean-human behavior too much. Therefore they were not activated in the release product.

---

## 28. Partial Fabrication: Final Limitation

Partial fabrication is the main remaining limitation.

The project did build partial-fabrication datasets, tests, feature audits, file gates, segment localizers, and independent evaluations. But the final result is not strong enough to claim reliable partial-fabrication detection.

### P5D independent evaluation

Input:

- `E:\FYP\testing_audios`
- folders: fabricated, T1, T2, T3, T4, T5
- total files: 25
- independent holdout files: 25
- seen in P5 training: 0
- seen in P5C controlled: 0

File-level results:

- evaluated files: 25/25,
- partial evidence recall: 1.0,
- non-partial false alarm rate: 0.0869565.

Localization:

- timestamp positive count: 1,
- top1 hit rate when positive: 0.0,
- top3 hit rate when positive: 1.0,
- top5 hit rate when positive: 1.0,
- median candidate timestamp error: 94.222625 seconds.

P5D assessment:

- independent evaluation completed,
- not acceptable for release packaging evaluation,
- reason: only 2 labelled partial-positive files, below the minimum 5 required.

### P5F expanded evaluation

P5F added `fabricated_20pct`:

- total manifest files: 35,
- new fabricated_20pct files: 10,
- fabricated_20pct timestamp labels loaded: 10,
- expanded partial file count: 12,
- expanded timestamp-positive count: 8.

P5F metrics:

- partial evidence recall: 0.75,
- fabricated_20pct recall: 0.70,
- new partial recall: 0.70,
- new partial false negatives: 3.

fabricated_20pct localization:

- top1 hit rate: 0.8571,
- top3 hit rate: 1.0,
- top5 hit rate: 1.0,
- median candidate timestamp error: about 2.24 seconds.

False partial evidence examples:

- `testing_audios/T1/T1.2.mp3`,
- `testing_audios/T4/T4.1.mp3`.

False negatives:

- `human_003_clean_partial_fake_20pct.wav`,
- `human_007_clean_partial_fake_20pct.wav`,
- `human_009_clean_partial_fake_20pct.wav`.

Release decision:

- Candidate acceptable for release packaging evaluation: **no**.
- Blocking reasons:
  - fabricated_20pct recall 0.7000 is below the 0.8000 target,
  - new partial recall 0.7000 is below the 0.8000 target,
  - new partial false negative count is greater than 0.

Final partial-fabrication status:

- experimental,
- manual-review candidate only,
- not a strong detector,
- not a conclusive verdict,
- known false positives and false negatives remain.

---

## 29. What the Final Product Can Honestly Claim

The final project can claim:

- It is an experimental forensic audio decision-support prototype.
- It extracts multiple evidence axes instead of returning only real/fake.
- It provides voice-origin evidence.
- It provides replay/rerecording evidence.
- It provides mixer/channel evidence.
- It provides experimental partial-fabrication candidate regions.
- It produces JSON and report-style outputs.
- It provides waveform/timeline visualization.
- It recommends manual review where needed.
- It explicitly avoids legal-proof language.
- It includes a local Gradio demo and FastAPI interface.
- It has a Phase 9G PASS release/handoff package.

The final project must not claim:

- final legal proof,
- court-ready authentication,
- guaranteed deepfake detection,
- reliable detection of every partial replacement,
- robustness on all real-world audio,
- production deployment readiness,
- that replay/mixer evidence means AI-generated,
- that no partial evidence means the file is authentic.

---

## 30. Final Architecture Summary

The final architecture is not the first CNN, not the ResNet, not the HybridResNet, and not AASIST.

The final architecture is:

1. **Audio preprocessing and segmentation**
   - load audio,
   - normalize/resample,
   - segment into analysis windows,
   - preserve duration and segment metadata.

2. **Feature extraction**
   - SSL embeddings for origin evidence,
   - acoustic features for replay and mixer/channel evidence,
   - partial segment features for candidate localization,
   - optional/reference historical model outputs only where safe.

3. **Independent evidence models**
   - origin model,
   - replay model,
   - mixer/channel model,
   - partial fabrication segment model.

4. **Fusion logic**
   - combine evidence axes,
   - avoid binary collapse,
   - handle replay/channel conflict,
   - downgrade uncertain cases,
   - recommend manual review.

5. **Forensic report layer**
   - voice origin wording,
   - evidence indicators,
   - suspicious/candidate segment summary,
   - recommendation level,
   - limitations,
   - "conclusive authenticity decision: no."

6. **Local product interface**
   - Gradio UI,
   - FastAPI API,
   - JSON outputs,
   - PDF/HTML/report outputs,
   - waveform/timeline visualization.

---

## 31. The Final Project Timeline

### Stage 1: Baseline anti-spoofing

The project began with ASVspoof data, LFCC features, and a baseline CNN. This created the first working model pipeline and produced LFCC EER values around 9.68% clean and 15.71% augmented.

### Stage 2: Feature comparison

The project compared LFCC and log-mel/MFCC-style spectrograms. Log-mel robust training performed slightly better on augmented data, with 15.25% EER.

### Stage 3: ResNet success

A deeper ResNet CNN produced excellent ASVspoof-domain results: 0.57% clean EER and 2.61% augmented EER. At this moment, the model looked successful.

### Stage 4: Domain-mismatch discovery

Real-world broadcast tests showed that the ResNet was not solving the full project goal. It predicted all 8 Trump/broadcast test examples as fake, including the real ones.

### Stage 5: Environmental feature work

The project added environmental/acoustic features. Anomaly detection failed around 24.5% accuracy. Supervised environmental classification reached 81.69% on ASVspoof but still did not solve broadcast generalization.

### Stage 6: Dataset rebuild

The project expanded into a unified ASVspoof + RealWorld dataset with LA, DF, PA, broadcast, podcast, social, read speech, and synthetic sources. The final unified dataset had 1,893,919 samples and speaker-independent splits.

### Stage 7: HybridResNetEnvironmental

A hybrid model combined log-mel spectrograms and 12 environmental features. It achieved 16.21/16.22% overall test EER and 16.14% RealWorld EER, with 89.78% binary accuracy but high bona fide false positives and only 64.36% multiclass accuracy.

### Stage 8: Explanation and raw-audio testing

The project added chunk-level inference, VAD, JSON/CSV outputs, and explanation logic. It achieved 8/8 on tuned Trump examples and 12/17 on all custom test audio, with Pakistani/Urdu domain weakness.

### Stage 9: Forensic scope expansion

The goal changed from binary detection to forensic voice authenticity analysis. The project began separating origin, manipulation, replay, mixer, channel, partial, and segment evidence.

### Stage 10: Controlled forensic tests

Phase 7 tested HybridResNet on clean human, direct AI, replay, mixer, and partial fabrication. HybridResNet was strong for manipulation evidence but over-flagged clean human.

### Stage 11: Fine-tuning and AASIST rejection

HybridResNet fine-tuning did not produce a standalone product model. AASIST also failed the clean-human/product semantics requirement. Both were rejected as final decision engines.

### Stage 12: Multi-axis architecture

Phase 8 froze the architecture around parallel origin, manipulation, and segment evidence with fusion, abstention, manual review, and forensic-safe reporting.

### Stage 13: Local demo release

Phase 9 packaged the system into a Gradio/FastAPI local demo with active origin, replay, mixer/channel, and experimental partial modules. Phase 9G passed and produced the final handoff package.

### Stage 14: Release-audit repair cycle

After Phase 9G, a release audit found that the demo was honest structurally but weak on several real-world `testing_audios` cases. The audit therefore froze the baseline, repaired the origin model, tested resampling/window/dual-resolution hypotheses, attempted but rejected a unified manipulation classifier, redesigned the partial axis, and added final evidence-band wording.

Key release-audit decisions:

| Audit phase | Decision |
|---|---|
| Phase 2 origin | Promoted processed-AI augmented origin model at threshold 0.92 |
| Phase 3 resampling/window/dual-resolution | Closed; no alternative beat the selected baselines honestly |
| Phase 4 manipulation v3 | Stopped; manipulated `testing_audios` Stage-1 recall was 20% |
| Phase 5 partial | Promoted no-F9 partial segment localizer at threshold 0.95 |
| Phase 6 calibration/wording | Added Low/Medium/High evidence bands and explicit inconclusive states |
| Phase 7 final packaging | Packaged final models/configs and ran the 25-file `testing_audios` matrix |

Final `testing_audios` axis matrix:

| Axis | Balanced accuracy | Recall | Main remaining failures |
|---|---:|---:|---|
| Origin | 0.8250 | 0.9000 | T1.2/T4.1 false positives; T4.5 compressed-AI miss |
| Replay | 0.7738 | 0.7143 | T3.2/T3.3 misses; T2.2/T3.4/T4.1 false positives |
| Mixer | 0.4783 | 0.0000 | T2.2/T3.4 mixer misses; T2.4 false positive |
| Partial | 1.0000 | 1.0000 | No final gated failures on the 25-file matrix |

---

## 32. What Was Learned

### 32.1 A good EER is not the same as a forensic solution

The ResNet model achieved 2.61% EER on augmented ASVspoof tests, but it failed on real broadcast examples. This taught that benchmark success does not automatically mean product success.

### 32.2 Environmental features need matching data

Environmental features are important, but they cannot generalize magically. Broadcast, YouTube, phone, mixer, and platform-compressed audio must be represented in training/evaluation data.

### 32.3 Replay is not AI

Human speech can be replayed. Replay evidence is manipulation evidence, not synthetic-origin evidence.

### 32.4 Mixer/channel processing is not AI

Mixer or channel artifacts can make human speech look suspicious. That does not mean the voice was AI-generated.

### 32.5 Partial fabrication cannot be solved by file-level averaging

A short inserted fake segment can disappear in a file-level average. Segment-level evidence is required.

### 32.6 Binary models collapse forensic meaning

The project repeatedly rediscovered this through ResNet, HybridResNet, and AASIST. A single spoof score cannot represent origin, replay, channel processing, partial insertion, and uncertainty.

### 32.7 The final product must be honest

The correct output is not "definitely real" or "definitely fake." The correct output is evidence, confidence/risk, candidate regions, limitations, and manual-review recommendation.

---

## 33. Final Limitations

The final project is complete, but it has explicit limitations.

1. **All axes are experimental evidence indicators.**
   - No axis is a conclusive fake/real decision.
   - Every elevated or mixed result still requires manual review.

2. **The system is not court-ready.**
   - It is a decision-support prototype, not legal proof.

3. **Real-world generalization is not guaranteed.**
   - Broader external testing is still needed, especially across unseen replay chains, platforms, speakers, codecs, and languages.

4. **Replay and mixer/channel effects reduce origin reliability.**
   - The system therefore uses cautious wording such as "inconclusive under replay/channel processing."
   - The final release matrix still misses some replay cases (T3.2/T3.3) and mixer/channel cases (T2.2/T3.4).

5. **AASIST and HybridResNet are not active final decision models.**
   - They are reference/shadow artifacts only.

6. **The release remains experimental even when deployed on the web.**
   - Phase 9G packages a local Gradio/FastAPI demo in `release/`.
   - A live Next.js web platform was deployed at https://www.deepfakedetection.dev/ with Phase 9 API at api.deepfakedetection.dev (Vercel + DigitalOcean + Firebase). See `thesis_working_notes/FRONTEND_AND_DEPLOYMENT_STORY.md`.
   - This is still an experimental forensic decision-support demo, not operational legal-evidence or court-ready deployment.

7. **Small accepted Phase 8/9 model datasets limit claims.**
   - Active release model cards explicitly mark the models as experimental prototypes.

8. **Partial fabrication improved but remains manual-review evidence.**
   - Phase 5 fixed the broad-activation failure by removing F9 features.
   - The final matrix detected T4.3 and T5_FAB_001 and produced no final gated partial false positives on the 25-file matrix.
   - It still highlights candidate regions rather than proving fabrication.

9. **Phase 4 unified manipulation was not shipped.**
   - The attempted two-stage manipulation v3 reached only 20% manipulated recall on `testing_audios`.
   - Final manipulation evidence therefore remains separated across origin, replay, mixer/channel, and partial axes.

---

## 34. Final Answer to the Project Question

The final answer is:

FASSD started as a CNN-based synthetic speech detector using LFCC and log-mel/MFCC-style spectrogram features. It achieved strong ASVspoof-domain performance, especially with a ResNet CNN. But the project goal required environmental and forensic audio evidence, so the dataset and architecture expanded. The system then added real-world broadcast/YouTube/social/podcast data, ASVspoof PA replay coverage, environmental features, and a HybridResNetEnvironmental model. That hybrid model improved the research pipeline but still behaved like a binary model and could not fully represent forensic cases. Controlled forensic testing, HybridResNet fine-tuning, and AASIST experiments proved that a single anti-spoof model was not enough. The final architecture became a multi-axis forensic audio intelligence prototype with separate origin, replay, mixer/channel, partial-fabrication, segment, fusion, and report layers. The Phase 9G release delivered the local Gradio/FastAPI demo, and the later release-audit cycle repaired the largest shipped weaknesses: origin was retrained for processed AI, partial localization was redesigned without F9 features, and the UI now uses evidence bands instead of raw confidence-like scores. The project then added a live Next.js web platform at deepfakedetection.dev connected to the Phase 9 API on DigitalOcean, making the multi-axis evidence system usable through a public dashboard with Firebase auth and history. The final system remains an experimental decision-support demo; its clearest remaining limitations are external replay/mixer generalization, platform-compressed AI, and the need for manual review of all elevated evidence.

---

## 37. Live Web Platform and Production Deployment

After Phase 9G and the release-audit cycle, frontend work turned the Phase 9 backend into a public web product. Full detail is in `thesis_working_notes/FRONTEND_AND_DEPLOYMENT_STORY.md`.

What changed:

- The first website assumed a **binary Hybrid ResNet** API (`REAL` / `FAKE`). The backend evolved to **Phase 9 multi-axis forensic evidence**, so the UI was redesigned as a **voice integrity console** with four evidence cards, real waveform visualization, segment highlights, and manual-review wording.
- **Production stack:** Next.js 16 on **Vercel** (https://www.deepfakedetection.dev/), Phase 9 FastAPI on a **DigitalOcean** Droplet behind **Caddy** (https://api.deepfakedetection.dev/), **Firebase** Auth + Firestore for user history.
- **Large-upload fix:** Vercel serverless proxy limit (~4.5 MB) forced **direct browser → DigitalOcean** uploads for `/analyze`; `INFERENCE_PROXY_TARGET` is mirrored to the client in `next.config.mjs`.
- **Frontend repo path (separate from FYP ML repo):** documented as `D:\FASSD\` with `new backend/release/` vendored Phase 9 API.

Key production issues resolved:

- Missing vendored `phase8f_fusion_rules.py` in release folder
- CORS for frontend origins on the API
- Firestore rules not published initially
- Stale Hybrid ResNet marketing copy updated to Phase 9 pipeline wording

Platform limitations (still experimental):

- Firestore history stores simplified fields, not full Phase 9 JSON
- No server-side audio retention after analysis
- Model weights (`.joblib`) uploaded manually to Droplet, not in git
- UI derives a simplified `isDeepfake` flag for history compatibility

The **primary user-facing software deliverable** is the deployed Next.js web platform at https://www.deepfakedetection.dev/ (separate hosting repository — see `thesis_working_notes/FRONTEND_AND_DEPLOYMENT_STORY.md`). The FYP repo `release/` folder contains the Phase 9 inference backend **source** that was vendored into the website repo for production API deployment.

---

## 35. Evidence Sources Used for This Story

Important project documents and outputs used to reconstruct this story:

- Prior Cursor chats were also cross-checked. The most relevant chat history confirms the same project arc: binary CNN/EER work, HybridResNet, forensic product pivot, Phase 9 local demo freeze, AASIST/HybridResNet rejection as active release models, strict product naming, forbidden verdict wording, and partial fabrication as experimental/manual-review only. Relevant prior chats include [project story request](cd278bc7-6fe6-481d-a605-5fde0a2530fe), [Phase 9 UI and release freeze](61937c97-9237-4549-9849-67cc9d5c1565), and [Phase 9 release packaging](6c1ab685-ca2f-42d2-b421-1266e609a401).
- `README.md`
- `FASSD - Scope.md`
- `reports/COMPLETE_PROJECT_STORY.md`
- `reports/PREVIOUS_PIPELINE_WORK.md`
- `reports/FULL_PROJECT_DOCUMENTATION.md`
- `reports/evaluation/comprehensive_evaluation_report.md`
- `data/statistics/unified_dataset_stats.json`
- `reports/FORENSIC_PRODUCT_ROADMAP.md`
- `reports/phase7/PHASE7_FINAL_CLOSURE_REPORT.md`
- `reports/phase7/PHASE7_FINAL_STATUS_FREEZE.md`
- `reports/phase7/PHASE7_EXPERIMENT_RESULTS_SUMMARY.md`
- `reports/phase8/PHASE8_START_HERE.md`
- `reports/phase8/architecture/PHASE8A_ARCHITECTURE_FREEZE.md`
- `reports/phase8/freeze/phase8g_limitations_and_claims.md`
- `reports/phase8/freeze/phase8g_phase9_handoff_plan.md`
- `reports/phase9/partial_redesign/phase9d_p5d/phase9d_p5d_independent_evaluation_report.md`
- `reports/phase9/partial_redesign/phase9d_p5f/phase9d_p5f_expanded_evaluation_report.md`
- `reports/phase9/validation/phase9d_p5f_expanded_evaluation_validation_report.md`
- `reports/phase9/app/phase9e_p4a_origin_support/phase9e_p4a_shadow_comparison_report.md`
- `reports/phase9/validation/phase9e_p4b_demo_freeze_validation_report.md`
- `reports/phase9/integration_docs/phase9f_known_limitations.md`
- `reports/phase9/integration_docs/phase9f_release_file_map.md`
- `reports/phase9/final_release/phase9g_final_release_report.md`
- `release/README_RELEASE.md`
- `release/models/origin/origin_file_model__ssl__model_card.md`
- `release/models/replay/replay_file_model__acoustic__model_card.md`
- `release/models/mixer/mixer_file_model__acoustic__model_card.md`
- `release/models/partial_fabrication_experimental_p5b/partial_report_contract.json`
- `reports/release_audit/phase2_origin_release_2026-06-13/phase2_origin_release_report.md`
- `reports/release_audit/phase3_controlled_experiments_2026-06-13/phase3_controlled_experiments_decision.md`
- `reports/release_audit/phase4_two_stage_manipulation_v3_2026-06-13/phase4_two_stage_manipulation_v3_decision.md`
- `reports/release_audit/phase5_partial_redesign_2026-06-13/phase5_partial_redesign_decision.md`
- `reports/release_audit/phase6_calibration_2026-06-13/phase6_consistency_report.md`
- `reports/release_audit/phase7_final_release_2026-06-13/phase7_final_release_report.md`
- `release/MODEL_REGISTRY.md`
- `release/config/evidence_calibration.json`
- `thesis_working_notes/FRONTEND_AND_DEPLOYMENT_STORY.md`
- `reports/website/PARTNER_INTEGRATION_GUIDE.md`

---

## 36. Closing Statement

This project looks messy only if it is judged as a straight line. In reality, each shift corrected a false simplification:

- first, the project learned that spectrogram CNN success is not enough;
- then, it learned that environmental features need real-world data;
- then, it learned that hybrid binary models still collapse forensic meaning;
- then, it learned that AASIST and stronger anti-spoof models still do not solve product semantics;
- finally, it became a multi-axis forensic evidence system.

That is the final contribution of the project: not just a model, but a documented experimental path from simple deepfake detection to a forensic audio decision-support prototype, with the limits stated honestly.
