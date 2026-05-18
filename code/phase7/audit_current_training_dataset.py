"""
Phase 7C0: Audit the current HybridResNetEnvironmental training dataset manifests.

Chunk-safe analysis of unified + speaker-independent splits. Does not train models.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[2]
CHUNK_SIZE = 100_000

MANIFEST_NAMES = {
    "unified": "unified_manifest.csv",
    "train": "train_speaker_independent.csv",
    "val": "val_speaker_independent.csv",
    "test": "test_speaker_independent.csv",
}

KNOWN_DOMAINS = {
    "studio", "read_speech", "broadcast", "podcast", "social", "synthetic",
    "phone", "whatsapp", "urdu", "pakistani",
}

DURATION_BUCKETS = [
    ("lt_1s", 0.0, 1.0),
    ("1_2s", 1.0, 2.0),
    ("2_4s", 2.0, 4.0),
    ("4_8s", 4.0, 8.0),
    ("8_15s", 8.0, 15.0),
    ("15_30s", 15.0, 30.0),
    ("gt_30s", 30.0, float("inf")),
]

SAMPLE_GROUPS = [
    ("label", "bonafide"),
    ("label", "spoof"),
    ("attack_type", "synthesis"),
    ("attack_type", "conversion"),
    ("attack_type", "replay"),
    ("attack_type", "bonafide"),
    ("dataset", "RealWorld"),
    ("dataset", "LA"),
    ("dataset", "DF"),
    ("dataset", "PA"),
    ("domain", "studio"),
    ("domain", "read_speech"),
    ("domain", "broadcast"),
    ("domain", "podcast"),
    ("domain", "social"),
    ("domain", "synthetic"),
]

# Best-available column for utterance/file identity (chunk rows may repeat per file).
FILE_ID_COLUMN_PRIORITY = [
    "filepath",
    "file_path",
    "audio_path",
    "path",
    "file_id",
    "utt_id",
    "utterance_id",
    "filename",
]

FILE_BALANCE_DIMENSIONS = [
    ("label", "label", "files_by_label"),
    ("attack_type", "attack_type", "files_by_attack"),
    ("dataset", "dataset", "files_by_dataset"),
    ("domain", "domain", "files_by_domain"),
    ("source", "source", "files_by_source"),
]


def _repo_rel(path: Path) -> str:
    try:
        return str(path.relative_to(_REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def _counter_to_rows(counter: Counter, key_name: str, scope: str = "unified") -> list[dict]:
    total = sum(counter.values()) or 1
    return [
        {
            "scope": scope,
            key_name: k,
            "count": v,
            "pct": round(100.0 * v / total, 4),
        }
        for k, v in counter.most_common()
    ]


def _duration_bucket(sec: float) -> str:
    for name, lo, hi in DURATION_BUCKETS:
        if lo <= sec < hi:
            return name
    return "unknown"


def _safe_str(val: Any) -> str:
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return ""
    return str(val).strip()


def detect_file_id_column(columns: list[str] | pd.Index) -> str | None:
    """Return first available file/utterance identity column."""
    cols = {str(c).strip() for c in columns}
    for name in FILE_ID_COLUMN_PRIORITY:
        if name in cols:
            return name
    return None


def _parse_duration(val: Any) -> float | None:
    s = _safe_str(val)
    if not s:
        return None
    try:
        d = float(s)
        return d if np.isfinite(d) and d >= 0 else None
    except ValueError:
        return None


class ChunkAggregator:
    """Single-pass chunked stats for one manifest."""

    def __init__(self, name: str):
        self.name = name
        self.total_rows = 0
        self.label = Counter()
        self.attack_type = Counter()
        self.dataset = Counter()
        self.domain = Counter()
        self.source = Counter()
        self.duration_buckets = Counter()
        self.filepaths: set[str] = set()
        self.speakers: set[str] = set()
        self.filepath_counts: Counter = Counter()
        self.file_id_counts: Counter = Counter()
        self.filename_counts: Counter = Counter()
        self.file_id_col: str | None = None
        self.file_key_counts: Counter = Counter()
        self.rows_without_file_key = 0
        self.files_by_label: dict[str, set[str]] = defaultdict(set)
        self.files_by_attack: dict[str, set[str]] = defaultdict(set)
        self.files_by_dataset: dict[str, set[str]] = defaultdict(set)
        self.files_by_domain: dict[str, set[str]] = defaultdict(set)
        self.files_by_source: dict[str, set[str]] = defaultdict(set)
        self.has_source_col = False
        self.conflicts: list[dict] = []
        self.max_conflicts = 50_000
        self.duration_sum = 0.0
        self.duration_n = 0
        self.duration_min = None
        self.duration_max = None
        self.missing_label = 0
        self.missing_attack = 0
        self.missing_speaker = 0
        self.missing_duration = 0
        self.has_duration_col = False
        self.has_file_id = False
        self._durations_for_median: list[float] = []
        self._median_cap = 500_000

    def _maybe_conflict(self, row: dict, issue: str) -> None:
        if len(self.conflicts) >= self.max_conflicts:
            return
        self.conflicts.append({
            "manifest": self.name,
            "issue": issue,
            "filepath": _safe_str(row.get("filepath")),
            "file_id": _safe_str(row.get("file_id")),
            "label": _safe_str(row.get("label")),
            "attack_type": _safe_str(row.get("attack_type")),
            "dataset": _safe_str(row.get("dataset")),
            "domain": _safe_str(row.get("domain")),
        })

    def _append_conflicts(self, chunk: pd.DataFrame, mask: pd.Series, issue: str) -> None:
        if not mask.any():
            return
        n = self.max_conflicts - len(self.conflicts)
        if n <= 0:
            return
        sub = chunk.loc[mask].head(n)
        for d in sub.to_dict("records"):
            self._maybe_conflict(d, issue)

    def process_chunk(self, chunk: pd.DataFrame) -> None:
        self.total_rows += len(chunk)
        if "duration" in chunk.columns:
            self.has_duration_col = True
        if "file_id" in chunk.columns:
            self.has_file_id = True
        if "source" in chunk.columns:
            self.has_source_col = True

        if self.file_id_col is None:
            self.file_id_col = detect_file_id_column(chunk.columns)

        self._process_file_balance(chunk)

        for col, counter in (
            ("label", self.label),
            ("attack_type", self.attack_type),
            ("dataset", self.dataset),
            ("domain", self.domain),
            ("source", self.source),
        ):
            if col in chunk.columns:
                vals = chunk[col].fillna("").astype(str).str.strip()
                vals = vals.where(vals != "", "<missing>")
                counter.update(vals.value_counts().to_dict())

        if "filepath" in chunk.columns:
            fps = chunk["filepath"].fillna("").astype(str).str.strip()
            valid = fps != ""
            self.filepaths.update(fps[valid].tolist())
            self.filepath_counts.update(fps[valid].value_counts().to_dict())

        if "file_id" in chunk.columns:
            fids = chunk["file_id"].fillna("").astype(str).str.strip()
            self.file_id_counts.update(fids[fids != ""].value_counts().to_dict())

        if "filename" in chunk.columns:
            fns = chunk["filename"].fillna("").astype(str).str.strip()
            self.filename_counts.update(fns[fns != ""].value_counts().to_dict())

        if "speaker_id" in chunk.columns:
            sp = chunk["speaker_id"].fillna("").astype(str).str.strip()
            self.speakers.update(sp[sp != ""].tolist())
            self.missing_speaker += int((sp == "").sum())

        lbl = chunk["label"].fillna("").astype(str).str.strip() if "label" in chunk.columns else pd.Series([""] * len(chunk))
        atk = chunk["attack_type"].fillna("").astype(str).str.strip() if "attack_type" in chunk.columns else pd.Series([""] * len(chunk))
        dom = chunk["domain"].fillna("").astype(str).str.strip() if "domain" in chunk.columns else pd.Series([""] * len(chunk))

        self.missing_label += int((lbl == "").sum())
        self.missing_attack += int((atk == "").sum())

        if "label" in chunk.columns:
            self._append_conflicts(chunk, lbl == "", "missing_label")
            self._append_conflicts(
                chunk,
                (lbl == "bonafide") & (atk != "bonafide") & (atk != ""),
                "bonafide_label_non_bonafide_attack",
            )
            self._append_conflicts(
                chunk,
                lbl.isin(["spoof", "fake"]) & (atk == "bonafide"),
                "spoof_label_bonafide_attack",
            )
        if "attack_type" in chunk.columns:
            self._append_conflicts(chunk, atk == "", "missing_attack_type")
        if "domain" in chunk.columns:
            unknown = dom != ""
            unknown = unknown & ~dom.str.lower().isin(KNOWN_DOMAINS)
            self._append_conflicts(chunk, unknown, "unknown_domain")

        if "duration" in chunk.columns:
            dur = pd.to_numeric(chunk["duration"], errors="coerce")
            valid = dur.notna() & (dur >= 0)
            self.missing_duration += int((~valid).sum())
            if valid.any():
                d = dur[valid]
                self.duration_sum += float(d.sum())
                self.duration_n += int(valid.sum())
                for val, cnt in d.apply(_duration_bucket).value_counts().items():
                    self.duration_buckets[val] += int(cnt)
                dmin, dmax = float(d.min()), float(d.max())
                if self.duration_min is None or dmin < self.duration_min:
                    self.duration_min = dmin
                if self.duration_max is None or dmax > self.duration_max:
                    self.duration_max = dmax
                need = self._median_cap - len(self._durations_for_median)
                if need > 0:
                    sample = d.sample(n=min(need, len(d)), random_state=42).tolist()
                    self._durations_for_median.extend(sample)

    def _process_file_balance(self, chunk: pd.DataFrame) -> None:
        if not self.file_id_col or self.file_id_col not in chunk.columns:
            return
        keys = chunk[self.file_id_col].fillna("").astype(str).str.strip()
        valid = keys != ""
        self.rows_without_file_key += int((~valid).sum())
        if not valid.any():
            return
        sub = chunk.loc[valid].copy()
        sub["_file_key"] = keys[valid]
        self.file_key_counts.update(sub["_file_key"].value_counts().to_dict())
        self.filepaths.update(sub["_file_key"].unique().tolist())

        for dim_name, col, attr in FILE_BALANCE_DIMENSIONS:
            if col not in sub.columns:
                continue
            if col == "source":
                self.has_source_col = True
            vals = sub[col].fillna("").astype(str).str.strip().replace("", "<missing>")
            files_map: dict[str, set[str]] = getattr(self, attr)
            for val, fk in zip(vals, sub["_file_key"]):
                files_map[val].add(fk)

    @property
    def unique_file_count(self) -> int:
        return len(self.file_key_counts) or len(self.filepaths)

    def avg_rows_per_file(self) -> float:
        n_files = self.unique_file_count
        if n_files == 0:
            return 0.0
        return round(self.total_rows / n_files, 4)

    def duration_stats(self) -> dict:
        if self.duration_n == 0:
            return {}
        med = float(np.median(self._durations_for_median)) if self._durations_for_median else ""
        return {
            "total_duration_sec": round(self.duration_sum, 2),
            "mean_duration_sec": round(self.duration_sum / self.duration_n, 4),
            "median_duration_sec": med,
            "min_duration_sec": self.duration_min,
            "max_duration_sec": self.duration_max,
            "rows_with_duration": self.duration_n,
            "rows_missing_duration": self.missing_duration,
        }

    def summary(self) -> dict:
        bonafide = self.label.get("bonafide", 0)
        spoof = self.label.get("spoof", 0) + self.label.get("fake", 0)
        total_l = bonafide + spoof or 1
        return {
            "manifest": self.name,
            "total_rows": self.total_rows,
            "unique_filepaths": len(self.filepaths),
            "unique_files": self.unique_file_count,
            "file_id_column": self.file_id_col or "",
            "avg_rows_per_file": self.avg_rows_per_file(),
            "rows_without_file_key": self.rows_without_file_key,
            "unique_speakers": len(self.speakers),
            "bonafide_count": bonafide,
            "spoof_count": spoof,
            "bonafide_pct": round(100 * bonafide / total_l, 4),
            "spoof_pct": round(100 * spoof / total_l, 4),
            "missing_label_rows": self.missing_label,
            "missing_attack_type_rows": self.missing_attack,
            "missing_speaker_rows": self.missing_speaker,
            "label_conflict_rows": len(self.conflicts),
            **self.duration_stats(),
        }


def iterate_manifest(path: Path, usecols: list[str] | None = None, chunk_size: int = CHUNK_SIZE):
    if not path.is_file():
        return
    kwargs = {"chunksize": chunk_size, "low_memory": False}
    if usecols:
        kwargs["usecols"] = usecols
    for chunk in pd.read_csv(path, **kwargs):
        yield chunk


def analyze_manifest(path: Path, name: str, chunk_size: int = CHUNK_SIZE) -> ChunkAggregator | None:
    if not path.is_file():
        return None
    agg = ChunkAggregator(name)
    print(f"  [scan] {name}: {_repo_rel(path)}")
    for chunk in iterate_manifest(path, chunk_size=chunk_size):
        agg.process_chunk(chunk)
    print(f"         rows={agg.total_rows:,}, speakers={len(agg.speakers):,}")
    return agg


def load_split_columns(path: Path, columns: list[str]) -> pd.DataFrame | None:
    if not path.is_file():
        return None
    cols = pd.read_csv(path, nrows=0).columns.tolist()
    use = [c for c in columns if c in cols]
    return pd.read_csv(path, usecols=use, low_memory=False)


def speaker_split_integrity(manifest_dir: Path) -> tuple[list[dict], dict]:
    rows = []
    info: dict[str, Any] = {}
    splits = {}
    for split in ("train", "val", "test"):
        p = manifest_dir / MANIFEST_NAMES[split]
        df = load_split_columns(p, ["speaker_id", "filepath", "file_id"])
        if df is None:
            info[f"{split}_missing"] = True
            continue
        splits[split] = df
        speakers = set(df["speaker_id"].dropna().astype(str).str.strip()) - {""}
        filepaths = set(df["filepath"].dropna().astype(str).str.strip()) - {""}
        info[f"{split}_rows"] = len(df)
        info[f"{split}_speakers"] = len(speakers)
        info[f"{split}_unique_filepaths"] = len(filepaths)
        info[f"{split}_speaker_set"] = speakers
        info[f"{split}_filepath_set"] = filepaths

    pairs = [
        ("train", "val", "train_val_speaker_overlap"),
        ("train", "test", "train_test_speaker_overlap"),
        ("val", "test", "val_test_speaker_overlap"),
    ]
    for a, b, key in pairs:
        if f"{a}_speaker_set" in info and f"{b}_speaker_set" in info:
            overlap = info[f"{a}_speaker_set"] & info[f"{b}_speaker_set"]
            info[key] = len(overlap)
            rows.append({
                "check": key,
                "split_a": a,
                "split_b": b,
                "overlap_count": len(overlap),
                "severity": "high" if len(overlap) > 0 else "none",
                "sample_ids": ";".join(sorted(overlap)[:10]),
            })

    fp_pairs = [
        ("train", "val", "duplicate_filepath_train_val"),
        ("train", "test", "duplicate_filepath_train_test"),
        ("val", "test", "duplicate_filepath_val_test"),
    ]
    for a, b, key in fp_pairs:
        if f"{a}_filepath_set" in info and f"{b}_filepath_set" in info:
            overlap = info[f"{a}_filepath_set"] & info[f"{b}_filepath_set"]
            info[key] = len(overlap)
            rows.append({
                "check": key,
                "split_a": a,
                "split_b": b,
                "overlap_count": len(overlap),
                "severity": "high" if len(overlap) > 0 else "none",
                "sample_ids": ";".join(sorted(overlap)[:3]),
            })

    return rows, info


def enrich_duplicate_labels(
    manifest_path: Path, dup_fps: set[str], chunk_size: int = CHUNK_SIZE
) -> tuple[dict, dict]:
    """Second pass: label/attack sets for duplicated filepaths only."""
    label_by_fp: dict[str, set[str]] = defaultdict(set)
    attack_by_fp: dict[str, set[str]] = defaultdict(set)
    if not dup_fps or not manifest_path.is_file():
        return label_by_fp, attack_by_fp
    for chunk in iterate_manifest(
        manifest_path, usecols=["filepath", "label", "attack_type"], chunk_size=chunk_size
    ):
        fps = chunk["filepath"].fillna("").astype(str).str.strip()
        hit = fps.isin(dup_fps)
        if not hit.any():
            continue
        sub = chunk.loc[hit]
        for fp, lbl, atk in zip(
            sub["filepath"].astype(str).str.strip(),
            sub["label"].fillna("").astype(str).str.strip(),
            sub["attack_type"].fillna("").astype(str).str.strip(),
        ):
            label_by_fp[fp].add(lbl or "<missing>")
            attack_by_fp[fp].add(atk or "<missing>")
    return label_by_fp, attack_by_fp


def build_duplicate_report(
    agg: ChunkAggregator,
    manifest_path: Path | None = None,
    chunk_size: int = CHUNK_SIZE,
) -> list[dict]:
    rows = []
    dup_fps = {fp for fp, cnt in agg.filepath_counts.items() if cnt > 1}
    label_by_fp, attack_by_fp = {}, {}
    if manifest_path and dup_fps:
        label_by_fp, attack_by_fp = enrich_duplicate_labels(
            manifest_path, dup_fps, chunk_size=chunk_size
        )

    for fp, cnt in sorted(dup_fps, key=lambda x: -agg.filepath_counts[x])[:5000]:
        labels = sorted(label_by_fp.get(fp, []))
        attacks = sorted(attack_by_fp.get(fp, []))
        issue = "duplicate_filepath"
        if len(labels) > 1:
            issue = "duplicate_filepath_multi_label"
        elif len(attacks) > 1:
            issue = "duplicate_filepath_multi_attack"
        rows.append({
            "issue": issue,
            "filepath": fp,
            "count": agg.filepath_counts[fp],
            "labels": "|".join(labels),
            "attack_types": "|".join(attacks),
        })
    if agg.has_file_id:
        for fid, cnt in agg.file_id_counts.most_common(2000):
            if cnt <= 1:
                break
            rows.append({
                "issue": "duplicate_file_id",
                "filepath": "",
                "count": cnt,
                "labels": fid,
                "attack_types": "",
            })
    return rows


def stratified_audio_sample(
    path: Path,
    sample_size: int,
    repo_root: Path,
    chunk_size: int = CHUNK_SIZE,
) -> tuple[list[dict], int]:
    """Reservoir-style capped sample per (dataset, label, attack_type, domain) stratum."""
    if not path.is_file() or sample_size <= 0:
        return [], 0

    strata: dict[tuple, list[dict]] = defaultdict(list)
    strata_counts: Counter = Counter()
    max_per_stratum = max(5, sample_size // 40)

    cols = ["filepath", "dataset", "label", "attack_type", "domain"]
    header = pd.read_csv(path, nrows=0).columns.tolist()
    usecols = [c for c in cols if c in header]

    extra = [c for c in ("filename", "source", "speaker_id", "duration") if c in header]
    read_cols = list(dict.fromkeys(usecols + extra))
    group_cols = ["dataset", "label", "attack_type", "domain"]

    for chunk in iterate_manifest(path, usecols=read_cols, chunk_size=chunk_size):
        for c in group_cols:
            if c not in chunk.columns:
                chunk[c] = "<missing>"
            chunk[c] = chunk[c].fillna("").astype(str).str.strip().replace("", "<missing>")
        for key, grp in chunk.groupby(group_cols, sort=False):
            strata_counts[key] += len(grp)
            bucket = strata[key]
            take = min(max_per_stratum, len(grp))
            sampled = grp.sample(n=take, random_state=42) if len(grp) > take else grp
            if len(bucket) + len(sampled) <= max_per_stratum:
                bucket.extend(sampled.to_dict("records"))
            else:
                combined = bucket + sampled.to_dict("records")
                bucket.clear()
                bucket.extend(
                    pd.DataFrame(combined).sample(
                        n=max_per_stratum, random_state=42
                    ).to_dict("records")
                )

    flat = [r for bucket in strata.values() for r in bucket]
    if len(flat) < sample_size:
        need = sample_size - len(flat)
        seen_fps = {_safe_str(r.get("filepath")) for r in flat}
        for chunk in iterate_manifest(path, usecols=read_cols, chunk_size=chunk_size):
            if need <= 0:
                break
            extra = chunk.sample(n=min(need, len(chunk)), random_state=43)
            for d in extra.to_dict("records"):
                fp = _safe_str(d.get("filepath"))
                if fp and fp not in seen_fps:
                    flat.append(d)
                    seen_fps.add(fp)
                    need -= 1
    if len(flat) > sample_size:
        rng = np.random.default_rng(42)
        idx = rng.choice(len(flat), size=sample_size, replace=False)
        flat = [flat[i] for i in idx]

    missing_rows = []
    missing_count = 0
    for row in flat:
        fp = _safe_str(row.get("filepath"))
        candidates = [Path(fp), repo_root / fp] if fp else []
        exists = any(p.is_file() for p in candidates)
        if not exists:
            missing_count += 1
        missing_rows.append({
            "filepath": fp,
            "dataset": _safe_str(row.get("dataset")),
            "label": _safe_str(row.get("label")),
            "attack_type": _safe_str(row.get("attack_type")),
            "domain": _safe_str(row.get("domain")),
            "file_exists": exists,
            "checked_path": str(candidates[0]) if candidates else "",
        })
    return missing_rows, missing_count


def build_manual_review_sample(
    manifest_dir: Path,
    per_group: int,
    repo_root: Path,
    chunk_size: int = CHUNK_SIZE,
) -> pd.DataFrame:
    """Sample rows from unified manifest for manual review."""
    path = manifest_dir / MANIFEST_NAMES["unified"]
    if not path.is_file():
        return pd.DataFrame()

    collected: dict[tuple, list[dict]] = defaultdict(list)
    out_cols = [
        "filepath", "filename", "dataset", "label", "attack_type",
        "domain", "source", "speaker_id", "duration", "split",
    ]

    for chunk in iterate_manifest(path, chunk_size=chunk_size):
        for field, value in SAMPLE_GROUPS:
            if field not in chunk.columns:
                continue
            key = (field, value)
            if len(collected[key]) >= per_group:
                continue
            mask = chunk[field].fillna("").astype(str).str.strip().str.lower() == str(value).lower()
            need = per_group - len(collected[key])
            for d in chunk.loc[mask].head(need).to_dict("records"):
                collected[key].append({c: d.get(c, "") for c in out_cols if c != "split"})
        if "domain" in chunk.columns:
            for dom_val in chunk["domain"].fillna("").astype(str).str.strip().unique():
                if not dom_val:
                    continue
                dkey = ("domain", dom_val)
                if len(collected[dkey]) >= per_group:
                    continue
                mask = chunk["domain"].fillna("").astype(str).str.strip() == dom_val
                need = per_group - len(collected[dkey])
                for d in chunk.loc[mask].head(need).to_dict("records"):
                    collected[dkey].append({c: d.get(c, "") for c in out_cols if c != "split"})

    # add split assignment from train/val/test
    fp_split = {}
    for split in ("train", "val", "test"):
        sp = manifest_dir / MANIFEST_NAMES[split]
        df = load_split_columns(sp, ["filepath"])
        if df is None:
            continue
        for fp in df["filepath"].dropna().astype(str):
            fp_split[fp.strip()] = split

    rows = []
    for bucket in collected.values():
        for r in bucket:
            fp = _safe_str(r.get("filepath"))
            r["split"] = fp_split.get(fp, "unified_only")
            rows.append(r)

    return pd.DataFrame(rows, columns=out_cols)


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def build_balance_summary(unified: ChunkAggregator, splits: dict[str, ChunkAggregator]) -> list[dict]:
    rows = []
    rows.append({"metric": "total_rows", "value": unified.total_rows, "notes": "unified_manifest"})
    rows.append({"metric": "bonafide_pct", "value": unified.summary()["bonafide_pct"], "notes": ""})
    rows.append({"metric": "spoof_pct", "value": unified.summary()["spoof_pct"], "notes": ""})
    if unified.dataset:
        top_ds, top_n = unified.dataset.most_common(1)[0]
        rows.append({
            "metric": "top_dataset",
            "value": top_ds,
            "notes": f"{top_n} rows ({round(100*top_n/unified.total_rows,2)}%)",
        })
    if unified.domain:
        top_dom, top_n = unified.domain.most_common(1)[0]
        rows.append({
            "metric": "top_domain",
            "value": top_dom,
            "notes": f"{top_n} rows ({round(100*top_n/unified.total_rows,2)}%)",
        })
    pa_replay = unified.dataset.get("PA", 0) + unified.attack_type.get("replay", 0)
    rows.append({
        "metric": "pa_rows",
        "value": unified.dataset.get("PA", 0),
        "notes": f"replay_attack_rows={unified.attack_type.get('replay', 0)}",
    })
    rows.append({
        "metric": "studio_domain_rows",
        "value": unified.domain.get("studio", 0),
        "notes": f"pct={round(100*unified.domain.get('studio',0)/max(1,unified.total_rows),2)}",
    })
    rows.append({
        "metric": "realworld_rows",
        "value": unified.dataset.get("RealWorld", 0),
        "notes": "non-ASVspoof real-world YouTube clips",
    })
    for name, agg in splits.items():
        if agg:
            rows.append({
                "metric": f"{name}_rows",
                "value": agg.total_rows,
                "notes": f"bonafide_pct={agg.summary()['bonafide_pct']}",
            })
    return rows


def build_file_level_rows(agg: ChunkAggregator) -> list[dict]:
    """Row/chunk vs unique-file counts per dimension value."""
    if not agg.file_id_col or agg.unique_file_count == 0:
        return []
    total_rows = agg.total_rows or 1
    total_files = agg.unique_file_count or 1
    rows: list[dict] = []
    for dim_name, col, attr in FILE_BALANCE_DIMENSIONS:
        counter = getattr(agg, col, None)
        if not isinstance(counter, Counter):
            continue
        files_map: dict[str, set[str]] = getattr(agg, attr)
        for val, row_count in counter.most_common():
            ufiles = len(files_map.get(val, set()))
            rows.append({
                "scope": agg.name,
                "dimension": dim_name,
                "value": val,
                "row_count": row_count,
                "unique_file_count": ufiles,
                "row_pct": round(100.0 * row_count / total_rows, 4),
                "file_pct": round(100.0 * ufiles / total_files, 4),
                "avg_rows_per_file": round(row_count / max(1, ufiles), 4),
            })
    return rows


def assign_chunk_weighting_bias_risk(rows: list[dict]) -> list[dict]:
    """Flag groups where chunk rows per file diverge strongly within a dimension."""
    by_dim: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_dim[r["dimension"]].append(r)

    out: list[dict] = []
    for dim, group in by_dim.items():
        eligible = [g for g in group if g.get("unique_file_count", 0) > 0]
        avgs = [g["avg_rows_per_file"] for g in eligible]
        if not avgs:
            for g in group:
                g["chunk_weighting_bias_risk"] = "n/a"
                out.append(g)
            continue
        min_avg = min(avgs)
        max_avg = max(avgs)
        ratio = max_avg / max(min_avg, 1e-9)
        mean_avg = sum(avgs) / len(avgs)
        dim_severity = "high" if ratio > 3.0 else "medium" if ratio > 1.75 else "low"
        for g in group:
            rpf = g.get("avg_rows_per_file", 0.0)
            if g.get("unique_file_count", 0) == 0:
                g["chunk_weighting_bias_risk"] = "n/a"
            elif rpf >= mean_avg * 2.5 and ratio > 2.0:
                g["chunk_weighting_bias_risk"] = "high"
            elif rpf >= mean_avg * 1.75 and ratio > 1.5:
                g["chunk_weighting_bias_risk"] = "medium"
            elif dim_severity in ("high", "medium"):
                g["chunk_weighting_bias_risk"] = dim_severity
            else:
                g["chunk_weighting_bias_risk"] = "low"
            out.append(g)
    return out


def build_chunk_vs_file_comparison(unified: ChunkAggregator) -> list[dict]:
    rows = build_file_level_rows(unified)
    return assign_chunk_weighting_bias_risk(rows)


def summarize_chunk_weighting_bias(comparison: list[dict]) -> dict[str, Any]:
    """Overall severity and top overweighted group."""
    if not comparison:
        return {
            "severity": "n/a",
            "file_id_column": "",
            "total_unique_files": 0,
            "avg_rows_per_file": 0.0,
            "top_group": "",
            "top_avg_rows_per_file": 0.0,
        }
    high = [r for r in comparison if r.get("chunk_weighting_bias_risk") == "high"]
    medium = [r for r in comparison if r.get("chunk_weighting_bias_risk") == "medium"]
    severity = "high" if high else "medium" if medium else "low"
    top = max(comparison, key=lambda r: (r.get("avg_rows_per_file", 0), r.get("row_count", 0)))
    return {
        "severity": severity,
        "top_group": f"{top.get('dimension')}={top.get('value')}",
        "top_avg_rows_per_file": top.get("avg_rows_per_file", 0),
        "high_risk_groups": len(high),
        "medium_risk_groups": len(medium),
    }


def assess_risks(
    unified: ChunkAggregator | None,
    split_info: dict,
    dup_count: int,
    conflict_count: int,
    missing_audio: int,
    audio_checked: int,
    file_balance: dict[str, Any] | None = None,
) -> list[dict]:
    risks = []

    def add(risk_id, title, severity, evidence, impact, mitigation):
        risks.append({
            "risk_id": risk_id,
            "title": title,
            "severity": severity,
            "evidence": evidence,
            "impact": impact,
            "mitigation": mitigation,
        })

    if unified is None:
        add("manifest_missing", "Training manifest missing", "high",
            "unified_manifest.csv not found", "Cannot verify training data",
            "Restore manifests from backup before Phase 7C")
        return risks

    spoof_pct = unified.summary()["spoof_pct"]
    sev_imb = "high" if spoof_pct > 75 else "medium" if spoof_pct > 65 else "low"
    add("class_imbalance", "Class imbalance (spoof vs bonafide)", sev_imb,
        f"Spoof {spoof_pct}% vs bonafide {unified.summary()['bonafide_pct']}% ({unified.total_rows:,} rows)",
        "Model may bias toward FAKE; bonafide FPR risk on deployment",
        "Balanced sampling or class weights in Phase 7C; add local bonafide Urdu/phone data")

    replay_pct = 100 * unified.attack_type.get("replay", 0) / max(1, unified.total_rows)
    pa_pct = 100 * unified.dataset.get("PA", 0) / max(1, unified.total_rows)
    sev_atk = "high" if replay_pct > 40 or pa_pct > 45 else "medium"
    add("attack_imbalance", "Attack / PA-replay dominance", sev_atk,
        f"replay={replay_pct:.1f}%, PA dataset={pa_pct:.1f}%",
        "Strong replay/PA cues; weak generalization to synthesis-only or non-PA replay",
        "Collect human/AI replay, mixer, WhatsApp chains; balance attack types in 7C")

    studio_pct = 100 * unified.domain.get("studio", 0) / max(1, unified.total_rows)
    sev_dom = "high" if studio_pct > 90 else "medium"
    add("domain_imbalance", "Studio domain dominance", sev_dom,
        f"studio={studio_pct:.1f}%; social={unified.domain.get('social',0)}; read_speech={unified.domain.get('read_speech',0)}",
        "Model may overfit clean studio conditions; phone/social/replay mismatch in 7A",
        "Collect phone, WhatsApp, room noise, local Pakistani recordings")

    urdu_keys = [k for k in unified.domain if "urdu" in k.lower() or "pakistan" in k.lower()]
    phone_rows = unified.domain.get("phone", 0)
    sev_lang = "high" if not urdu_keys and phone_rows == 0 else "medium"
    add("language_mismatch", "Urdu/Pakistani / phone domain gap", sev_lang,
        f"Urdu-tagged domains={urdu_keys or 'none'}; phone domain rows={phone_rows}",
        "Phase 7A Urdu clean human borderline / replay confusion",
        "50–100 clean Urdu/Pakistani human + spoof conditions before fine-tuning")

    sp_overlap = split_info.get("train_val_speaker_overlap", 0) + split_info.get("train_test_speaker_overlap", 0)
    sev_sp = "high" if sp_overlap > 0 else "low"
    add("speaker_leakage", "Speaker leakage across splits", sev_sp,
        f"train∩val={split_info.get('train_val_speaker_overlap', 'n/a')}, "
        f"train∩test={split_info.get('train_test_speaker_overlap', 'n/a')}",
        "Inflated eval metrics; poor speaker-independent generalization",
        "Re-split if overlap > 0; keep speaker families grouped in 7C")

    sev_dup = "high" if dup_count > 100 else "medium" if dup_count > 0 else "low"
    add("file_duplicate", "Duplicate file paths or IDs", sev_dup,
        f"duplicate_filepath_entries={dup_count}",
        "Train/val leakage or overweighted samples",
        "Deduplicate manifest; audit top duplicate_file_report.csv rows")

    sev_lbl = "high" if conflict_count > 0 else "low"
    add("label_conflict", "Label vs attack_type conflicts", sev_lbl,
        f"conflict_rows={conflict_count}, missing_label={unified.missing_label}",
        "Noisy supervision for attack-aware heads",
        "Fix label mapping; exclude conflict rows from 7C training")

    miss_pct = 100 * missing_audio / max(1, audio_checked)
    sev_miss = "high" if miss_pct > 5 else "medium" if miss_pct > 1 else "low"
    add("missing_audio", "Missing audio files (sampled)", sev_miss,
        f"{missing_audio}/{audio_checked} missing in stratified sample ({miss_pct:.1f}%)",
        "Broken training indices; HDF5/manifest misalignment",
        "Repair paths or re-extract features for missing files")

    add("product_mismatch", "Product label schema mismatch", "high",
        "Training uses label+attack_type; Phase 7 product uses origin+manipulation",
        "Fine-tuning only REAL/FAKE will not fix 7A origin vs manipulation confusion",
        "Train/calibrate separate origin and manipulation outputs in 7C")

    if file_balance:
        fb_sev = file_balance.get("severity", "n/a")
        if fb_sev == "n/a" and not file_balance.get("file_id_column"):
            add(
                "chunk_weighting_bias",
                "Chunk weighting bias (file-level audit unavailable)",
                "medium",
                "No filepath/file_id/utterance_id column detected in manifest",
                "Cannot verify whether some classes are overweighted by more chunks per file",
                "Add a stable file identifier column to manifests before Phase 7C training design",
            )
        elif fb_sev in ("high", "medium", "low"):
            add(
                "chunk_weighting_bias",
                "Chunk weighting bias (rows vs unique files)",
                fb_sev,
                file_balance.get(
                    "evidence",
                    f"top_group={file_balance.get('top_group')}; "
                    f"avg_rows_per_file={file_balance.get('avg_rows_per_file')}; "
                    f"max_group_avg={file_balance.get('top_avg_rows_per_file')}",
                ),
                "Model may overlearn conditions with more chunks per file (long clips or heavy chunking)",
                "Use file-balanced or speaker-balanced sampling in Phase 7C; cap chunks per file if needed",
            )

    return risks


def write_risk_markdown(risks: list[dict], path: Path) -> None:
    lines = ["# Dataset Risk Assessment — Phase 7C0", ""]
    for r in risks:
        lines += [
            f"## {r['risk_id']}: {r['title']}",
            "",
            f"- **Severity:** {r['severity']}",
            f"- **Evidence:** {r['evidence']}",
            f"- **Impact:** {r['impact']}",
            f"- **Mitigation:** {r['mitigation']}",
            "",
        ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_recommendations(path: Path) -> None:
    text = """# Phase 7C Data Collection Recommendations

