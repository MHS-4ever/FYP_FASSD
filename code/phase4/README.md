# Phase 4: Hybrid Model Training

**Status**: ✅ **COMPLETED (TRAINED + CHECKPOINTS SAVED)**  
**Priority**: 🔴 CRITICAL  
**Duration**: Week 3-4  
**Dependencies**: Phase 3 (Hybrid Architecture) ✅ COMPLETE, Phase 2 (Feature Extraction) ✅ COMPLETE  
**Completion Date**: December 2025

---

## 🎯 Quick Start (Recommended: PC / FAST)

**Final proven PC training command (RTX 3070, batch=128):**

```powershell
cd C:\FYP
conda activate fassd
python code/phase4/train_hybrid_fast.py --train_manifest data/manifests/train_speaker_independent.csv --val_manifest data/manifests/val_speaker_independent.csv --spectrogram_h5 C:/FYP/data/features/logmel_chunked.h5 --environmental_h5 C:/FYP/data/features/environmental_packed.h5 --output_dir models_saved --batch_size 128 --epochs 20 --profile_batches 0
```

**Output:** best checkpoint + periodic checkpoints + CSV log in `models_saved/`.

---

## 📁 Scripts in This Folder

| Script                           | Purpose                   | When to Use                          |
| -------------------------------- | ------------------------- | ------------------------------------ |
| `hybrid_dataset.py`              | Dataset class for hybrid features | Imported by training script (automatic) |
| `train_hybrid_model.py`          | Main training script      | Run to train the hybrid model        |
| `run_phase4.py`                  | Orchestrator script       | Run to execute training with defaults |
| `README.md`                      | This documentation        | Reference for using Phase 4 scripts  |
| `train_hybrid_fast.py`           | FAST training (chunk-aligned batch reads) | Use when `logmel_chunked.h5` is available |
| `hybrid_dataset_fast.py`         | FAST dataset/loader for chunked HDF5 | Used by `train_hybrid_fast.py` |
| `repack_h5_chunked.py`           | Repack spectrogram HDF5 to larger chunks | One-time fix for I/O bottleneck |
| `convert_h5_uncompressed.py`     | Convert gzip-packed HDF5 → uncompressed | One-time fix when gzip caused extreme slowness |
| `pre_training_check.py`          | Verify GPU, data integrity, and I/O speed | Run before long trainings |

---

## ✅ What Phase 4 Produced

- **Best checkpoint**: `models_saved/hybrid_resnet_environmental_best.pth` (best val EER **20.17%**, epoch 17)
- **Periodic checkpoints**: `models_saved/hybrid_resnet_environmental_epoch_{5,10,15,20}.pth`
- **Training log**: `models_saved/logs/training_hybrid_fast.csv`

---

## 📁 Required Inputs

- **Manifests**
  - `data/manifests/train_speaker_independent.csv`
  - `data/manifests/val_speaker_independent.csv`
  - `data/manifests/test_speaker_independent.csv` (used in Phase 5)
- **HDF5 features**
  - Spectrogram (final fast file): `C:/FYP/data/features/logmel_chunked.h5`
  - Environmental: `C:/FYP/data/features/environmental_packed.h5`

---

## 🧪 One-time Preparation Scripts (only if needed)

### Convert gzip HDF5 → uncompressed (fixes decompression bottleneck)

```powershell
cd E:\FYP
conda activate fassd
python code/phase4/convert_h5_uncompressed.py
```

### Repack spectrogram HDF5 to chunked layout (fixes random-access bottleneck)

```powershell
cd E:\FYP
conda activate fassd
python code/phase4/repack_h5_chunked.py --input D:/FYP/data/features/logmel_packed.h5 --output E:/FYP/data/features/logmel_chunked.h5 --chunk_samples 256
```

---

## 🔎 Pre-training verification (recommended)

```powershell
cd C:\FYP
conda activate fassd
python code/phase4/pre_training_check.py
```

---

## 🚀 Training (Final / Proven)

```powershell
cd C:\FYP
conda activate fassd
python code/phase4/train_hybrid_fast.py --train_manifest data/manifests/train_speaker_independent.csv --val_manifest data/manifests/val_speaker_independent.csv --spectrogram_h5 C:/FYP/data/features/logmel_chunked.h5 --environmental_h5 C:/FYP/data/features/environmental_packed.h5 --output_dir models_saved --batch_size 128 --epochs 20 --profile_batches 0
```

### What is `--profile_batches`?

Optional debugging flag:
- If `--profile_batches 200`, the first 200 train batches display timing (`load_ms`, `h2d_ms`, `step_ms`).
- Use `0` for normal training.

---

## 📦 Outputs

```text
models_saved/
  hybrid_resnet_environmental_best.pth
  hybrid_resnet_environmental_epoch_5.pth
  hybrid_resnet_environmental_epoch_10.pth
  hybrid_resnet_environmental_epoch_15.pth
  hybrid_resnet_environmental_epoch_20.pth
  logs/
    training_hybrid_fast.csv
```

---

## 🐛 Minimal Troubleshooting

- **CUDA OOM**: lower `--batch_size` (e.g., 64).
- **Slow batches**: run with `--profile_batches 200` and check:
  - `load_ms` high → disk/HDF5/path issue
  - `step_ms` high → batch too large / GPU compute limited
- ASVspoof/Real-world EER not shown
- Only overall metrics displayed

**Explanation:**

- Per-domain metrics only computed during full evaluation (every 5 epochs)
- Quick evaluation (every epoch) only shows overall metrics
- This is normal behavior to save time

**To see per-domain metrics every epoch:**

- Modify `train_hybrid_model.py` to always run full evaluation
- Or wait for full evaluation epochs (every 5 epochs)

---

### Issue: Windows Multiprocessing Errors

**Error Message:**

```
RuntimeError: An attempt has been made to start a new process before the current process has finished its bootstrapping phase.
```

**Solutions:**

1. **Reduce number of workers:**
   ```bash
   python code/phase4/train_hybrid_model.py ... --num_workers 4
   ```

2. **Use persistent workers:**
   - Already enabled by default
   - Helps with Windows multiprocessing

3. **Check HDF5 file handles:**
   - Dataset class opens HDF5 files per worker (safe)
   - Should not cause issues

---

## 📝 Notes

- **KEY METRIC**: Real-world domain EER < 20% (this is the critical requirement)
- Monitor per-domain performance throughout training
- If Real-world performance is poor, may need Phase 7 (Domain Adaptation)
- Keep training logs for analysis
- Document any training issues or adjustments
- Best model is saved automatically (lowest validation EER)

---

## 🔗 Next Steps

- **Phase 5: Evaluation** (next): evaluate `models_saved/hybrid_resnet_environmental_best.pth` on `data/manifests/test_speaker_independent.csv`.
- **Phase 6/7**: analysis + domain adaptation if needed.

---

**Last Updated**: December 27, 2025  
**Status**: ✅ **COMPLETED**

