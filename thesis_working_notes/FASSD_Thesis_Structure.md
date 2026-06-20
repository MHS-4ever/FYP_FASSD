# Complete Revised Thesis Structure for FASSD

**Forensic Acoustics for Synthetic Speech Detection**

> **Per-heading writing notes:** `thesis_working_notes/FASSD_THESIS_SECTION_NOTES.md`  
> **Primary software deliverable:** https://www.deepfakedetection.dev/ (separate hosting repository)

## Front Matter

### Title Page

Add project title, student names, registration numbers, supervisor name, department, institute, and submission month/year according to the IST format.

### Approval by Board of Examiners

Use the official approval page format with signature spaces for supervisor, co-supervisor if any, and examiners.

### Authors’ Declaration

Use the university declaration format and state that the work was completed under supervision with proper acknowledgement of sources.

### Certificate

Add the supervisor certificate page in the format required by the template.

### Copyright Page

Use the copyright wording provided by the university template.

### Dedication

Add a short dedication to family, teachers, or people who supported the project.

### Acknowledgement

Thank the supervisor, department, institute, teammate, and any approved external guidance. Mention NCCIA only if the supervisor allows it.

### Abstract

Write a 200–250 word summary of the problem, methodology, main implementation work, key results, and final contribution of FASSD.

### Table of Contents

Auto-generate after the final document is formatted.

### List of Tables

Auto-generate after final tables are inserted.

### List of Figures

Auto-generate after final figures/screenshots are inserted.

### List of Abbreviations

- FASSD

- AI

- ASVspoof

- LA

- DF

- PA

- LFCC

- MFCC

- LCNN

- CNN

- ResNet

- AASIST

- SSL

- EER

- AUC

- VAD

- API

- UI

- JSON

- PDF

- SNR

- RT60

- and SDG

## Chapter 1: Introduction

### 1.1 Motivation

Explain why AI-generated speech is a problem for identity verification, digital trust, misinformation, and forensic audio review.

### 1.2 Background

Introduce synthetic speech, deepfake audio, spoofed speech, replayed audio, and why machine learning is used for detection.

### 1.3 Problem Statement

Define the main problem: detecting bonafide and spoofed speech while also considering forensic acoustic cues such as replay, noise, reverberation, and channel artifacts.

### 1.4 Approved Scope and Extended Development Boundary

Explain the official approved proposal scope first, then explain that later multi-axis forensic evidence, report generation, and interface work were extended development.

> **Required table:** Official Scope vs Extended Development Work.

### 1.5 Project Objectives

#### 1.5.1 Official Approved Objectives

List the approved objectives from the proposal: bonafide/spoof classification, forensic acoustic cues, embedded deepfake voice detection, replayed synthetic speech detection, augmented/real-world evaluation, and software deliverable.

#### 1.5.2 Extended Implementation Objectives