Based on **Phase 7C0 current-dataset audit** + **Phase 7A product analysis** + **Phase 7B gap analysis**.

---

## 1. What the old dataset already covers well

- Large-scale **ASVspoof LA / DF / PA** coverage (synthesis, conversion, replay attacks).
- **Studio** read/speech and clean-channel bonafide/spoof pairs.
- **~1.89M** chunked samples with aligned **log-mel** + **12-D environmental** features.
- Strong **spoof diversity** for academic logical-access, deepfake, and physical-access replay.

---

## 2. What the old dataset does not cover well

- **Urdu / Pakistani** speakers (not represented as a labeled domain).
- **Phone-recorded** and **room/noisy** capture (minimal vs studio).
- **WhatsApp / social compression** pipelines (very few social-domain rows vs studio).
- **Human replay** as product-level manipulation (PA replay ≠ phone human replay).
- **Mixer / equalizer** processed human chains.
- **Partial AI insertion** with segment timestamps.
- **Forensic origin + manipulation labels** (training is label + attack_type only).

---

## 3. Minimum data to collect before Phase 7C

| Category | Minimum count | Purpose | Label type |
|----------|---------------|---------|------------|
| Clean human Urdu/Pakistani | 50–100 | Reduce bonafide borderline on local speech | origin: human_likely; manipulation: clean_original |
| Direct AI Urdu/English | 50–100 | File + segment AI detection | origin: ai_likely; manipulation: clean_original |
| Human replay | 30–50 | Manipulation without implying AI origin | human_likely + replayed_or_re_recorded |
| AI replay | 30–50 | AI content through speaker/phone | ai_likely + replayed_or_re_recorded |
| Mixer/channel processed human | 30–50 | T2-style manipulation sensitivity | human_likely + channel_processed |
| Mixer/channel processed AI | 20–30 | Processed AI chains | ai_likely + channel_processed |
| WhatsApp compressed human | 30–50 | Platform robustness | human_likely + platform_compressed |
| WhatsApp compressed AI | 30–50 | Compressed AI detection | ai_likely + platform_compressed |
| Edited/spliced human | 30–50 | Editing manipulation class | human_likely + edited_or_spliced |
| Partial AI insertion (with timestamps) | 20–40 | Segment-level evaluation (T4/T5) | mixed_or_partial_ai + segment labels |
| Phone-recorded / noisy room | 30–50 | Domain gap vs studio | human_likely + noisy_low_quality / phone capture |

