# Phase 8B Status

**Phase 8B status:** SCRIPT CREATED / NOT YET EXECUTED

**Schema version:** `phase8b_v1`  
**Phase 8A:** CANDIDATE FROZEN — human sign-off pending  
**Phase 8C status:** NOT STARTED

---

## Scripts delivered

| Script | Path |
|--------|------|
| Builder | `code/phase8/evidence_table/build_phase8b_evidence_tables.py` |
| Schema utils | `code/phase8/evidence_table/phase8b_schema_utils.py` |
| Validator | `code/phase8/validation/validate_phase8b_evidence_tables.py` |

## Documentation

| Doc | Path |
|-----|------|
| Builder design | `reports/phase8/evidence_table/phase8b_builder_design.md` |
| Expected outputs | `reports/phase8/evidence_table/phase8b_expected_outputs.md` |

---

## Next action (user)

1. Run builder on selected manifest(s), for example:

```text
python code/phase8/evidence_table/build_phase8b_evidence_tables.py ^
  --input_manifests reports/phase7/phase7c1_collection/phase7c1_collection_manifest.csv ^
  --allow_missing_audio
```

2. Run validator:

```text
python code/phase8/validation/validate_phase8b_evidence_tables.py
```

3. Review generated artifacts:

- `reports/phase8/evidence_table/phase8b_file_evidence_table.csv`
- `reports/phase8/evidence_table/phase8b_segment_evidence_table.csv`
- `reports/phase8/evidence_table/phase8b_build_report.md`
- `reports/phase8/validation/phase8b_evidence_table_validation_report.md`

---

## Next review (assistant)

After user runs builder: review CSV columns, label distributions, warnings, and validation PASS/FAIL before Phase 8C.

---

## Hard rules (unchanged)

- No training / inference in 8B  
- No evidence scores invented from labels  
- No `evidence_origin_score` / `origin_score` columns  
- No Phase 7 output overwrites  

---

## Phase progression

| Phase | Status |
|-------|--------|
| 8A / 8A-C1 | Documentation complete — sign-off pending |
| 8B | Scripts ready — **NOT YET EXECUTED** |
| 8C | NOT STARTED |
| 8D | NOT STARTED |
| 8E | NOT STARTED |
| 8F | NOT STARTED |