List the later objectives: multi-axis evidence, origin/replay/mixer/channel/partial-fabrication indicators, evidence-based reporting, and deployed web-based frontend (https://www.deepfakedetection.dev/ — separate hosting repository).

### 1.6 Scope of the Study

State what the thesis covers, including dataset preparation, feature extraction, model training, evaluation, final evidence system, report generation, and software interface.

### 1.7 Development Model

Explain that the project followed a hybrid iterative-incremental model with prototyping because the machine-learning pipeline required repeated testing, comparison, and improvement.

> **Required figure:** FASSD Iterative-Incremental Development Flow.

### 1.8 Environment and Sustainability

Explain the environmental and sustainability aspect of FASSD as a software-based cybersecurity and digital trust project, including responsible use of computational resources.

### 1.9 Relevance to Sustainable Development Goals

Briefly connect the project to relevant SDGs such as innovation, secure digital infrastructure, and institutional trust. Keep this section concise.

### 1.10 Thesis Outline

Give a short roadmap of the remaining chapters.

## Chapter 2: Literature Survey

### 2.1 Historical Background

Discuss the development of synthetic speech, voice conversion, spoofing attacks, and audio deepfake detection.

### 2.2 Synthetic Speech and Audio Deepfakes

Explain how AI-generated speech and voice cloning work at a high level and why they are difficult to detect.

### 2.3 Audio Anti-Spoofing

Discuss bonafide/spoof classification and the common anti-spoofing problem setup used in audio detection research.

### 2.4 ASVspoof Dataset and Evaluation Tracks

Explain ASVspoof and its relevance to FASSD, especially Logical Access, DeepFake, and replay/physical access concepts.

> **Required table:** ASVspoof Tracks and Relevance to FASSD.

### 2.5 Audio Features for Deepfake Detection

Discuss LFCC, MFCC/log-mel spectrograms, and acoustic/environmental features used in audio classification.

### 2.6 Deep Learning Models for Audio Detection

Review CNN/LCNN, ResNet-style models, and other deep learning approaches relevant to spoof detection.

### 2.7 Data Augmentation and Real-World Robustness

Discuss why noise, reverberation, codecs, replay simulation, and compression are used to improve generalization.

### 2.8 Advanced Anti-Spoofing and SSL-Based Methods

Discuss AASIST and self-supervised speech embeddings such as wav2vec2/WavLM-style approaches where supported by literature.

### 2.9 Forensic Audio Cues and Manipulation Evidence

Discuss replay signatures, background noise artifacts, reverberation, device/channel effects, and why these cues matter in forensic audio.

### 2.10 Partial Fabrication and Segment-Level Analysis

Explain why a full-file score may miss inserted synthetic regions and why segment-level evidence is useful.

### 2.11 Research Gaps

Identify the main gaps: many systems focus on binary classification, benchmark performance may not generalize to practical forensic cases, and separate evidence axes are needed for origin, replay, channel effects, and partial fabrication.

> **Required table:** Research Gaps and FASSD Response.

### 2.12 Summary of Literature Survey

Summarize how the literature supports both the approved scope and the later extended FASSD architecture.

## Chapter 3: Methodology And System Design

### 3.1 Overview of Methodology

Introduce the complete workflow from dataset preparation to final system output.

> **Required figure:** Overall FASSD Workflow.

### 3.2 Research Design

Explain that FASSD used experimental machine learning with iterative development, where each phase was tested and improved based on results.

### 3.3 Official Approved Methodology

Describe the proposal-based method: ASVspoof 2021 DF/LA, LFCC, Log-Mel, LCNN, augmentation, evaluation metrics, and software tool.

### 3.4 Extended Methodology

Explain how the project later expanded into ResNet, environmental features, HybridResNetEnvironmental, AASIST testing, and the final multi-axis evidence system.

### 3.5 Dataset Preparation

Describe datasets, manifests, labels, ASVspoof usage, augmented data, and any real-world/custom data supported by the project documentation.

> **Required table:** Dataset Summary.

### 3.6 Audio Preprocessing

Explain audio loading, conversion, resampling, normalization, segmentation, and preparation before feature extraction.

### 3.7 Data Augmentation

Describe augmentation methods such as noise, reverberation, codec distortion, replay simulation, gain, or clipping only where supported by the project files.

### 3.8 Feature Extraction

Explain the feature sets used in different phases of the project.

#### 3.8.1 LFCC Features

Describe LFCC extraction and its use in the early baseline.

#### 3.8.2 Log-Mel Spectrogram Features

Describe Log-Mel features and why they were compared with LFCC.

#### 3.8.3 Environmental and Acoustic Features

Describe forensic acoustic features such as noise, reverberation, SNR, spectral indicators, and channel-related cues.

#### 3.8.4 SSL Embeddings

Describe SSL embeddings for origin evidence if used in the final active system.

> **Required table:** Feature Sets Used in FASSD.

### 3.9 Baseline CNN/LCNN Model

Describe the initial baseline model and its role in the official approved scope.

### 3.10 ResNet-Based Model

Describe why a deeper ResNet-style model was tested after the baseline.

### 3.11 Environmental Feature Classifier

Explain the purpose of environmental/acoustic classification and why it was added after early real-world limitations.

### 3.12 HybridResNetEnvironmental Model

Explain how spectrogram features and environmental features were combined in a hybrid model.

### 3.13 AASIST Experiment

Explain why AASIST was tested and why it was kept as a reference/shadow model rather than the final active decision model.

### 3.14 Final Multi-Axis Forensic Architecture

Describe the final system architecture with separate evidence axes for origin, replay, mixer/channel, partial fabrication, segment evidence, fusion, and report generation.

> **Required figure:** Final Multi-Axis FASSD Architecture.

#### 3.14.1 Origin Evidence Axis

Explain the model or logic used to estimate whether the voice-origin evidence appears human, AI, mixed, or unknown.

#### 3.14.2 Replay/Rerecording Evidence Axis

Explain replay evidence and clarify that replay evidence does not automatically mean AI-generated speech.

#### 3.14.3 Mixer/Channel Evidence Axis

Explain mixer/channel processing evidence and why it is treated separately from AI-origin evidence.

#### 3.14.4 Partial Fabrication Evidence Axis

Explain segment-level candidate detection for possible inserted or replaced synthetic regions.

#### 3.14.5 Fusion and Manual Review Logic

Explain how the system combines evidence axes and uses cautious output instead of a forced legal-style verdict.

### 3.15 Report Generation

Describe JSON, PDF/report outputs, evidence bands, candidate segments, safety wording, and limitation statements.

### 3.16 System Interface and Deployment Design

Explain the system interface clearly: the primary user-facing software deliverable is the deployed Next.js web application at https://www.deepfakedetection.dev/ (separate hosting repository), integrated with the Phase 9 FastAPI inference API on DigitalOcean. The FYP repository `release/` folder contains the ML inference backend source used to build that API.

> **Required figure:** System Deployment Architecture.

### 3.17 API Design

Describe important backend API endpoints such as health check, model information, audio analysis, and report generation.

> **Optional table:** API Endpoints and Purpose. This can be moved to appendix if the chapter becomes too long.

### 3.18 Storage and Output Structure

Describe uploaded audio handling, generated reports, JSON outputs, case IDs, folders, or database structure if used in the system.

> **Optional table:** Storage/Output Structure. Use only if actual details are available.

### 3.19 Hardware and Software Environment

Mention the development machine, GPU, Python, PyTorch, Librosa, and other major tools/libraries.

> **Required table:** Hardware and Software Environment.

### 3.20 Ethical and Safety Considerations

Explain privacy, responsible use, manual review, no court-ready claim, and the risk of over-trusting automatic detection.

### 3.21 Methodology Limitations

Discuss dataset dependence, real-world generalization, compressed audio, replay/channel ambiguity, and partial-fabrication uncertainty.

## Chapter 4: Results And Discussion

### 4.1 Evaluation Overview

Explain the metrics used, such as EER, ROC-AUC, accuracy, confusion matrix, balanced accuracy, recall, and false positive behavior.

### 4.2 Baseline CNN/LCNN Results

Present the early baseline results and explain what they showed about the first working detection pipeline.

### 4.3 LFCC and Log-Mel Feature Comparison

Compare the feature results and explain why later phases moved beyond the first baseline.

### 4.4 ResNet Results

Present ResNet results and discuss why strong benchmark performance did not fully solve practical forensic detection.

### 4.5 Environmental Classifier Results

Present environmental classifier results and discuss their usefulness and limitations.

### 4.6 HybridResNetEnvironmental Results

Present hybrid model results, including binary and multiclass performance where available.

### 4.7 Controlled Forensic Evaluation Results

Present results for clean human, direct AI, replayed audio, mixer/channel processed audio, and partial fabrication cases.

### 4.8 AASIST and Historical Model Comparison

Present why AASIST and HybridResNet/ResNet were not selected as final active decision models.

### 4.9 Final Multi-Axis Evidence Results

Present final results for origin, replay, mixer/channel, and partial fabrication axes.

> **Required table:** Final Evidence-Axis Results.

### 4.10 Release/Demo Validation Results

Present final demo/release validation results, including inference success, pass/limitation counts, and known weaknesses.

### 4.11 Release Audit Results

Present the final testing audio matrix and explain what it showed about remaining origin, replay, mixer, and partial limitations.

> **Required table:** Consolidated Key Results Summary.

### 4.12 Interface and Report Output

Show selected screenshots of the final interface/report output and explain what the user receives after analysis.

> **Required screenshots:** 2–4 maximum, such as upload page, analysis result, report output, and waveform/timeline if available.

### 4.13 Discussion Against Literature

Compare FASSD with the literature, focusing on the difference between benchmark anti-spoofing and practical forensic review needs.

### 4.14 Official Objective-Wise Discussion

Explain how each official approved objective was achieved or partially achieved.

> **Required table:** Official Objectives vs Achieved Work.

### 4.15 Extended Contribution Discussion

Discuss the value of the extended multi-axis system, manual-review wording, partial-candidate evidence, and reporting layer.

### 4.16 Failure Cases and Limitations

Discuss false positives, missed cases, replay/mixer ambiguity, compressed audio weakness, and partial-fabrication limitations.

> **Required table:** Limitations and Failure Cases.

### 4.17 Summary of Results

Summarize the most important findings from Chapter 4.

## Chapter 5: Conclusion And Future Work

### 5.1 Conclusion

Summarize how FASSD achieved the approved software-based deepfake speech detection scope and expanded into an experimental forensic audio decision-support system.

### 5.2 Objective-Wise Conclusion

Briefly conclude each official and extended objective.

### 5.3 Main Contributions

State the main contributions: dataset/feature pipeline, model experiments, forensic acoustic analysis, multi-axis evidence design, report generation, and software interface.

### 5.4 Limitations

Restate the main limitations honestly without weakening the value of the project.

### 5.5 Future Work

Suggest broader external testing, improved replay/mixer generalization, better compressed-audio handling, stronger partial localization, web platform enhancements (full Phase 9 JSON in history, build quality), improved dataset diversity, and expert forensic validation.

### 5.6 Final Statement

End with a short final statement about FASSD as a BSCS-level foundation for deepfake audio detection and forensic audio decision support.

## References

### References

Use numbered references in citation order according to the IST format. Include only sources actually used in the thesis, such as ASVspoof, LFCC/LCNN, AASIST, SSL embeddings, audio deepfake surveys, replay/channel literature, and relevant dataset/tool references.

## Appendices

### Appendix A: Official Project Proposal Details

Add approved title, scope, objectives, implementation method, and deliverable summary.

### Appendix B: Dataset and Manifest Details

Add detailed dataset distributions, manifest samples, and label descriptions if too large for Chapter 3.

### Appendix C: Feature Extraction Details

Add extended feature details for LFCC, Log-Mel, environmental/acoustic features, and SSL embeddings.

### Appendix D: Model and Configuration Details

Add model settings, thresholds, active/inactive model list, and configuration files.

### Appendix E: API Documentation

Add endpoint details, request/response examples, and JSON samples.

### Appendix F: UI and Report Screenshots

Add extra screenshots that are useful but not necessary in Chapter 4.

### Appendix G: Additional Results

Add large result tables, confusion matrices, validation outputs, and release audit details.

### Appendix H: Ethical and Safety Wording

Add final claim limitations, manual-review warnings, and forbidden claim list.

### Appendix I: Repository/File Structure

Add important folders and files for reproducibility.