---

## 4. Recommended split strategy

- Keep **Phase 7A T1–T5 (25 files)** as **controlled holdout** — never merge into main training.
- New Phase 7C corpus: explicit **train / val / test** with **speaker-independent** splits where possible.
- Group **paired variants** (e.g. `human_001_clean`, `human_001_replay`, `human_001_whatsapp`) in the **same split**.
- Hold out at least one full **condition family** per manipulation type for sanity checks.

---

## 4b. Chunk vs file / utterance balance (sampler design)

The unified manifest is **chunk-level** (multiple rows per source file). Phase 7C0 audit reports both row counts and **unique-file** counts.

- **Balance by speaker/file first**, then by chunks — do not let one long file or heavily chunked domain dominate gradients.
- Keep **paired variants** in the same split (see above).
- Use a **file-balanced sampler** or **cap chunks per file** when `avg_rows_per_file` differs widely across label, attack, dataset, or domain (see `chunk_vs_file_balance_comparison.csv`).
- Review `file_level_balance_summary.csv` before finalizing batch composition.

---

## 5. Training warning

- **Do not** fine-tune on REAL/FAKE alone.
- Calibrate or train **separate origin and manipulation** outputs aligned with Phase 7D report layer.
- Keep **HybridResNetEnvironmental** baseline checkpoint for before/after comparison.
- Start Phase 7C fine-tuning only after this audit is reviewed and new local data is collected and validated (Phase 7B-style labels).

