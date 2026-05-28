# Integration Guide (Website Teammate)

Phase 9A provides a skeleton API contract for integration planning only.

## Expected FastAPI Endpoint

- `POST /analyze-audio`

## Request Format

- `multipart/form-data`
- `audio_file`: uploaded file (required)
- `case_id`: string (optional)

## Response Format (Skeleton)

- `case_id`
- `status`
- `audio_metadata`
- `origin_evidence`
- `replay_evidence`
- `mixer_channel_evidence`
- `partial_fabrication_evidence`
- `segment_candidates`
- `fusion_status`
- `forensic_summary`
- `manual_review_required`
- `limitations`

## Website Display Guidance

- Render each evidence axis separately.
- Show status as experimental prototype.
- Show manual review requirement clearly.
- Label segment candidates as candidate indicators, not final conclusions.

## Wording to Avoid

- Avoid statements that imply production readiness or legal finality.
- Avoid representing placeholders as calibrated inference.

## Current Phase Note

Phase 9A is skeleton-only. Full inference behavior is delivered later in Phase 9B/9C.
