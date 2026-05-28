# Phase 8 Evidence Model Registry

All models below are experimental forensic evidence models on controlled Phase 7C1 data.

## 1) origin_file_model
- phase created: 8E-1
- dataset: Phase 8E-0 origin file dataset
- target: clean human vs clean AI synthetic origin evidence
- feature set: ssl
- model type: logistic_regression_l2
- threshold candidate: 0.2
- allowed use: origin evidence indicator for fusion/manual review
- forbidden use: final fake/real verdict or court-ready claim
- limitations: controlled dataset; domain shift risk
- status: experimental_forensic_evidence_model

## 2) replay_file_model
- phase created: 8E-1
- dataset: Phase 8E-0 replay file dataset
- target: replay/rerecording evidence
- feature set: acoustic
- model type: logistic_regression_l2
- threshold candidate: 0.65
- allowed use: replay evidence indicator in fusion
- forbidden use: direct AI-origin claim from replay alone
- limitations: controlled dataset; replay is not origin class
- status: experimental_forensic_evidence_model

## 3) mixer_file_model
- phase created: 8E-1
- dataset: Phase 8E-0 mixer file dataset
- target: mixer/channel processing evidence
- feature set: acoustic
- model type: logistic_regression_l2
- threshold candidate: 0.75
- allowed use: mixer/channel evidence indicator in fusion
- forbidden use: direct AI-origin claim from mixer alone
- limitations: controlled dataset; channel effects vary in real-world audio
- status: experimental_forensic_evidence_model

## 4) partial_fabrication_segment_model
- phase created: 8E-3
- dataset: timestamp-aligned segment labels from Phase 8E-2
- target: fabricated_region vs outside_fabricated_region
- feature set: combined
- model type: logistic_regression_l2
- threshold candidate: selected from Phase 8E-3 threshold grid
- allowed use: candidate segment localization evidence
- forbidden use: final proof of fabrication
- limitations: timestamp annotation quality and controlled dataset scope
- status: experimental_forensic_evidence_model
