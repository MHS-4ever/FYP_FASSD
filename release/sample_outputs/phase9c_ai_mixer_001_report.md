# Experimental Forensic Analysis Report

Case ID: phase9c_ai_mixer_001
Status: experimental_forensic_prototype

## Summary
Experimental prototype evidence indicators generated from packaged Phase 9B models. Fusion status: suspicious_mixer_channel_experimental. Successful axis predictions: 4/4. Candidate segments: 5. Manual review required. Output is consistent with multi-axis review workflow support only.

## Evidence axes (separate indicators)
Origin: experimental evidence indicator 'elevated_ai_origin_indicator' (strength=borderline, probability=0.242). This is not a final forensic proof.
Replay: experimental evidence indicator 'low_indicator' (strength=borderline, probability=0.558). This is not a final forensic proof.
Mixer/channel: experimental evidence indicator 'elevated_mixer_channel_indicator' (strength=high, probability=0.954). This is not a final forensic proof.
Partial fabrication: partial segment activation was not used as elevated partial-fabrication evidence because stronger replay/mixer/channel evidence may explain the segment-level changes.

## Candidate segments
Top candidate segments: candidate segment seg_0006 (12.0s-16.0s) partial indicator=1.0; candidate segment seg_0004 (8.0s-12.0s) partial indicator=0.9999999999999549; candidate segment seg_0021 (42.0s-46.0s) partial indicator=0.9999999999983695. Manual review recommended.

## Fusion
Fusion status: suspicious_mixer_channel_experimental
Risk level: medium
Manual review required: True

## Limitations
- experimental_forensic_prototype
- multi-axis evidence only; no fake_score or real_score
- AASIST/HybridResNet reference models inactive
- manual review recommended for elevated or mixed indicators
