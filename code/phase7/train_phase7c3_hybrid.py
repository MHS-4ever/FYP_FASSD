"""
Phase 7C3: Fine-tune HybridResNetEnvironmental from Phase 7C2 feature caches.

- Binary head = origin proxy (human=0/real, ai|mixed=1/fake); masked by use_origin_loss.
- Attack head = attack type; masked by use_attack_loss.
- No partial head in v1 (partial_target logged only).
- Never overwrites base checkpoint.
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

ORIGIN_IGNORE = -1
ATTACK_IGNORE = -1
BEST_CKPT_NAME = "hybrid_resnet_environmental_phase7c3_best.pth"
LAST_CKPT_NAME = "hybrid_resnet_environmental_phase7c3_last.pth"

LONG_TENSOR_KEYS = (
    "origin_target",
    "attack_target",
    "partial_target",
    "use_origin_loss",
    "use_attack_loss",
    "use_partial_loss",
)


class Phase7C3H5Dataset(Dataset):
    """HDF5 cache dataset; keeps file open when num_workers=0 (faster, Windows-safe)."""

    def __init__(self, h5_path: Path, keep_open: bool = True):
        self.h5_path = Path(h5_path)
        self._keep_open = keep_open
        self._h5f: h5py.File | None = None
        with h5py.File(self.h5_path, "r") as h5f:
            self.n = int(h5f.attrs.get("n_samples", h5f["features_logmel"].shape[0]))

    def _file(self) -> h5py.File:
        if self._keep_open:
            if self._h5f is None:
                self._h5f = h5py.File(self.h5_path, "r")
            return self._h5f
        return h5py.File(self.h5_path, "r")

    def __len__(self):
        return self.n

    def __getitem__(self, idx):
        if self._keep_open:
            h5f = self._file()
            close_after = False
        else:
            h5f = h5py.File(self.h5_path, "r")
            close_after = True
        try:
            logmel = np.asarray(h5f["features_logmel"][idx], dtype=np.float32)
            env = np.asarray(h5f["features_env"][idx], dtype=np.float32)
            return {
                "spectrogram": torch.from_numpy(logmel).unsqueeze(0).float(),
                "environmental": torch.from_numpy(env).float(),
                "origin_target": int(h5f["origin_target"][idx]),
                "attack_target": int(h5f["attack_target"][idx]),
                "partial_target": int(h5f["partial_target"][idx]),
                "sample_weight": float(h5f["sample_weight"][idx]),
                "use_origin_loss": int(h5f["use_origin_loss"][idx]),
                "use_attack_loss": int(h5f["use_attack_loss"][idx]),
                "use_partial_loss": int(h5f["use_partial_loss"][idx]),
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


def collate_fn(batch_list: list[dict]) -> dict:
    """Explicit collation — Python ints/floats must not go through torch.stack."""
    out: dict = {}
    out["spectrogram"] = torch.stack([b["spectrogram"] for b in batch_list], dim=0)
    out["environmental"] = torch.stack([b["environmental"] for b in batch_list], dim=0)
    out["origin_target"] = torch.tensor([b["origin_target"] for b in batch_list], dtype=torch.long)
    out["attack_target"] = torch.tensor([b["attack_target"] for b in batch_list], dtype=torch.long)
    out["partial_target"] = torch.tensor([b["partial_target"] for b in batch_list], dtype=torch.long)
    out["use_origin_loss"] = torch.tensor([b["use_origin_loss"] for b in batch_list], dtype=torch.long)
    out["use_attack_loss"] = torch.tensor([b["use_attack_loss"] for b in batch_list], dtype=torch.long)
    out["use_partial_loss"] = torch.tensor([b["use_partial_loss"] for b in batch_list], dtype=torch.long)
    out["sample_weight"] = torch.tensor([b["sample_weight"] for b in batch_list], dtype=torch.float32)
    out["manipulation_type"] = [b["manipulation_type"] for b in batch_list]
    out["source_origin"] = [b["source_origin"] for b in batch_list]
    out["data_source"] = [b["data_source"] for b in batch_list]
    return out


def print_device_info(device: torch.device, train_n: int, val_n: int, batch_size: int) -> None:
    print("=" * 60)
    print("Phase 7C3 training — device / resources")
    print(f"  device: {device}")
    print(f"  CUDA available: {torch.cuda.is_available()}")
    if device.type == "cuda":
        print(f"  GPU: {torch.cuda.get_device_name(0)}")
        props = torch.cuda.get_device_properties(0)
        vram_gb = getattr(props, "total_memory", 0) / (1024**3)
        print(f"  Total VRAM: {vram_gb:.2f} GB")
    print(f"  train rows: {train_n} | val rows: {val_n} | batch_size: {batch_size}")
    est_mb = batch_size * (64 * 400 * 4 + 12 * 4) * 2 / (1024**2)
    print(f"  ~{est_mb:.1f} MB input tensors per batch (order-of-magnitude)")
    print("=" * 60)


def set_backbone_frozen(model: HybridResNetEnvironmental, frozen: bool) -> None:
    for module in (model.resnet_branch, model.environmental_branch):
        for p in module.parameters():
            p.requires_grad = not frozen


def compute_masked_losses(
    binary_logits: torch.Tensor,
    attack_logits: torch.Tensor,
    batch: dict,
    attack_loss_weight: float = 0.5,
):
    # Model returns raw logits [B,2] and [B,4] — CrossEntropy only (no extra sigmoid).
    origin_t = batch["origin_target"]
    attack_t = batch["attack_target"]
    weights = batch["sample_weight"]
    origin_mask = batch["use_origin_loss"].bool() & (origin_t != ORIGIN_IGNORE)
    attack_mask = batch["use_attack_loss"].bool() & (attack_t != ATTACK_IGNORE)

    origin_loss = torch.tensor(0.0, device=binary_logits.device)
    attack_loss = torch.tensor(0.0, device=binary_logits.device)

    if origin_mask.any():
        ol = F.cross_entropy(
            binary_logits[origin_mask],
            origin_t[origin_mask].long(),
            reduction="none",
        )
        w = weights[origin_mask]
        origin_loss = (ol * w).sum() / w.sum().clamp(min=1e-6)

    if attack_mask.any():
        al = F.cross_entropy(
            attack_logits[attack_mask],
            attack_t[attack_mask].long(),
            reduction="none",
        )
        w = weights[attack_mask]
        attack_loss = (al * w).sum() / w.sum().clamp(min=1e-6)

    total = origin_loss + attack_loss_weight * attack_loss
    return total, origin_loss, attack_loss


@torch.no_grad()
def evaluate_epoch(model, loader, device, use_amp: bool) -> dict:
    model.eval()
    totals = {
        "loss": 0.0,
        "origin_correct": 0,
        "origin_total": 0,
        "attack_correct": 0,
        "attack_total": 0,
        "clean_human_accept": 0,
        "clean_human_total": 0,
        "direct_ai_detect": 0,
        "direct_ai_total": 0,
        "replay_detect": 0,
        "replay_total": 0,
        "partial_rows": 0,
    }
    n_batches = 0
    for batch in loader:
        spec = batch["spectrogram"].to(device, non_blocking=True)
        env = batch["environmental"].to(device, non_blocking=True)
        for k in LONG_TENSOR_KEYS:
            batch[k] = batch[k].to(device, non_blocking=True)
        batch["sample_weight"] = batch["sample_weight"].to(device, non_blocking=True)

        with autocast("cuda", enabled=use_amp and device.type == "cuda"):
            binary_logits, attack_logits = model(spec, env)
            loss, _, _ = compute_masked_losses(binary_logits, attack_logits, batch)

        totals["loss"] += float(loss.item())
        n_batches += 1

        pred_origin = binary_logits.argmax(dim=1)
        pred_attack = attack_logits.argmax(dim=1)
        origin_mask = batch["use_origin_loss"].bool() & (batch["origin_target"] != ORIGIN_IGNORE)
        attack_mask = batch["use_attack_loss"].bool() & (batch["attack_target"] != ATTACK_IGNORE)

        if origin_mask.any():
            totals["origin_correct"] += int((pred_origin[origin_mask] == batch["origin_target"][origin_mask]).sum())
            totals["origin_total"] += int(origin_mask.sum())

        if attack_mask.any():
            totals["attack_correct"] += int((pred_attack[attack_mask] == batch["attack_target"][attack_mask]).sum())
            totals["attack_total"] += int(attack_mask.sum())

        manip = batch["manipulation_type"]
        for i in range(len(manip)):
            m = manip[i].lower()
            so = batch["source_origin"][i].lower()
            po, pa = int(pred_origin[i].item()), int(pred_attack[i].item())
            if m == "clean_direct" and so == "human":
                totals["clean_human_total"] += 1
                if po == 0:
                    totals["clean_human_accept"] += 1
            if m == "clean_direct" and so == "ai":
                totals["direct_ai_total"] += 1
                if po == 1:
                    totals["direct_ai_detect"] += 1
            if m in {"human_replay", "ai_replay"}:
                totals["replay_total"] += 1
                if po == 1 or pa != 0:
                    totals["replay_detect"] += 1
            if int(batch["partial_target"][i].item()) == 1:
                totals["partial_rows"] += 1

    return {
        "val_loss": totals["loss"] / max(n_batches, 1),
        "val_origin_accuracy": totals["origin_correct"] / totals["origin_total"] if totals["origin_total"] else 0.0,
        "val_attack_accuracy": totals["attack_correct"] / totals["attack_total"] if totals["attack_total"] else 0.0,
        "val_human_clean_acceptance": totals["clean_human_accept"] / totals["clean_human_total"]
        if totals["clean_human_total"]
        else 0.0,
        "val_direct_ai_detection": totals["direct_ai_detect"] / totals["direct_ai_total"]
        if totals["direct_ai_total"]
        else 0.0,
        "val_replay_detection": totals["replay_detect"] / totals["replay_total"] if totals["replay_total"] else 0.0,
        "val_partial_rows_count": totals["partial_rows"],
    }


def train_model(args: argparse.Namespace) -> None:
    device = torch.device(args.device if (args.device == "cpu" or torch.cuda.is_available()) else "cpu")
    use_amp = bool(args.amp and device.type == "cuda")
    output_dir = Path(args.output_dir)
    ckpt_dir = output_dir / "checkpoints"
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    keep_h5_open = args.num_workers == 0
    train_ds = Phase7C3H5Dataset(Path(args.train_h5), keep_open=keep_h5_open)
    val_ds = Phase7C3H5Dataset(Path(args.val_h5), keep_open=keep_h5_open)

    print_device_info(device, len(train_ds), len(val_ds), args.batch_size)

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
    if not base_ckpt.is_file():
        raise FileNotFoundError(base_ckpt)

    ckpt_data = torch.load(str(base_ckpt), map_location=device, weights_only=False)
    state_dict = ckpt_data.get("model_state_dict", ckpt_data)
    model = HybridResNetEnvironmental(n_attack_types=4, dropout=0.3).to(device)
    model.load_state_dict(state_dict)
    print(f"[OK] Loaded base checkpoint (read-only): {base_ckpt}")

    # Optimizer on ALL parameters so unfreezing backbone after epoch 2 is effective.
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    scaler = GradScaler("cuda", enabled=use_amp)

    log_rows = []
    best_val = float("inf")
    best_epoch = -1
    patience_left = args.patience
    best_metrics: dict = {}

    try:
        for epoch in range(1, args.epochs + 1):
            set_backbone_frozen(model, epoch <= args.freeze_backbone_epochs)

            model.train()
            train_loss_sum = 0.0
            n_train = 0
            pbar = tqdm(train_loader, desc=f"Epoch {epoch}/{args.epochs}")
            for batch in pbar:
                spec = batch["spectrogram"].to(device, non_blocking=True)
                env = batch["environmental"].to(device, non_blocking=True)
                for k in LONG_TENSOR_KEYS:
                    batch[k] = batch[k].to(device, non_blocking=True)
                batch["sample_weight"] = batch["sample_weight"].to(device, non_blocking=True)

                optimizer.zero_grad(set_to_none=True)
                with autocast("cuda", enabled=use_amp):
                    binary_logits, attack_logits = model(spec, env)
                    loss, _, _ = compute_masked_losses(binary_logits, attack_logits, batch)

                if use_amp:
                    scaler.scale(loss).backward()
                    if args.gradient_clip > 0:
                        scaler.unscale_(optimizer)
                        torch.nn.utils.clip_grad_norm_(model.parameters(), args.gradient_clip)
                    scaler.step(optimizer)
                    scaler.update()
                else:
                    loss.backward()
                    if args.gradient_clip > 0:
                        torch.nn.utils.clip_grad_norm_(model.parameters(), args.gradient_clip)
                    optimizer.step()

                train_loss_sum += float(loss.item())
                n_train += 1
                pbar.set_postfix(loss=f"{loss.item():.4f}")

            val_metrics = evaluate_epoch(model, val_loader, device, use_amp)
            train_loss = train_loss_sum / max(n_train, 1)

            row = {
                "epoch": epoch,
                "train_loss": train_loss,
                "val_loss": val_metrics["val_loss"],
                "val_origin_accuracy": val_metrics["val_origin_accuracy"],
                "val_attack_accuracy": val_metrics["val_attack_accuracy"],
                "val_human_clean_acceptance": val_metrics["val_human_clean_acceptance"],
                "val_direct_ai_detection": val_metrics["val_direct_ai_detection"],
                "val_replay_detection": val_metrics["val_replay_detection"],
                "val_partial_rows_count": val_metrics["val_partial_rows_count"],
                "learning_rate": optimizer.param_groups[0]["lr"],
                "backbone_frozen": epoch <= args.freeze_backbone_epochs,
                "amp": use_amp,
            }
            log_rows.append(row)
            print(
                f"[Epoch {epoch}] train_loss={train_loss:.4f} val_loss={val_metrics['val_loss']:.4f} "
                f"origin_acc={val_metrics['val_origin_accuracy']:.3f} "
                f"clean_human={val_metrics['val_human_clean_acceptance']:.3f} "
                f"direct_ai={val_metrics['val_direct_ai_detection']:.3f}"
            )

            torch.save(
                {"epoch": epoch, "model_state_dict": model.state_dict(), "val_metrics": val_metrics},
                ckpt_dir / LAST_CKPT_NAME,
            )

            if val_metrics["val_loss"] < best_val:
                best_val = val_metrics["val_loss"]
                best_epoch = epoch
                best_metrics = val_metrics
                patience_left = args.patience
                torch.save(
                    {
                        "epoch": epoch,
                        "model_state_dict": model.state_dict(),
                        "base_ckpt": str(base_ckpt),
                        "val_metrics": val_metrics,
                    },
                    ckpt_dir / BEST_CKPT_NAME,
                )
                print(f"[SAVE] Best checkpoint -> {ckpt_dir / BEST_CKPT_NAME}")
            else:
                patience_left -= 1
                if patience_left <= 0:
                    print("[STOP] Early stopping")
                    break
    finally:
        train_ds.close()
        val_ds.close()

    log_df = pd.DataFrame(log_rows)
    log_path = output_dir / "training_log.csv"
    log_df.to_csv(log_path, index=False)
    print(f"[SAVE] {log_path}")

    best_json = {
        "base_ckpt": str(base_ckpt),
        "best_epoch": best_epoch,
        "best_val_loss": best_val,
        **{k: float(v) if isinstance(v, (float, np.floating)) else v for k, v in best_metrics.items()},
        "note": "Partial fabrication not trained in Phase 7C3-v1 (no partial head).",
    }
    (output_dir / "best_checkpoint_metrics.json").write_text(json.dumps(best_json, indent=2), encoding="utf-8")

    summary = [
        "# Phase 7C3 Training Summary",
        "",
        f"- Base checkpoint (unchanged): `{base_ckpt}`",
        f"- Train rows: {len(train_ds)} | Val rows: {len(val_ds)}",
        f"- Epochs run: {len(log_rows)} | Best epoch: **{best_epoch}**",
        f"- Best val loss: **{best_val:.4f}**",
        f"- AMP: **{use_amp}**",
        "",
    ]
    for k, v in best_metrics.items():
        summary.append(f"- {k}: {v}")
    summary.extend(
        [
            "",
            "- Partial fabrication: clip-level cache only; region metrics via 7C1 baseline runner.",
            "- Accept checkpoint only after Phase 7C1 + 7A holdout before/after review.",
            "",
        ]
    )
    (output_dir / "training_summary.md").write_text("\n".join(summary), encoding="utf-8")
    print(f"[SAVE] {output_dir / 'training_summary.md'}")


def parse_args():
    p = argparse.ArgumentParser(description="Phase 7C3 — fine-tune hybrid model")
    p.add_argument("--train_h5", type=str, required=True)
    p.add_argument("--val_h5", type=str, required=True)
    p.add_argument("--base_ckpt", type=str, required=True)
    p.add_argument("--output_dir", type=str, default="reports/phase7/phase7c3_finetune/training")
    p.add_argument("--epochs", type=int, default=12)
    p.add_argument("--batch_size", type=int, default=16)
    p.add_argument("--lr", type=float, default=1e-5)
    p.add_argument("--weight_decay", type=float, default=1e-4)
    p.add_argument("--freeze_backbone_epochs", type=int, default=2)
    p.add_argument("--patience", type=int, default=4)
    p.add_argument("--gradient_clip", type=float, default=1.0)
    p.add_argument("--device", type=str, default="cuda")
    p.add_argument("--num_workers", type=int, default=0, help="DataLoader workers (0=Windows-safe)")
    p.add_argument("--amp", action="store_true", help="Mixed precision on CUDA")
    return p.parse_args()


def main():
    train_model(parse_args())


if __name__ == "__main__":
    main()
