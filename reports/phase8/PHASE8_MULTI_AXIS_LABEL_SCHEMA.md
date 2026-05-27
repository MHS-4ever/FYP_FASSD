# Phase 8 Multi-Axis Label Schema

**Status:** Draft for Phase 8A freeze  
**Rule:** `risk_positive` ≠ AI-generated

---

## Design principle

Forensic labels are **evidence axes**, not a single court verdict. Reports must separate:

- What we infer about **origin**  
- What we infer about **manipulation / processing**  
- Where in time suspicion concentrates  

---

## Origin axis

| Field | Values | Meaning |
|-------|--------|---------|
| `origin_human` | 0/1 or score | Evidence supports human-produced speech |
| `origin_ai` | 0/1 or score | Evidence supports AI/synthetic generation |
| `origin_mixed` | 0/1 or score | Mixed-origin over file or segments |
| `origin_unknown` | 0/1 or score | Insufficient evidence — abstain |

**Note:** Human-origin replay is `origin_human` + manipulation replay — not `origin_ai`.

---

## Manipulation axes

| Field | Description |
|-------|-------------|
| `manipulation_clean` | No meaningful manipulation detected |
| `manipulation_direct_synthetic` | Full-file or dominant synthetic speech |
| `manipulation_replay` | Rerecording / replay attack pattern |
| `manipulation_mixer_channel` | Mixer, channel, or broadcast-style processing |
| `manipulation_partial_fabrication` | Localized inserted/synthetic region |
| `manipulation_edited_spliced` | Cuts/splices/edits |
| `manipulation_compressed_low_quality` | Heavy compression or quality loss |

Multiple axes may be active (e.g. AI mixer = `origin_ai` + `manipulation_mixer_channel`).

---

## Segment axis

| Field | Description |
|-------|-------------|
| `suspicious_segment_present` | Any window above segment threshold |
| `suspicious_start_time` | Start (seconds) of highest-suspicion region |
| `suspicious_end_time` | End (seconds) |
| `inside_region_score` | Mean/max score inside annotated partial region |
| `outside_region_score` | Score outside region |
| `region_delta` | inside − outside (partial fabrication signal) |

---

## Decision / fusion fields

| Field | Description |
|-------|-------------|
| `final_status` | Controlled vocabulary (e.g. accept, review, suspicious_manipulation, …) |
| `risk_level` | low / medium / high |
| `manual_review_required` | bool |
| `evidence_summary` | Short forensic-safe text for report layer |

---

## Compatibility with Phase 7

| Phase 7 field | Phase 8 mapping |
|---------------|-----------------|
| `risk_target` | Forensic-risk positive (training) — **not** origin alone |
| `expected_risk_binary` | Legacy — do not equate to AI-generated |
| `aasist_status` | Archived role status — input feature only |
| `baseline_status` | Hybrid role status — input feature |

---

## Clarifications (mandatory wording)

1. **risk_positive** means elevated forensic concern, not “fake.”  
2. **AI-generated** requires `origin_ai` evidence, not manipulation alone.  
3. **Replay** can be human-origin.  
4. **Partial fabrication** requires segment axis, not file mean only.  

---

## Schema location (planned)

- `reports/phase8/label_schema/` — extended tables and examples  
- `reports/phase8/evidence_table/` — column spec for 8B builder  
