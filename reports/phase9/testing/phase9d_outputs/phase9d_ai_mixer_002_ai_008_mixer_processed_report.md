# Experimental Forensic Analysis Report

Case ID: phase9d_ai_mixer_002_ai_008_mixer_processed
Status: experimental_forensic_prototype

## Summary
Experimental prototype evidence indicators generated from packaged Phase 9B models. Fusion status: suspicious_mixed_evidence_experimental. Successful axis predictions: 4/4. Candidate segments: 5. Manual review required. Output is consistent with multi-axis review workflow support only.

## Evidence axes (separate indicators)
Origin: experimental evidence indicator 'elevated_ai_origin_indicator' (strength=high, probability=0.539). This is not a final forensic proof.
Replay: experimental evidence indicator 'low_indicator' (strength=low, probability=0.295). This is not a final forensic proof.
Mixer/channel: experimental evidence indicator 'elevated_mixer_channel_indicator' (strength=high, probability=0.993). This is not a final forensic proof.
Partial fabrication: partial segment activation was not used as elevated partial-fabrication evidence because stronger replay/mixer/channel evidence may explain the segment-level changes.

## Candidate segments
Top candidate segments: candidate segment seg_0003 (6.0s-10.0s) partial indicator=0.9999986683282233; candidate segment seg_0019 (38.0s-42.0s) partial indicator=0.9999312780687328; candidate segment seg_0007 (14.0s-18.0s) partial indicator=0.9997936469037902. Manual review recommended.

## Fusion
Fusion status: suspicious_mixed_evidence_experimental
Risk level: high
Manual review required: True

## Limitations
- experimental_forensic_prototype
- multi-axis evidence only; no single binary authenticity score
- AASIST/HybridResNet reference models inactive
- manual review recommended for elevated or mixed indicators
