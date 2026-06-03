# Phase 9E-P4A — AASIST / HybridResNet Shadow Origin-Support Design

## Why AASIST/ResNet are tested

AASIST and HybridResNet are binary / deep anti-spoofing style models from earlier Phase 7 baseline work. They may improve **voice origin** discrimination (AI-generated vs likely human) when used as optional support signals.

They are **not** replay detectors, mixer/channel detectors, or partial-fabrication localizers in the release architecture.

## Why this phase is shadow-only

Phase 9E-P3/P3-P1 fixed the release decision hierarchy:

1. Voice origin (SSL origin model)
2. Forensic indicators (replay, mixer, partial)
3. Recommendation

P4A adds **parallel shadow scoring** only. Active release inference, fusion, and UI decisions are unchanged unless a future phase (9E-P4B) validates improvement and explicitly enables integration.

## Model audit result

See generated report: `phase9e_p4a_reference_model_audit.md`

Each reference package is audited for:

- weights on disk under `release/models/reference/`
- config / vendor inference code (AASIST)
- architecture code (HybridResNet under `code/phase3/`)
- runnable vs audit-only status with documented reason

## Evaluation modes

| Mode | Scope |
|------|--------|
| `quick` | 1 base × 8 variants (~8 files) — fast safety check |
| `full` | All 184 Phase 7C1 variant files |

```bat
python code\phase9\partial_redesign\run_phase9e_p4a_origin_support_shadow_eval.py --mode quick --max_base_audios 1
python code\phase9\partial_redesign\validate_phase9e_p4a_origin_support.py --mode quick
```

## Metrics

Per model (SSL baseline, AASIST, HybridResNet):

- Origin accuracy on AI / human variant groups
- `direct_origin_accuracy` — `ai_clean` + `human_clean` only
- `processed_origin_stability` — replay/mixer/fabricated (reported, not hard-fail)
- Agreement / disagreement with SSL origin
- `cases_helped_current_ssl` / `cases_hurt_current_ssl` / `net_help_score`
- Runtime and error counts

## Decision criteria (report only — no auto-activation)

| Classification | Meaning |
|----------------|---------|
| `activate_candidate` | Runnable, net help > 0, direct accuracy ≥ SSL, human_clean false-AI not worse, runtime OK |
| `keep_shadow_only` | Runnable but insufficient evidence to activate |
| `audit_only_not_runnable` | Missing weights/vendor/code |
| `reject_for_now` | High errors or hurts SSL more than helps |

**P4A never activates models.** Recommendation is input to Phase 9E-P4B.

## How results affect Phase 9E-P4B

P4B (future) may:

- Wire optional origin ensemble if `activate_candidate` is supported by full-mode metrics
- Keep shadow-only logging if `keep_shadow_only` or `audit_only_not_runnable`
- Document rejection if `reject_for_now`

## Replay / mixer / partial unaffected

Shadow wrappers return origin labels only. They do not modify:

- `replay_evidence`
- `mixer_channel_evidence`
- `partial_fabrication`
- `build_voice_origin_result()` active path (unless explicitly enabled in a later phase)

## Safety

- No retraining
- No threshold changes
- No writes to `release/models/` active artifacts or `models_saved/active`
- `used_for_voice_origin: false` on all shadow outputs
