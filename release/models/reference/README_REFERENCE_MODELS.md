# Reference Models (Phase 9B-R)

This folder stores **legacy_reference_experimental** checkpoints (AASIST, HybridResNet) for history and comparison only.

## Why separate from active release models?

Active Phase 9B/9C evidence models are multi-axis indicators:
- origin
- replay
- mixer/channel
- partial fabrication segment

AASIST and HybridResNet are earlier baseline/reference architectures. They are **not** part of the current active fusion/inference path.

## Defaults

- `active_in_fusion`: false
- `used_by_default`: false
- `not_final_forensic_decision`: true

## Allowed later use

- reference comparison
- historical documentation
- future validation candidate (only after separate review)

## Not allowed

- treating outputs as final fake/real proof
- court-ready claims
- replacing multi-axis evidence without validation

## Manual copy

Run:
`python code/phase9/release/copy_phase9br_reference_models.py`

Optional auto-discovery:
`python code/phase9/release/copy_phase9br_reference_models.py --auto_scan`
