# Phase 8C-A1 Status

**Phase 8C-A1 status:** COMPLETED (audit run successful — validate outputs)

---

## Prior phases

| Phase | Status |
|-------|--------|
| Phase 8B | **COMPLETED** for controlled Phase 7C1 |
| Phase 8C | **COMPLETED** for controlled Phase 7C1 (184 files, 4189 segments, fast mode, validation PASS) |
| Phase 8C-A1 | **COMPLETED** (descriptive audit + plots) |
| Phase 8D | **NOT STARTED** |

---

## Scripts

| Script | Path |
|--------|------|
| Audit | `code/phase8/features/audit_phase8c_acoustic_features.py` |
| Validator | `code/phase8/validation/validate_phase8c_a1_audit.py` |
| Design | `reports/phase8/features/phase8c_a1_acoustic_feature_audit_design.md` |

---

## Next action (user)

```text
python code/phase8/features/audit_phase8c_acoustic_features.py --make_plots

python code/phase8/validation/validate_phase8c_a1_audit.py
```

Outputs under: `reports/phase8/features/audit/`

---

## Next review (assistant)

After user runs audit: review `phase8c_a1_acoustic_feature_audit_report.md`, top candidates, missingness, and validation PASS/FAIL.

---

## Hard rules

- Descriptive audit only — no training, no predictions  
- Do not modify Phase 8B or Phase 8C feature CSVs  
- No fake/real or forensic decision columns  
- Phase 8D **NOT STARTED**

---

## Future long-running Phase 8 scripts

Must include:

1. Progress display (tqdm or fallback)  
2. `--max_files` / test mode where useful  
3. `--resume` for large CSV outputs  
4. Clear terminal summary  
5. Validation script after generation  
