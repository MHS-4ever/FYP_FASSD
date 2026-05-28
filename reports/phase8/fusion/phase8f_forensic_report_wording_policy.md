# Phase 8F Forensic Report Wording Policy

## Safe Wording (Use)
- "evidence indicator"
- "experimental model output"
- "candidate segment"
- "manual review recommended"
- "consistent with"
- "does not by itself prove"

## Forbidden Wording (Do Not Use)
- "definitely fake"
- "definitely real"
- "criminal proof"
- "court-proven"
- "guaranteed AI"
- "guaranteed human"

## Axis-Specific Guidance
- replay elevation must include: "does not mean AI-generated"
- mixer/channel elevation must include: "does not mean AI-generated"
- partial fabrication must be phrased as timestamp/segment candidate evidence
- all statuses must be marked experimental
- if axis is missing/not_evaluated: "This evidence axis was not evaluated in the current retrospective fusion record. No conclusion is drawn from this missing axis."
- do not print `nan` as evidence text or candidate range text

## Example Phrasing

### AI Origin Only
"Origin evidence is elevated and consistent with AI-synthetic origin indicators in this experimental model output. This does not by itself prove fabrication."

### Replay Only
"Replay/rerecording evidence is elevated. This does not mean the speech is AI-generated; it indicates a possible playback/rerecording channel effect."

### Mixer Only
"Mixer/channel evidence is elevated. This does not imply AI-generated origin and may reflect channel processing or production artifacts."

### Partial Fabrication
"Partial fabrication indicators are elevated for candidate segments in the reported timestamp ranges. These are candidate segment findings and manual review is recommended."

### Mixed Evidence
"Multiple evidence axes are elevated, producing a mixed experimental evidence pattern. Manual review is recommended to resolve competing indicators."

### Inconclusive / Manual Review
"Evidence is incomplete, borderline, or conflicting across axes. The result is inconclusive in this experimental workflow, and manual review is recommended."

Required final sentence for inconclusive reports:
"Manual review is recommended because the evidence is incomplete, borderline, or inconclusive."

### Missing Axis / Retrospective OOF
"This evidence axis was not evaluated in the current retrospective fusion record. No conclusion is drawn from this missing axis."
