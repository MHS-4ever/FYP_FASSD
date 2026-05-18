# FASSD Next Actions

**Product:** [Forensic Voice Authenticity Analyzer](UPDATED_PROJECT_SCOPE.md)  
**Canonical Phase 7 docs:** [phase7/README.md](phase7/README.md)  
**Gate:** No Phase 7C fine-tuning until Phase 7C1 collection is planned, recorded, and validated.

---

## Signed off

- **Phase 7A** — Controlled forensic testing  
- **Phase 7B** — Forensic label preparation (T1–T5 `controlled_holdout`)  
- **Phase 7C0** — Current/original training dataset audit  

---

## Current next actions

1. **Complete [Phase 7C1 — New Forensic Data Collection Plan](phase7/PHASE7C1_NEW_FORENSIC_DATA_COLLECTION_PLAN.md)** — manifest schema, naming, pairing, splits, minimum counts.  
2. **Collect** new forensic dataset using **Phase 7B** labels (`origin_label`, `manipulation_label`, segment timestamps where needed).  
3. **Validate** new collection (audio exists, labels, no split leakage, category targets).  
4. **Only then** start **Phase 7C** hybrid fine-tuning (not on legacy corpus alone; never merge Phase 7A holdout).

---

## Recording checklist (7C1 collection)

- [ ] **20–30 s** default clips; **30–45 s** for partial insertion  
- [ ] No clip **&lt; 8 s**; **0.5–1 s** silence at start/end  
- [ ] **Paired** variants (`human_001_clean`, `human_001_replay`, …) in **same split**  
- [ ] Partial inserts: mandatory `suspicious_start_time` / `suspicious_end_time`  
- [ ] Urdu/Pakistani prioritized across categories  

---

## Do not do yet

- Do **not** fine-tune on the legacy unified dataset alone.  
- Do **not** merge **Phase 7A T1–T5** into training (`controlled_holdout`).  
- Do **not** train binary REAL/FAKE only — use origin + manipulation labels.  
- Do **not** split **paired** samples across train/test.  
- Do **not** start Phase **7E** before 7C (and 7D spec) review.  
- Do **not** change Phase 6 core inference unless explicitly requested.

---

## Quick links

| Doc | Use |
|-----|-----|
| [phase7/PHASE7C1_NEW_FORENSIC_DATA_COLLECTION_PLAN.md](phase7/PHASE7C1_NEW_FORENSIC_DATA_COLLECTION_PLAN.md) | **Active** collection plan |
| [phase7/PHASE7_MASTER_PLAN.md](phase7/PHASE7_MASTER_PLAN.md) | Phase gates and sign-off status |
| [phase7_dataset/](phase7_dataset/) | Phase 7B label outputs |
| [phase7_current_dataset_audit/](phase7_current_dataset_audit/) | Phase 7C0 audit |
| [CURSOR_WORKFLOW_GUIDE.md](CURSOR_WORKFLOW_GUIDE.md) | Efficient Cursor usage |
| [FORENSIC_PRODUCT_MASTER_PLAN.md](FORENSIC_PRODUCT_MASTER_PLAN.md) | Product layers and strategy |
