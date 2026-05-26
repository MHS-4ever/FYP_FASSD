# Phase 7E1 — AASIST Smoke Test

**Generated:** 2026-05-26T19:43:18.975929+00:00  
**Verdict:** `PASS`  
**Next action:** Proceed to Phase 7E2 dataset adapter; optional 7E3A pretrained eval with same config/checkpoint.  

## Summary

| Field | Value |
|-------|-------|
| model_variant | `AASIST-L` |
| config_path | `E:\FYP\code\phase7\aasist\vendor\AASIST\config\AASIST-L.conf` |
| checkpoint_path | `E:\FYP\code\phase7\aasist\vendor\AASIST\models\weights\AASIST-L.pth` |
| nb_samp | `64600` |
| model module/class | `models.AASIST.Model` |
| checkpoint_load_status | `loaded_ok` |
| missing_keys_count | `0` |
| unexpected_keys_count | `0` |
| dummy_input_shape | `[1, 64600]` |
| output_shape | `[1, 2]` |
| forward_success | `True` |

## Environment

| Python | `C:\Users\mhasn\miniconda3\envs\fassd\python.exe` |
| PyTorch | `2.5.1+cu121` |
| CUDA | `True` |
| GPU | `NVIDIA GeForce RTX 3050 6GB Laptop GPU` |
| VRAM before | `{'allocated_gb': 0.0, 'reserved_gb': 0.0}` |
| VRAM after | `{'allocated_gb': 0.0086, 'reserved_gb': 0.2461}` |

## Checkpoint load

```json
{
  "checkpoint_path": "E:\\FYP\\code\\phase7\\aasist\\vendor\\AASIST\\models\\weights\\AASIST-L.pth",
  "checkpoint_load_status": "loaded_ok",
  "missing_keys_count": 0,
  "unexpected_keys_count": 0,
  "missing_keys_sample": [],
  "unexpected_keys_sample": [],
  "state_dict_key": "root"
}
```

## Forward

```json
{
  "mode": "dummy",
  "dummy_input_shape": [
    1,
    64600
  ],
  "output_tuple": true,
  "last_hidden_shape": [
    1,
    160
  ],
  "output_shape": [
    1,
    2
  ],
  "forward_success": true,
  "output_is_batch_x_2": true
}
```

