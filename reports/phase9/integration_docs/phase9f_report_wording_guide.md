# Phase 9F — Report Wording Guide

UI and API text must use **evidence-indicator** language only. This guide defines allowed and forbidden phrasing for the Deepfake Audio Detector local demo.

**Conclusive authenticity decision: no** — always communicate this to end users.

---

## Allowed wording (use these)

### Voice origin

- Voice origin: Likely AI-generated
- Voice origin: Likely human
- Voice origin: Inconclusive
- Voice origin: Inconclusive under replay/channel processing
- Voice origin: Likely AI-generated with processing indicators *(when replay/mixer overlap)*

### Forensic evidence axes

- AI-origin evidence detected
- Replay/rerecording evidence detected
- Mixer/channel processing evidence detected
- Partial replacement candidate for review
- Candidate region for optional review

### Safety and recommendations

- Conclusive authenticity decision: no
- Manual forensic review is recommended when indicators are present
- Optional review may be useful for sensitive cases
- Experimental forensic evidence indicators only

### Recommendation levels (machine values)

| Level | Typical UI text |
|-------|-----------------|
| `none` | No strong indicators; routine caution still applies |
| `optional_review` | Optional review may be useful (e.g. segment candidate on clean human) |
| `review_recommended` | Manual forensic review is recommended |
| `unavailable` | Analysis unavailable for this axis |

### Partial fabrication (experimental)

- Experimental partial-fabrication evidence was detected… candidate region for manual forensic review
- No partial-fabrication evidence was detected… does not prove authentic
- Partial-fabrication analysis was unavailable…

---

## Forbidden wording (never use in user-facing UI)

The following phrases must **not** appear in product UI, API summaries shown to users, or marketing copy:

- definitely fake
- definitely real
- final verdict
- final fake
- final real
- court proof
- court-ready
- court ready
- production-ready
- production ready

*(This list is the explicit forbidden-wording section — validators may reference it.)*

---

## Overlap and processing notes

When replay and mixer/channel evidence co-occur, use overlap wording from `axis_interpretation`:

- Replay-like/channel artifact overlap observed. Mixer/channel processing should be reviewed as the dominant indicator.
- Mixer/channel processing evidence is dominant; replay-like artifacts may overlap.

When origin is unreliable due to processing:

- Replay or channel processing can reduce reliability of AI-vs-human origin cues.

---

## PDF and JSON consistency

- PDF reports (`release/src/pdf_report_generator.py`) and API JSON (`build_api_analyze_response`) share formatting from `app_report_formatting.py`.
- Display `safety.wording` on every report view.
- Show `limitations[]` when non-empty.

---

## Frontend display checklist

1. **Hero card:** `voice_origin_result.display_text`
2. **Evidence cards:** one card per entry in `evidence_axis_cards` (title, status, user_text)
3. **Recommendation banner:** `recommendation` + `recommendation_level`
4. **Partial section:** label as experimental; never imply guaranteed tampering detection
5. **Safety footer:** `safety.wording` + conclusive authenticity decision: no
6. **Advanced panel (collapsed):** raw JSON, `phase9c_report`, segment tables

---

## Mapping API fields to UI labels

| API field | UI use |
|-----------|--------|
| `voice_origin_result.display_text` | Primary headline |
| `forensic_indicator_summary` | Subtitle / chip row |
| `evidence_axis_cards[].axis_name` | Card title |
| `evidence_axis_cards[].user_text` | Card body |
| `partial_fabrication.user_facing_message` | Partial card detail |
| `recommendation` | Action banner |
| `limitations` | Disclaimer list |
