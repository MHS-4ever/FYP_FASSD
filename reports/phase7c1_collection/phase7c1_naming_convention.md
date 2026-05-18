# Phase 7C1 — Naming Convention (Round-1)

**Scope:** 15+ speakers × **8 variants** per `base_id` ≈ **120 files** (first domain-adaptation experiment).

---

## Pattern

```text
{origin_prefix}_{base_id:03d}_{variant_suffix}.wav
```

| Prefix | Meaning |
|--------|---------|
| `human` | Human-origin source chain |
| `ai` | AI/synthetic source chain |

**`base_id`** matches across all 8 files for one speaker/script session (e.g. `001` → `human_001_*`, `ai_001_*`).

---

## Eight required variants per base_id

| # | Filename example | `variant_id` |
|---|------------------|--------------|
| 1 | `human_001_clean.wav` | `human_clean` |
| 2 | `human_001_replay_laptop_mobile.wav` | `human_replay_laptop_mobile` |
| 3 | `human_001_mixer_processed.wav` | `human_mixer_processed` |
| 4 | `human_001_fabricated.wav` | `human_fabricated` |
| 5 | `ai_001_direct.wav` | `ai_direct` |
| 6 | `ai_001_replay_laptop_mobile.wav` | `ai_replay_laptop_mobile` |
| 7 | `ai_001_mixer_processed.wav` | `ai_mixer_processed` |
| 8 | `ai_001_fabricated.wav` | `ai_fabricated` |

---

## Speaker IDs

- `speaker_001`, `speaker_002`, … (15+ speakers)
- Record `speaker_gender`: `male` | `female` | `unknown`
- Include **male and female** speakers in Round-1

---

## Audio path (manifest)

Store under:

```text
data/phase7c1/raw/human_001_clean.wav
```

Use repo-relative paths in the collection manifest.

---

## Not required in Round-1

- WhatsApp / social platform filenames  
- YouTube / TikTok / Facebook chains  
- Long 60–120 s evidence simulations  
- 300+ files before first experiment  
