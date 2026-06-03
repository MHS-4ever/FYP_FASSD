# Phase 9F — Known Limitations

Honest scope limits for **Deepfake Audio Detector — Local Demo** (research: **Forensic Acoustic for Synthetic Speech Detection**). Phase 9E-P4B demo freeze accepted; Phase 9F documents these for teammate handoff.

---

## Partial fabrication

- Partial fabrication is **experimental** and **manual-review candidate only** in the release app path.
- Status: `experimental_manual_review_only` (`partial_fabrication_experimental_p5b`).
- **Full partial replacement detection is not guaranteed.** Segment-level candidates may appear on clean human audio and are labeled **optional review**, not strong suspicious evidence.
- The release demo maps Phase 9C segment partial axis into the P6 report contract; the **full P5B file-gate cascade is not the primary wired demo path**.
- P5F holdout metrics (documented in module metadata): fabricated_20pct recall 0.70, known false negatives and false positives remain.

---

## Voice origin (SSL model)

- Voice origin uses the active **SSL origin model** only. Output is experimental evidence, **not** a conclusive authenticity decision.
- **Replay or channel/mixer processing** can reduce reliability of AI-vs-human origin cues.
- App uses cautious wording: *Voice origin: Inconclusive under replay/channel processing* when appropriate.
- **Replay and mixer/channel artifacts may overlap**; overlap notes explain dominant indicators.

---

## Reference models (AASIST / HybridResNet)

- Shadow-tested in Phase 9E-P4A on 184 files.
- **Decision: `reject_for_now`** for both — elevated clean-human false-AI rates; negative net help vs SSL baseline.
- Remain **reference/shadow only** — **not active** in voice origin, replay, mixer, or partial decisions.
- Weights may exist under `release/models/reference/` for history only.

---

## Safety and scope

- **Conclusive authenticity decision: no.**
- Manual forensic review is recommended when strong indicators are present.
- **Optional review** may be useful for sensitive segment-only candidates.
- **Local demo only** — not intended for operational deployment, legal proceedings, or courtroom evidence use.
- No operational deployment readiness claim.
- No legal-evidence readiness claim.

---

## Regression baseline (Phase 9E-P3)

- 184/184 files evaluated, 0 inference failures.
- `human_clean_false_suspicious_rate = 0.0` after P3-P1 wording cleanup.
- Validates release formatting; does not prove real-world generalization.

---

## Phase 9F / 9G constraints

Phase 9F and 9G are documentation and packaging only:

- No retraining
- No threshold changes
- No inference logic changes
- No AASIST/ResNet activation
- No overwrite of `release/models/` artifacts

---

## Validation references

| Report | Path |
|--------|------|
| P3 release correctness | `reports/phase9/validation/phase9e_p3_release_correctness_validation_report.md` |
| P4A origin support | `reports/phase9/validation/phase9e_p4a_origin_support_validation_report.md` |
| P4B demo freeze | `reports/phase9/validation/phase9e_p4b_demo_freeze_validation_report.md` |
| P4B known limitations (source) | `reports/phase9/app/phase9e_p4b_demo_freeze/phase9e_p4b_known_limitations.md` |
