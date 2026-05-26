"""
Phase 7E3C: AASIST-L fine-tuning training script (implementation only; do not run in Cursor).

Constraints:
- Do not modify vendor AASIST source.
- Do not overwrite official pretrained checkpoint.
- Use 7E3B fine-tune manifests (window rows).

Default imbalance strategy (first run):
- balanced_sampler=true
- use_sample_weight=true
- class_balanced_loss=false (optional flag; default disabled)
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
import pandas as pd

from collections import Counter

from _common import ensure_dir, resolve_path, utc_now_iso, write_json, write_markdown
from aasist_eval_common import (
    OFFICIAL_SPOOF_CLASS_INDEX,
    TARGET_SAMPLE_RATE,
    extract_aasist_logits,
    load_aasist_config,
    load_audio_mono_16k,
    resolve_audio_path,
)

from _common import add_aasist_src_to_path


@dataclass(frozen=True)
class TrainConfig:
    train_manifest: Path
    val_manifest: Path
    aasist_src: Path
    config_path: Path
    base_checkpoint: Path
    output_dir: Path
    device: str
    batch_size: int
    num_workers: int
    epochs: int
    lr: float
    weight_decay: float
    balanced_sampler: bool
    use_sample_weight: bool
    class_balanced_loss: bool
    amp: bool
    freeze_frontend_epochs: int
    patience: int
    limit_train: int | None
    limit_val: int | None
    random_seed: int
    grad_clip: float


def _set_seeds(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch

        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    except Exception:
        # Training script should still import for doc review on systems without torch.
        pass


def _safe_device(device: str) -> str:
    try:
        import torch

        if device == "cuda" and torch.cuda.is_available():
            return "cuda"
    except Exception:
        pass
    return "cpu"


def _extract_manifest_window(
    wav: np.ndarray,
    start_sec: float,
    end_sec: float,
    nb_samp: int,
) -> np.ndarray:
    """
    Convert manifest time window to AASIST fixed-length nb_samp waveform.
    - Crop/pad deterministically using (start_sec,end_sec) as anchor.
    """
    start = max(0, int(round(start_sec * TARGET_SAMPLE_RATE)))
    end = max(start, int(round(end_sec * TARGET_SAMPLE_RATE)))
    seg = wav[start:end]
    if len(seg) <= 0:
        seg = np.zeros((0,), dtype=np.float32)

    if len(seg) >= nb_samp:
        return seg[:nb_samp].astype(np.float32, copy=False)

    out = np.zeros((nb_samp,), dtype=np.float32)
    out[: len(seg)] = seg.astype(np.float32, copy=False)
    return out


class AasistFineTuneDataset:
    def __init__(self, df: pd.DataFrame, nb_samp: int, limit: int | None = None) -> None:
        self.df = df.reset_index(drop=True)
        if limit is not None:
            self.df = self.df.iloc[: int(limit)].reset_index(drop=True)
        self.nb_samp = int(nb_samp)

        required = [
            "audio_path",
            "aasist_label",
            "risk_target",
            "window_start_time",
            "window_end_time",
            "sample_weight",
            "source_branch_role",
        ]
        missing = [c for c in required if c not in self.df.columns]
        if missing:
            raise ValueError(f"manifest missing required columns: {missing}")

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int) -> dict[str, Any]:
        r = self.df.iloc[int(idx)]
        ap = resolve_audio_path(str(r["audio_path"]))
        if ap is None:
            raise FileNotFoundError(f"audio_not_found:{r['audio_path']}")

        wav, _meta = load_audio_mono_16k(ap)
        x = _extract_manifest_window(
            wav,
            float(r["window_start_time"]),
            float(r["window_end_time"]),
            self.nb_samp,
        )
        y = int(r["aasist_label"])
        rt = int(r["risk_target"])
        sw = float(r["sample_weight"])
        role = str(r.get("source_branch_role", ""))

        return {
            "x": x,
            "y": y,
            "risk_target": rt,
            "sample_weight": sw,
            "role": role,
        }


def _collate(batch: list[dict[str, Any]]) -> dict[str, Any]:
    import torch

    xs = torch.from_numpy(np.stack([b["x"] for b in batch], axis=0)).float()
    ys = torch.tensor([b["y"] for b in batch], dtype=torch.long)
    sw = torch.tensor([float(b["sample_weight"]) for b in batch], dtype=torch.float32)
    roles = [str(b.get("role", "")) for b in batch]
    return {"x": xs, "y": ys, "sample_weight": sw, "roles": roles}


def _balanced_sampler_weights(labels: np.ndarray) -> np.ndarray:
    counts = Counter(labels.tolist())
    w = np.zeros((len(labels),), dtype=np.float64)
    for i, y in enumerate(labels.tolist()):
        w[i] = 1.0 / float(counts.get(y, 1))
    return w


def _compute_role_rates(
    roles: list[str],
    y_true: list[int],
    spoof_scores: list[float],
    threshold: float = 0.5,
) -> dict[str, Any]:
    """
    Window-level role metrics on validation.

    predicted_risk = 1 if spoof_score >= threshold else 0
    Role detection = predicted_risk == 1 (risk-positive)
    """
    def _match(role_key: str) -> list[int]:
        return [i for i, r in enumerate(roles) if role_key in r.lower()]

    pred_risk = [int(s >= threshold) for s in spoof_scores]

    def _count_detect(role_key: str) -> tuple[int, int]:
        idxs = _match(role_key)
        if not idxs:
            return 0, 0
        det = sum(pred_risk[i] for i in idxs)
        return det, len(idxs)

    ch_false, ch_total = _count_detect("clean_human")
    ch_accept = (ch_total - ch_false) if ch_total else 0

    direct_det, direct_total = _count_detect("direct_ai")
    ai_replay_det, ai_replay_total = _count_detect("ai_replay")
    human_replay_det, human_replay_total = _count_detect("human_replay")
    ai_mixer_det, ai_mixer_total = _count_detect("ai_mixer")
    human_mixer_det, human_mixer_total = _count_detect("human_mixer")
    partial_det, partial_total = _count_detect("partial_fabrication")

    def _rate(n: int, d: int) -> float:
        return float(n / d) if d > 0 else 0.0

    clean_human_false_alarm_rate = _rate(ch_false, ch_total)
    direct_ai_detect_rate = _rate(direct_det, direct_total)
    ai_replay_detect_rate = _rate(ai_replay_det, ai_replay_total)
    human_replay_detect_rate = _rate(human_replay_det, human_replay_total)
    ai_mixer_detect_rate = _rate(ai_mixer_det, ai_mixer_total)
    human_mixer_detect_rate = _rate(human_mixer_det, human_mixer_total)
    partial_detect_rate = _rate(partial_det, partial_total)

    clean_score = 1.0 - clean_human_false_alarm_rate
    replay_score = 0.5 * (human_replay_detect_rate + ai_replay_detect_rate)
    mixer_score = 0.5 * (human_mixer_detect_rate + ai_mixer_detect_rate)

    product_score = (
        0.35 * clean_score
        + 0.25 * direct_ai_detect_rate
        + 0.15 * replay_score
        + 0.15 * mixer_score
        + 0.10 * partial_detect_rate
    )
    if clean_human_false_alarm_rate > 0.45:
        product_score *= 0.70

    return {
        "val_clean_human_false_alarm_count": int(ch_false),
        "val_clean_human_false_alarm_rate": float(clean_human_false_alarm_rate),
        "val_clean_human_accept_count": int(ch_accept),
        "val_direct_ai_detect_count": int(direct_det),
        "val_ai_replay_detect_count": int(ai_replay_det),
        "val_human_replay_detect_count": int(human_replay_det),
        "val_human_mixer_detect_count": int(human_mixer_det),
        "val_ai_mixer_detect_count": int(ai_mixer_det),
        "val_partial_detect_count": int(partial_det),
        "val_product_score": float(product_score),
        "role_denoms": {
            "clean_human": int(ch_total),
            "direct_ai": int(direct_total),
            "ai_replay": int(ai_replay_total),
            "human_replay": int(human_replay_total),
            "ai_mixer": int(ai_mixer_total),
            "human_mixer": int(human_mixer_total),
            "partial_fabrication": int(partial_total),
        },
    }


def _print_run_summary(
    cfg: TrainConfig,
    dev: str,
    train_rows: int,
    val_rows: int,
    checkpoint_load: dict[str, Any],
) -> None:
    import torch

    cuda_ok = torch.cuda.is_available()
    gpu_name = torch.cuda.get_device_name(0) if cuda_ok else "n/a"
    print("=== Phase 7E3C AASIST-L fine-tune ===")
    print(f"device (resolved): {dev}")
    print(f"CUDA available: {cuda_ok}")
    print(f"GPU name: {gpu_name}")
    print(f"train rows: {train_rows}")
    print(f"val rows: {val_rows}")
    print(f"batch_size: {cfg.batch_size}")
    print(f"balanced_sampler: {cfg.balanced_sampler}")
    print(f"use_sample_weight: {cfg.use_sample_weight}")
    print(f"class_balanced_loss: {cfg.class_balanced_loss}")
    print(f"lr: {cfg.lr}")
    print(f"grad_clip: {cfg.grad_clip}")
    print(f"amp: {cfg.amp}")
    print(f"base_checkpoint: {cfg.base_checkpoint}")
    print(f"output_dir: {cfg.output_dir}")
    print(
        f"checkpoint_load: missing={checkpoint_load.get('missing_keys_count', '?')} "
        f"unexpected={checkpoint_load.get('unexpected_keys_count', '?')}"
    )


def _write_training_summary(
    out_dir: Path,
    cfg: TrainConfig,
    best_loss: dict[str, Any] | None,
    best_product: dict[str, Any] | None,
    warnings: list[str],
    checkpoint_load: dict[str, Any],
) -> None:
    lines = [
        "# Phase 7E3C — AASIST-L Fine-Tune Training Summary",
        "",
        f"**Generated:** {utc_now_iso()}",
        "",
        "## Run config",
        "",
        "```json",
        json.dumps({k: str(v) if isinstance(v, Path) else v for k, v in cfg.__dict__.items()}, indent=2),
        "```",
        "",
        "## Checkpoint load",
        "",
        "```json",
        json.dumps(checkpoint_load, indent=2),
        "```",
        "",
        "## Best checkpoints",
        "",
        f"- **best_loss:** `{best_loss.get('checkpoint_path') if best_loss else ''}`",
        f"- **best_product:** `{best_product.get('checkpoint_path') if best_product else ''}`",
        "",
        "## Notes",
        "",
        "- Default design uses **balanced sampler + sample weights**, with **class-balanced loss disabled** unless explicitly enabled.",
        "- Product score heavily penalizes clean-human false alarms.",
        "- Classifier logits taken from `model(x)[-1]` (official AASIST tuple output).",
        "",
    ]
    if warnings:
        lines.extend(["## Warnings", ""] + [f"- {w}" for w in warnings] + [""])
    write_markdown(out_dir / "training_summary.md", lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 7E3C: Fine-tune AASIST-L (do not run inside Cursor).")
    parser.add_argument("--train_manifest", required=True, type=str)
    parser.add_argument("--val_manifest", required=True, type=str)
    parser.add_argument("--aasist_src", required=True, type=str)
    parser.add_argument("--config_path", required=True, type=str)
    parser.add_argument("--base_checkpoint", required=True, type=str)
    parser.add_argument("--output_dir", required=True, type=str)
    parser.add_argument("--device", default="cuda", type=str)
    parser.add_argument("--batch_size", default=8, type=int)
    parser.add_argument("--num_workers", default=0, type=int)
    parser.add_argument("--epochs", default=10, type=int)
    parser.add_argument("--lr", default=2e-6, type=float)
    parser.add_argument("--weight_decay", default=1e-4, type=float)
    parser.add_argument("--balanced_sampler", action="store_true")
    parser.add_argument("--use_sample_weight", action="store_true")
    parser.add_argument("--class_balanced_loss", action="store_true")
    parser.add_argument("--amp", action="store_true")
    parser.add_argument("--freeze_frontend_epochs", default=0, type=int)
    parser.add_argument("--patience", default=4, type=int)
    parser.add_argument("--limit_train", default=None, type=int)
    parser.add_argument("--limit_val", default=None, type=int)
    parser.add_argument("--random_seed", default=42, type=int)
    parser.add_argument("--grad_clip", default=1.0, type=float)
    args = parser.parse_args()

    cfg = TrainConfig(
        train_manifest=resolve_path(args.train_manifest),
        val_manifest=resolve_path(args.val_manifest),
        aasist_src=resolve_path(args.aasist_src),
        config_path=resolve_path(args.config_path),
        base_checkpoint=resolve_path(args.base_checkpoint),
        output_dir=resolve_path(args.output_dir),
        device=str(args.device),
        batch_size=int(args.batch_size),
        num_workers=int(args.num_workers),
        epochs=int(args.epochs),
        lr=float(args.lr),
        weight_decay=float(args.weight_decay),
        balanced_sampler=bool(args.balanced_sampler),
        use_sample_weight=bool(args.use_sample_weight),
        class_balanced_loss=bool(args.class_balanced_loss),
        amp=bool(args.amp),
        freeze_frontend_epochs=int(args.freeze_frontend_epochs),
        patience=int(args.patience),
        limit_train=args.limit_train,
        limit_val=args.limit_val,
        random_seed=int(args.random_seed),
        grad_clip=float(args.grad_clip),
    )

    _set_seeds(cfg.random_seed)
    dev = _safe_device(cfg.device)

    out_dir = ensure_dir(cfg.output_dir)
    ckpt_dir = ensure_dir(out_dir / "checkpoints")

    if not cfg.base_checkpoint.is_file():
        raise FileNotFoundError(f"base_checkpoint not found: {cfg.base_checkpoint}")
    if cfg.base_checkpoint.resolve().parent == ckpt_dir.resolve():
        raise ValueError("Refusing to use a base_checkpoint inside output checkpoints dir.")

    # Torch imports here to keep file reviewable even if torch missing.
    import torch
    from torch import nn
    from torch.utils.data import DataLoader, WeightedRandomSampler

    add_aasist_src_to_path(cfg.aasist_src)
    config, model_config = load_aasist_config(cfg.config_path)
    nb_samp = int(model_config.get("nb_samp", 64600))

    # Vendor model import (read-only usage)
    from models.AASIST import Model  # type: ignore

    model = Model(model_config).to(dev)
    ckpt = torch.load(str(cfg.base_checkpoint), map_location=dev)
    state = ckpt
    if isinstance(ckpt, dict):
        for key in ("model_state_dict", "state_dict", "model"):
            if key in ckpt and isinstance(ckpt[key], dict):
                state = ckpt[key]
                break
    load_result = model.load_state_dict(state, strict=False)
    checkpoint_load: dict[str, Any] = {
        "status": "loaded",
        "base_checkpoint": str(cfg.base_checkpoint),
        "missing_keys_count": len(load_result.missing_keys),
        "unexpected_keys_count": len(load_result.unexpected_keys),
        "missing_keys_sample": list(load_result.missing_keys[:10]),
        "unexpected_keys_sample": list(load_result.unexpected_keys[:10]),
    }

    train_df = pd.read_csv(cfg.train_manifest)
    val_df = pd.read_csv(cfg.val_manifest)
    train_row_count = len(train_df) if cfg.limit_train is None else min(len(train_df), int(cfg.limit_train))
    val_row_count = len(val_df) if cfg.limit_val is None else min(len(val_df), int(cfg.limit_val))

    warnings: list[str] = []
    if checkpoint_load["missing_keys_count"] > 50:
        warnings.append(
            f"checkpoint_load: high missing_keys_count={checkpoint_load['missing_keys_count']} "
            "(verify base checkpoint matches AASIST-L)"
        )

    write_json(
        out_dir / "run_config.json",
        {
            **{k: str(v) if isinstance(v, Path) else v for k, v in cfg.__dict__.items()},
            "device_resolved": dev,
            "official_spoof_class_index": OFFICIAL_SPOOF_CLASS_INDEX,
            "checkpoint_load": checkpoint_load,
        },
    )

    _print_run_summary(cfg, dev, train_row_count, val_row_count, checkpoint_load)

    train_ds = AasistFineTuneDataset(train_df, nb_samp=nb_samp, limit=cfg.limit_train)
    val_ds = AasistFineTuneDataset(val_df, nb_samp=nb_samp, limit=cfg.limit_val)

    # Sampler (balances aasist_label exposure; does not apply sample_weight here)
    sampler = None
    if cfg.balanced_sampler:
        y = train_df["aasist_label"].astype(int).to_numpy()
        if cfg.limit_train is not None:
            y = y[: int(cfg.limit_train)]
        w = _balanced_sampler_weights(y)
        sampler = WeightedRandomSampler(weights=torch.from_numpy(w).double(), num_samples=len(w), replacement=True)

    train_loader = DataLoader(
        train_ds,
        batch_size=cfg.batch_size,
        shuffle=(sampler is None),
        sampler=sampler,
        num_workers=cfg.num_workers,
        collate_fn=_collate,
        pin_memory=(dev == "cuda"),
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=max(1, min(32, cfg.batch_size * 2)),
        shuffle=False,
        num_workers=cfg.num_workers,
        collate_fn=_collate,
        pin_memory=(dev == "cuda"),
    )

    # Loss
    ce = nn.CrossEntropyLoss(reduction="none")
    class_weights_t = None
    if cfg.class_balanced_loss:
        # Optional: class-balanced loss via inverse frequency on train set.
        counts = Counter(train_df["aasist_label"].astype(int).tolist())
        w0 = 1.0 / float(counts.get(0, 1))
        w1 = 1.0 / float(counts.get(1, 1))
        class_weights_t = torch.tensor([w0, w1], dtype=torch.float32, device=dev)

    opt = torch.optim.AdamW(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)
    scaler = torch.cuda.amp.GradScaler(enabled=(cfg.amp and dev == "cuda"))

    log_path = out_dir / "training_log.csv"
    log_fields = [
        "epoch",
        "train_loss",
        "val_loss",
        "val_accuracy",
        "val_product_score",
        "val_clean_human_false_alarm_count",
        "val_clean_human_false_alarm_rate",
        "val_clean_human_accept_count",
        "val_direct_ai_detect_count",
        "val_ai_replay_detect_count",
        "val_human_replay_detect_count",
        "val_human_mixer_detect_count",
        "val_ai_mixer_detect_count",
        "val_partial_detect_count",
        "learning_rate",
    ]
    with log_path.open("w", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=log_fields).writeheader()

    best_loss = math.inf
    best_product = -math.inf
    best_loss_meta: dict[str, Any] | None = None
    best_product_meta: dict[str, Any] | None = None

    epochs_no_improve = 0
    use_amp = bool(cfg.amp and dev == "cuda")

    for epoch in range(1, cfg.epochs + 1):
        model.train()

        # Optional freeze (best-effort; depends on vendor module names).
        if epoch <= cfg.freeze_frontend_epochs:
            for name, p in model.named_parameters():
                if any(k in name.lower() for k in ("frontend", "feature", "spec")):
                    p.requires_grad_(False)
        else:
            for p in model.parameters():
                p.requires_grad_(True)

        train_losses: list[float] = []
        for batch in train_loader:
            x = batch["x"].to(dev)
            y = batch["y"].to(dev)
            sw = batch["sample_weight"].to(dev)

            opt.zero_grad(set_to_none=True)
            if use_amp:
                with torch.cuda.amp.autocast(enabled=True):
                    logits = extract_aasist_logits(model(x))
                    per = ce(logits, y)
                    if class_weights_t is not None:
                        per = per * class_weights_t.gather(0, y)
                    if cfg.use_sample_weight:
                        per = per * sw
                    loss = per.mean()
                scaler.scale(loss).backward()
                scaler.unscale_(opt)
                torch.nn.utils.clip_grad_norm_(model.parameters(), cfg.grad_clip)
                scaler.step(opt)
                scaler.update()
            else:
                logits = extract_aasist_logits(model(x))
                per = ce(logits, y)
                if class_weights_t is not None:
                    per = per * class_weights_t.gather(0, y)
                if cfg.use_sample_weight:
                    per = per * sw
                loss = per.mean()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), cfg.grad_clip)
                opt.step()
            train_losses.append(float(loss.detach().cpu().item()))

        train_loss = float(np.mean(train_losses)) if train_losses else float("nan")

        # Validation
        model.eval()
        val_losses: list[float] = []
        correct = 0
        total = 0
        all_roles: list[str] = []
        all_scores: list[float] = []
        all_y: list[int] = []

        softmax = nn.Softmax(dim=1)
        for batch in val_loader:
            x = batch["x"].to(dev)
            y = batch["y"].to(dev)
            sw = batch["sample_weight"].to(dev)
            roles = batch["roles"]

            with torch.no_grad():
                logits = extract_aasist_logits(model(x))
                per = ce(logits, y)
                if class_weights_t is not None:
                    per = per * class_weights_t.gather(0, y)
                if cfg.use_sample_weight:
                    per = per * sw
                val_losses.append(float(per.mean().detach().cpu().item()))

                probs = softmax(logits)
                # spoof_score = softmax(class spoof_index=0)
                spoof_score = probs[:, OFFICIAL_SPOOF_CLASS_INDEX].detach().cpu().numpy().astype(np.float64)
                pred = probs.argmax(dim=1)
                correct += int((pred == y).sum().cpu().item())
                total += int(y.numel())

            all_roles.extend([str(r) for r in roles])
            all_scores.extend([float(s) for s in spoof_score.tolist()])
            all_y.extend([int(v) for v in y.detach().cpu().tolist()])

        val_loss = float(np.mean(val_losses)) if val_losses else float("nan")
        val_acc = float(correct / total) if total > 0 else 0.0
        role_metrics = _compute_role_rates(all_roles, all_y, all_scores, threshold=0.5)

        lr_now = float(opt.param_groups[0]["lr"])

        row = {
            "epoch": epoch,
            "train_loss": train_loss,
            "val_loss": val_loss,
            "val_accuracy": val_acc,
            "learning_rate": lr_now,
            **{k: role_metrics.get(k) for k in log_fields if k.startswith("val_") and k in role_metrics},
        }
        with log_path.open("a", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=log_fields).writerow(row)

        # Always save epoch checkpoint
        epoch_ckpt = ckpt_dir / f"aasist_l_phase7e3c_epoch_{epoch:02d}.pth"
        torch.save({"model_state_dict": model.state_dict(), "epoch": epoch, "run_config": config}, epoch_ckpt)
        torch.save({"model_state_dict": model.state_dict(), "epoch": epoch, "run_config": config}, ckpt_dir / "aasist_l_phase7e3c_last.pth")

        # Best-loss selection
        if val_loss < best_loss:
            best_loss = val_loss
            best_loss_meta = {
                "epoch": epoch,
                "val_loss": val_loss,
                "val_product_score": float(role_metrics["val_product_score"]),
                "checkpoint_path": str(ckpt_dir / "aasist_l_phase7e3c_best_loss.pth"),
            }
            torch.save(
                {"model_state_dict": model.state_dict(), "epoch": epoch, "run_config": config, "metrics": row},
                ckpt_dir / "aasist_l_phase7e3c_best_loss.pth",
            )

        # Best-product selection + early stopping
        product = float(role_metrics["val_product_score"])
        improved = product > best_product + 1e-6
        if improved:
            best_product = product
            best_product_meta = {
                "epoch": epoch,
                "val_loss": val_loss,
                "val_product_score": product,
                "checkpoint_path": str(ckpt_dir / "aasist_l_phase7e3c_best_product.pth"),
            }
            torch.save(
                {"model_state_dict": model.state_dict(), "epoch": epoch, "run_config": config, "metrics": row},
                ckpt_dir / "aasist_l_phase7e3c_best_product.pth",
            )
            epochs_no_improve = 0
        else:
            epochs_no_improve += 1

        if epochs_no_improve >= cfg.patience:
            warnings.append(f"early_stopping: no product improvement for {cfg.patience} epochs")
            break

    # Export best checkpoint metrics
    best_metrics = {"best_loss": best_loss_meta, "best_product": best_product_meta}
    write_json(out_dir / "best_checkpoint_metrics.json", best_metrics)
    _write_training_summary(out_dir, cfg, best_loss_meta, best_product_meta, warnings, checkpoint_load)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

