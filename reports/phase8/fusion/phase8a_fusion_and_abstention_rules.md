# Phase 8A — Fusion and Abstention Rules (Words Only)

**Status:** CANDIDATE FROZEN — `phase8a_v1_1`; pending human sign-off  
**Version:** 8A.1.1 (`phase8a_v1_1`)  
**Not code:** These rules define intended behavior for fusion layer and report generation.

---

## 0. Origin score fields (mandatory)

Fusion reads **four file-level origin scores** — never a single `evidence_origin_score`:

- `evidence_origin_human_score`
- `evidence_origin_ai_score`
- `evidence_origin_mixed_score`
- `evidence_origin_unknown_score`

Segment rules use the parallel segment fields:

- `segment_origin_human_score`, `segment_origin_ai_score`, `segment_origin_mixed_score`, `segment_origin_unknown_score`

**Strength shorthand:** “human Strong” means `evidence_origin_human_score` in Strong band and `evidence_origin_ai_score` Weak/None unless noted.

---

## 1. Evidence strength levels

All axis scores map to qualitative strength for rule matching:

| Level | Score range (default band) | Meaning |
|-------|----------------------------|---------|
| **None** | [0.00, 0.25) | No meaningful support |
| **Weak** | [0.25, 0.50) | Hint only — cannot alone trigger strong suspicion |
| **Moderate** | [0.50, 0.75) | Contributes with other evidence |
| **Strong** | [0.75, 1.00] | Primary driver for that axis |

Bands are **calibration parameters** (locked on 7C1 for development; not tuned on 7A for product claims). Fusion records which levels fired in `fusion_trace` and `forensic_summary`.

---

## 2. Manipulation-vs-origin separation rules

1. **Origin decisions** use the four origin scores (and segment origin localization), not manipulation scores alone.  
2. **Manipulation decisions** use replay, mixer, partial, splice, quality scores — independent of assuming AI.  
3. **Never promote** `replay_rerecorded` or `mixer_channel_processed` to `ai_synthetic`.  
4. **`risk_positive` / high Hybrid** increases manipulation review priority; does not set `evidence_origin_ai_score` without separate origin evidence.  
5. **Conflict:** Strong manipulation + weak origin → suspicious manipulation or inconclusive — **not** automatic AI.  
6. **`clean` manipulation label:** Means no replay/mixer/splice/partial manipulation detected — **not** “human” and **not** “safe.” Direct AI cases may have `calibrated_manipulation_labels` = `clean` with `calibrated_origin_label` = `ai_synthetic`.

---

## 3. Clean-human protection rules

Apply before issuing strong suspicious origin:

1. If `evidence_origin_human_score` is **Moderate+** AND `evidence_origin_ai_score` is **Weak/None**, AND manipulation scores are **None/Weak** for replay, partial, splice → favor `accept_human_clean`.  
2. If only `evidence_quality_score` is **Moderate+** but `evidence_origin_human_score` is **Moderate+** and AI origin Weak → `inconclusive_manual_review` or accept with quality caveat — **not** `suspicious_origin` for AI. Set `manual_review_reason` = `quality_limited` when applicable.  
3. Clean-human false alarm ceiling enforced in validation: ≤ 5/23 on 7C1 (see validation doc).  
4. When replay/mixer scores are **Weak** on known clean human → do not flag manipulation Strong.

---

## 4. Conflict handling

| Conflict type | Resolution (first pass) |
|---------------|-------------------------|
| Strong human vs Strong AI origin scores | `mixed` or `unknown` + `manual_review_required`; `manual_review_reason` = `conflicting_origin_evidence` |
| Strong human origin vs Strong replay | `human` + `replay_rerecorded` → `suspicious_manipulation` |
| Strong AI origin vs Strong clean manipulation | Valid: `ai_synthetic` + `clean` → `suspicious_origin`; re-check segments if `segment_origin_ai_score` local |
| Strong partial segment vs Weak file AI origin | `mixed` + `partial_fabrication` → `suspicious_mixed` |
| All origin scores Weak | `inconclusive_manual_review`; `manual_review_reason` = `weak_origin_evidence` |
| Strong quality degradation, all else Weak | `unknown` + `compressed_low_quality` → `inconclusive_manual_review`; `quality_limited` |
| Segment AI-local vs file human-dominant | `suspicious_mixed` or review; `suspicious_segment_file_conflict` |

---

## 5. Abstention and manual-review conditions

Set `manual_review_required = true` when any of:

- `final_forensic_status` = `inconclusive_manual_review`  
- All four origin scores Weak (none Moderate+)  
- Manipulation Strong but `calibrated_origin_label` = `unknown` → `strong_manipulation_weak_origin`  
- Segment flags disagree with file-level origin dominance (e.g. `segment_origin_ai_score` Strong, file human Strong)  
- Known eval role is partial fabrication but no segment exceeds threshold → quality audit / `borderline_scores`  
- User-upload blind case with all Weak evidence → `unknown_domain`  

Reports must say **“manual review recommended”** — never “confirmed fake.”

---

## 6. Segment aggregation rules

