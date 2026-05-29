# Experimental Forensic Analysis Report

Case ID: phase9d_ai_replay_004_ai_011_replay_laptop_mobile
Status: experimental_forensic_prototype

## Summary
Experimental prototype evidence indicators generated from packaged Phase 9B models. Fusion status: suspicious_replay_experimental. Successful axis predictions: 4/4. Candidate segments: 5. Manual review required. Output is consistent with multi-axis review workflow support only.

## Evidence axes (separate indicators)
Origin: experimental evidence indicator 'low_indicator' (strength=low, probability=0.048). This is not a final forensic proof.
Replay: experimental evidence indicator 'elevated_replay_rerecording_indicator' (strength=high, probability=1.000). This is not a final forensic proof.
Mixer/channel: experimental evidence indicator 'low_indicator' (strength=low, probability=0.079). This is not a final forensic proof.
Partial fabrication: partial segment activation was broad across the file, so it is not treated as localized partial-fabrication evidence.

## Candidate segments
Top candidate segments: candidate segment seg_0005 (10.0s-14.0s) partial indicator=1.0; candidate segment seg_0020 (40.0s-44.0s) partial indicator=0.9999999999999982; candidate segment seg_0009 (18.0s-22.0s) partial indicator=0.999999999968026. Manual review recommended.

## Fusion
Fusion status: suspicious_replay_experimental
Risk level: medium
Manual review required: True

## Limitations
- experimental_forensic_prototype
- multi-axis evidence only; no single binary authenticity score
- AASIST/HybridResNet reference models inactive
- manual review recommended for elevated or mixed indicators
