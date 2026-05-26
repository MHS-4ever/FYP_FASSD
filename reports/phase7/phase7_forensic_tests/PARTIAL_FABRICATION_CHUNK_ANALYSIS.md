# Partial Fabrication — Chunk-Level Analysis (Phase 7A)

**Scope 3 test:** Mostly real audio with a short **inserted AI** segment.  
**Do not judge this case by whole-file REAL/FAKE alone.**

---

## Reference test case: `T5_FAB_001`

| Field | Value |
|-------|--------|
| **test_id** | `T5_FAB_001` |
| **Total duration** | 34 seconds |
| **Ground-truth suspicious region** | **14.0 s – 21.0 s** (AI-generated insert) |
| **Rest of file** | Real (human) audio |
| **Expected whole-file behavior** | `prediction` may still be **REAL** (most chunks are human-like) |
| **Important check** | Chunk spoof scores **higher inside 14–21 s** than outside |

**Manifest row** (canonical example — copy into `forensic_test_manifest.csv`):

```csv
test_id,priority,audio_path,source_origin,manipulation_type,language,speaker_type,device_chain,platform,ground_truth_origin,ground_truth_manipulation,partial_fabrication_detected,suspicious_start_time,suspicious_end_time,expected_forensic_result,notes
T5_FAB_001,P0,E:/FYP/testing_audios/fabricated/fabricated_001.wav,mixed,partial_ai_insert,urdu,known_public,edited_real_plus_ai,none,mixed,mixed,true,14.0,21.0,Mostly real audio with inserted AI-generated segment from 14s to 21s,Total duration 34 seconds. Fake inserted region is 14s to 21s.
```

**Audio path (when recorded):** `testing_audios/fabricated/fabricated_001.wav`

---

## Why whole-file verdict is insufficient

| Whole-file signal | Partial-fabrication reality |
|-------------------|----------------------------|
| `pct_vote` &lt; 0.70 → **REAL** | Correct for *majority* of duration |
| Low `decision_score` | Inserts only **7 s** of **34 s** (~21% of timeline) |
| User sees “REAL” | **Misleading** — inserted fake segment hidden |

**Phase 7A pass criterion for this class:** chunk timeline must show elevated spoof/synthesis/conversion **inside 14–21 s** vs outside, even if whole-file = REAL.

---

## Chunk time ranges (Phase 6 defaults)

Inference uses (from `explain_prediction.py`):

- `chunk_duration` = **4.0 s**
- `overlap` = **1.0 s** → hop = **3.0 s**

Chunk *i* (0-based) approximately:

- `start_sec` = *i* × 3.0  
- `end_sec` = `start_sec` + 4.0  

(Use exact `start_sec` / `end_sec` if exported per chunk in future JSON; until then use this schedule.)

### Inside suspicious region

A chunk is **inside** the suspicious region **if its time range overlaps** `[suspicious_start_time, suspicious_end_time]`.

Overlap rule:

```
chunk overlaps region iff:
  chunk_start < region_end  AND  chunk_end > region_start
```

For **T5_FAB_001** (region 14.0–21.0 s), chunks with start 9, 12, 15, 18 typically overlap; chunks 0, 3, 6, 21+ are mostly outside (verify per file after VAD).

---

## Metrics to calculate (per file)

After obtaining **per-chunk spoof probability** (and per-chunk attack argmax), split chunks into **inside** vs **outside** the manifest region.

| Metric | Definition |
|--------|------------|
| `inside_region_avg_spoof` | Mean spoof prob of **inside** chunks |
| `outside_region_avg_spoof` | Mean spoof prob of **outside** chunks |
| `inside_region_max_spoof` | Max spoof prob among **inside** chunks |
| `outside_region_max_spoof` | Max spoof prob among **outside** chunks |
| `inside_region_dominant_attack` | Most frequent attack class among **inside** chunks (bonafide / synthesis / conversion / replay) |
| `outside_region_dominant_attack` | Most frequent attack class among **outside** chunks |

Also record for context:

| Field | Source |
|-------|--------|
| `whole_file_prediction` | Phase 6 `prediction` |
| `whole_file_decision_score` | Phase 6 `decision_score` |
| `n_chunks_inside` | Count inside region |
| `n_chunks_outside` | Count outside region |

---

## `partial_region_detected` (computed flag)

Set **`partial_region_detected` = true** if **any** of:

1. `inside_region_avg_spoof >= outside_region_avg_spoof + 0.15`  
2. `inside_region_max_spoof >= 0.65`  
3. **Attack contrast:** inside region dominant attack is **synthesis** or **conversion**, while outside region is **mostly bonafide**

Otherwise `partial_region_detected` = false.

Compare to ground truth `partial_fabrication_detected` in manifest for 7A evaluation:

| Ground truth | Computed | Assessment |
|------------|----------|------------|
| true | true | **Detect success** |
| true | false | **Miss** — need 7C/7D timeline work |
| false | true | **False partial alarm** |

---

## Forensic report wording (when detected)

Even if `prediction` = **REAL**, if `partial_region_detected` = true use **Case H** (Phase 7D):

> The recording is mostly human-like overall, but one or more suspicious segments were detected (e.g. **14.0–21.0 s**). These may indicate partial fabrication or inserted synthetic speech.

Add to report:

- `origin_label`: `mixed_or_partial_ai`  
- `manipulation_label`: `edited_or_spliced` or `environment_mismatch`  
- `suspicious_timeline`: entry for 14.0–21.0 s  

---

## How to get chunk scores today (no new code yet)

1. Run Phase 6 with `--debug_chunk_stats` (aggregate min/p50/max only — **not per-chunk times**).  
2. For **7A manual analysis**, re-run with planned export OR compute chunk times from formula above and note spoof probs from a one-off script when you request implementation.  
3. Document results in `forensic_test_results.csv` columns (see template).

**Planned (Phase 7):** `analyze_forensic_test_results.py` will compute inside/outside metrics automatically from per-chunk JSON.

---

## Related

- [PHASE7A_CONTROLLED_TEST_SUITE.md](../phase7/PHASE7A_CONTROLLED_TEST_SUITE.md)  
- [PHASE7D_FORENSIC_REPORT_LAYER.md](../pipeline_phases/PHASE7D_FORENSIC_REPORT_LAYER.md) — Case H  
- [forensic_test_manifest_template.csv](forensic_test_manifest_template.csv)  
- [forensic_test_results_template.csv](results/forensic_test_results_template.csv)