1. Compute file-level manipulation scores as **max** or **top-k mean** of segment manipulation scores (parameter locked in 8F config).  
2. **File-level origin scores:** aggregate segment origin four-tuples (e.g. max per dimension, or weighted by duration) — **do not** collapse to one scalar before fusion.  
3. `partial_fabrication`: require **≥1** segment with `partial_fabrication_score` **Moderate+** OR `region_delta` **Moderate+** inside annotated region.  
4. `suspicious_segment_flag` on any **Strong** segment → elevate file to at least `suspicious_mixed` or `suspicious_manipulation` depending on `segment_reason`.  
5. File-level accept clean human: **no** segment may have Strong replay, partial, or splice; file `evidence_origin_human_score` Moderate+ and `evidence_origin_ai_score` Weak/None.  
6. Timestamps for UI: segment with max `partial_fabrication_score`, or max `segment_origin_ai_score`, or max `segment_origin_mixed_score` as appropriate to case.

---

## 7. Decision mapping (summary)

| Pattern | `calibrated_origin_label` | `calibrated_manipulation_labels` | `final_forensic_status` |
|---------|---------------------------|----------------------------------|-------------------------|
| Human Strong, AI Weak, all manip Weak/None | `human` | `clean` | `accept_human_clean` |
| AI Strong, human Weak, manip Weak/None | `ai_synthetic` | `clean` | `suspicious_origin` |
| Human Strong, replay Strong | `human` | `replay_rerecorded` | `suspicious_manipulation` |
| AI Strong, replay Strong | `ai_synthetic` | `replay_rerecorded` | `suspicious_manipulation` or `suspicious_origin` |
| Human Strong, mixer Strong | `human` | `mixer_channel_processed` | `suspicious_manipulation` |
| AI Strong, mixer Strong | `ai_synthetic` | `mixer_channel_processed` | `suspicious_manipulation` |
| Mixed/partial segment evidence | `mixed` | `partial_fabrication` | `suspicious_mixed` |
| Quality Strong, else Weak | `unknown` | `compressed_low_quality` | `inconclusive_manual_review` |

---

## 8. Worked examples (8 scenarios)

### Example 1 — Clean human

- **Scores:** `evidence_origin_human_score` Strong; `evidence_origin_ai_score` Weak/None; replay/mixer/partial/splice None; quality Weak.  
- **Segments:** all `suspicious_segment_flag` false.  
- **Output:** `human` + `clean` → `accept_human_clean`, `manual_review_required` false, `manual_review_reason` = `none`.  
- **Summary:** “No significant manipulation indicators; origin evidence consistent with human speech.”

### Example 2 — Direct AI

- **Scores:** `evidence_origin_ai_score` Strong; `evidence_origin_human_score` Weak/None; manipulation all Weak/None → **`clean` manipulation is valid**.  
- **Output:** `ai_synthetic` + `clean` → `suspicious_origin`.  
- **Summary:** “Origin evidence consistent with AI-synthetic speech; no separate replay/mixer manipulation indicators.”

### Example 3 — Human replay

- **Scores:** `evidence_origin_human_score` Moderate+; `evidence_origin_ai_score` Weak; replay Strong.  
- **Output:** `human` + `replay_rerecorded` → `suspicious_manipulation`.  
- **Summary:** “Rerecording/replay indicators present; origin evidence remains human — not evidence of AI generation.”

### Example 4 — AI replay

- **Scores:** `evidence_origin_ai_score` Moderate+; replay Strong.  
- **Output:** `ai_synthetic` + `replay_rerecorded` → `suspicious_manipulation` (origin cited in summary).  
- **Summary:** “AI-synthetic origin with replay/rerecording pattern detected.”

### Example 5 — Human mixer/channel processed

- **Scores:** human Strong; AI Weak; mixer Strong; replay Weak.  
- **Output:** `human` + `mixer_channel_processed` → `suspicious_manipulation`.  
- **Summary:** “Channel/mixer processing detected on human-origin speech — does not indicate AI generation.”

### Example 6 — AI mixer/channel processed

- **Scores:** AI Strong; mixer Strong.  
- **Output:** `ai_synthetic` + `mixer_channel_processed` → `suspicious_manipulation`.  
- **Summary:** “AI-synthetic origin with mixer/channel processing evidence.”

### Example 7 — Partial fabrication

- **Scores:** file `evidence_origin_mixed_score` or segment-driven mixed; partial Strong in segments; `region_delta` Strong.  
- **Output:** `mixed` + `partial_fabrication` → `suspicious_mixed`.  
- **Summary:** “Localized suspicious region(s) suggest partial fabrication; mixed origin over time.”

### Example 8 — Low-quality inconclusive audio

- **Scores:** quality Strong; all origin and manipulation Weak.  
- **Output:** `unknown` + `compressed_low_quality` → `inconclusive_manual_review`, `manual_review_reason` = `quality_limited`.  
- **Summary:** “Audio quality limits reliable origin and manipulation assessment; manual review recommended.”

---

## 9. Relation to Phase 7C4-v2

7C4-v2 outputs are **inputs** to fusion v3, not a bypass. Multi-axis rules above take precedence when 7C4-v2 conflicts with origin/manipulation separation. Do not map 7C4-v2 risk decisions directly to `evidence_origin_ai_score`.

---

## 10. Phase 8B note

Phase 8B may implement a **dry-run** fusion stub using these rules on existing CSVs. Full calibrated fusion is Phase 8F. Populate `fusion_trace`, `forensic_risk_level`, and `manual_review_reason` on every file row.

**Phase 8B:** NOT STARTED
