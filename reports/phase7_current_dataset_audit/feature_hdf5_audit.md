# Feature HDF5 Audit — Phase 7C0

**Generated:** 2026-05-17 22:28 UTC

Audits HDF5 stores referenced by HybridResNetEnvironmental training (no full-file load).

## `data/features/logmel_chunked.h5`

- **Size:** 193.9835 GB
- **Top-level keys:** `features, indices, metadata`
- **Samples:** 1,893,919
- **Per-sample shape:** `(64, 400)`

### Datasets / groups

- `features`: shape=(1893919, 64, 400), dtype=float32, compression=none, chunks=(256, 64, 400)
- `indices` (group): keys=['h5_idx', 'manifest_idx']
- `indices/h5_idx`: shape=(1893919,), dtype=int32, compression=none, chunks=default
- `indices/manifest_idx`: shape=(1893919,), dtype=int64, compression=none, chunks=default
- `metadata` (group): keys=[]

### Shape validation

- `logmel_shape_ok`: True
- `expected`: [64,400] or [1,64,400]
- `actual`: (64, 400)

### Sample statistics (random subset)

**features:** min=-80.0, max=0.0, mean=-31.46032107327366, std=29.32580427487891, NaN=0, Inf=0

## `data/features/environmental_packed.h5`

- **Size:** 0.1145 GB
- **Top-level keys:** `features, indices, metadata`
- **Samples:** 1,893,919
- **Per-sample shape:** `(12,)`

### Datasets / groups

- `features`: shape=(1893919, 12), dtype=float32, compression=none, chunks=(100, 12)
- `indices` (group): keys=['h5_idx', 'manifest_idx']
- `indices/h5_idx`: shape=(1893919,), dtype=int32, compression=none, chunks=default
- `indices/manifest_idx`: shape=(1893919,), dtype=int64, compression=none, chunks=default
- `metadata` (group): keys=[]

### Shape validation

- `env_dim_ok`: True
- `expected`: 12
- `actual`: 12

### Sample statistics (random subset)

**features:** min=-62.13546371459961, max=38.628475189208984, mean=-1.1030053309548338, std=12.60873853693047, NaN=0, Inf=0

## `data/features/logmel_packed.h5`

**Status:** file not found on disk.

## Training note

Production training/eval for the current hybrid checkpoint uses `logmel_chunked.h5` + `environmental_packed.h5` (see `reports/evaluation/comprehensive_evaluation_report.md`). `logmel_packed.h5` may exist as the Phase 2 packed source before chunk repack.
