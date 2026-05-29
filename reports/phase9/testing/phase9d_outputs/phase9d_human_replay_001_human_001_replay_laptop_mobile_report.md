# Experimental Forensic Analysis Report

Case ID: phase9d_human_replay_001_human_001_replay_laptop_mobile
Status: experimental_forensic_prototype

## Summary
Experimental prototype evidence indicators generated from packaged Phase 9B models. Fusion status: suspicious_replay_experimental. Successful axis predictions: 4/4. Candidate segments: 5. Manual review required. Output is consistent with multi-axis review workflow support only.

## Evidence axes (separate indicators)
Origin: experimental evidence indicator 'low_indicator' (strength=low, probability=0.000). This is not a final forensic proof.
Replay: experimental evidence indicator 'elevated_replay_rerecording_indicator' (strength=high, probability=0.996). This is not a final forensic proof.
Mixer/channel: experimental evidence indicator 'low_indicator' (strength=low, probability=0.146). This is not a final forensic proof.
Partial fabrication: partial segment activation was not used as elevated partial-fabrication evidence because stronger replay/mixer/channel evidence may explain the segment-level changes.

## Candidate segments
Top candidate segments: candidate segment seg_0006 (12.0s-16.0s) partial indicator=0.9999999677712287; candidate segment seg_0010 (20.0s-24.0s) partial indicator=0.9999998535793281; candidate segment seg_0004 (8.0s-12.0s) partial indicator=0.9999996631249874. Manual review recommended.

## Fusion
Fusion status: suspicious_replay_experimental
Risk level: medium
Manual review required: True

## Limitations
- experimental_forensic_prototype
- multi-axis evidence only; no single binary authenticity score
- AASIST/HybridResNet reference models inactive
- manual review recommended for elevated or mixed indicators
