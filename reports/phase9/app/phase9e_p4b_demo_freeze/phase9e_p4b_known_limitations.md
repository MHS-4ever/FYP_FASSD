# Phase 9E-P4B — Known Limitations (Demo Freeze)

This document records honest limitations for the **Deepfake Audio Detector — Local Demo** (research: **Forensic Acoustic for Synthetic Speech Detection**). The demo is frozen for FYP presentation; it is not operational deployment or legal evidence software.

## Partial fabrication

- Partial fabrication remains **experimental** and **manual-review candidate** only in the release app path.
- The app maps the Phase 9C segment partial axis into the P6 report contract; the **full P5B file-gate cascade is not wired** in this demo path.
- Full partial replacement detection is **not guaranteed**. Segment-level candidates may appear on clean human audio and are labeled **optional review**, not strong suspicious evidence.

## Voice origin (SSL model)

- Voice origin uses the active **SSL origin model** only. It is experimental evidence, not a conclusive authenticity decision.
- **Replay or channel/mixer processing** can reduce reliability of AI-vs-human origin cues; the app uses cautious wording such as *Voice origin: Inconclusive under replay/channel processing*.
- **Replay and mixer/channel artifacts may overlap**; overlap wording explains that mixer/channel processing may be the dominant indicator.

## Reference models (AASIST / HybridResNet)

- AASIST and HybridResNet were **shadow-tested** in Phase 9E-P4A (184 files).
- **Decision: reject_for_now** for both — high clean-human false-AI rates; net help vs SSL baseline was negative.
- They remain **reference/shadow only** and are **not active** in voice origin, replay, mixer, or partial decisions.

## Safety and scope

- **Conclusive authenticity decision: no.**
- Manual forensic review is recommended when strong indicators are present; **optional review** may be useful for sensitive segment-only candidates.
- **Local demo only** — not intended for production deployment, legal proceedings, or courtroom evidence use.
- No retraining, threshold changes, or model artifact overwrites were made in Phase 9E-P4B.

## Regression baseline (Phase 9E-P3 full)

- 184/184 files evaluated, 0 inference failures.
- `human_clean_false_suspicious_rate = 0.0`.
- P3-P1 wording cleanup accepted (optional review for clean segment candidates).
