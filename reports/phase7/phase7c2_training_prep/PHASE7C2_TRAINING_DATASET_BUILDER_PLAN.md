# Phase 7C2 — Training Dataset Builder Plan

**Status:** **Signed off** — approved for Phase 7C3; **no fine-tuning run in 7C2**

---

## 1. Goal

Create safe **train / val / test** manifests that combine:

1. A **balanced old subset** (general spoof knowledge)
2. **Phase 7C1** forensic collection (local product behavior, higher weights)
3. **Loss masks** and **sample weights** for multi-task training
4. **Holdout protection** for Phase 7A (T1–T5)

---

## 2. Why not the full old dataset (~1.89M rows)

Phase 7C1 has only **184** files. Adding all legacy rows would **drown** local forensic signal and preserve studio/PA/replay bias from ASVspoof-heavy corpora.

---

## 3. Why not Phase 7C1 only

The current model still relies on broad **synthesis / conversion / spoof** diversity from legacy data. Training on 184 files alone risks **forgetting** general deepfake detection.

---

## 4. Balanced old subset strategy

Per split, sample up to **N rows per attack group** (deterministic seed **42**):

| Group | Old mapping |
|-------|-------------|
| bonafide | `label=bonafide` |
| synthesis | `label=spoof`, `attack_type=synthesis` |
| conversion | `label=spoof`, `attack_type=conversion` |
| replay | `label=spoof`, `attack_type=replay` |

**Approved caps:** train **250** per attack (max **1000** old + **128** 7C1 = **1128**), val **50** each (**224** total), test **50** each (**232** total).  
Rejected first draft (1000/200/200): ~97% old rows — 7C1 drowned despite weights.

---

## 5. Phase 7C1 weighting strategy

Base weights by variant (see `phase7c2_sample_weighting_rules.md`). Additional bonuses from **baseline_status** (false alarms, missed AI, missed partial). Cap: **4.0**.

---

## 6. Loss masking strategy

Old **replay** rows: `use_origin_loss=false` so PA replay does not teach “replay ⇒ AI origin.”

Phase 7C1: all four loss heads enabled (`origin`, `manipulation`, `attack`, `partial`).

---

## 7. Holdout protection

Scan combined manifests against `reports/phase7/phase7_forensic_tests/forensic_test_manifest.csv` by path, basename, and test_id/sample_id. **Any overlap is critical.**

---

## 8. Validation rules

See `validate_phase7c2_training_manifests.py` — duplicate paths, cross-split leakage, 7C1 `base_id` integrity, weights, timestamps on fabricated rows.

---

## 9. What this enables for Phase 7C fine-tuning

After sign-off:

- Phase **7C3** can implement the actual fine-tuning script reading these manifests
- Multi-task losses respect `use_*_loss` columns
- Weighted sampling uses `sample_weight`

---

## 10. What not to do

- Do **not** train in Phase 7C2
- Do **not** merge Phase 7A holdout
- Do **not** use REAL/FAKE-only labels
- Do **not** randomly split Phase 7C1 `base_id` groups across train/val/test
