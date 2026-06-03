# Phase 9E-P4A Reference Model Audit

**Summary:** one or more reference origin-support models runnable for shadow eval

## aasist

- package_path: `E:\FYP\release\models\reference\aasist`
- weights_found: True
- config_found: True
- inference_code_found: True
- expected_input_format: mono float32 waveform @16kHz, fixed-length windows (nb_samp from AASIST-L config)
- runnable_in_release: True
- reason_if_not_runnable: —
- estimated_runtime_risk: medium (sliding windows on long files)
- gpu_memory_risk: medium (windowed inference; batch size 1 default)
- action: runnable_shadow_eval

## hybrid_resnet

- package_path: `E:\FYP\release\models\reference\hybrid_resnet`
- weights_found: True
- config_found: True
- inference_code_found: True
- expected_input_format: mono @16kHz → log-mel [64x400] + 12-D environmental features per 4s chunk
- runnable_in_release: True
- reason_if_not_runnable: —
- estimated_runtime_risk: medium (librosa feature extraction per chunk)
- gpu_memory_risk: low-medium (chunked 4s windows)
- action: runnable_shadow_eval

Active release fusion unchanged; shadow eval only.
