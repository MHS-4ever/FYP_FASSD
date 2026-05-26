"""
Phase 7E1: AASIST import / instantiation / forward smoke test (official vendor path).

Uses models.AASIST.Model(d_args) with config["model_config"] — does not run main.py.
Does not train or download datasets.
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path
from typing import Any

from _common import (
    REPO_ROOT,
    add_aasist_src_to_path,
    collect_gpu_info,
    resolve_path,
    try_import_installed_aasist,
    utc_now_iso,
    vram_snapshot,
    write_json,
    write_markdown,
)

OFFICIAL_MODEL_MODULE = "models.AASIST"
OFFICIAL_MODEL_CLASS = "Model"


def _variant_defaults(variant: str) -> tuple[str, str]:
    if variant == "AASIST":
        return "config/AASIST.conf", "models/weights/AASIST.pth"
    return "config/AASIST-L.conf", "models/weights/AASIST-L.pth"


def _resolve_config_path(
    aasist_src: Path,
    variant: str,
    config_path: Path | None,
) -> Path | None:
    if config_path and config_path.is_file():
        return config_path
    for rel in _variant_defaults(variant)[0], "config/AASIST-L.conf", "config/AASIST.conf":
        candidate = aasist_src / rel
        if candidate.is_file():
            return candidate
    return None


def _resolve_checkpoint_path(
    aasist_src: Path,
    variant: str,
    checkpoint_path: Path | None,
) -> Path | None:
    if checkpoint_path and checkpoint_path.is_file():
        return checkpoint_path
    for rel in _variant_defaults(variant)[1], "models/weights/AASIST-L.pth", "models/weights/AASIST.pth":
        candidate = aasist_src / rel
        if candidate.is_file():
            return candidate
    return None


def _load_config_json(config_path: Path) -> tuple[dict[str, Any] | None, dict[str, Any], str | None]:
    meta: dict[str, Any] = {"config_path": str(config_path)}
    try:
        with config_path.open("r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:  # noqa: BLE001
        return None, meta, f"config_load_failed: {e!r}"

    if "model_config" not in config:
        return None, meta, "config_missing_model_config_key"

    meta["model_config_keys"] = list(config["model_config"].keys())
    meta["architecture"] = config["model_config"].get("architecture")
    return config, meta, None


def _import_official_model(aasist_src: Path, model_config: dict[str, Any]) -> tuple[Any | None, dict[str, Any], str | None]:
    import importlib

    meta: dict[str, Any] = {
        "model_module": OFFICIAL_MODEL_MODULE,
        "model_class": OFFICIAL_MODEL_CLASS,
    }
    path_notes = add_aasist_src_to_path(aasist_src)
    meta["sys_path_notes"] = path_notes

    try:
        mod = importlib.import_module(OFFICIAL_MODEL_MODULE)
    except Exception as e:  # noqa: BLE001
        return None, meta, f"import_failed: {e!r}"

    ModelCls = getattr(mod, OFFICIAL_MODEL_CLASS, None)
    if ModelCls is None:
        return None, meta, f"class_{OFFICIAL_MODEL_CLASS}_not_found"

    try:
        model = ModelCls(model_config)
    except Exception as e:  # noqa: BLE001
        return None, meta, f"instantiate_failed: {e!r}"

    meta["instantiation"] = "Model(model_config)"
    return model, meta, None


def _load_aasist_checkpoint(
    model: Any,
    checkpoint_path: Path,
    device: str,
) -> dict[str, Any]:
    import torch

    out: dict[str, Any] = {
        "checkpoint_path": str(checkpoint_path),
        "checkpoint_load_status": "not_attempted",
        "missing_keys_count": None,
        "unexpected_keys_count": None,
        "missing_keys_sample": [],
        "unexpected_keys_sample": [],
    }
    dev = device if device == "cuda" and torch.cuda.is_available() else "cpu"
    try:
        try:
            ckpt = torch.load(str(checkpoint_path), map_location=dev, weights_only=False)
        except TypeError:
            ckpt = torch.load(str(checkpoint_path), map_location=dev)
    except Exception as e:  # noqa: BLE001
        out["checkpoint_load_status"] = "load_failed"
        out["error"] = repr(e)
        return out

    state = ckpt
    if isinstance(ckpt, dict):
        for key in ("model_state_dict", "state_dict", "model", "net"):
            if key in ckpt and isinstance(ckpt[key], dict):
                state = ckpt[key]
                out["state_dict_key"] = key
                break
        if state is ckpt and all(isinstance(k, str) for k in ckpt.keys()):
            # raw state_dict
            state = ckpt
            out["state_dict_key"] = "root"

    if not isinstance(state, dict):
        out["checkpoint_load_status"] = "not_a_state_dict"
        out["error"] = f"unexpected_checkpoint_type:{type(ckpt).__name__}"
        return out

    try:
        incompatible = model.load_state_dict(state, strict=False)
        missing = list(incompatible.missing_keys)
        unexpected = list(incompatible.unexpected_keys)
        out["missing_keys_count"] = len(missing)
        out["unexpected_keys_count"] = len(unexpected)
        out["missing_keys_sample"] = missing[:20]
        out["unexpected_keys_sample"] = unexpected[:20]
        if missing or unexpected:
            out["checkpoint_load_status"] = "loaded_with_mismatch"
        else:
            out["checkpoint_load_status"] = "loaded_ok"
    except Exception as e:  # noqa: BLE001
        out["checkpoint_load_status"] = "state_dict_failed"
        out["error"] = repr(e)

    return out


def _run_official_forward(
    model: Any,
    x: Any,
) -> tuple[bool, dict[str, Any], str | None]:
    import torch

    meta: dict[str, Any] = {"dummy_input_shape": list(x.shape)}
    try:
        model.eval()
        with torch.no_grad():
            out = model(x)
        if isinstance(out, tuple) and len(out) == 2:
            last_hidden, output = out
            meta["output_tuple"] = True
            meta["last_hidden_shape"] = list(last_hidden.shape) if hasattr(last_hidden, "shape") else None
            meta["output_shape"] = list(output.shape) if hasattr(output, "shape") else None
            y = output
        else:
            meta["output_tuple"] = False
            y = out
            meta["output_shape"] = list(y.shape) if hasattr(y, "shape") else None

        if hasattr(y, "shape") and len(y.shape) == 2 and y.shape[-1] == 2:
            meta["forward_success"] = True
            meta["output_is_batch_x_2"] = True
            return True, meta, None

        meta["forward_success"] = True
        meta["output_is_batch_x_2"] = False
        return True, meta, f"unexpected_output_shape:{meta.get('output_shape')}"
    except Exception as e:  # noqa: BLE001
        meta["forward_success"] = False
        return False, meta, f"forward_failed: {e!r}"


def _load_audio_tensor(audio_path: Path, nb_samp: int) -> tuple[Any | None, dict[str, Any], str | None]:
    """Load waveform and trim/pad to nb_samp for official AASIST input [B, T]."""
    import torch

    meta: dict[str, Any] = {"audio_path": str(audio_path), "nb_samp": nb_samp}
    torchaudio = None
    try:
        import torchaudio as _torchaudio  # type: ignore[import-untyped]

        torchaudio = _torchaudio
    except Exception as e:  # noqa: BLE001
        meta["torchaudio_import_unavailable"] = repr(e)

    x = None
    if torchaudio is not None:
        try:
            wav, sr = torchaudio.load(str(audio_path))
            if wav.shape[0] > 1:
                wav = wav.mean(dim=0, keepdim=True)
            x = wav.squeeze(0)
            meta["loader"] = "torchaudio"
            meta["sample_rate"] = int(sr)
        except Exception as e:  # noqa: BLE001
            meta["torchaudio_load_failed"] = repr(e)

    if x is None:
        try:
            import soundfile as sf

            wav, sr = sf.read(str(audio_path), dtype="float32")
            if wav.ndim > 1:
                wav = wav.mean(axis=1)
            x = torch.from_numpy(wav)
            meta["loader"] = "soundfile"
            meta["sample_rate"] = int(sr)
        except Exception as e:  # noqa: BLE001
            return None, meta, f"audio_load_failed: {e!r}"

    if x.numel() >= nb_samp:
        x = x[:nb_samp]
    else:
        pad = nb_samp - x.numel()
        x = torch.nn.functional.pad(x, (0, pad))
    x = x.unsqueeze(0)
    meta["padded_or_trimmed_to_nb_samp"] = True
    return x, meta, None


def _next_action_for_verdict(verdict: str) -> str:
    actions = {
        "PASS": "Proceed to Phase 7E2 dataset adapter; optional 7E3A pretrained eval with same config/checkpoint.",
        "PASS_NO_CHECKPOINT": "Provide or verify pretrained weights for 7E3A; 7E2 adapter can proceed if import/forward OK.",
        "CONFIG_REQUIRED": "Fix --config_path or place config under vendor/AASIST/config/.",
        "CHECKPOINT_LOAD_WARNING": "Forward works; fix checkpoint path or key mismatch before 7E3A.",
        "FAILED": "Fix import/instantiation/forward; check (fassd) env and vendor/AASIST tree.",
        "SOURCE_REQUIRED": "Clone official AASIST into code/phase7/aasist/vendor/AASIST.",
    }
    return actions.get(verdict, "Review phase7e1_smoke_test_report.md")


def run_smoke_test(
    aasist_src: Path | None,
    *,
    model_variant: str,
    config_path: Path | None,
    checkpoint_path: Path | None,
    audio_path: Path | None,
    device: str,
    dummy_only: bool,
    allow_missing_source: bool,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "timestamp_utc": utc_now_iso(),
        "python_executable": sys.executable,
        "repo_root": str(REPO_ROOT),
        "aasist_src": str(aasist_src) if aasist_src else None,
        "model_variant": model_variant,
        "config_path": None,
        "checkpoint_path": None,
        "nb_samp": None,
        "model_module": OFFICIAL_MODEL_MODULE,
        "model_class": OFFICIAL_MODEL_CLASS,
        "checkpoint_load_status": "not_attempted",
        "missing_keys_count": None,
        "unexpected_keys_count": None,
        "dummy_input_shape": None,
        "output_shape": None,
        "forward_success": False,
        "device_requested": device,
        "dummy_only": dummy_only,
        "gpu": collect_gpu_info(),
        "vram_before": vram_snapshot(),
        "vram_after": {},
        "errors": [],
        "verdict": "SOURCE_REQUIRED",
        "next_action": "",
    }

    if device == "cuda" and not result["gpu"].get("cuda_available"):
        result["errors"].append("cuda_requested_but_unavailable")
        result["verdict"] = "FAILED"
        result["next_action"] = _next_action_for_verdict("FAILED")
        return result

    result["mode_b_installed"] = try_import_installed_aasist()

    if not aasist_src or not aasist_src.is_dir():
        result["user_actions"] = [
            "Place official AASIST source in code/phase7/aasist/vendor/AASIST",
            "Re-run with --model_variant AASIST-L",
        ]
        if not allow_missing_source:
            result["exit_code_hint"] = 1
        result["next_action"] = _next_action_for_verdict("SOURCE_REQUIRED")
        return result

    resolved_config = _resolve_config_path(aasist_src, model_variant, config_path)
    resolved_ckpt = _resolve_checkpoint_path(aasist_src, model_variant, checkpoint_path)

    result["config_path"] = str(resolved_config) if resolved_config else None
    result["checkpoint_path"] = str(resolved_ckpt) if resolved_ckpt else None

    if not resolved_config:
        result["verdict"] = "CONFIG_REQUIRED"
        result["errors"].append("config_not_found")
        result["next_action"] = _next_action_for_verdict("CONFIG_REQUIRED")
        return result

    config, cfg_meta, cfg_err = _load_config_json(resolved_config)
    result["config_load"] = cfg_meta
    if cfg_err or config is None:
        result["verdict"] = "CONFIG_REQUIRED"
        result["errors"].append(cfg_err or "config_load_failed")
        result["next_action"] = _next_action_for_verdict("CONFIG_REQUIRED")
        return result

    model_config = config["model_config"]
    if model_config.get("architecture") != "AASIST":
        result["errors"].append(f"unexpected_architecture:{model_config.get('architecture')}")

    nb_samp = int(model_config.get("nb_samp", 64600))
    result["nb_samp"] = nb_samp

    model, inst_meta, inst_err = _import_official_model(aasist_src, model_config)
    result["instantiation"] = inst_meta
    if inst_err or model is None:
        result["verdict"] = "FAILED"
        result["errors"].append(inst_err or "model_instantiation_failed")
        result["next_action"] = _next_action_for_verdict("FAILED")
        return result

    import torch

    dev = device if device == "cuda" and torch.cuda.is_available() else "cpu"
    model = model.to(dev)
    result["instantiation"]["device"] = dev

    ckpt_requested = checkpoint_path is not None and str(checkpoint_path) != ""
    ckpt_loaded = False
    ckpt_warning = False

    if resolved_ckpt:
        ck_detail = _load_aasist_checkpoint(model, resolved_ckpt, device)
        result["checkpoint_load"] = ck_detail
        result["checkpoint_load_status"] = ck_detail.get("checkpoint_load_status")
        result["missing_keys_count"] = ck_detail.get("missing_keys_count")
        result["unexpected_keys_count"] = ck_detail.get("unexpected_keys_count")
        status = ck_detail.get("checkpoint_load_status")
        if status == "loaded_ok":
            ckpt_loaded = True
        elif status == "loaded_with_mismatch":
            ckpt_loaded = True
            ckpt_warning = True
        elif ckpt_requested:
            ckpt_warning = True
    else:
        result["checkpoint_load_status"] = "not_provided"
        result["checkpoint_load"] = {"note": "no checkpoint file found or provided"}

    # Forward
    if audio_path and audio_path.is_file() and not dummy_only:
        x, audio_meta, audio_err = _load_audio_tensor(audio_path, nb_samp)
        result["forward"] = {"mode": "audio", "audio_meta": audio_meta}
        if audio_err or x is None:
            result["verdict"] = "FAILED"
            result["errors"].append(audio_err or "audio_load_failed")
        else:
            x = x.to(dev)
            ok, fwd_meta, fwd_err = _run_official_forward(model, x)
            result["forward"].update(fwd_meta)
            result["dummy_input_shape"] = fwd_meta.get("dummy_input_shape")
            result["output_shape"] = fwd_meta.get("output_shape")
            result["forward_success"] = ok and fwd_meta.get("output_is_batch_x_2", False)
            if not result["forward_success"]:
                result["errors"].append(fwd_err or "forward_or_shape_failed")
    else:
        x = torch.randn(1, nb_samp, device=dev)
        ok, fwd_meta, fwd_err = _run_official_forward(model, x)
        result["forward"] = {"mode": "dummy", **fwd_meta}
        result["dummy_input_shape"] = fwd_meta.get("dummy_input_shape")
        result["output_shape"] = fwd_meta.get("output_shape")
        result["forward_success"] = ok and fwd_meta.get("output_is_batch_x_2", False)
        if not result["forward_success"]:
            result["errors"].append(fwd_err or "forward_or_shape_failed")

    result["vram_after"] = vram_snapshot()

    if not result["forward_success"]:
        result["verdict"] = "FAILED"
    elif ckpt_warning:
        result["verdict"] = "CHECKPOINT_LOAD_WARNING"
    elif ckpt_loaded:
        result["verdict"] = "PASS"
    else:
        result["verdict"] = "PASS_NO_CHECKPOINT"

    result["next_action"] = _next_action_for_verdict(result["verdict"])
    return result


def _md(data: dict[str, Any]) -> list[str]:
    lines = [
        "# Phase 7E1 — AASIST Smoke Test",
        "",
        f"**Generated:** {data['timestamp_utc']}  ",
        f"**Verdict:** `{data.get('verdict')}`  ",
        f"**Next action:** {data.get('next_action', '')}  ",
        "",
        "## Summary",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| model_variant | `{data.get('model_variant')}` |",
        f"| config_path | `{data.get('config_path') or '-'}` |",
        f"| checkpoint_path | `{data.get('checkpoint_path') or '-'}` |",
        f"| nb_samp | `{data.get('nb_samp')}` |",
        f"| model module/class | `{data.get('model_module')}.{data.get('model_class')}` |",
        f"| checkpoint_load_status | `{data.get('checkpoint_load_status')}` |",
        f"| missing_keys_count | `{data.get('missing_keys_count')}` |",
        f"| unexpected_keys_count | `{data.get('unexpected_keys_count')}` |",
        f"| dummy_input_shape | `{data.get('dummy_input_shape')}` |",
        f"| output_shape | `{data.get('output_shape')}` |",
        f"| forward_success | `{data.get('forward_success')}` |",
        "",
        "## Environment",
        "",
        f"| Python | `{data.get('python_executable')}` |",
        f"| PyTorch | `{data.get('gpu', {}).get('torch_version', 'N/A')}` |",
        f"| CUDA | `{data.get('gpu', {}).get('cuda_available')}` |",
        f"| GPU | `{data.get('gpu', {}).get('gpu_name', 'N/A')}` |",
        f"| VRAM before | `{data.get('vram_before')}` |",
        f"| VRAM after | `{data.get('vram_after')}` |",
        "",
    ]
    if data.get("errors"):
        lines.append("## Errors")
        for e in data["errors"]:
            lines.append(f"- {e}")
        lines.append("")
    if data.get("checkpoint_load"):
        lines.append("## Checkpoint load")
        lines.append("")
        lines.append(f"```json\n{json_pretty(data['checkpoint_load'])}\n```")
        lines.append("")
    if data.get("forward"):
        lines.append("## Forward")
        lines.append("")
        lines.append(f"```json\n{json_pretty(data['forward'])}\n```")
        lines.append("")
    return lines


def json_pretty(obj: Any) -> str:
    return json.dumps(obj, indent=2, default=str)


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 7E1 AASIST smoke test (official Model path)")
    parser.add_argument("--aasist_src", type=str, default="code/phase7/aasist/vendor/AASIST")
    parser.add_argument(
        "--output_dir",
        type=str,
        default="reports/phase7/phase7e_aasist_experiment/phase7e1_smoke_test",
    )
    parser.add_argument("--device", type=str, default="cuda", choices=("cuda", "cpu"))
    parser.add_argument("--config_path", type=str, default="")
    parser.add_argument("--checkpoint_path", type=str, default="")
    parser.add_argument("--audio_path", type=str, default="")
    parser.add_argument("--model_variant", type=str, default="AASIST-L", choices=("AASIST-L", "AASIST"))
    parser.add_argument("--dummy_only", action="store_true")
    parser.add_argument("--allow_missing_source", action="store_true")
    args = parser.parse_args()

    src = resolve_path(args.aasist_src)
    out = resolve_path(args.output_dir)
    config = resolve_path(args.config_path) if args.config_path else None
    ckpt = resolve_path(args.checkpoint_path) if args.checkpoint_path else None
    audio = resolve_path(args.audio_path) if args.audio_path else None

    try:
        data = run_smoke_test(
            src if src.is_dir() else None,
            model_variant=args.model_variant,
            config_path=config,
            checkpoint_path=ckpt,
            audio_path=audio if audio and audio.is_file() else None,
            device=args.device,
            dummy_only=args.dummy_only,
            allow_missing_source=args.allow_missing_source,
        )
    except Exception:
        data = {
            "timestamp_utc": utc_now_iso(),
            "verdict": "FAILED",
            "traceback": traceback.format_exc(),
            "next_action": _next_action_for_verdict("FAILED"),
        }

    write_json(out / "phase7e1_smoke_test_result.json", data)
    write_markdown(out / "phase7e1_smoke_test_report.md", _md(data))

    print(f"Phase 7E1 smoke test verdict: {data['verdict']}")
    print(f"Next action: {data.get('next_action', '')}")
    print(f"Wrote: {out / 'phase7e1_smoke_test_result.json'}")

    if data["verdict"] in ("FAILED", "CONFIG_REQUIRED") and not args.allow_missing_source:
        return 1
    if data["verdict"] == "SOURCE_REQUIRED" and not args.allow_missing_source:
        return 1
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    raise SystemExit(main())
