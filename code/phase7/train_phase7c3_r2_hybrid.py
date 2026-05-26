"""
Phase 7C3-R2: Fine-tune HybridResNetEnvironmental with forensic-risk binary target.

- Binary head target: risk_target (0 low-risk clean, 1 suspicious/manipulated)
- Attack head target: bonafide/synthesis/voice_conversion/replay
- Outputs go to reports/phase7/phase7c3_finetune_r2/training

Does not overwrite base checkpoint.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from torch.amp import GradScaler, autocast
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "code"))

from phase3.hybrid_resnet_environmental import HybridResNetEnvironmental

RISK_IGNORE = -1
ATTACK_IGNORE = -1


class Phase7C3R2H5Dataset(Dataset):
    def __init__(self, h5_path: Path, keep_open: bool = True):
        self.h5_path = Path(h5_path)
        self.keep_open = keep_open
        self._h5f: h5py.File | None = None
        with h5py.File(self.h5_path, "r") as h5f:
            self.n = int(h5f.attrs.get("n_samples", h5f["features_logmel"].shape[0]))

    def __len__(self):
        return self.n

    def _file(self):
        if self.keep_open:
            if self._h5f is None:
                self._h5f = h5py.File(self.h5_path, "r")
            return self._h5f
        return h5py.File(self.h5_path, "r")

    def __getitem__(self, idx):
        if self.keep_open:
            h5f = self._file()
            close_after = False
        else:
            h5f = h5py.File(self.h5_path, "r")
            close_after = True
        try:
            return {
                "spectrogram": torch.from_numpy(np.asarray(h5f["features_logmel"][idx], dtype=np.float32)).unsqueeze(0),
                "environmental": torch.from_numpy(np.asarray(h5f["features_env"][idx], dtype=np.float32)),
                "risk_target": int(h5f["risk_target"][idx]),
                "attack_target": int(h5f["attack_target"][idx]),
                "sample_weight": float(h5f["sample_weight"][idx]),
                "use_risk_loss": int(h5f["use_risk_loss"][idx]),
                "use_attack_loss": int(h5f["use_attack_loss"][idx]),
                "manipulation_type": h5f["manipulation_type"][idx].decode("utf-8"),
                "source_origin": h5f["source_origin"][idx].decode("utf-8"),
                "data_source": h5f["data_source"][idx].decode("utf-8"),
            }
        finally:
            if close_after:
                h5f.close()

    def close(self):
        if self._h5f is not None:
            self._h5f.close()
            self._h5f = None

    def __del__(self):
        self.close()


def collate_fn(batch: list[dict]) -> dict:
    return {
        "spectrogram": torch.stack([x["spectrogram"] for x in batch]).float(),
        "environmental": torch.stack([x["environmental"] for x in batch]).float(),
        "risk_target": torch.tensor([x["risk_target"] for x in batch], dtype=torch.long),
        "attack_target": torch.tensor([x["attack_target"] for x in batch], dtype=torch.long),
        "sample_weight": torch.tensor([x["sample_weight"] for x in batch], dtype=torch.float32),
        "use_risk_loss": torch.tensor([x["use_risk_loss"] for x in batch], dtype=torch.long),
        "use_attack_loss": torch.tensor([x["use_attack_loss"] for x in batch], dtype=torch.long),
        "manipulation_type": [x["manipulation_type"] for x in batch],
        "source_origin": [x["source_origin"] for x in batch],
        "data_source": [x["data_source"] for x in batch],
    }


def compute_losses(bin_logits, attack_logits, batch):
    risk_t = batch["risk_target"]
    attack_t = batch["attack_target"]
    w = batch["sample_weight"]
    risk_mask = batch["use_risk_loss"].bool() & (risk_t != RISK_IGNORE)
    attack_mask = batch["use_attack_loss"].bool() & (attack_t != ATTACK_IGNORE)

    risk_loss = torch.tensor(0.0, device=bin_logits.device)
    attack_loss = torch.tensor(0.0, device=bin_logits.device)

    if risk_mask.any():
        loss_vec = F.cross_entropy(bin_logits[risk_mask], risk_t[risk_mask], reduction="none")
        ww = w[risk_mask]
        risk_loss = (loss_vec * ww).sum() / ww.sum().clamp(min=1e-6)
    if attack_mask.any():
        loss_vec = F.cross_entropy(attack_logits[attack_mask], attack_t[attack_mask], reduction="none")
        ww = w[attack_mask]
        attack_loss = (loss_vec * ww).sum() / ww.sum().clamp(min=1e-6)
    total = risk_loss + 0.5 * attack_loss
    return total, risk_loss, attack_loss


def set_backbone_frozen(model: HybridResNetEnvironmental, frozen: bool):
    for module in (model.resnet_branch, model.environmental_branch):
        for p in module.parameters():
            p.requires_grad = not frozen


@torch.no_grad()
def evaluate_epoch(model, loader, device, use_amp: bool):
    model.eval()
    totals = {
        "loss": 0.0,
        "risk_correct": 0,
        "risk_total": 0,
        "attack_correct": 0,
        "attack_total": 0,
        "clean_human_accept": 0,
        "clean_human_total": 0,
        "direct_ai_detect": 0,
        "direct_ai_total": 0,
        "replay_detect": 0,
        "replay_total": 0,
        "partial_or_mixer_detect": 0,
        "partial_or_mixer_total": 0,
    }
    n_batches = 0
    for batch in loader:
        spec = batch["spectrogram"].to(device, non_blocking=True)
        env = batch["environmental"].to(device, non_blocking=True)
        for k in ("risk_target", "attack_target", "use_risk_loss", "use_attack_loss"):
            batch[k] = batch[k].to(device, non_blocking=True)
        batch["sample_weight"] = batch["sample_weight"].to(device, non_blocking=True)

        with autocast("cuda", enabled=use_amp):
            b_logits, a_logits = model(spec, env)
            loss, _, _ = compute_losses(b_logits, a_logits, batch)
        totals["loss"] += float(loss.item())
        n_batches += 1

        pred_risk = b_logits.argmax(dim=1)
        pred_attack = a_logits.argmax(dim=1)
        rmask = batch["use_risk_loss"].bool() & (batch["risk_target"] != RISK_IGNORE)
        amask = batch["use_attack_loss"].bool() & (batch["attack_target"] != ATTACK_IGNORE)
        if rmask.any():
            totals["risk_correct"] += int((pred_risk[rmask] == batch["risk_target"][rmask]).sum())
            totals["risk_total"] += int(rmask.sum())
        if amask.any():
            totals["attack_correct"] += int((pred_attack[amask] == batch["attack_target"][amask]).sum())
            totals["attack_total"] += int(amask.sum())

        for i, m in enumerate(batch["manipulation_type"]):
            manip = m.lower()
            src = batch["source_origin"][i].lower()
            pr = int(pred_risk[i].item())
            pa = int(pred_attack[i].item())
            if manip == "clean_direct" and src == "human":
                totals["clean_human_total"] += 1
                if pr == 0:
                    totals["clean_human_accept"] += 1
            if manip == "clean_direct" and src == "ai":
                totals["direct_ai_total"] += 1
                if pr == 1:
                    totals["direct_ai_detect"] += 1
            if manip in {"human_replay", "ai_replay", "mixer_processed"}:
                totals["replay_total"] += 1
                if pr == 1 or pa != 0:
                    totals["replay_detect"] += 1
            if manip in {"partial_ai_insert", "mixer_processed"}:
                totals["partial_or_mixer_total"] += 1
                if pr == 1:
                    totals["partial_or_mixer_detect"] += 1

    clean_human_acceptance = totals["clean_human_accept"] / totals["clean_human_total"] if totals["clean_human_total"] else 0.0
    direct_ai_detection = totals["direct_ai_detect"] / totals["direct_ai_total"] if totals["direct_ai_total"] else 0.0
    replay_detection = totals["replay_detect"] / totals["replay_total"] if totals["replay_total"] else 0.0
    partial_or_mixer_detection = (
        totals["partial_or_mixer_detect"] / totals["partial_or_mixer_total"] if totals["partial_or_mixer_total"] else 0.0
    )
    product_score = (
        0.30 * clean_human_acceptance
        + 0.30 * direct_ai_detection
        + 0.20 * replay_detection
        + 0.20 * partial_or_mixer_detection
    )
    return {
        "val_loss": totals["loss"] / max(n_batches, 1),
        "val_risk_accuracy": totals["risk_correct"] / totals["risk_total"] if totals["risk_total"] else 0.0,
        "val_attack_accuracy": totals["attack_correct"] / totals["attack_total"] if totals["attack_total"] else 0.0,
        "clean_human_acceptance": clean_human_acceptance,
        "direct_ai_detection": direct_ai_detection,
        "replay_detection": replay_detection,
        "partial_or_mixer_detection": partial_or_mixer_detection,
        "product_score": product_score,
    }


def _print_device(device, train_n, val_n, batch):
    print("=" * 60)
    print("Phase 7C3-R2 training")
    print(f"device={device}, cuda={torch.cuda.is_available()}")
    if device.type == "cuda":
        print(f"gpu={torch.cuda.get_device_name(0)}")
    print(f"train_rows={train_n}, val_rows={val_n}, batch_size={batch}")
    print("=" * 60)


def train(args):
    out_dir = Path(args.output_dir)
    ckpt_dir = out_dir / "checkpoints"
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    device = torch.device(args.device if (args.device == "cpu" or torch.cuda.is_available()) else "cpu")
    use_amp = bool(args.amp and device.type == "cuda")

    train_ds = Phase7C3R2H5Dataset(Path(args.train_h5), keep_open=(args.num_workers == 0))
    val_ds = Phase7C3R2H5Dataset(Path(args.val_h5), keep_open=(args.num_workers == 0))
    _print_device(device, len(train_ds), len(val_ds), args.batch_size)

    loader_kw = {
        "batch_size": args.batch_size,
        "collate_fn": collate_fn,
        "num_workers": args.num_workers,
        "pin_memory": device.type == "cuda",
    }
    if args.num_workers > 0:
        loader_kw["persistent_workers"] = True

    train_loader = DataLoader(train_ds, shuffle=True, **loader_kw)
    val_loader = DataLoader(val_ds, shuffle=False, **loader_kw)

    base_ckpt = Path(args.base_ckpt).resolve()
    ckpt = torch.load(str(base_ckpt), map_location=device, weights_only=False)
    state = ckpt.get("model_state_dict", ckpt)
    model = HybridResNetEnvironmental(n_attack_types=4, dropout=0.3).to(device)
    model.load_state_dict(state)
    print(f"[OK] base checkpoint loaded read-only: {base_ckpt}")

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    scaler = GradScaler("cuda", enabled=use_amp)

    best_loss = float("inf")
    best_product = float("-inf")
    best_loss_epoch = -1
    best_product_epoch = -1
    patience_left = args.patience
    logs = []

    try:
        for epoch in range(1, args.epochs + 1):
            set_backbone_frozen(model, epoch <= args.freeze_backbone_epochs)
            model.train()
            t_loss = 0.0
            n = 0
            pbar = tqdm(train_loader, desc=f"R2 epoch {epoch}/{args.epochs}")
            for batch in pbar:
                spec = batch["spectrogram"].to(device, non_blocking=True)
                env = batch["environmental"].to(device, non_blocking=True)
                for k in ("risk_target", "attack_target", "use_risk_loss", "use_attack_loss"):
                    batch[k] = batch[k].to(device, non_blocking=True)
                batch["sample_weight"] = batch["sample_weight"].to(device, non_blocking=True)

                optimizer.zero_grad(set_to_none=True)
                with autocast("cuda", enabled=use_amp):
                    b_logits, a_logits = model(spec, env)
                    loss, _, _ = compute_losses(b_logits, a_logits, batch)
                if use_amp:
                    scaler.scale(loss).backward()
                    torch.nn.utils.clip_grad_norm_(model.parameters(), args.gradient_clip)
                    scaler.step(optimizer)
                    scaler.update()
                else:
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(model.parameters(), args.gradient_clip)
                    optimizer.step()
                t_loss += float(loss.item())
                n += 1
                pbar.set_postfix(loss=f"{loss.item():.4f}")

            val = evaluate_epoch(model, val_loader, device, use_amp)
            epoch_log = {
                "epoch": epoch,
                "train_loss": t_loss / max(n, 1),
                **val,
                "learning_rate": optimizer.param_groups[0]["lr"],
                "backbone_frozen": epoch <= args.freeze_backbone_epochs,
                "amp": use_amp,
            }
            logs.append(epoch_log)
            print(
                f"[Epoch {epoch}] val_loss={val['val_loss']:.4f} product={val['product_score']:.4f} "
                f"clean={val['clean_human_acceptance']:.3f} ai={val['direct_ai_detection']:.3f}"
            )

            torch.save(
                {"epoch": epoch, "model_state_dict": model.state_dict(), "val_metrics": val, "base_ckpt": str(base_ckpt)},
                ckpt_dir / f"hybrid_resnet_environmental_phase7c3_r2_epoch_{epoch:02d}.pth",
            )
            torch.save(
                {"epoch": epoch, "model_state_dict": model.state_dict(), "val_metrics": val, "base_ckpt": str(base_ckpt)},
                ckpt_dir / "hybrid_resnet_environmental_phase7c3_r2_last.pth",
            )

            improved_loss = val["val_loss"] < best_loss
            improved_product = val["product_score"] > best_product
            if improved_loss:
                best_loss = val["val_loss"]
                best_loss_epoch = epoch
                torch.save(
                    {"epoch": epoch, "model_state_dict": model.state_dict(), "val_metrics": val, "base_ckpt": str(base_ckpt)},
                    ckpt_dir / "hybrid_resnet_environmental_phase7c3_r2_best_loss.pth",
                )
            if improved_product:
                best_product = val["product_score"]
                best_product_epoch = epoch
                torch.save(
                    {"epoch": epoch, "model_state_dict": model.state_dict(), "val_metrics": val, "base_ckpt": str(base_ckpt)},
                    ckpt_dir / "hybrid_resnet_environmental_phase7c3_r2_best_product.pth",
                )

            if improved_loss:
                patience_left = args.patience
            else:
                patience_left -= 1
                if patience_left <= 0:
                    print("[STOP] early stopping by val_loss patience")
                    break
    finally:
        train_ds.close()
        val_ds.close()

    pd.DataFrame(logs).to_csv(out_dir / "training_log.csv", index=False)
    summary = {
        "base_ckpt": str(base_ckpt),
        "epochs_run": len(logs),
        "best_loss": best_loss,
        "best_loss_epoch": best_loss_epoch,
        "best_product_score": best_product,
        "best_product_epoch": best_product_epoch,
        "checkpoint_paths": {
            "best_loss": str(ckpt_dir / "hybrid_resnet_environmental_phase7c3_r2_best_loss.pth"),
            "best_product": str(ckpt_dir / "hybrid_resnet_environmental_phase7c3_r2_best_product.pth"),
            "last": str(ckpt_dir / "hybrid_resnet_environmental_phase7c3_r2_last.pth"),
        },
    }
    (out_dir / "best_checkpoint_metrics.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"[SAVE] {out_dir / 'training_log.csv'}")
    print(f"[SAVE] {out_dir / 'best_checkpoint_metrics.json'}")


def parse_args():
    p = argparse.ArgumentParser(description="Phase 7C3-R2 hybrid fine-tuning")
    p.add_argument("--train_h5", type=str, required=True)
    p.add_argument("--val_h5", type=str, required=True)
    p.add_argument("--base_ckpt", type=str, required=True)
    p.add_argument("--output_dir", type=str, default="reports/phase7/phase7c3_finetune_r2/training")
    p.add_argument("--epochs", type=int, default=12)
    p.add_argument("--batch_size", type=int, default=16)
    p.add_argument("--num_workers", type=int, default=0)
    p.add_argument("--lr", type=float, default=5e-6)
    p.add_argument("--weight_decay", type=float, default=1e-4)
    p.add_argument("--freeze_backbone_epochs", type=int, default=1)
    p.add_argument("--patience", type=int, default=4)
    p.add_argument("--gradient_clip", type=float, default=1.0)
    p.add_argument("--device", type=str, default="cuda")
    p.add_argument("--amp", action="store_true")
    return p.parse_args()


def main():
    train(parse_args())


if __name__ == "__main__":
    main()

