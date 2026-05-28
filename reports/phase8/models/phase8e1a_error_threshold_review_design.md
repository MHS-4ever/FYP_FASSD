# Phase 8E-1A Error and Threshold Review Design

## Why Phase 8E-1A Exists
Phase 8E-1 produced experimental cross-validated file-level evidence outputs. Before any fusion work, Phase 8E-1A reviews where those outputs fail, how probabilities behave, and which threshold candidates may be safer for later fusion exploration.

## Why Error Analysis Before Fusion
- Fusion logic must understand false-positive and false-negative patterns by axis.
- Clean-human and clean-negative protection requires explicit error review.
- Small datasets can hide risk behind high aggregate accuracy.

## What Threshold Review Means
Phase 8E-1A computes threshold-grid tradeoffs per task/feature set using existing out-of-fold probabilities:
- clean false-positive behavior
- positive detection behavior
- balanced accuracy and F1 behavior

This produces candidate thresholds for review only.

## Why Recommendations Are Not Final Thresholds
- The dataset is small and controlled.
- OOF predictions are experimental.
- Threshold candidates require additional validation and manual review policies.

## Calibration Review Without Fitting
Phase 8E-1A evaluates calibration quality (Brier score, ECE, reliability summaries) from existing probabilities only.
No Platt, isotonic, or other calibration model is fitted.

## Protection Priorities
- Origin: prioritize clean-human false-AI protection.
- Replay/Mixer: prioritize clean-negative false-positive protection.

## Relation to Phase 8F Fusion
Outputs from this phase inform Phase 8F candidate selection and abstention/manual-review strategy, while explicitly avoiding hard forensic claims.
