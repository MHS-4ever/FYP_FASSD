# Experimental Forensic Analysis Report

Case ID: phase9d_human_mixer_002_human_010_mixer_processed
Status: experimental_forensic_prototype

## Summary
Experimental prototype evidence indicators generated from packaged Phase 9B models. Fusion status: suspicious_mixer_channel_experimental. Successful axis predictions: 4/4. Candidate segments: 5. Manual review required. Output is consistent with multi-axis review workflow support only.

## Evidence axes (separate indicators)
Origin: experimental evidence indicator 'low_indicator' (strength=low, probability=0.001). This is not a final forensic proof.
Replay: experimental evidence indicator 'low_indicator' (strength=borderline, probability=0.619). This is not a final forensic proof.
Mixer/channel: experimental evidence indicator 'elevated_mixer_channel_indicator' (strength=high, probability=0.998). This is not a final forensic proof.
Partial fabrication: partial segment activation was not used as elevated partial-fabrication evidence because stronger replay/mixer/channel evidence may explain the segment-level changes.

## Candidate segments
Top candidate segments: candidate segment seg_0002 (4.0s-8.0s) partial indicator=0.9999998690322756; candidate segment seg_0010 (20.0s-24.0s) partial indicator=0.9999989866066779; candidate segment seg_0017 (34.0s-37.0347s) partial indicator=0.9999647145560508. Manual review recommended.

## Fusion
Fusion status: suspicious_mixer_channel_experimental
Risk level: medium
Manual review required: True

## Limitations
- experimental_forensic_prototype
- multi-axis evidence only; no single binary authenticity score
- AASIST/HybridResNet reference models inactive
- manual review recommended for elevated or mixed indicators
