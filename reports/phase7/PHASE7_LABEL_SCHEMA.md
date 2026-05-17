# Phase 7 Forensic Label Schema

**Used in:** 7A manifest, 7B training CSV, 7D report output, 7F fusion  
**Product plan:** [FORENSIC_PRODUCT_MASTER_PLAN.md](../FORENSIC_PRODUCT_MASTER_PLAN.md)

---

## Product output labels (derived / report)

### `origin_label`

| Value | Meaning |
|-------|---------|
| `human_likely` | Speech content favors human origin |
| `ai_likely` | Speech content favors synthetic/spoof-like origin |
| `mixed_or_partial_ai` | Mixed file or partial AI insertion |
| `uncertain` | Borderline or conflicting evidence |

### `manipulation_label`

| Value | Meaning |
|-------|---------|
| `clean_original` | No strong replay/channel/edit/platform signals |
| `replayed_or_re_recorded` | Replay / second-hop recording likely |
| `channel_processed` | Mixer, EQ, PA, or chain processing |
| `platform_compressed` | Social/codec compression risk |
| `edited_or_spliced` | Editing or splice-like inconsistency |
| `environment_mismatch` | Environmental inconsistency across chunks |
| `noisy_low_quality` | Too poor for confident analysis |
| `uncertain` | Insufficient evidence |

### `attack_hint` (auxiliary)

| Value | Meaning |
|-------|---------|
| `bonafide` | Model favors bonafide |
| `synthesis` | Synthesis-like signal |
| `voice_conversion` | Conversion-like signal |
| `replay` | Replay-like signal |
| `unknown` | Low confidence or conflicting |

### `risk_level`

| Value | Meaning |
|-------|---------|
| `low` | Clear origin; weak manipulation signals |
| `medium` | Borderline or moderate effects |
| `high` | Strong spoof-like or integrity concerns |
| `inconclusive` | Short audio, VAD issues, near threshold |

---

## Ground truth labels (manifest / training)

### `ground_truth_origin`

`human` | `ai` | `mixed` | `unknown`

### `ground_truth_manipulation`

`clean` | `replayed` | `processed` | `compressed` | `edited` | `mixed` | `unknown`

### `manipulation_type` (recording condition)

| Value | Description |
|-------|-------------|
| `clean_direct` | Direct mic, no replay |
| `human_replay` | Human → speaker → re-record |
| `ai_replay` | AI → speaker → re-record |
| `mixer_processed` | Mixer/EQ/PA chain |
| `whatsapp_compressed` | WhatsApp or similar |
| `youtube_broadcast` | YouTube or broadcast chain |
| `phone_recorded` | Phone-native capture |
| `edited_spliced` | Edit or splice (non-AI insert) |
| `partial_ai_insert` | Mostly real + AI segment |
| `noisy_room` | Deliberate noisy environment |
| `unknown` | Unspecified |

### `platform`

`none` | `whatsapp` | `youtube` | `facebook` | `tiktok` | `screen_recording` | `unknown`

### `language`

`english` | `urdu` | `punjabi` | `hindi` | `mixed` | `unknown`

### `speaker_type`

`known_public` | `local_speaker` | `self_recorded` | `unknown`

### Partial fabrication fields

| Field | Type | Description |
|-------|------|-------------|
| `partial_fabrication_detected` | bool | Ground truth: true if partial fake present |
| `suspicious_start_time` | float (s) | Start of known or detected suspicious region |
| `suspicious_end_time` | float (s) | End of region |
| `partial_region_detected` | bool | **Computed** in 7A analysis (see partial-fab doc) |

---

## Interpretation rules (mandatory)

1. **REAL ≠ original.** REAL means human-like under the model, not unedited or authentic.  
2. **FAKE ≠ legally proven fake.** FAKE means spoof-like evidence, not automatic fraud proof.  
3. **Attack hint does not override** forensic interpretation — it is auxiliary.  
4. **Partial fabrication** requires **segment-level** analysis; whole-file REAL can still flag Case H when inside-region scores exceed outside rules.  
5. **Layered labels** are the product output; binary `prediction` is internal.  

---

## Mapping hints (7D)

| Scenario | Typical origin | Typical manipulation |
|----------|----------------|------------------------|
| Clean human direct | human_likely | clean_original |
| Human replay | human_likely | replayed_or_re_recorded |
| Direct AI | ai_likely | clean_original or uncertain |
| AI replay | ai_likely | replayed_or_re_recorded |
| WhatsApp human | human_likely | platform_compressed |
| Partial AI insert (T5) | mixed_or_partial_ai | edited_or_spliced |

Full wording: [PHASE7D_FORENSIC_REPORT_LAYER.md](PHASE7D_FORENSIC_REPORT_LAYER.md).
