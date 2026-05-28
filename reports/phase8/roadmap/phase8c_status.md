# Phase 8C Status

**Phase 8C status:** SCRIPT CREATED · **8C-P1 patched** — ready for full run with `--segment_feature_mode fast --resume`

**Schema version:** `phase8c_v1`

---

## Prior phases

| Phase | Status |
|-------|--------|
| Phase 8B | **COMPLETED** for controlled Phase 7C1 (184 files, 4189 segments, validation PASS) |
| Phase 8C | Scripts + P1 patch (progress, resume, fast segments) |
| Phase 8D | **NOT STARTED** |

---

## 8C-P1 changes

- Progress bars (tqdm or fallback every `--progress_every`)
- `--segment_feature_mode fast|full` (default **fast**)
- `--resume` + periodic CSV flush
- Runtime summary in terminal and report
- `--skip_existing` deprecated → use `--resume`

---

## Recommended full extraction

```text
python code/phase8/features/extract_phase8c_acoustic_features.py ^
  --allow_missing_audio ^
  --segment_feature_mode fast ^
  --resume

python code/phase8/validation/validate_phase8c_features.py
```

If interrupted, re-run the **same command** with `--resume`.

For complete segment MFCC/contrast on a subset later:

```text
python code/phase8/features/extract_phase8c_acoustic_features.py ^
  --max_files 20 ^
  --segment_feature_mode full ^
  --allow_missing_audio
```

---

## Scripts

| Script | Path |
|--------|------|
| Extraction | `code/phase8/features/extract_phase8c_acoustic_features.py` |
| Utils | `code/phase8/features/phase8c_feature_utils.py` |
| Progress | `code/phase8/common/progress_utils.py` |
| Validator | `code/phase8/validation/validate_phase8c_features.py` |

---

## Future long-running Phase 8 scripts (required pattern)

All future long-running Phase 8 scripts must include:

1. **Progress display** (tqdm or fallback + `--no_progress` / `--progress_every`)
2. **`--max_files` / `--max_items`** test mode
3. **`--resume`** when outputs are large CSVs
4. **Periodic flush** to disk for interrupt safety
5. **Clear terminal summary** (counts, runtime, skips, warnings)
6. **Validation script** run after generation

---

## Hard rules

- No training / checkpoint inference  
- No modification of Phase 8B evidence tables  
- No evidence scores or fake/real decisions  
- Phase 8D **NOT STARTED**
