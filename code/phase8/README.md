# Phase 8 — Multi-Axis Forensic Audio Intelligence (Code)

**Status:** Initialized — **no implementation yet**  
**Reports hub:** [reports/phase8/README.md](../../reports/phase8/README.md)

---

## Purpose

Phase 8 builds a **multi-axis forensic audio intelligence architecture** after Phase 7 demonstrated that single binary spoof/fake or origin-style models are **insufficient** for the forensic product goal.

Phase 8 does **not** begin by training another binary classifier.

---

## Folder map

| Folder | Planned role |
|--------|----------------|
| `evidence_table/` | Per-file / per-segment evidence table builder (Phase 8B) |
| `features/` | Acoustic, channel, partial-region, and SSL embedding extraction |
| `models/` | Lightweight multi-axis classifiers (not monolithic fake/real) |
| `fusion/` | Calibrated fusion, abstention, manual-review routing |
| `reporting/` | Report-ready evidence summaries (Phase 8G) |
| `validation/` | Locked evaluation + checkpoint organization (`organize_model_checkpoints.py`) |

---

## Rules (hard)

- **Do not** train a binary fake/real or spoof/bonafide model without **multi-axis design approval** (Phase 8A freeze).
- **Do not** use hard AI/human first-stage routing as the primary architecture.
- **Do not** overwrite Phase 7 experiment CSVs, checkpoints, or eval outputs.
- **Do not** claim court-ready or final forensic proof from prototype fusion.

---

## Planned modules (not implemented)

1. Evidence table schema + builder  
2. Feature extractors (acoustic/channel + frozen SSL later)  
3. Parallel axis scorers (origin, manipulation, segment)  
4. Fusion layer with abstention  
5. Validation harness vs Phase 7 locked benchmarks  
6. Report layer integration (after evidence layer stabilizes)

---

## Checkpoint organization (copy only)

Organize usable and archived checkpoints into `models_saved/` without moving originals:

```text
python code/phase8/validation/organize_model_checkpoints.py --models_root models_saved
```

Registry outputs: `models_saved/registry/CHECKPOINT_REGISTRY.md`

- **active/** — HybridResNet baseline evidence (required)
- **prototype_evidence/** — 7C3-R2 support-only (not standalone)
- **pretrained_reference/** — official AASIST weights (reference only)
- **rejected_archive/** — fine-tuned AASIST rejected checkpoints (archive only)

Use `--dry_run` to preview; `--overwrite` only when replacing a mismatched copy.

---

## Next step

Review Phase 8 planning docs under `reports/phase8/` — start with [PHASE8_START_HERE.md](../../reports/phase8/PHASE8_START_HERE.md).
