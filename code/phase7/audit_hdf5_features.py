"""
Phase 7C0: Audit HDF5 feature files used by HybridResNetEnvironmental training.

Samples HDF5 safely (no full load). Writes feature_hdf5_audit.md and feature_shape_summary.csv.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import h5py
import numpy as np

_REPO_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_H5_FILES = (
    "logmel_chunked.h5",
    "environmental_packed.h5",
    "logmel_packed.h5",
)

EXPECTED_LOGMEL_SHAPES = {(64, 400), (1, 64, 400)}
EXPECTED_ENV_DIM = 12
SAMPLE_INDICES = 32


def _repo_rel(path: Path) -> str:
    try:
        return str(path.relative_to(_REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def _dataset_info(h5f: h5py.File, key: str) -> dict:
    if key not in h5f:
        return {"present": False}
    ds = h5f[key]
    info = {
        "present": True,
        "shape": tuple(ds.shape),
        "dtype": str(ds.dtype),
        "ndim": ds.ndim,
    }
    if hasattr(ds, "compression") and ds.compression:
        info["compression"] = ds.compression
    if hasattr(ds, "chunks") and ds.chunks:
        info["chunks"] = tuple(ds.chunks)
    return info


def _sample_stats(arr: np.ndarray) -> dict:
    flat = np.asarray(arr, dtype=np.float64).ravel()
    nan_count = int(np.isnan(flat).sum())
    inf_count = int(np.isinf(flat).sum())
    finite = flat[np.isfinite(flat)]
    if finite.size == 0:
        return {
            "min": "",
            "max": "",
            "mean": "",
            "std": "",
            "nan_count": nan_count,
            "inf_count": inf_count,
        }
    return {
        "min": float(finite.min()),
        "max": float(finite.max()),
        "mean": float(finite.mean()),
        "std": float(finite.std()),
        "nan_count": nan_count,
        "inf_count": inf_count,
    }


def audit_h5_file(path: Path, sample_n: int = SAMPLE_INDICES) -> dict:
    result = {
        "path": _repo_rel(path),
        "exists": path.is_file(),
        "size_gb": round(path.stat().st_size / 1e9, 4) if path.is_file() else None,
        "top_level_keys": [],
        "datasets": {},
        "attrs": {},
        "sample_stats": {},
        "shape_checks": {},
        "errors": [],
    }
    if not path.is_file():
        return result

    try:
        with h5py.File(path, "r") as h5f:
            result["top_level_keys"] = list(h5f.keys())
            for k in h5f.keys():
                obj = h5f[k]
                if isinstance(obj, h5py.Dataset):
                    result["datasets"][k] = _dataset_info(h5f, k)
                elif isinstance(obj, h5py.Group):
                    result["datasets"][k] = {
                        "type": "group",
                        "keys": list(obj.keys()),
                    }
                    for sub in obj.keys():
                        sub_key = f"{k}/{sub}"
                        if isinstance(obj[sub], h5py.Dataset):
                            result["datasets"][sub_key] = _dataset_info(h5f, sub_key)

            result["attrs"] = {a: str(h5f.attrs[a]) for a in h5f.attrs}

            features_key = None
            for candidate in ("features", "logmel", "spectrogram"):
                if candidate in h5f and isinstance(h5f[candidate], h5py.Dataset):
                    features_key = candidate
                    break

            if features_key:
                ds = h5f[features_key]
                n = ds.shape[0]
                result["num_samples"] = int(n)
                if ds.ndim >= 2:
                    feat_shape = tuple(ds.shape[1:])
                    result["feature_shape"] = feat_shape
                    if "logmel" in path.name.lower():
                        tail = feat_shape[-2:] if len(feat_shape) >= 2 else feat_shape
                        ok = tail in {(64, 400)} or feat_shape in EXPECTED_LOGMEL_SHAPES
                        result["shape_checks"]["logmel_shape_ok"] = ok
                        result["shape_checks"]["expected"] = "[64,400] or [1,64,400]"
                        result["shape_checks"]["actual"] = str(feat_shape)
                    if "environmental" in path.name.lower():
                        dim = feat_shape[0] if feat_shape else 0
                        result["shape_checks"]["env_dim_ok"] = dim == EXPECTED_ENV_DIM
                        result["shape_checks"]["expected"] = str(EXPECTED_ENV_DIM)
                        result["shape_checks"]["actual"] = str(dim)

                rng = np.random.default_rng(42)
                idx = rng.choice(n, size=min(sample_n, n), replace=False)
                idx = np.sort(idx)
                chunks = []
                for i in idx:
                    row = ds[int(i)]
                    chunks.append(np.asarray(row))
                sample_arr = np.stack(chunks, axis=0)
                result["sample_stats"][features_key] = _sample_stats(sample_arr)
    except Exception as exc:
        result["errors"].append(str(exc))

    return result


def write_csv(rows: list[dict], out_path: Path) -> None:
    if not rows:
        out_path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def write_markdown(results: list[dict], out_path: Path) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Feature HDF5 Audit — Phase 7C0",
        "",
        f"**Generated:** {ts}",
        "",
        "Audits HDF5 stores referenced by HybridResNetEnvironmental training (no full-file load).",
        "",
    ]
    for r in results:
        lines.append(f"## `{r['path']}`")
        lines.append("")
        if not r["exists"]:
            lines.append("**Status:** file not found on disk.")
            lines.append("")
            continue
        lines.append(f"- **Size:** {r.get('size_gb')} GB")
        lines.append(f"- **Top-level keys:** `{', '.join(r.get('top_level_keys', []))}`")
        if r.get("num_samples"):
            lines.append(f"- **Samples:** {r['num_samples']:,}")
        if r.get("feature_shape"):
            lines.append(f"- **Per-sample shape:** `{r['feature_shape']}`")
        if r.get("datasets"):
            lines.append("")
            lines.append("### Datasets / groups")
            lines.append("")
            for name, info in r["datasets"].items():
                if info.get("type") == "group":
                    lines.append(f"- `{name}` (group): keys={info.get('keys')}")
                elif info.get("present"):
                    lines.append(
                        f"- `{name}`: shape={info.get('shape')}, dtype={info.get('dtype')}, "
                        f"compression={info.get('compression', 'none')}, chunks={info.get('chunks', 'default')}"
                    )
        if r.get("shape_checks"):
            lines.append("")
            lines.append("### Shape validation")
            lines.append("")
            for k, v in r["shape_checks"].items():
                lines.append(f"- `{k}`: {v}")
        if r.get("sample_stats"):
            lines.append("")
            lines.append("### Sample statistics (random subset)")
            lines.append("")
            for k, st in r["sample_stats"].items():
                lines.append(f"**{k}:** min={st.get('min')}, max={st.get('max')}, "
                             f"mean={st.get('mean')}, std={st.get('std')}, "
                             f"NaN={st.get('nan_count')}, Inf={st.get('inf_count')}")
        if r.get("errors"):
            lines.append("")
            lines.append(f"**Errors:** {'; '.join(r['errors'])}")
        lines.append("")

    lines.append("## Training note")
    lines.append("")
    lines.append(
        "Production training/eval for the current hybrid checkpoint uses "
        "`logmel_chunked.h5` + `environmental_packed.h5` (see `reports/evaluation/comprehensive_evaluation_report.md`). "
        "`logmel_packed.h5` may exist as the Phase 2 packed source before chunk repack."
    )
    lines.append("")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


def print_summary(results: list[dict]) -> None:
    print("\n" + "=" * 72)
    print("HDF5 FEATURE AUDIT SUMMARY")
    print("=" * 72)
    for r in results:
        status = "FOUND" if r["exists"] else "MISSING"
        print(f"  [{status}] {r['path']}")
        if r["exists"] and r.get("num_samples"):
            print(f"         samples={r['num_samples']:,}, shape={r.get('feature_shape')}")
            sc = r.get("shape_checks", {})
            if "logmel_shape_ok" in sc:
                print(f"         logmel shape OK: {sc['logmel_shape_ok']}")
            if "env_dim_ok" in sc:
                print(f"         env dim OK: {sc['env_dim_ok']}")
    print("=" * 72)


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit training HDF5 feature files (Phase 7C0)")
    parser.add_argument("--features_dir", type=str, default="data/features")
    parser.add_argument("--output_dir", type=str, default="reports/phase7/phase7_current_dataset_audit")
    parser.add_argument("--sample_n", type=int, default=SAMPLE_INDICES)
    args = parser.parse_args()

    features_dir = (_REPO_ROOT / args.features_dir).resolve()
    output_dir = (_REPO_ROOT / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    csv_rows = []
    for name in DEFAULT_H5_FILES:
        path = features_dir / name
        audit = audit_h5_file(path, sample_n=args.sample_n)
        results.append(audit)
        feat_shape = audit.get("feature_shape", "")
        sc = audit.get("shape_checks", {})
        csv_rows.append({
            "file": audit["path"],
            "exists": audit["exists"],
            "size_gb": audit.get("size_gb", ""),
            "num_samples": audit.get("num_samples", ""),
            "feature_shape": str(feat_shape),
            "shape_check_ok": sc.get("logmel_shape_ok", sc.get("env_dim_ok", "")),
            "compression": "",
            "notes": "; ".join(audit.get("errors", [])),
        })
        if audit["exists"] and audit.get("datasets"):
            for dname, dinfo in audit["datasets"].items():
                if dinfo.get("present"):
                    csv_rows.append({
                        "file": audit["path"],
                        "exists": True,
                        "size_gb": "",
                        "num_samples": dinfo.get("shape", ("",))[0] if dinfo.get("shape") else "",
                        "feature_shape": str(dinfo.get("shape", "")),
                        "shape_check_ok": "",
                        "compression": dinfo.get("compression", "none"),
                        "notes": f"dataset={dname}",
                    })

    write_markdown(results, output_dir / "feature_hdf5_audit.md")
    write_csv(csv_rows, output_dir / "feature_shape_summary.csv")
    (output_dir / "feature_hdf5_audit.json").write_text(
        json.dumps(results, indent=2, default=str), encoding="utf-8"
    )
    print_summary(results)
    print(f"\n[OK] Wrote {output_dir / 'feature_hdf5_audit.md'}")
    print(f"[OK] Wrote {output_dir / 'feature_shape_summary.csv'}")


if __name__ == "__main__":
    main()
