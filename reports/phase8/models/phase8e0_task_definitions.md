# Phase 8E-0 Task Definitions

## Scope
Phase 8E-0 defines safe dataset subsets for later training phases. This phase does not train any model.

## Task 1: Origin (File-Level)
- **Goal:** classify `human` vs `ai_synthetic` at file level.
- **Targets:** `target_origin_multiclass`, `target_is_ai_synthetic`.
- **Eligible rows:** clean rows where `known_origin_label` is `human` or `ai_synthetic`.
- **Excluded rows:** mixed origin, unknown origin, replay, mixer/channel, partial fabrication, edited/spliced, unknown manipulation.

## Task 2: Replay (File-Level)
- **Goal:** detect replay/rerecording evidence.
- **Targets:** `target_is_replay` (`1` replay, `0` clean).
- **Eligible rows:** replay-rerecorded positives and clean negatives (clean is the negative class).
- **Excluded rows:** mixer/channel, partial fabrication, edited/spliced, unknown manipulation.

## Task 3: Mixer/Channel (File-Level)
- **Goal:** detect mixer/channel processing evidence.
- **Targets:** `target_is_mixer_channel` (`1` mixer/channel processed, `0` clean).
- **Eligible rows:** mixer/channel positives and clean negatives (clean is the negative class).
- **Excluded rows:** replay, partial fabrication, edited/spliced, unknown manipulation.

## Task 4: Partial Fabrication (Localization Prep Only)
- **Goal:** prepare segment-level context for later localization/fusion, not direct inherited-label classifier training.
- **Targets:** inherited context fields only (e.g., `inherited_target_is_partial_fabrication_file`).
- **Eligibility:** `eligible_partial_segment_training=false` for inherited labels.
- **Required for future training:** true fabricated timestamps and inside/outside localization evidence.
- **Important:** inherited file-level partial labels are not supervised segment labels.

## Eligible vs Ineligible Rows
- Eligibility is encoded with explicit flags (`eligible_origin_file_model`, `eligible_replay_file_model`, `eligible_mixer_file_model`, `eligible_partial_segment_training`).
- Ineligible rows remain in master datasets for context and analysis but are excluded from task-specific training datasets.

## Important Interpretation Rules
- `risk_positive` does **not** imply AI-generated origin.
- Replay evidence does **not** imply AI-generated origin.
- Mixer/channel evidence does **not** imply AI-generated origin.
- Partial fabrication requires timestamp/inside-outside evidence before supervised segment training.
- Phase 8E-0 outputs are dataset preparation artifacts only, not model training outputs.
