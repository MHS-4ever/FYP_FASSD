# Phase 9G Final Release Report

Generated: 2026-06-03T21:14:58.685+00:00

**Phase 9G status:** PASS

## Identity

- **Release name:** phase9g_deepfake_audio_detector_demo_handoff
- **Product name:** Deepfake Audio Detector — Local Demo
- **Research / FYP name:** Forensic Acoustic for Synthetic Speech Detection

## Frozen phase status

- Phase 9E-P3 release correctness: PASS
- Phase 9E-P4A origin support shadow: PASS (reject_for_now)
- Phase 9E-P4B demo freeze: PASS
- Phase 9F integration docs: PASS

## Active models

- Registry entries: origin_file_model, replay_file_model, mixer_file_model, partial_fabrication_segment_model
- Integration module: partial_fabrication_experimental_p5b (experimental_manual_review_only)

## Inactive reference models

- AASIST: reject_for_now
- HybridResNet/ResNet: reject_for_now

## Known limitations

- Partial fabrication experimental / manual-review candidate only
- Full partial replacement detection not guaranteed
- Replay/channel processing reduces origin reliability
- Local demo only — no operational deployment or legal-evidence claims
- Conclusive authenticity decision: no

## Run commands

```bat
cd /d E:\FYP\release
conda activate fassd
python app_gradio.py
```

```bat
cd /d E:\FYP\release
run_fastapi.bat
```

## Package contents summary

- Files in manifest: 71
- Total uncompressed bytes: 37248295
- Zip path: `release_packages/phase9g_deepfake_audio_detector_demo_handoff.zip`

## Checksum summary

- Manifest: `reports/phase9/final_release/phase9g_final_release_manifest.csv`
- SHA256 list: `reports/phase9/final_release/phase9g_final_checksums_sha256.txt`

## Final go/no-go decision

**GO** — Release package is ready for demo/handoff.

## Next handoff instruction

1. Extract the zip to a clean directory preserving `release/` layout.
2. Create conda env `fassd` and install `release/requirements_release.txt`.
3. Read `reports/phase9/integration_docs/phase9f_teammate_handoff.md`.
4. Run Gradio or FastAPI locally; do not claim operational or legal-evidence readiness.

## Safety

This packaging step did not retrain models, change thresholds, or activate AASIST/ResNet.
