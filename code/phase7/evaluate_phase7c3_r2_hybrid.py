"""
Phase 7C3-R2: Evaluate forensic-risk fine-tuned HybridResNetEnvironmental on H5 cache.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd
import torch
from torch.utils.data import DataLoader
from tqdm import tqdm

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "code"))

from phase3.hybrid_resnet_environmental import HybridResNetEnvironmental
from phase7.train_phase7c3_r2_hybrid import Phase7C3R2H5Dataset, collate_fn

RISK_IGNORE = -1
ATTACK_IGNORE = -1


def _acc(df: pd.DataFrame, target_col: str, pred_col: str, mask_col: str) -> float | None:
    sub = df[df[mask_col] == 1]
    sub = sub[sub[target_col] >= 0]
    if sub.empty:
        return None
    return float((sub[target_col] == sub[pred_col]).mean())


def _product_metrics(df: pd.DataFrame) -> dict:
    out = {}
    clean = df[(df["manipulation_type"] == "clean_direct") & (df["source_origin"] == "human")]
    dai = df[(df["manipulation_type"] == "clean_direct") & (df["source_origin"] == "ai")]
    replay = df[df["manipulation_type"].isin(["human_replay", "ai_replay", "mixer_processed"])]
    pom = df[df["manipulation_type"].isin(["partial_ai_insert", "mixer_processed"])]
    out["clean_human_acceptance"] = float((clean["pred_risk"] == 0).mean()) if len(clean) else 0.0
    out["direct_ai_detection"] = float((dai["pred_risk"] == 1).mean()) if len(dai) else 0.0
    out["replay_detection"] = float(((replay["pred_risk"] == 1) | (replay["pred_attack"] != 0)).mean()) if len(replay) else 0.0
    out["partial_or_mixer_detection"] = float((pom["pred_risk"] == 1).mean()) if len(pom) else 0.0
    out["product_score"] = (
        0.30 * out["clean_human_acceptance"]
        + 0.30 * out["direct_ai_detection"]
        + 0.20 * out["replay_detection"]
        + 0.20 * out["partial_or_mixer_detection"]
    )
    return out


@torch.no_grad()
def evaluate(h5_path: Path, ckpt_path: Path, batch_size: int, num_workers: int, device: torch.device) -> pd.DataFrame:
    ds = Phase7C3R2H5Dataset(h5_path, keep_open=(num_workers == 0))
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
        for batch in tqdm(loader, desc="R2 eval"):
            spec = batch["spectrogram"].to(device, non_blocking=True)
            env = batch["environmental"].to(device, non_blocking=True)
            b_logits, a_logits = model(spec, env)
            pred_risk = b_logits.argmax(dim=1).cpu().numpy()
            pred_attack = a_logits.argmax(dim=1).cpu().numpy()
            risk_prob = torch.softmax(b_logits, dim=1)[:, 1].cpu().numpy()
            for i in range(len(batch["manipulation_type"])):
                rows.append(
                    {
                        "pred_risk": int(pred_risk[i]),
                        "pred_attack": int(pred_attack[i]),
                        "risk_prob": float(risk_prob[i]),
                        "risk_target": int(batch["risk_target"][i]),
                        "attack_target": int(batch["attack_target"][i]),
                        "use_risk_loss": int(batch["use_risk_loss"][i]),
                        "use_attack_loss": int(batch["use_attack_loss"][i]),
                        "sample_weight": float(batch["sample_weight"][i]),
                        "manipulation_type": batch["manipulation_type"][i],
                        "source_origin": batch["source_origin"][i],
                        "data_source": batch["data_source"][i],
                    }
                )
    finally:
        ds.close()
    return pd.DataFrame(rows)


def write_report(df: pd.DataFrame, output_md: Path):
    risk_acc = _acc(df, "risk_target", "pred_risk", "use_risk_loss")
    attack_acc = _acc(df, "attack_target", "pred_attack", "use_attack_loss")
    pm = _product_metrics(df)
    lines = [
        "# Phase 7C3-R2 Evaluation Report",
        "",
        f"- Rows: **{len(df)}**",
        f"- Risk accuracy (masked): `{risk_acc}`",
        f"- Attack accuracy (masked): `{attack_acc}`",
        "",
        "## Product proxy",
        "",
    ]
    for k, v in pm.items():
        lines.append(f"- {k}: {v}")
    lines += ["", "## By data_source", ""]
    for src, sub in df.groupby("data_source"):
        lines.append(f"- {src}: n={len(sub)}, risk_acc={_acc(sub, 'risk_target', 'pred_risk', 'use_risk_loss')}")
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"[SAVE] {output_md}")


def parse_args():
    p = argparse.ArgumentParser(description="Phase 7C3-R2 evaluate hybrid")
    p.add_argument("--test_h5", type=str, required=True)
    p.add_argument("--ckpt", type=str, required=True)
    p.add_argument("--output_csv", type=str, required=True)
    p.add_argument("--output_md", type=str, required=True)
    p.add_argument("--batch_size", type=int, default=32)
    p.add_argument("--num_workers", type=int, default=0)
    p.add_argument("--device", type=str, default="cuda")
    return p.parse_args()


def main():
    args = parse_args()
    device = torch.device(args.device if (args.device == "cpu" or torch.cuda.is_available()) else "cpu")
    print(f"[DEVICE] {device} | CUDA={torch.cuda.is_available()}")
    if device.type == "cuda":
        print(f"[GPU] {torch.cuda.get_device_name(0)}")
    df = evaluate(Path(args.test_h5), Path(args.ckpt), args.batch_size, args.num_workers, device)
    out_csv = Path(args.output_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)
    print(f"[SAVE] {out_csv}")
    write_report(df, Path(args.output_md))


if __name__ == "__main__":
    main()

