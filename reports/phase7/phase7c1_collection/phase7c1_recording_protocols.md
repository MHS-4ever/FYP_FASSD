# Phase 7C1 — Recording Protocols (Round-1)

**Collected (Round-1):** **23** base IDs × 8 variants = **184 files**  
**Purpose:** First domain-adaptation / fine-tuning experiment — not final product-grade scale.

---

## 1. Script and language

- Each speaker reads **one paragraph** from prepared scripts:
  - **English**
  - **Urdu / Roman Urdu**
  - **English + Urdu mixed** (where possible)
- Assign `script_id` in the manifest (e.g. `script_en_01`, `script_urdu_01`, `script_mixed_01`).
- Mix languages across speakers when possible.

---

## 2. Duration

| Rule | Value |
|------|--------|
| **Recommended** | **30–60 seconds** per final file |
| **Minimum** | **≥ 8 seconds** (reject shorter) |
| **Silence** | **0.5–1 s** at start and end |

Partial-fabrication files (`*_fabricated.wav`) should be long enough to contain a clear inserted region (typically **30–45 s** total).

---

## 3. Eight variants per base_id (recording order)

1. **Human clean** — direct mic/USB; minimal processing  
2. **Human replay** — play clean (or source) on laptop speaker → record on mobile  
3. **Human mixer** — same content through laptop + mixer/EQ + mobile (not voice conversion)  
4. **Human fabricated** — mostly human with **AI segment inserted**; log insert times  
5. **AI direct** — TTS/clone of same script text  
6. **AI replay** — AI → laptop speaker → mobile  
7. **AI mixer** — AI through mixer/channel chain  
8. **AI fabricated** — mixed/partial insert; log times; note if mostly AI with human insert  

Use the **same script text** per `base_id` where pairing is intended.

---

## 4. Devices (Round-1)

| Variant | Typical `device_chain` |
|---------|------------------------|
| Clean | `mobile_direct` or `usb_mic` |
| Replay | `laptop_speaker_to_mobile` |
| Mixer | `laptop_mixer_mobile_recording` — audio played on laptop; **mixer/EQ adjusted during playback**; re-recorded on mobile |
| Fabricated | `edited_real_plus_ai` / `edited_mixed` |

`platform` may be `none` for Round-1 (WhatsApp **not** mandatory).

---

## 5. Partial insertion timestamps

For `human_*_fabricated` and `ai_*_fabricated`:

- Set `partial_fabrication_binary=1`
- **Required:** `suspicious_start_time`, `suspicious_end_time` (seconds)
- Measure after editing; re-validate manifest

---

## 6. Quality before manifest entry

- Listen for clipping, dropouts, wrong script  
- Confirm variant matches filename and labels  
- Fill `duration`, `sample_rate`, `channels` after export  

---

## 7. Holdout reminder

**Phase 7A T1–T5 (25 files)** remain **`controlled_holdout`** — do not copy into `data/phase7c1/raw/` as training data.
