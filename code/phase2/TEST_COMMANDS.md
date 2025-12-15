# Phase 2 Test Commands

Quick reference for testing Phase 2 scripts with 1000 samples before running the full extraction.

---

## 🧪 Individual Script Testing (1000 samples)

### Step 1: Extract Spectrogram Features

```bash
python code/phase2/extract_spectrogram_features.py \
    --manifest data/manifests/unified_manifest.csv \
    --output_dir data/features/spectrograms \
    --max_samples 1000
```

**Expected output:**
- Creates `data/features/spectrograms/` directory
- Generates 1000 `.npy` files (e.g., `00000000_<audio_name>_logmel.npy`)
- Shows progress bar and summary statistics

---

### Step 2: Extract Environmental Features

```bash
python code/phase2/extract_environmental_features.py \
    --manifest data/manifests/unified_manifest.csv \
    --output_dir data/features/environmental \
    --max_samples 1000
```

**Expected output:**
- Creates `data/features/environmental/` directory
- Generates 1000 `.npy` files (e.g., `00000000_<audio_name>_env.npy`)
- Shows progress bar and summary statistics

---

### Step 3: Pack Features to HDF5

```bash
python code/phase2/pack_features_to_hdf5.py \
    --manifest data/manifests/unified_manifest.csv \
    --spectrogram_dir data/features/spectrograms \
    --environmental_dir data/features/environmental \
    --output_dir data/features
```

**Expected output:**
- Creates `data/features/logmel_packed.h5`
- Creates `data/features/environmental_packed.h5`
- Creates `data/features/features_manifest_unified.csv`
- Creates `data/features/packing_stats.json`
- Shows packing progress and file sizes

---

### Step 4: Verify Features

```bash
python code/phase2/verify_features.py \
    --manifest data/features/features_manifest_unified.csv \
    --spectrogram_h5 data/features/logmel_packed.h5 \
    --environmental_h5 data/features/environmental_packed.h5
```

**Expected output:**
- Verifies spectrogram features (shape, NaN/Inf checks)
- Verifies environmental features (shape, NaN/Inf checks)
- Verifies manifest indices
- Creates `data/features/verification_report.json`
- Shows verification summary

---

## 🚀 Master Script (Full Pipeline)

After testing individual scripts, run the orchestrator:

### Test Mode (1000 samples)

```bash
python code/phase2/run_phase2.py --max_samples 1000
```

### Full Extraction (All samples)

```bash
python code/phase2/run_phase2.py --resume
```

**Note:** The `--resume` flag allows you to continue from where you left off if the process is interrupted.

---

## 📋 Verification Checklist

After running all steps, verify:

- [ ] Spectrogram files exist: `data/features/spectrograms/*.npy` (1000 files)
- [ ] Environmental files exist: `data/features/environmental/*.npy` (1000 files)
- [ ] HDF5 files created: `logmel_packed.h5` and `environmental_packed.h5`
- [ ] Manifest updated: `features_manifest_unified.csv` has `spectrogram_idx` and `environmental_idx` columns
- [ ] Verification report: `verification_report.json` shows all checks passed
- [ ] No errors in extraction logs

---

## 🔍 Quick Verification Commands

```bash
# Count extracted files
ls data/features/spectrograms/*.npy | wc -l
ls data/features/environmental/*.npy | wc -l

# Check HDF5 file sizes
ls -lh data/features/*.h5

# View verification report
cat data/features/verification_report.json
```

---

## ⚠️ Troubleshooting

**Issue: File not found errors**
- Verify manifest path is correct
- Check that audio files exist at paths specified in manifest

**Issue: Shape mismatches**
- Check that audio files are valid and not corrupted
- Verify sample rate is 16kHz

**Issue: Out of memory**
- Reduce `--max_samples` for testing
- Ensure sufficient disk space for .npy files

---

**Last Updated**: December 2025

