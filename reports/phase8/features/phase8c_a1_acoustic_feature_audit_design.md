# Phase 8C-A1 — Acoustic Feature Audit Design

**Status:** Scripts created — **NOT YET EXECUTED** (unless user runs audit)  
**Code:** `code/phase8/features/audit_phase8c_acoustic_features.py`

---

## Purpose

Phase 8C-A1 is a **descriptive sanity audit** of Phase 8C acoustic/channel features on the controlled Phase 7C1 set. It answers whether features are internally consistent, which columns are missing, and whether **known** label groups show measurable shifts — **before** Phase 8D (SSL embeddings) or Phase 8E (lightweight models).

---

## Why this audit exists

| Question | Phase 8C-A1 approach |
|----------|----------------------|
| Are CSVs consistent with 8B? | ID and row-count checks |
| Which features are empty? | Missingness report + usability flags |
| Do replay/mixer/partial groups differ? | Group means/medians + effect-size ranking |
| Any extraction artifacts? | Zero variance, 100% missing, status counts |
| What is safe for 8E? | Top candidates with cautious notes |

This is **not** classifier accuracy, not AI detection, not forensic proof.

---

## What descriptive group differences mean

- We compare **known experiment labels** (origin/manipulation from manifests) to feature distributions.
- A large effect size means groups **differ descriptively** on that indicator — not that the feature alone detects fraud.
- Rankings help **prioritize** features for later modeling — they do not validate a product decision.

---

## Segment label inheritance

Phase 8B segment rows do not carry separate manipulation ground truth per window in this controlled set. The audit joins **file-level** `known_origin_label` and `known_manipulation_labels` onto segments by `file_id`.

**Wording in reports:** “Segment group analysis is based on file-level known labels unless true segment annotations are available.”

---

## Fast segment mode limitations

Phase 8C used `--segment_feature_mode fast`. Expect:

- 100% blank: segment `mfcc_*`, `spectral_contrast_mean`
- Often blank: `very_high_band_energy_ratio` at 16 kHz (Nyquist 8 kHz)

Missing columns are **expected**, not extraction failures. Usability flags: `usable`, `limited`, `exclude_for_now`.

---

## Comparisons (file-level)

1. Clean human vs clean AI-synthetic (both `clean` manipulation)  
2. Clean vs replay_rerecorded  
3. Clean vs mixer_channel_processed  
4. Clean vs partial/edited combo (`edited_spliced;partial_fabrication`)  
5. Human vs AI-synthetic (all manipulations)  
6. Clean vs non-clean  

## Comparisons (segment-level, inherited labels)

1. Clean vs replay (inherited)  
2. Clean vs mixer (inherited)  
3. Clean vs partial combo (inherited)  

---

## Outputs

| File | Content |
|------|---------|
| `phase8c_a1_file_feature_summary.csv` | Stats by origin/manipulation/all |
| `phase8c_a1_segment_feature_summary.csv` | Segment stats (inherited labels) |
| `phase8c_a1_missingness_report.csv` | Missing % + usability |
| `phase8c_a1_group_difference_*.csv` | Pairwise descriptive diffs |
| `phase8c_a1_top_candidate_features.csv` | Ranked candidates per comparison |
| `phase8c_a1_feature_correlation_summary.csv` | Redundancy pairs |
| `phase8c_a1_acoustic_feature_audit_report.md` | Human-readable summary |
| `figures/` | Optional matplotlib plots |

---

## CLI

```text
python code/phase8/features/audit_phase8c_acoustic_features.py --make_plots

python code/phase8/validation/validate_phase8c_a1_audit.py
```

Options: `--no_progress`, `--progress_every`, `--top_k`, `--max_features_for_plots`.

---

## Forensic product alignment

Supports the multi-axis goal by identifying **channel/replay/quality indicators** that may later inform manipulation evidence scores — separate from origin (AI vs human) and without collapsing to fake/real.

**Phase 8D:** NOT STARTED.

---

## Progress rule (future scripts)

Long-running Phase 8 scripts must include: progress display, test limits (`--max_files`), resume where applicable, terminal summary, validation after generation.
