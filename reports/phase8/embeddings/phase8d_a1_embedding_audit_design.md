# Phase 8D-A1 — SSL Embedding Sanity Audit Design

**Status:** Script created — **NOT YET EXECUTED**  
**Scope:** Descriptive analysis only

---

## Purpose

Phase 8D-A1 performs a descriptive sanity audit of frozen SSL embeddings from Phase 8D.
It checks data quality, internal consistency, missingness, and group-wise descriptive separation before Phase 8E.

This is not model training, not classification, and not forensic proof.

---

## Why this audit is needed before Phase 8E

- Confirms embeddings are usable (non-blank, finite, consistent dimensions).
- Identifies unstable/redundant dimensions and missingness risks.
- Provides initial candidate dimensions for later lightweight modeling.
- Avoids pushing noisy or degenerate features into Phase 8E.

---

## What descriptive embedding differences mean

- Group differences here are **descriptive** and label-conditioned.
- Effect-size ranking indicates potential separability, not predictive performance.
- Any candidate dimension still requires Phase 8E training + calibration validation.

---

## Key analyses

1. ID/row consistency vs Phase 8B tables  
2. Missingness, zero variance, all-blank rows  
3. File-level descriptive summaries by:
   - `known_origin_label`
   - `known_manipulation_labels`
4. Segment-level summaries using inherited file labels
5. Group differences (absolute mean diff + Cohen-style effect size)
6. Embedding norm summaries (`l2_norm`, mean/max abs)
7. Correlation summary for redundancy among dimensions

---

## Required caution

- Segment group analysis uses **file-level inherited labels** unless true segment annotations are available.
- Individual embedding dimensions are latent factors and less interpretable than handcrafted acoustic features.
- A single embedding dimension is **not a standalone detector**.

---

## Why this supports forensic product goals

The audit helps curate robust representation signals that can later support:

- origin evidence heads,
- manipulation evidence heads,
- mixed/partial behavior modeling,

without collapsing into fake/real claims.

---

## Not in scope

- Any training/fine-tuning
- Any classifier fitting
- Any predictions
- Any fake/real score or final forensic decision
- Any modification of Phase 8B/8C/8D generated data files

---

## Progress and execution hygiene

The audit script includes progress display (tqdm/fallback), and paired validator checks output integrity.

Future long-running scripts should continue to include:

- progress reporting
- bounded test mode where useful
- clear terminal summary
- post-generation validation

---

## Outputs

- `phase8d_a1_file_embedding_summary.csv`
- `phase8d_a1_segment_embedding_summary.csv`
- `phase8d_a1_missingness_report.csv`
- `phase8d_a1_group_difference_file_embeddings.csv`
- `phase8d_a1_group_difference_segment_embeddings.csv`
- `phase8d_a1_top_candidate_embedding_dims.csv`
- `phase8d_a1_embedding_correlation_summary.csv`
- `phase8d_a1_embedding_norm_summary.csv`
- `phase8d_a1_ssl_embedding_audit_report.md`

