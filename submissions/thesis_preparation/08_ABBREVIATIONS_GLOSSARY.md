# Abbreviations and Glossary

Terms relevant to FASSD only. Expand per supervisor/template requirements.

---

## Abbreviations

| Abbreviation | Full form |
|--------------|-----------|
| AI | Artificial Intelligence |
| API | Application Programming Interface |
| ASV | Automatic Speaker Verification |
| ASVspoof | Automatic Speaker Verification Spoofing and Countermeasures Challenge |
| AUC | Area Under the Curve (ROC) |
| AASIST | Anti-spoofing with Attention-based Spectrogram-Temporal modeling |
| CNN | Convolutional Neural Network |
| DF | DeepFake track (ASVspoof 2021) |
| EER | Equal Error Rate |
| FASSD | Forensic Acoustics for Synthetic Speech Detection |
| FPR | False Positive Rate |
| FYP | Final Year Project |
| HDF5 | Hierarchical Data Format version 5 |
| JSON | JavaScript Object Notation |
| LA | Logical Access track (ASVspoof 2021) |
| LCNN | Lightweight Convolutional Neural Network |
| LFCC | Linear Frequency Cepstral Coefficients |
| LR | Logistic Regression |
| MFCC | Mel-Frequency Cepstral Coefficients |
| MLP | Multi-Layer Perceptron |
| MP4 | MPEG-4 Part 14 (media container) |
| OOF | Out-of-Fold (cross-validation predictions) |
| PA | Physical Access / replay track (ASVspoof 2021) |
| PDF | Portable Document Format |
| ResNet | Residual Network |
| RIR | Room Impulse Response |
| ROC | Receiver Operating Characteristic |
| RT60 | Reverberation time (decay to −60 dB) |
| SDG | Sustainable Development Goal (United Nations) |
| SNR | Signal-to-Noise Ratio |
| SSL | Self-Supervised Learning (speech representation) |
| TTS | Text-to-Speech |
| UI | User Interface |
| VAD | Voice Activity Detection |
| VC | Voice Conversion |
| wav2vec2 | Self-supervised speech representation model family (Meta) |
| WavLM | Self-supervised speech pre-training model (Microsoft) |

---

## Project-Specific Terms

| Term | Definition |
|------|------------|
| Origin evidence | Indicator whether speech content is likely human-generated, AI-synthetic, mixed, or unknown — not a legal verdict (`FASSD - Scope.md`) |
| Replay evidence | Indicator of rerecording/playback chain artifacts — **does not imply AI-generated** (`release/MODEL_REGISTRY.md`) |
| Mixer/channel evidence | Indicator of mixer, PA, phone, or channel processing — **does not imply AI-generated** (same) |
| Partial fabrication evidence | Segment-level candidate regions where inserted/replaced content may exist; manual review required (`partial_report_contract.json`) |
| Evidence band | User-facing Low / Medium / High strength label from Phase 6 calibration (`release/config/evidence_calibration.json`) |
| Leakage-safe split | Train/dev/test split preventing speaker/base/pair leakage (`FASSD - Scope.md`) |
| testing_audios | External heterogeneous forensic test set used in release audit (25 files in final matrix) |
| Phase 7C1 | Local controlled forensic dataset (184 files, 8 conditions) |
| HybridResNetEnvironmental | Combined log-mel ResNet + 12 environmental features model — **reference/inactive** in final release |
| reject_for_now | Phase 9 decision to keep AASIST/HybridResNet out of active inference (`phase9g_final_release_report.md`) |
| experimental_manual_review_only | Partial module status requiring human review (`phase9f_known_limitations.md`) |
| F9 features | Removed within-file percentile/max-normalized deviation features that caused broad partial activation (`release/MODEL_REGISTRY.md`) |
| bonafide | Genuine human speech in anti-spoofing terminology |
| spoof | Non-bonafide / synthetic or attacked speech in anti-spoofing terminology |
| risk_positive | Forensic-risk flag in Phase 7 — **not synonymous with AI-generated** (`PHASE8A_ARCHITECTURE_FREEZE.md`) |

---

## Glossary (Selected)

| Term | Meaning in FASSD context |
|------|--------------------------|
| Deepfake audio | Colloquial term for synthetically generated or manipulated speech audio; thesis prefers "synthetic speech" or "spoofed audio" where precise |
| Forensic acoustics | Analysis of recording chain, environment, and manipulation indicators beyond content-only detection |
| Decision-support prototype | System that presents evidence for human review rather than automated legal determination |
| Multi-axis fusion | Combining parallel origin, replay, mixer, and partial indicators with abstention rules |
| Controlled forensic evaluation | Phase 7 program using labeled local roles (clean, replay, mixer, partial, AI variants) |
| Release audit | Post-Phase-9 repair cycle (Phases 0–7) fixing origin, partial, and UI wording before final matrix |

---

## Terms Intentionally Avoided in Thesis

| Avoid | Prefer |
|-------|--------|
| Forensic Deepfake Audio Detector (product title) | FASSD — Forensic Acoustics for Synthetic Speech Detection |
| Proves fake / proves real | Indicates evidence consistent with … / recommends manual review |
| Court-ready | Experimental decision-support prototype |
| Detects all deepfakes | Detects selected evidence indicators under evaluated conditions |
