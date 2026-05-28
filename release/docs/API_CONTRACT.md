# API Contract (Phase 9A Skeleton)

## Base Status

- release status: experimental_forensic_prototype
- phase: 9A skeleton

## Endpoints

- `GET /`
- `GET /health`
- `GET /model-info`
- `POST /analyze-audio`

## Analyze Audio Request

- content type: `multipart/form-data`
- fields:
  - `audio_file` (required)
  - `case_id` (optional)

## Analyze Audio Response (Skeleton)

- `case_id: string | null`
- `status: "skeleton_ready"`
- `audio_metadata: object`
- `origin_evidence: object`
- `replay_evidence: object`
- `mixer_channel_evidence: object`
- `partial_fabrication_evidence: object`
- `segment_candidates: array`
- `fusion_status: string`
- `forensic_summary: string`
- `manual_review_required: bool`
- `limitations: string[]`

## Contract Notes

- Placeholder behavior is expected until Phase 9B/9C.
- Evidence axes must stay separate.
- No single final forensic decision field in Phase 9A.
