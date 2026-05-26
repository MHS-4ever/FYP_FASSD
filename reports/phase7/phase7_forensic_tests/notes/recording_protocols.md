# Forensic P0 Recording Protocols (Template)

Fill this when you create test audio. Consistent protocols make Phase 7A analysis comparable.

---

## General

| Setting | Recommendation |
|---------|----------------|
| Sample rate | 16 kHz preferred (or record high quality and resample in notes) |
| Format | WAV for masters; export compressed copies for WhatsApp tests |
| **Default duration** | **20–30 seconds** of speech per test case (P0 standard) |
| **Minimum duration** | **Do not use clips shorter than 8 seconds** (unreliable pooling/VAD) |
| **Edited / partial AI** | **30–45 seconds** per file |
| **Long-evidence simulation** | **60–120 seconds** only for **later** P1/P2 long-file tests — not default P0 |
| **Silence** | Keep **~0.5–1 s** silence at start and end (avoid long dead air) |
| **Paired samples** | **Prefer paired sets**: same script/content across clean, replay, mixer, WhatsApp, and AI versions of the same utterance |
| Metadata | Log device, room, date, exact duration in manifest `notes` column |

### Duration by test type (quick reference)

| Test type | Target speech duration |
|-----------|-------------------------|
| P0 clean human / direct AI / replay / mixer / WhatsApp | **20–30 s** |
| P0 minimum (any type) | **≥ 8 s** (below this: do not use for 7A) |
| Edited / spliced (`edited_spliced`) | **30–45 s** |
| Partial AI insertion (`partial_ai_insert`) | **30–45 s** |
| Long broadcast / multi-segment simulation | **60–120 s** (later batches only) |

### Partial fabrication (Scope 3) — Phase 7A

| Case | Build | Duration guidance |
|------|-------|-------------------|
| Long + AI insert | Record ~110 s human, insert ~10 s AI/cloned in editor | **~120–130 s** total; note insert times in manifest |
| Medium + AI insert | ~55 s human + ~5 s AI | **~60–65 s** |
| Cloned sentence | Single AI sentence in real paragraph | **30–45 s** |
| Human splice (different room) | Insert human clip from other recording | **30–45 s**; ground truth `partial_fabrication_detected=false` but `edited` |
| WhatsApp + AI insert | Compress then or insert before forward | Document order in `notes` |

Log **exact** `suspicious_start_time` / `suspicious_end_time` (seconds) in manifest for evaluation.

---

### Paired recording workflow (recommended)

For each script ID (e.g. `SCRIPT_01`):

1. Record or generate **clean human** master (20–30 s).  
2. Generate **direct AI** of the **same text**.  
3. Produce **human_replay** and **ai_replay** from those masters.  
4. Produce **mixer_processed** variants of human and AI masters.  
5. Produce **whatsapp_compressed** forwards of human and AI masters.  

Use the same `notes` field to link pairs: e.g. `pair_id=SCRIPT_01`.

---

## Condition: Clean human — mobile (`clean_direct` / `phone_recorded`)

- Record directly on phone voice memo / recorder app.
- Minimal post-processing.
- `ground_truth_origin`: human  
- `ground_truth_manipulation`: clean  

---

## Condition: Clean human — laptop/USB (`clean_direct`)

- USB mic or laptop mic in quiet room.
- `device_chain`: e.g. `laptop_USB_AT2020`

---

## Condition: Direct AI (`clean_direct`, source ai)

- TTS or voice clone file saved directly (no replay hop).
- Note tool in manifest `notes`.

---

## Condition: Human replay (`human_replay`)

1. Play clean human audio from laptop speaker at fixed volume.  
2. Record with phone at 0.5–1 m.  
3. `ground_truth_origin`: human  
4. `ground_truth_manipulation`: replayed  

---

## Condition: AI replay (`ai_replay`)

Same chain as human replay but source file is AI.

---

## Condition: Mixer processed (`mixer_processed`)

- Route human or AI through mixer/EQ (or software EQ).
- Record output to file or second device.
- Document chain in `device_chain`.

---

## Condition: WhatsApp compressed (`whatsapp_compressed`)

1. Start from a master human or AI file.  
2. Send through WhatsApp (or export equivalent opus compression).  
3. Save received/forwarded file for analysis.  
4. `platform`: whatsapp  

---

## Naming convention (suggested)

`P0_{origin}_{manipulation}_{lang}_{index}.wav`

Example: `P0_human_humanreplay_urdu_01.wav`
