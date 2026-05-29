# Experimental Forensic Analysis Report

Case ID: phase9c_replay_001
Status: experimental_forensic_prototype

## Summary
Experimental prototype evidence indicators generated from packaged Phase 9B models. Fusion status: suspicious_replay_experimental. Successful axis predictions: 4/4. Candidate segments: 5. Manual review required. Output is consistent with multi-axis review workflow support only.

## Evidence axes (separate indicators)
Origin: experimental evidence indicator 'low_indicator' (strength=low, probability=0.011). This is not a final forensic proof.
Replay: experimental evidence indicator 'elevated_replay_rerecording_indicator' (strength=high, probability=0.996). This is not a final forensic proof.
Mixer/channel: experimental evidence indicator 'low_indicator' (strength=low, probability=0.106). This is not a final forensic proof.
Partial fabrication: partial segment activation was broad across the file, so it is not treated as localized partial-fabrication evidence.

## Candidate segments
Top candidate segments: candidate segment seg_0016 (32.0s-36.0s) partial indicator=1.0; candidate segment seg_0006 (12.0s-16.0s) partial indicator=0.9999999999999625; candidate segment seg_0022 (44.0s-48.0s) partial indicator=0.9999999999999338. Manual review recommended.

## Fusion
Fusion status: suspicious_replay_experimental
Risk level: medium
Manual review required: True

## Limitations
- experimental_forensic_prototype
- multi-axis evidence only; no fake_score or real_score
- AASIST/HybridResNet reference models inactive
- manual review recommended for elevated or mixed indicators
