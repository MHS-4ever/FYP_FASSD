# Phase 7C2 — Label Mapping Rules

## Old dataset → forensic schema

| Old condition | origin_label | manipulation_label | attack_hint | origin_binary | manipulation_binary | use_origin_loss |
|---------------|--------------|--------------------|-------------|---------------|----------------------|-----------------|
| `label=bonafide` | human_likely | clean_original | bonafide | human | clean | true |
| spoof + synthesis | ai_likely | clean_original | synthesis | ai | clean | true |
| spoof + conversion | ai_likely | clean_original | voice_conversion | ai | clean | true |
| spoof + replay | uncertain | replayed_or_re_recorded | replay | unknown | manipulated | **false** |

Unknown label/attack combinations → excluded from subset.

## Phase 7C1

Trusted from collection manifest:

- `origin_label`, `manipulation_label`, `attack_hint`, `risk_level`
- `partial_fabrication_binary`, suspicious region timestamps
- Binary fields derived:
  - `human_likely` → `origin_binary=human`
  - `ai_likely` → `ai`
  - `mixed_or_partial_ai` → `mixed`
  - `clean_original` → `manipulation_binary=clean`
  - else (non-uncertain) → `manipulated`

## Multi-task training targets (future 7C)

| Task | Values |
|------|--------|
| Origin | human / ai / mixed / unknown |
| Manipulation | clean / replayed / processed / edited / compressed / noisy / uncertain |
| Attack | bonafide / synthesis / voice_conversion / replay / unknown |
| Partial | 0 / 1 |
