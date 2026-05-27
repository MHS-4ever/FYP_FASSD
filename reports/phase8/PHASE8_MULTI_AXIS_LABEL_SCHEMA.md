# Phase 8 Multi-Axis Label Schema

> **Historical draft — superseded** by [label_schema/phase8a_multi_axis_label_schema.md](label_schema/phase8a_multi_axis_label_schema.md).  
> **Implement Phase 8B only from the Phase 8A file above.**

**Status:** Superseded · `phase8a_v1_1`  
**Rule:** `risk_positive` ≠ AI-generated · `clean` manipulation ≠ human-safe

---

## Deprecated field names in this draft

This root copy used pre-freeze names. **Do not use in code or CSV headers.**

| Deprecated (this file) | Frozen Phase 8A |
|------------------------|-----------------|
| `origin_human` (0/1 field) | `human` label + `evidence_origin_human_score` |
| `origin_ai` | `ai_synthetic` + `evidence_origin_ai_score` |
| `origin_mixed` | `mixed` + `evidence_origin_mixed_score` |
| `origin_unknown` | `unknown` + `evidence_origin_unknown_score` |
| `manipulation_direct_synthetic` | **Invalid manipulation label** — use `ai_synthetic` origin |
| `manipulation_replay` | `replay_rerecorded` |
| `manipulation_mixer_channel` | `mixer_channel_processed` |
| `manipulation_partial_fabrication` | `partial_fabrication` |
| `manipulation_edited_spliced` | `edited_spliced` |
| `manipulation_compressed_low_quality` | `compressed_low_quality` |
| `final_status` | `final_forensic_status` |
| `risk_level` | `forensic_risk_level` |
| `evidence_summary` | `forensic_summary` |

---

## Design principle (still valid)

Forensic labels are **evidence axes**, not a single court verdict. Reports separate origin, manipulation, and segment/time evidence.

**Human-origin replay:** `human` + `replay_rerecorded` — not `ai_synthetic`.

**Direct AI with no replay/mixer:** `ai_synthetic` + `clean` manipulation is **valid**.

---

## Where to read the full frozen schema

- Origin, manipulation, decision labels: [label_schema/phase8a_multi_axis_label_schema.md](label_schema/phase8a_multi_axis_label_schema.md)  
- CSV columns: [evidence_table/phase8a_evidence_table_schema.md](evidence_table/phase8a_evidence_table_schema.md)  
- Fusion: [fusion/phase8a_fusion_and_abstention_rules.md](fusion/phase8a_fusion_and_abstention_rules.md)

**Phase 8B:** NOT STARTED
