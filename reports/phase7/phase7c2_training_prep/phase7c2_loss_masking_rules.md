# Phase 7C2 — Loss Masking Rules

Every manifest row includes boolean strings: **`true`** / **`false`**

| Column | Meaning |
|--------|---------|
| `use_origin_loss` | Train origin head |
| `use_manipulation_loss` | Train manipulation head |
| `use_attack_loss` | Train attack-type head |
| `use_partial_loss` | Train partial-fabrication head |

## Old replay (critical)

```
use_origin_loss = false
use_manipulation_loss = true
use_attack_loss = true
use_partial_loss = true
```

Rationale: ASVspoof PA replay must not imply AI origin.

## Phase 7C1

All four masks **`true`** — trusted dual labels and partial timestamps.

## Old bonafide / synthesis / conversion

All four masks **`true`**.
