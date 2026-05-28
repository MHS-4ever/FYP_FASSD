# Phase 8D-A1 SSL Embedding Audit Report

**Generated:** 2026-05-28 09:48:13 UTC
**Runtime:** 46.53s

> **Descriptive analysis only** — no training, no predictions, no model performance claims.

## 1. Consistency checks

- Embedding rows and IDs align with Phase 8B tables.

## 2. Segment label inheritance

Segment group analysis is based on file-level known labels unless true segment annotations are available.

## 3. Missingness and limitations

- exclude_for_now: 0 entries
- limited: 0 entries

## 4. Top candidate embedding dimensions (descriptive)

### clean_human_vs_clean_ai_synthetic
- `ssl_emb_434` effect_size=4.796534648330947 direction=higher_in_group_a — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_742` effect_size=4.692376114314712 direction=higher_in_group_b — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_690` effect_size=4.514135840082694 direction=higher_in_group_b — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_138` effect_size=4.385308599362779 direction=higher_in_group_a — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_729` effect_size=4.140948758514412 direction=higher_in_group_a — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_110` effect_size=4.125218593503353 direction=higher_in_group_b — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_241` effect_size=3.969893791647681 direction=higher_in_group_b — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_560` effect_size=3.8866233569997255 direction=higher_in_group_b — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector

### clean_vs_mixer_channel_processed
- `ssl_emb_390` effect_size=2.5638082515508613 direction=higher_in_group_a — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_336` effect_size=2.2334407459772785 direction=higher_in_group_b — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_582` effect_size=2.220135691240053 direction=higher_in_group_a — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_369` effect_size=2.2192354733553823 direction=higher_in_group_b — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_445` effect_size=2.141742731050344 direction=higher_in_group_a — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_668` effect_size=2.10534019665883 direction=higher_in_group_b — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_527` effect_size=2.0960323450853737 direction=higher_in_group_b — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_703` effect_size=2.05792324933527 direction=higher_in_group_a — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector

### clean_vs_non_clean
- `ssl_emb_445` effect_size=1.377939837280158 direction=higher_in_group_a — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_369` effect_size=1.371115894390167 direction=higher_in_group_b — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_762` effect_size=1.3440190462085913 direction=higher_in_group_b — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_336` effect_size=1.342884010501598 direction=higher_in_group_b — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_370` effect_size=1.335677333647915 direction=higher_in_group_a — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_581` effect_size=1.319788426691729 direction=higher_in_group_a — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_390` effect_size=1.3051902760351013 direction=higher_in_group_a — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_576` effect_size=1.2952707195115973 direction=higher_in_group_b — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector

### clean_vs_partial_combo
- `ssl_emb_375` effect_size=0.9390369882593382 direction=higher_in_group_a — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_542` effect_size=0.8826301038461113 direction=higher_in_group_a — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_470` effect_size=0.8366170682408062 direction=higher_in_group_a — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_279` effect_size=0.8169520554987453 direction=higher_in_group_b — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_142` effect_size=0.8075029006372918 direction=higher_in_group_a — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_526` effect_size=0.77907416008466 direction=higher_in_group_a — possible candidate for later modeling; descriptive only; requires validation in Phase 8E
- `ssl_emb_124` effect_size=0.7705167599664338 direction=higher_in_group_a — possible candidate for later modeling; descriptive only; requires validation in Phase 8E
- `ssl_emb_044` effect_size=0.7651708917750415 direction=higher_in_group_b — possible candidate for later modeling; descriptive only; requires validation in Phase 8E

### clean_vs_replay_rerecorded
- `ssl_emb_336` effect_size=3.626235372599293 direction=higher_in_group_b — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_576` effect_size=3.5841557911880213 direction=higher_in_group_b — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_445` effect_size=3.417989950772638 direction=higher_in_group_a — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_255` effect_size=3.3741304318086205 direction=higher_in_group_a — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_141` effect_size=3.2724467172226146 direction=higher_in_group_a — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_378` effect_size=3.20195485643559 direction=higher_in_group_a — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_603` effect_size=3.17480243056061 direction=higher_in_group_b — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_063` effect_size=3.1733350878049222 direction=higher_in_group_a — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector

### human_vs_ai_synthetic
- `ssl_emb_442` effect_size=2.8158588195133114 direction=higher_in_group_b — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_690` effect_size=2.7487544121545193 direction=higher_in_group_b — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_671` effect_size=2.7052462534343364 direction=higher_in_group_a — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_506` effect_size=2.589560559554148 direction=higher_in_group_b — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_617` effect_size=2.4857321106393706 direction=higher_in_group_b — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_481` effect_size=2.344867954908456 direction=higher_in_group_a — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_407` effect_size=2.325040232735744 direction=higher_in_group_b — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_288` effect_size=2.252895669594819 direction=higher_in_group_b — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector

### mixed_vs_clean_human
- `ssl_emb_729` effect_size=2.289039277887295 direction=higher_in_group_b — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_690` effect_size=2.233251892468253 direction=higher_in_group_a — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_095` effect_size=2.1628652763640295 direction=higher_in_group_a — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_481` effect_size=2.0077857626172526 direction=higher_in_group_b — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_601` effect_size=2.0029199546311123 direction=higher_in_group_a — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_427` effect_size=1.9903352160186145 direction=higher_in_group_a — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_605` effect_size=1.9687754161723636 direction=higher_in_group_b — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_575` effect_size=1.9624871394774168 direction=higher_in_group_b — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector

### seg_clean_vs_mixer_inherited
- `ssl_emb_668` effect_size=1.4999607764923504 direction=higher_in_group_b — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_369` effect_size=1.4577551624999368 direction=higher_in_group_b — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_590` effect_size=1.432854016105757 direction=higher_in_group_a — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_456` effect_size=1.4258869839712134 direction=higher_in_group_a — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_398` effect_size=1.407800944950758 direction=higher_in_group_b — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_095` effect_size=1.398409598530844 direction=higher_in_group_a — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_644` effect_size=1.3196441566561814 direction=higher_in_group_a — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector
- `ssl_emb_350` effect_size=1.3037566174003774 direction=higher_in_group_b — embedding dimension shows descriptive separation; possible candidate for later modeling; not a standalone detector

## 5. Notes for Phase 8E

- Candidate dimensions are only descriptive indicators.
- Embedding dimensions are less interpretable than handcrafted acoustic features.
- Calibration and model validation are still required in Phase 8E.

## 6. Outputs

- `reports/phase8/embeddings/audit`
