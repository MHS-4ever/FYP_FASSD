# Phase 7C3-R2 Fine-Tuning Plan

## 1) Why v1 was rejected

Phase 7C3-v1 improved clean human but collapsed replay/mixer/partial and Phase 7A holdout behavior.  
Root issue: binary head was trained as origin proxy instead of forensic-risk proxy.

## 2) R2 core correction

Keep **HybridResNetEnvironmental** architecture unchanged.

- Binary head target = `forensic_risk_binary`
  - `0`: clean/bonafide low-risk
  - `1`: AI/replay/mixer/edited/partial/suspicious manipulated
- Attack head target = bonafide / synthesis / voice_conversion / replay

## 3) Target mapping

### Old subset

- bonafide -> risk 0
- synthesis -> risk 1
- conversion -> risk 1
- replay -> risk 1

### Phase7C1

- human clean -> risk 0
- direct AI -> risk 1
- human replay -> risk 1
- AI replay -> risk 1
- human mixer -> risk 1
- AI mixer -> risk 1
- partial fabrication -> risk 1

## 4) Window strategy

- Old rows: first 4s (single window)
- Phase7C1 clean/direct/replay/mixer: 3 windows per file (start/mid/end), `--phase7c1_windows 3`
- Partial fabrication: suspicious-centered 4s only

## 5) Sample weighting

### Old rows
- all old groups = 1.0

### Phase7C1 base
- clean human 2.5
- direct AI 3.0
- human replay 2.5
- AI replay 2.5
- human mixer 2.5
- AI mixer 2.5
- partial suspicious 3.0

### Bonus from baseline failures
- clean_human_false_alarm +0.5
- direct_ai_missed +0.75
- direct_ai_file_level_missed_but_segment_suspicious +0.5
- partial_fabrication_missed +0.75

Cap at 4.0.

## 6) Losses

```text
risk_loss   = CE(binary_logits, risk_target)
attack_loss = CE(attack_logits, attack_target) [masked when unknown]
total_loss  = risk_loss + 0.5 * attack_loss
```

## 7) Checkpoint strategy

Save every epoch +:

- `hybrid_resnet_environmental_phase7c3_r2_best_loss.pth`
- `hybrid_resnet_environmental_phase7c3_r2_best_product.pth`
- `hybrid_resnet_environmental_phase7c3_r2_last.pth`

Product proxy score:

```text
0.30 * clean_human_acceptance
+ 0.30 * direct_ai_detection
+ 0.20 * replay_detection
+ 0.20 * partial_or_mixer_detection
```

## 8) Acceptance criteria

- Clean human false alarms remain low
- Direct AI detection improves
- Replay/mixer detection does not collapse
- Partial fabrication detection remains close/improves
- Phase7A holdout does not collapse

## 9) Safety

- v1 artifacts preserved in `reports/phase7/phase7c3_finetune/`
- R2 artifacts written only in `reports/phase7/phase7c3_finetune_r2/`
- Base checkpoint never overwritten