---

## 6. Rule

**No Phase 7C fine-tuning until:**

1. `CURRENT_TRAINING_DATASET_AUDIT.md` reviewed  
2. `dataset_risk_assessment.md` accepted  
3. Minimum collection table above progressed  
4. Phase 7A holdout remains untouched for evaluation
"""
    path.write_text(text, encoding="utf-8")


def write_main_audit_md(
    path: Path,
    manifest_status: dict[str, bool],
    unified: ChunkAggregator | None,
    splits: dict[str, ChunkAggregator | None],
    split_info: dict,
    missing_audio_rows: list[dict],
    dup_rows: list[dict],
    risks: list[dict],
    hdf5_note: str,
    file_balance: dict[str, Any] | None = None,
    chunk_comparison: list[dict] | None = None,
) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Current Training Dataset Audit — Phase 7C0",
        "",
        f"**Generated:** {ts}",
        "",
        "**Model:** HybridResNetEnvironmental (`hybrid_resnet_environmental_best.pth`)",
        "",
        "**Scope:** Audit only — no training, no fine-tuning, no Phase 6/7A/7B changes.",
        "",
        "---",
        "",
        "## 1. Executive summary",
        "",
    ]

    if unified:
        top_ds = unified.dataset.most_common(3)
        top_dom = unified.domain.most_common(3)
        lines += [
            f"- **Unified samples:** {unified.total_rows:,} rows; **speakers:** {len(unified.speakers):,}",
            f"- **Bonafide / spoof:** {unified.summary()['bonafide_pct']:.1f}% / {unified.summary()['spoof_pct']:.1f}%",
            f"- **Dominant datasets:** {', '.join(f'{k} ({v:,})' for k, v in top_ds)}",
            f"- **Dominant domains:** {', '.join(f'{k} ({v:,})' for k, v in top_dom)}",
            "- **Main imbalance risks:** spoof-heavy (~83%); PA + replay dominate; studio domain >96% of rows.",
            "- **Main domain gaps:** Urdu/Pakistani, phone capture, WhatsApp/social compression underrepresented vs Phase 7A needs.",
            "",
        ]
    else:
        lines += ["- **Unified manifest not found** — see manifest status below.", ""]

    lines += ["## 2. Manifest files found/missing", "", "| File | Status |", "|------|--------|"]
    for key, fname in MANIFEST_NAMES.items():
        ok = manifest_status.get(key, False)
        lines.append(f"| `{fname}` | {'found' if ok else '**missing**'} |")
    lines += ["", "---", "", "## 3. Full dataset distribution", ""]
    if unified:
        for title, counter, col in [
            ("### Labels", unified.label, "label"),
            ("### Attack types", unified.attack_type, "attack_type"),
            ("### Datasets", unified.dataset, "dataset"),
            ("### Domains", unified.domain, "domain"),
        ]:
            lines.append(title)
            lines.append("")
            for k, v in counter.most_common():
                pct = 100 * v / unified.total_rows
                lines.append(f"- **{k}:** {v:,} ({pct:.2f}%)")
            lines.append("")

    lines += [
        "## 4. Chunk-level vs file-level balance",
        "",
        "Row counts in sections 3–4 are **chunk/row-level** (one manifest row per training chunk). "
        "Because the unified manifest may contain **multiple rows per source file**, file-level balance can differ from row-level balance.",
        "",
    ]
    if file_balance and file_balance.get("file_id_column"):
        lines += [
            f"- **File identity column:** `{file_balance['file_id_column']}`",
            f"- **Unique files (unified):** {file_balance.get('total_unique_files', 0):,}",
            f"- **Avg rows per file:** {file_balance.get('avg_rows_per_file', 0)}",
            f"- **Chunk weighting bias severity:** {file_balance.get('severity', 'n/a')}",
            f"- **Highest avg chunks/file:** {file_balance.get('top_group', 'n/a')} "
            f"({file_balance.get('top_avg_rows_per_file', 0)} rows/file)",
            "",
        ]
        if float(file_balance.get("avg_rows_per_file", 0) or 0) <= 1.01:
            lines += [
                "- **Current corpus:** Each manifest row maps to a **distinct** `filepath` "
                "(~1.0 rows/file). Row-% and file-% are therefore aligned for this dataset; "
                "re-run this comparison after adding manifests with multiple chunks per source file.",
                "",
            ]
        lines += [
            "**Interpretation:** If some labels, attack types, datasets, or domains have much higher "
            "`avg_rows_per_file`, training may overweight those conditions unless sampling is file-balanced.",
            "",
            "**Phase 7C sampler:** Avoid over-weighting long files or heavily chunked domains; prefer "
            "file-balanced or speaker-balanced batching (see `chunk_vs_file_balance_comparison.csv`).",
            "",
        ]
        if chunk_comparison:
            high = [r for r in chunk_comparison if r.get("chunk_weighting_bias_risk") == "high"][:8]
            if high:
                lines.append("**Groups flagged high chunk-weighting bias risk:**")
                lines.append("")
                for r in high:
                    lines.append(
                        f"- `{r['dimension']}={r['value']}`: {r['row_count']:,} rows / "
                        f"{r['unique_file_count']:,} files (avg {r['avg_rows_per_file']} rows/file)"
                    )
                lines.append("")
        lines += [
            "CSV outputs: `file_level_balance_summary.csv`, `file_level_attack_distribution.csv`, "
            "`file_level_domain_distribution.csv`, `chunk_vs_file_balance_comparison.csv`.",
            "",
        ]
    else:
        lines += [
            "- **File-level audit could not be performed** — no filepath / file_id / utterance_id column found.",
            "",
        ]

    lines += ["## 5. Train/val/test split distribution", ""]
    for split_name in ("train", "val", "test"):
        agg = splits.get(split_name)
        if not agg:
            lines.append(f"- **{split_name}:** manifest missing")
            continue
        s = agg.summary()
        lines.append(
            f"- **{split_name}:** {s['total_rows']:,} rows; {s['unique_speakers']:,} speakers; "
            f"bonafide {s['bonafide_pct']:.1f}% / spoof {s['spoof_pct']:.1f}%"
        )
    lines += ["", "See `split_balance_summary.csv` for detail.", ""]

    lines += ["## 6. Speaker independence check", ""]
    lines.append(
        f"- train ∩ val speakers: **{split_info.get('train_val_speaker_overlap', 'n/a')}**"
    )
    lines.append(
        f"- train ∩ test speakers: **{split_info.get('train_test_speaker_overlap', 'n/a')}**"
    )
    lines.append(
        f"- val ∩ test speakers: **{split_info.get('val_test_speaker_overlap', 'n/a')}**"
    )
    lines.append(
        f"- Duplicate filepaths across splits: train/val={split_info.get('duplicate_filepath_train_val', 'n/a')}, "
        f"train/test={split_info.get('duplicate_filepath_train_test', 'n/a')}"
    )
    lines.append("")
    lines.append("Full matrix: `speaker_split_integrity.csv`")
    lines.append("")

    lines += ["## 7. Duration analysis", ""]
    if unified and unified.duration_n:
        ds = unified.duration_stats()
        pct_dur = 100 * unified.duration_n / max(1, unified.total_rows)
        lines += [
            f"- Rows with duration value: {ds.get('rows_with_duration', 0):,} "
            f"({pct_dur:.1f}% of unified; primarily **RealWorld** clips)",
            f"- Mean / median: {ds.get('mean_duration_sec')} / {ds.get('median_duration_sec')} sec",
            f"- Min / max: {ds.get('min_duration_sec')} / {ds.get('max_duration_sec')} sec",
            "- ASVspoof LA/DF/PA rows typically have **empty** duration in manifest (clip-length fixed in feature pipeline).",
            "",
            "Buckets: `duration_distribution.csv`",
            "",
        ]
    else:
        lines += ["- Duration column sparse or missing in manifest.", ""]

    lines += ["## 8. Missing audio check", ""]
    miss = sum(1 for r in missing_audio_rows if not r.get("file_exists"))
    lines += [
        f"- Stratified sample checked: **{len(missing_audio_rows)}** files",
        f"- Missing on disk: **{miss}**",
        "",
        "Detail: `missing_audio_report.csv`",
        "",
    ]

    lines += ["## 9. Duplicate / leakage check", ""]
    lines += [f"- Duplicate filepath reports: **{len(dup_rows)}** (see `duplicate_file_report.csv`)", ""]

    lines += ["## 10. Label conflict check", ""]
    if unified:
        lines += [f"- Conflict rows captured: **{len(unified.conflicts)}**", "", "Detail: `label_conflict_report.csv`", ""]
    lines += ["## 11. Feature HDF5 summary", "", hdf5_note, ""]
    lines += ["## 12. Phase 7 risks", ""]
    for r in risks:
        if r["severity"] in ("high", "medium"):
            lines.append(f"- **{r['title']}** ({r['severity']}): {r['evidence']}")
    lines += [
        "",
        "## 13. What this means for Phase 7C",
        "",
        "- **Do not fine-tune blindly** on the legacy unified corpus without addressing imbalance and domain gaps.",
        "- **Collect controlled forensic labels** (origin + manipulation) per Phase 7B schema.",
        "- **Balance local Urdu/phone/social/replay data** before training.",
        "- **Phase 7A T1–T5 (25 files)** remain **holdout**, not training data.",
        "",
        "See also: `dataset_risk_assessment.md`, `phase7c_data_collection_recommendations.md`.",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def print_terminal_summary(
    manifest_status: dict,
    unified: ChunkAggregator | None,
    splits: dict,
    split_info: dict,
    dup_rows: list,
    conflicts: int,
    missing_audio: int,
    audio_n: int,
    hdf5_found: list[str],
    risks: list[dict],
    file_balance: dict[str, Any] | None = None,
) -> None:
    print("\n" + "=" * 72)
    print("PHASE 7C0 — CURRENT TRAINING DATASET AUDIT SUMMARY")
    print("=" * 72)
    print("Manifest files:")
    for k, ok in manifest_status.items():
        print(f"  {MANIFEST_NAMES[k]}: {'FOUND' if ok else 'MISSING'}")
    if unified:
        print(f"Unified rows: {unified.total_rows:,}")
        for sn in ("train", "val", "test"):
            a = splits.get(sn)
            print(f"  {sn}: {a.total_rows:,}" if a else f"  {sn}: MISSING")
        print(f"Bonafide/spoof: {unified.summary()['bonafide_pct']:.1f}% / {unified.summary()['spoof_pct']:.1f}%")
        print("Attack types:", dict(unified.attack_type.most_common()))
        if unified.dataset:
            print("Top datasets:", unified.dataset.most_common(3))
        if unified.domain:
            print("Top domains:", unified.domain.most_common(3))
    print(f"Speaker overlap train∩val: {split_info.get('train_val_speaker_overlap', 'n/a')}")
    print(f"Speaker overlap train∩test: {split_info.get('train_test_speaker_overlap', 'n/a')}")
    print(f"Missing audio (sample): {missing_audio}/{audio_n}")
    print(f"Duplicate filepath entries: {len(dup_rows)}")
    print(f"Label conflicts: {conflicts}")
    print(f"HDF5 found: {', '.join(hdf5_found) or 'none'}")
    high = [r["title"] for r in risks if r["severity"] == "high"]
    print(f"Major risks ({len(high)}): {', '.join(high[:5])}")
    print("")
    print("File-level balance:")
    if file_balance and file_balance.get("file_id_column"):
        print(f"  File identity column: {file_balance['file_id_column']}")
        print(f"  Total unique files (unified): {file_balance.get('total_unique_files', 0):,}")
        print(f"  Avg rows per file: {file_balance.get('avg_rows_per_file', 0)}")
        print(f"  Top avg rows/file: {file_balance.get('top_group', 'n/a')} "
              f"({file_balance.get('top_avg_rows_per_file', 0)})")
        print(f"  Chunk weighting bias severity: {file_balance.get('severity', 'n/a')}")
    else:
        print("  File-level audit unavailable (no file identity column)")
    print("Recommended next action: Review audit markdown + collect Phase 7C local data before fine-tuning.")
    print("=" * 72)


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit current hybrid training dataset (Phase 7C0)")
    parser.add_argument("--manifest_dir", type=str, default="data/manifests")
    parser.add_argument("--output_dir", type=str, default="reports/phase7_current_dataset_audit")
    parser.add_argument("--sample_per_group", type=int, default=20)
    parser.add_argument("--check_audio_exists_sample", type=int, default=5000)
    parser.add_argument("--chunk_size", type=int, default=CHUNK_SIZE)
    args = parser.parse_args()

    manifest_dir = (_REPO_ROOT / args.manifest_dir).resolve()
    chunk_size = args.chunk_size
    output_dir = (_REPO_ROOT / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print("Phase 7C0 — Current Training Dataset Audit")
    print("=" * 72)

    manifest_status = {
        key: (manifest_dir / fname).is_file() for key, fname in MANIFEST_NAMES.items()
    }

    unified = analyze_manifest(
        manifest_dir / MANIFEST_NAMES["unified"], "unified", chunk_size=chunk_size
    )
    splits: dict[str, ChunkAggregator | None] = {}
    for split in ("train", "val", "test"):
        splits[split] = analyze_manifest(
            manifest_dir / MANIFEST_NAMES[split], split, chunk_size=chunk_size
        )

    integrity_rows, split_info = speaker_split_integrity(manifest_dir)
    write_csv(output_dir / "speaker_split_integrity.csv", integrity_rows)

    if unified:
        write_csv(output_dir / "dataset_balance_summary.csv", build_balance_summary(unified, splits))
        write_csv(output_dir / "attack_type_distribution.csv", _counter_to_rows(unified.attack_type, "attack_type"))
        write_csv(output_dir / "domain_distribution.csv", _counter_to_rows(unified.domain, "domain"))

        dur_rows = [
            {"bucket": k, "count": v, "pct": round(100 * v / max(1, sum(unified.duration_buckets.values())), 4)}
            for k, v in unified.duration_buckets.most_common()
        ]
        write_csv(output_dir / "duration_distribution.csv", dur_rows)

        dup_rows = build_duplicate_report(
            unified, manifest_dir / MANIFEST_NAMES["unified"], chunk_size=chunk_size
        )
        write_csv(output_dir / "duplicate_file_report.csv", dup_rows)

        conflict_rows = unified.conflicts[:100_000]
        write_csv(output_dir / "label_conflict_report.csv", conflict_rows)

    else:
        dup_rows = []
        conflict_rows = []

    split_rows = []
    for split_name, agg in splits.items():
        if not agg:
            continue
        for metric, counter in (
            ("label", agg.label),
            ("attack_type", agg.attack_type),
            ("dataset", agg.dataset),
            ("domain", agg.domain),
        ):
            for row in _counter_to_rows(counter, metric, scope=split_name):
                s = agg.summary()
                row["split"] = split_name
                row["split_rows"] = s["total_rows"]
                row["split_speakers"] = s["unique_speakers"]
                split_rows.append(row)
    write_csv(output_dir / "split_balance_summary.csv", split_rows)

    missing_rows, missing_count = stratified_audio_sample(
        manifest_dir / MANIFEST_NAMES["unified"],
        args.check_audio_exists_sample,
        _REPO_ROOT,
        chunk_size=chunk_size,
    )
    write_csv(output_dir / "missing_audio_report.csv", missing_rows)

    review_df = build_manual_review_sample(
        manifest_dir, args.sample_per_group, _REPO_ROOT, chunk_size=chunk_size
    )
    review_path = output_dir / "sampled_manifest_for_manual_review.csv"
    review_df.to_csv(review_path, index=False)

    hdf5_audit = output_dir / "feature_hdf5_audit.md"
    hdf5_note = (
        f"See `{_repo_rel(hdf5_audit)}` and `feature_shape_summary.csv` "
        "(run `audit_hdf5_features.py` if not yet generated)."
    )
    if hdf5_audit.is_file():
        hdf5_note = "HDF5 audit completed — see `feature_hdf5_audit.md` and `feature_shape_summary.csv`."

    file_level_summary: list[dict] = []
    chunk_comparison: list[dict] = []
    file_balance: dict[str, Any] = {}

    if unified:
        for agg in [unified] + [splits[s] for s in ("train", "val", "test") if splits.get(s)]:
            file_level_summary.extend(build_file_level_rows(agg))
        chunk_comparison = build_chunk_vs_file_comparison(unified)
        bias_summary = summarize_chunk_weighting_bias(chunk_comparison)
        file_balance = {
            "file_id_column": unified.file_id_col or "",
            "total_unique_files": unified.unique_file_count,
            "avg_rows_per_file": unified.avg_rows_per_file(),
            "severity": bias_summary["severity"],
            "top_group": bias_summary["top_group"],
            "top_avg_rows_per_file": bias_summary["top_avg_rows_per_file"],
            "evidence": (
                f"unique_files={unified.unique_file_count:,}; "
                f"avg_rows_per_file={unified.avg_rows_per_file()}; "
                f"highest={bias_summary['top_group']} @ {bias_summary['top_avg_rows_per_file']} rows/file; "
                f"high_risk_groups={bias_summary.get('high_risk_groups', 0)}; "
                f"medium_risk_groups={bias_summary.get('medium_risk_groups', 0)}"
            ),
        }
        write_csv(output_dir / "file_level_balance_summary.csv", file_level_summary)
        write_csv(
            output_dir / "file_level_attack_distribution.csv",
            [r for r in file_level_summary if r.get("dimension") == "attack_type"],
        )
        write_csv(
            output_dir / "file_level_domain_distribution.csv",
            [r for r in file_level_summary if r.get("dimension") == "domain"],
        )
        write_csv(output_dir / "chunk_vs_file_balance_comparison.csv", chunk_comparison)

    risks = assess_risks(
        unified,
        split_info,
        len(dup_rows),
        len(conflict_rows) if unified else 0,
        missing_count,
        len(missing_rows),
        file_balance=file_balance or None,
    )
    write_risk_markdown(risks, output_dir / "dataset_risk_assessment.md")
    write_recommendations(output_dir / "phase7c_data_collection_recommendations.md")
    write_main_audit_md(
        output_dir / "CURRENT_TRAINING_DATASET_AUDIT.md",
        manifest_status,
        unified,
        splits,
        split_info,
        missing_rows,
        dup_rows,
        risks,
        hdf5_note,
        file_balance=file_balance or None,
        chunk_comparison=chunk_comparison,
    )

    readme = output_dir / "README.md"
    readme.write_text(
        "# Phase 7C0 — Current Training Dataset Audit\n\n"
        "Audit of manifests and HDF5 features used to train **HybridResNetEnvironmental**.\n\n"
        "## Main documents\n\n"
        "- [CURRENT_TRAINING_DATASET_AUDIT.md](CURRENT_TRAINING_DATASET_AUDIT.md)\n"
        "- [dataset_risk_assessment.md](dataset_risk_assessment.md)\n"
        "- [phase7c_data_collection_recommendations.md](phase7c_data_collection_recommendations.md)\n"
        "- [feature_hdf5_audit.md](feature_hdf5_audit.md)\n\n"
        "## File-level balance CSVs\n\n"
        "- `file_level_balance_summary.csv`\n"
        "- `file_level_attack_distribution.csv`\n"
        "- `file_level_domain_distribution.csv`\n"
        "- `chunk_vs_file_balance_comparison.csv`\n\n"
        "## Regenerate\n\n"
        "```text\n"
        "python code/phase7/audit_current_training_dataset.py ^\n"
        "  --manifest_dir data/manifests ^\n"
        "  --output_dir reports/phase7_current_dataset_audit ^\n"
        "  --sample_per_group 20 ^\n"
        "  --check_audio_exists_sample 5000\n\n"
        "python code/phase7/audit_hdf5_features.py ^\n"
        "  --features_dir data/features ^\n"
        "  --output_dir reports/phase7_current_dataset_audit\n"
        "```\n",
        encoding="utf-8",
    )

    hdf5_found = []
    for name in ("logmel_chunked.h5", "environmental_packed.h5", "logmel_packed.h5"):
        if (_REPO_ROOT / "data/features" / name).is_file():
            hdf5_found.append(name)

    print_terminal_summary(
        manifest_status,
        unified,
        splits,
        split_info,
        dup_rows,
        len(conflict_rows) if unified else 0,
        missing_count,
        len(missing_rows),
        hdf5_found,
        risks,
        file_balance=file_balance or None,
    )
    print(f"\n[OK] Reports written to: {output_dir}")

    if unified and file_balance:
        print("\n--- File-level balance (Phase 7C0) ---")
        print(f"File identity column: {file_balance.get('file_id_column', 'n/a')}")
        print(f"Total unique files: {file_balance.get('total_unique_files', 0):,}")
        print(f"Avg rows per file: {file_balance.get('avg_rows_per_file', 0)}")
        print(
            f"Top class/domain (highest rows/file): {file_balance.get('top_group', 'n/a')} "
            f"({file_balance.get('top_avg_rows_per_file', 0)} rows/file)"
        )
        print(f"Chunk weighting bias severity: {file_balance.get('severity', 'n/a')}")


if __name__ == "__main__":
    main()
