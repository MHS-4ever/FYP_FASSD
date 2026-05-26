"""
Phase 7C3: Evaluate fine-tuned hybrid on Phase 7C2 feature cache (val/test).

Model outputs logits; metrics use masked origin/attack accuracy and category breakdowns.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import h5py
import pandas as pd
import torch
from torch.utils.data import DataLoader
from tqdm import tqdm

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "code"))

from phase3.hybrid_resnet_environmental import HybridResNetEnvironmental
from phase7.train_phase7c3_hybrid import Phase7C3H5Dataset, collate_fn, print_device_info


def print_eval_device(device: torch.device, n_rows: int, batch_size: int) -> None:
    print("=" * 60)
    print("Phase 7C3 evaluation — device")
    print(f"  device: {device}")
    print(f"  CUDA available: {torch.cuda.is_available()}")
    if device.type == "cuda":
        print(f"  GPU: {torch.cuda.get_device_name(0)}")
    print(f"  rows: {n_rows} | batch_size: {batch_size}")
    print("=" * 60)


@torch.no_grad()
def run_eval(
    h5_path: Path,
    ckpt_path: Path,
    device: torch.device,
    batch_size: int,
    num_workers: int,
) -> pd.DataFrame:
    keep_open = num_workers == 0
    ds = Phase7C3H5Dataset(h5_path, keep_open=keep_open)
    loader_kw = {
        "batch_size": batch_size,
        "shuffle": False,
        "collate_fn": collate_fn,
        "num_workers": num_workers,
        "pin_memory": device.type == "cuda",
    }
    if num_workers > 0:
        loader_kw["persistent_workers"] = True
    loader = DataLoader(ds, **loader_kw)

    ckpt = torch.load(str(ckpt_path), map_location=device, weights_only=False)
    state = ckpt.get("model_state_dict", ckpt)
    model = HybridResNetEnvironmental(n_attack_types=4, dropout=0.3).to(device)
    model.load_state_dict(state)
    model.eval()

    rows = []
    try:
        for batch in tqdm(loader, desc="Eval"):
            spec = batch["spectrogram"].to(device, non_blocking=True)
            env = batch["environmental"].to(device, non_blocking=True)
            binary_logits, attack_logits = model(spec, env)
            pred_origin = binary_logits.argmax(dim=1).cpu().numpy()
            pred_attack = attack_logits.argmax(dim=1).cpu().numpy()
            prob_fake = torch.softmax(binary_logits, dim=1)[:, 1].cpu().numpy()

            n = len(batch["manipulation_type"])
            for i in range(n):
                rows.append(
                    {
                        "pred_origin": int(pred_origin[i]),
                        "pred_attack": int(pred_attack[i]),
                        "prob_fake": float(prob_fake[i]),
                        "origin_target": int(batch["origin_target"][i]),
                        "attack_target": int(batch["attack_target"][i]),
                        "use_origin_loss": int(batch["use_origin_loss"][i]),
                        "use_attack_loss": int(batch["use_attack_loss"][i]),
                        "partial_target": int(batch["partial_target"][i]),
                        "manipulation_type": batch["manipulation_type"][i],
                        "source_origin": batch["source_origin"][i],
                        "data_source": batch["data_source"][i],
                        "sample_weight": float(batch["sample_weight"][i]),
                    }
                )
    finally:
        ds.close()
    return pd.DataFrame(rows)


def _accuracy(df: pd.DataFrame, mask_col: str, pred_col: str, target_col: str) -> float | None:
    sub = df[df[mask_col].astype(bool) & (df[target_col] >= 0)]
    if sub.empty:
        return None
    return float((sub[pred_col] == sub[target_col]).mean())


def _category_metrics(df: pd.DataFrame) -> dict:
    out = {}
    clean_human = df[(df["manipulation_type"] == "clean_direct") & (df["source_origin"] == "human")]
    if len(clean_human):
        out["clean_human_acceptance"] = float((clean_human["pred_origin"] == 0).mean())
        out["clean_human_n"] = len(clean_human)
    direct_ai = df[(df["manipulation_type"] == "clean_direct") & (df["source_origin"] == "ai")]
    if len(direct_ai):
        out["direct_ai_detection"] = float((direct_ai["pred_origin"] == 1).mean())
        out["direct_ai_n"] = len(direct_ai)
    human_replay = df[df["manipulation_type"] == "human_replay"]
    if len(human_replay):
        out["human_replay_origin_not_fake"] = float((human_replay["pred_origin"] == 0).mean())
    return out


def write_report(df: pd.DataFrame, output_md: Path, split_label: str) -> None:
    lines = [
        f"# Phase 7C2 {split_label} — Fine-tuned Model Evaluation (clip cache)",
        "",
        f"- Rows: **{len(df)}**",
        "",
        "## Overall (masked)",
        "",
        f"- Origin accuracy: `{_accuracy(df, 'use_origin_loss', 'pred_origin', 'origin_target')}`",
        f"- Attack accuracy: `{_accuracy(df, 'use_attack_loss', 'pred_attack', 'attack_target')}`",
        "",
        "## By data_source",
        "",
    ]
    for src in sorted(df["data_source"].unique()):
        sub = df[df["data_source"] == src]
        lines.append(f"### {src} (n={len(sub)})")
        lines.append(f"- Origin acc: `{_accuracy(sub, 'use_origin_loss', 'pred_origin', 'origin_target')}`")
        lines.append(f"- Attack acc: `{_accuracy(sub, 'use_attack_loss', 'pred_attack', 'attack_target')}`")
        lines.append("")

    lines.extend(
        [
            "## Category metrics (7C1-style on 4s window)",
            "",
            "## Limits",
            "",
            "- Not full-file pct_vote; partial region eval needs 7C1 baseline runner.",
            "",
        ]
    )
    for src in ["old", "phase7c1"]:
        sub = df[df["data_source"] == src] if src in df["data_source"].values else pd.DataFrame()
        if sub.empty:
            continue
        cm = _category_metrics(sub)
        lines.append(f"### {src}")
        for k, v in cm.items():
            lines.append(f"- {k}: {v}")
        lines.append("")

    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"[SAVE] {output_md}")


def parse_args():
    p = argparse.ArgumentParser(description="Phase 7C3 — evaluate on feature cache")
    p.add_argument("--test_h5", type=str, required=True)
    p.add_argument("--ckpt", type=str, required=True)
    p.add_argument("--output_csv", type=str, required=True)
    p.add_argument("--output_md", type=str, required=True)
    p.add_argument("--device", type=str, default="cuda")
    p.add_argument("--batch_size", type=int, default=32)
    p.add_argument("--num_workers", type=int, default=0)
    return p.parse_args()


def main():
    args = parse_args()
    device = torch.device(args.device if (args.device == "cpu" or torch.cuda.is_available()) else "cpu")
    h5_path = Path(args.test_h5)
    with h5py.File(h5_path, "r") as hf:
        n_rows = int(hf.attrs.get("n_samples", 0))
    print_eval_device(device, n_rows, args.batch_size)
    df = run_eval(h5_path, Path(args.ckpt), device, args.batch_size, args.num_workers)
    out_csv = Path(args.output_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)
    print(f"[SAVE] {out_csv}")
    split_label = "test" if "test" in str(args.test_h5).lower() else "val"
    write_report(df, Path(args.output_md), split_label)


if __name__ == "__main__":
    main()
