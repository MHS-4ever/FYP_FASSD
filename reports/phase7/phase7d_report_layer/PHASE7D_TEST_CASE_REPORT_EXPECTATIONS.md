# Phase 7D — Test Case Report Expectations

Expected report behavior when Phase 7D1 processes Phase 7C4-v2 outputs.  
Use for QA on `build_phase7d_forensic_report.py` and for reviewing `examples/` illustrations.

**Ground truth** from manifests is for **internal QA only** — must not appear as “correct answer” in user-facing narrative.

---

## Summary matrix

| # | Case type | Typical `calibrated_status` | Risk | Manual review | Must not claim |
|---|-----------|----------------------------|------|---------------|----------------|
| 1 | Clean human accepted | `clean_human_accepted` | low | false* | “100% authentic” |
| 2 | Clean human borderline | `clean_human_borderline` | medium | true | “fake” |
| 3 | Direct AI segment suspicious | `direct_ai_file_level_missed_but_segment_suspicious` | high | true | File-level AI proof |
| 4 | Human replay | `human_replay_manipulation_detected` | medium/high | true | “AI-generated” |
| 5 | AI replay | `ai_replay_detected` or segment variant | high | true | “definitely fake” |
| 6 | Mixer processed | `human_mixer_*` / `ai_mixer_*` | medium/high | true | Origin from channel alone |
| 7 | Partial fabrication | `partial_fabrication_detected` | high | true | Whole-file “fake” |

\*Organizational policy may still require review.

---

## 1. Clean human accepted

**Trigger:** `calibrated_status=clean_human_accepted`  
**Rare on 7C1** (≈1/23).

| Expectation | Detail |
|-------------|--------|
| `overall_risk_level` | `low` |
| `manual_review_required` | `false` unless policy override |
| Narrative | No strong synthetic/manipulation evidence under current settings |
| Segments | Optional; only if chunks above display threshold |
| Limitations | Still include prototype + evaluation-scope bullets |

**Must not:** State “certified real”, “safe for legal use without review”.

---

## 2. Clean human borderline

**Trigger:** `calibrated_status=clean_human_borderline`  
**Common on 7C1** (≈15/23).

| Expectation | Detail |
|-------------|--------|
| `overall_risk_level` | `medium` |
| `manual_review_required` | `true` |
| Narrative | Conflicting evidence; segment review |
| Segments | List baseline high-spoof chunks if present |
| Model block | Show baseline vs R2 disagreement |

**Must not:** Label file as AI/synthetic in executive summary.

**Example doc:** [examples/clean_human_borderline_example.md](examples/clean_human_borderline_example.md)

---

## 3. Direct AI segment suspicious

**Trigger:** `direct_ai_file_level_missed_but_segment_suspicious` (and similar)

| Expectation | Detail |
|-------------|--------|
| `overall_risk_level` | `high` |
| `origin_hint` | `ai_suspicious` |
| `manipulation_hint` | `synthetic_segment_indicators` |
| Narrative | Explain file-level miss vs segment suspicion |
| Segments | **Required** — top spoof chunks |

**Must not:** Say “AI proven” or hide file-level REAL pooled vote when applicable.

**Example doc:** [examples/direct_ai_segment_suspicious_example.md](examples/direct_ai_segment_suspicious_example.md)

---

## 4. Human replay

**Trigger:** `human_replay_manipulation_detected`

| Expectation | Detail |
|-------------|--------|
| `origin_hint` | `likely_human` |
| `manipulation_hint` | `replayed_or_rerecorded` |
| Narrative | Human-origin + replay/rerecording indicators |
| Risk | `medium` or `high` if chunk ratio high |

**Must not:** Conflate replay with AI synthesis in headline.

**Example doc:** [examples/human_replay_detected_example.md](examples/human_replay_detected_example.md)

---

## 5. AI replay

**Trigger:** `ai_replay_detected` or `ai_replay_file_level_missed_but_segment_suspicious`

| Expectation | Detail |
|-------------|--------|
| `overall_risk_level` | `high` |
| `origin_hint` | `ai_suspicious` |
| `manipulation_hint` | `replayed_or_rerecorded` |
| Narrative | AI-related indicators + replay/channel |

**Must not:** “Guaranteed deepfake”.

**Example doc:** [examples/ai_replay_segment_suspicious_example.md](examples/ai_replay_segment_suspicious_example.md)

---

## 6. Mixer processed

**Trigger:** `human_mixer_manipulation_detected`, `ai_mixer_detected`, segment variants

| Expectation | Detail |
|-------------|--------|
| `manipulation_hint` | `channel_processed` |
| `origin_hint` | `likely_human` or `ai_suspicious` per `source_origin` |
| Narrative | Channel/mixer artifacts; origin depends on source |

**Must not:** Infer origin solely from channel processing.

**Example doc:** [examples/mixer_processed_detected_example.md](examples/mixer_processed_detected_example.md)

---

## 7. Partial fabrication

**Trigger:** `partial_fabrication_detected`

| Expectation | Detail |
|-------------|--------|
| `overall_risk_level` | `high` |
| `manipulation_hint` | `edited_or_partially_synthetic` |
| Segments | Labeled suspicious window + inside-region chunks |
| Metrics | `partial_region_delta`, inside/outside spoof in evidence table |

**Must not:** Call entire file “fake” if pooled vote is REAL.

**Example doc:** [examples/partial_fabrication_detected_example.md](examples/partial_fabrication_detected_example.md)

---

## Cross-cutting QA checks

1. Every report has non-empty `limitations` and `disclaimer`.  
2. No forbidden phrases (wording guide).  
3. `manual_review_required=true` for all `medium` and `high` risk.  
4. Error-case rows include extra limitation, not status override.  
5. JSON and Markdown for same `sample_id` are semantically identical.  

---

## 7D1 sample pack (planned)

Generate reports for at least:

| sample_id pattern | Case |
|-------------------|------|
| `*_clean` (accepted if any) | #1 |
| `*_clean` (borderline) | #2 |
| `*_direct_ai` or segment miss | #3 |
| `*_human_replay` | #4 |
| `*_ai_replay` | #5 |
| `*_mixer` | #6 |
| `*_partial` / `T*_FAB_*` | #7 |

Store under `reports/phase7/phase7d_report_layer/outputs/samples/` after implementation.
