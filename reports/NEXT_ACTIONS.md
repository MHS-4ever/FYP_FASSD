# FASSD Next Actions

**Product:** [Forensic Voice Authenticity Analyzer](UPDATED_PROJECT_SCOPE.md)  
**Canonical Phase 7 docs:** [phase7/README.md](phase7/README.md)  
**Phase 7C frozen:** [phase7/PHASE7C_FINAL_DECISION_RECORD.md](phase7/PHASE7C_FINAL_DECISION_RECORD.md) | [phase7/PHASE7C_STATUS_FREEZE.md](phase7/PHASE7C_STATUS_FREEZE.md)

---

## Signed off

- **Phase 7A** — Controlled forensic testing  
- **Phase 7B** — Forensic label preparation (T1–T5 `controlled_holdout`)  
- **Phase 7C0** — Current/original training dataset audit  
- **Phase 7C1** — Collection (184 files) + baseline evaluation  
- **Phase 7C2** — Training manifests (balanced old subset + weighted 7C1)  
- **Phase 7C4-v2** — Decision-layer prototype (**accepted** on Phase 7C1 criteria; not a final model)

---

## Current next actions (Phase 7D — planning complete)

**Phase 7C decision record completed.** Do **not** train or fine-tune. Do **not** change Phase 7C4-v2 decision logic yet. Do **not** implement PDF or web UI.

1. **Review Phase 7D specs** in [phase7/phase7d_report_layer/](phase7/phase7d_report_layer/) (schema, wording, mapping, examples).  
2. **Primary spec:** [phase7/phase7d_report_layer/PHASE7D_FORENSIC_REPORT_LAYER_PLAN.md](phase7/phase7d_report_layer/PHASE7D_FORENSIC_REPORT_LAYER_PLAN.md).  
3. **Next implementation (7D1):** `code/phase7/build_phase7d_forensic_report.py` — JSON + Markdown from `phase7c4_v2_candidate_decisions.csv` (not started until approved).  
4. **Inputs frozen:** `reports/phase7/phase7c4_calibration_v2/calibration_outputs/phase7c4_v2_candidate_decisions.csv` + baseline/R2/partial/chunk evidence.  
5. Optional: run `check_phase7c4_holdout_impact.py` on Phase 7A before 7D2 holdout reports.  
6. Resume training only after 7D integration and/or new controlled data + evaluation protocol.

### Phase 7D document index

| Doc | Purpose |
|-----|---------|
| [phase7/phase7d_report_layer/README.md](phase7/phase7d_report_layer/README.md) | Hub |
| [PHASE7D_REPORT_OUTPUT_SCHEMA.md](phase7/phase7d_report_layer/PHASE7D_REPORT_OUTPUT_SCHEMA.md) | JSON fields |
| [PHASE7D_DECISION_TO_REPORT_MAPPING.md](phase7/phase7d_report_layer/PHASE7D_DECISION_TO_REPORT_MAPPING.md) | Status → report |
| [PHASE7D_REPORT_WORDING_GUIDE.md](phase7/phase7d_report_layer/PHASE7D_REPORT_WORDING_GUIDE.md) | Safe language |
| [PHASE7D_TEST_CASE_REPORT_EXPECTATIONS.md](phase7/phase7d_report_layer/PHASE7D_TEST_CASE_REPORT_EXPECTATIONS.md) | QA cases |

### Environment

Use **`python`** inside the activated **`(fassd)`** conda environment — not `py -3` (system Python may lack project dependencies).

### Re-run v2 decision layer (reference only; does not change frozen decision)

```text
python code/phase7/apply_phase7c4_v2_decision_layer.py
```

Defaults write to `reports/phase7/phase7c4_calibration_v2/`. See [phase7/phase7c4_calibration_v2/README.md](phase7/phase7c4_calibration_v2/README.md).

---

## Phase 7C — frozen decisions (summary)

| Item | Status |
|------|--------|
| Phase 6 baseline checkpoint | Evidence source — **yes** |
| 7C3-v1 | **Rejected** |
| 7C3-R2 checkpoints | **Rejected** standalone; evidence-only in fusion |
| 7C4-v1 | **Rejected** |
| 7C4-v2 | **Accepted** decision-layer prototype only |

Detail: [phase7/PHASE7C_FINAL_DECISION_RECORD.md](phase7/PHASE7C_FINAL_DECISION_RECORD.md).

---

## Historical commands (archived)

Phase 7C4 v1 (rejected), threshold sweep, and 7C3-R2 training commands are preserved in git history and subfolder READMEs. Do not treat their outputs as current product defaults.

- v1 calibration: `reports/phase7/phase7c4_calibration/`  
- v1 fine-tune: `reports/phase7/phase7c3_finetune/`  
- R2 fine-tune: `reports/phase7/phase7c3_finetune_r2/`

---

## Recording checklist (7C1 collection — reference)

- [ ] **20–30 s** default clips; **30–45 s** for partial insertion  
- [ ] No clip **&lt; 8 s**; **0.5–1 s** silence at start/end  
- [ ] **Paired** variants in **same split**  
- [ ] Partial inserts: mandatory `suspicious_start_time` / `suspicious_end_time`  
- [ ] Urdu/Pakistani prioritized across categories  

---

## Do not do yet

- Do **not** fine-tune or train new checkpoints without a new evaluation plan.  
- Do **not** deploy 7C3-v1, standalone R2, or 7C4-v1 as product scorers.  
- Do **not** claim final forensic accuracy or market-ready automation from 7C4-v2.  
- Do **not** merge **Phase 7A T1–T5** into training (`controlled_holdout`).  
- Do **not** start Phase **7E** before 7D report layer review.  
- Do **not** change Phase 6 core inference unless explicitly requested.

---

## Quick links

| Doc | Use |
|-----|-----|
| [phase7/PHASE7C_FINAL_DECISION_RECORD.md](phase7/PHASE7C_FINAL_DECISION_RECORD.md) | **Frozen** 7C decisions |
| [phase7/PHASE7D_FORENSIC_REPORT_LAYER.md](phase7/PHASE7D_FORENSIC_REPORT_LAYER.md) | **Active** next phase |
| [phase7/PHASE7_MASTER_PLAN.md](phase7/PHASE7_MASTER_PLAN.md) | Phase gates and sign-off status |
| [phase7/phase7_dataset/](phase7/phase7_dataset/) | Phase 7B label outputs |
| [phase7/phase7_current_dataset_audit/](phase7/phase7_current_dataset_audit/) | Phase 7C0 audit |
| [CURSOR_WORKFLOW_GUIDE.md](CURSOR_WORKFLOW_GUIDE.md) | Efficient Cursor usage |
| [FORENSIC_PRODUCT_MASTER_PLAN.md](FORENSIC_PRODUCT_MASTER_PLAN.md) | Product layers and strategy |
