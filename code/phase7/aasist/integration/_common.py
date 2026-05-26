"""
Shared helpers for Phase 7E1–7E3A AASIST integration scripts.

Used by: build/run/analyze/compare scripts and aasist_eval_common.py
- REPO_ROOT resolution
- Path helpers (resolve_path, ensure_dir)
- JSON/markdown writers
- AASIST vendor sys.path injection (add_aasist_src_to_path)
- GPU/VRAM snapshots for eval logs
"""

from __future__ import annotations

import ast
import importlib
import importlib.util
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

# code/phase7/aasist/integration/_common.py -> repo root is parents[4]
REPO_ROOT = Path(__file__).resolve().parents[4]

SEARCH_SYMBOLS = (
    "AASIST",
    "Model",
    "AASISTModel",
    "RawNet",
    "forward",
    "inference",
)

CONFIG_EXTENSIONS = {".yaml", ".yml", ".json", ".conf", ".cfg", ".ini"}
CHECKPOINT_EXTENSIONS = {".pth", ".pt", ".ckpt", ".bin", ".tar", ".tar.gz"}
AUDIO_EXTENSIONS = {".wav", ".flac", ".mp3", ".ogg"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def resolve_path(path: str | Path, *, base: Path | None = None) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p.resolve()
    root = base or REPO_ROOT
    return (root / p).resolve()


def write_json(path: Path, data: Any) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def write_markdown(path: Path, lines: Iterable[str]) -> None:
    ensure_dir(path.parent)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def add_aasist_src_to_path(aasist_src: Path | None) -> list[str]:
    """Prepend aasist_src to sys.path if it exists. Returns notes."""
    notes: list[str] = []
    if aasist_src is None or not aasist_src.is_dir():
        return notes
    src = str(aasist_src.resolve())
    if src not in sys.path:
        sys.path.insert(0, src)
        notes.append(f"sys.path.insert(0, {src!r})")
    return notes


def try_import_installed_aasist() -> dict[str, Any]:
    """Mode B: check if any installed package exposes AASIST-like symbols."""
    out: dict[str, Any] = {"attempts": [], "found": False}
    candidates = ("aasist", "AASIST", "anti_spoofing")
    for name in candidates:
        spec = importlib.util.find_spec(name)  # type: ignore[attr-defined]
        entry = {"module": name, "spec_found": spec is not None}
        if spec is not None:
            try:
                mod = importlib.import_module(name)
                entry["imported"] = True
                entry["file"] = getattr(mod, "__file__", None)
                for sym in ("AASIST", "Model", "AASISTModel"):
                    if hasattr(mod, sym):
                        entry["symbol"] = sym
                        out["found"] = True
            except Exception as e:  # noqa: BLE001
                entry["imported"] = False
                entry["error"] = repr(e)
        out["attempts"].append(entry)
    return out


def list_python_files(root: Path, *, max_files: int = 500) -> list[Path]:
    if not root.is_dir():
        return []
    files: list[Path] = []
    for p in root.rglob("*.py"):
        if any(part.startswith(".") for part in p.parts):
            continue
        if "__pycache__" in p.parts:
            continue
        files.append(p)
        if len(files) >= max_files:
            break
    return sorted(files)


def list_files_by_extensions(root: Path, extensions: set[str], *, max_files: int = 200) -> list[Path]:
    if not root.is_dir():
        return []
    out: list[Path] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() in extensions or "".join(p.suffixes).lower() in extensions:
            out.append(p)
            if len(out) >= max_files:
                break
    return sorted(out)


def grep_symbols_in_file(path: Path, symbols: tuple[str, ...] = SEARCH_SYMBOLS) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    hits = []
    for sym in symbols:
        if re.search(rf"\b{re.escape(sym)}\b", text):
            hits.append(sym)
    return hits


def find_classes_in_py(path: Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"), filename=str(path))
    except (OSError, SyntaxError):
        return []
    return [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]


def module_name_from_path(root: Path, py_file: Path) -> str:
    rel = py_file.relative_to(root)
    parts = list(rel.parts[:-1]) + [rel.stem]
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts) if parts else rel.stem


def discover_model_candidates(root: Path) -> list[dict[str, Any]]:
    """Find Python modules with AASIST-like class names (AST only, no import)."""
    candidates: list[dict[str, Any]] = []
    target_names = {"AASIST", "Model", "AASISTModel", "RawNet2", "RawNet"}
    for py in list_python_files(root):
        classes = find_classes_in_py(py)
        matched = [c for c in classes if c in target_names or "AASIST" in c or "aasist" in c.lower()]
        if matched or any(s in grep_symbols_in_file(py) for s in ("AASIST", "AASISTModel")):
            candidates.append(
                {
                    "file": str(py.relative_to(root)).replace("\\", "/"),
                    "module": module_name_from_path(root, py),
                    "classes": classes,
                    "matched_classes": matched,
                    "symbol_hits": grep_symbols_in_file(py),
                }
            )
    return candidates


def read_text_snippet(path: Path, max_chars: int = 8000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:max_chars]
    except OSError:
        return ""


def extract_io_hints_from_text(text: str) -> dict[str, list[str]]:
    hints: dict[str, list[str]] = {
        "sample_rate": [],
        "input_length": [],
        "n_fft": [],
        "labels": [],
        "checkpoint_keys": [],
    }
    patterns = {
        "sample_rate": [
            r"sample_rate['\"]?\s*[:=]\s*(\d+)",
            r"sr['\"]?\s*[:=]\s*(\d+)",
            r"(\d{4,6})\s*#\s*sample",
        ],
        "input_length": [
            r"(?:num_samples|input_length|max_len|seq_len)['\"]?\s*[:=]\s*(\d+)",
        ],
        "n_fft": [r"n_fft['\"]?\s*[:=]\s*(\d+)"],
        "labels": [
            r"bonafide",
            r"spoof",
            r"label",
        ],
        "checkpoint_keys": [
            r"load_state_dict",
            r"state_dict",
            r"checkpoint",
        ],
    }
    for key, pats in patterns.items():
        for pat in pats:
            for m in re.finditer(pat, text, re.IGNORECASE):
                hints[key].append(m.group(0) if key == "labels" or key == "checkpoint_keys" else m.group(1))
    return hints


def safe_import_module(module_name: str) -> tuple[Any | None, str | None]:
    try:
        return importlib.import_module(module_name), None
    except Exception as e:  # noqa: BLE001
        return None, repr(e)


def try_instantiate_class(cls: type, config_path: Path | None) -> tuple[Any | None, str | None]:
    """Try common constructor patterns without training."""
    attempts: list[str] = []

    def _try(fn, label: str):
        try:
            return fn(), None
        except Exception as e:  # noqa: BLE001
            attempts.append(f"{label}: {e!r}")
            return None, None

    if config_path and config_path.is_file():
        for label, fn in [
            ("cls(config_path)", lambda: cls(str(config_path))),
            ("cls(config)", lambda: cls(str(config_path))),
        ]:
            obj, _ = _try(fn, label)
            if obj is not None:
                return obj, None

    for label, fn in [
        ("cls()", lambda: cls()),
        ("cls({})", lambda: cls({})),
    ]:
        obj, _ = _try(fn, label)
        if obj is not None:
            return obj, None

    return None, "; ".join(attempts) if attempts else "instantiation_failed"


def try_load_checkpoint(model: Any, checkpoint_path: Path, device: str) -> tuple[bool, str | None]:
    try:
        import torch
    except ImportError:
        return False, "torch_not_installed"

    try:
        ckpt = torch.load(str(checkpoint_path), map_location=device, weights_only=False)
    except TypeError:
        ckpt = torch.load(str(checkpoint_path), map_location=device)
    except Exception as e:  # noqa: BLE001
        return False, f"load_failed: {e!r}"

    state = ckpt
    if isinstance(ckpt, dict):
        for key in ("model", "model_state_dict", "state_dict", "net", "generator"):
            if key in ckpt and isinstance(ckpt[key], dict):
                state = ckpt[key]
                break

    if hasattr(model, "load_state_dict") and isinstance(state, dict):
        try:
            model.load_state_dict(state, strict=False)
            return True, None
        except Exception as e:  # noqa: BLE001
            return False, f"state_dict_load: {e!r}"
    return False, "no_compatible_load_state_dict"


def try_dummy_forward(model: Any, device: str) -> tuple[bool, str | None, dict[str, Any]]:
    import torch

    meta: dict[str, Any] = {}
    model_dev = model
    if hasattr(model, "to"):
        try:
            model_dev = model.to(device)
        except Exception as e:  # noqa: BLE001
            return False, f"model.to: {e!r}", meta

    # Common anti-spoof input shapes: [B, T] or [B, 1, T]
    shapes = [
        (1, 64600),
        (1, 1, 64600),
        (1, 48000),
        (1, 1, 48000),
    ]
    errors: list[str] = []
    for shape in shapes:
        x = torch.randn(*shape, device=device if device == "cuda" and torch.cuda.is_available() else "cpu")
        try:
            if hasattr(model_dev, "forward"):
                with torch.no_grad():
                    y = model_dev(x)
                meta["input_shape"] = list(shape)
                meta["output_type"] = type(y).__name__
                if hasattr(y, "shape"):
                    meta["output_shape"] = list(y.shape)
                return True, None, meta
        except Exception as e:  # noqa: BLE001
            errors.append(f"shape{shape}: {e!r}")
    return False, "; ".join(errors[:3]), meta


def collect_gpu_info() -> dict[str, Any]:
    info: dict[str, Any] = {"cuda_available": False}
    try:
        import torch

        info["torch_version"] = torch.__version__
        info["cuda_available"] = bool(torch.cuda.is_available())
        if torch.cuda.is_available():
            info["cuda_version"] = getattr(torch.version, "cuda", None)
            info["device_count"] = torch.cuda.device_count()
            info["gpu_name"] = torch.cuda.get_device_name(0)
            props = torch.cuda.get_device_properties(0)
            info["gpu_total_memory_gb"] = round(props.total_memory / (1024**3), 3)
            try:
                free, total = torch.cuda.mem_get_info(0)
                info["gpu_free_memory_gb"] = round(free / (1024**3), 3)
            except Exception as e:  # noqa: BLE001
                info["mem_get_info_error"] = str(e)
    except ImportError:
        info["torch_installed"] = False
    return info


def vram_snapshot() -> dict[str, Any]:
    snap: dict[str, Any] = {}
    try:
        import torch

        if torch.cuda.is_available():
            snap["allocated_gb"] = round(torch.cuda.memory_allocated() / (1024**3), 4)
            snap["reserved_gb"] = round(torch.cuda.memory_reserved() / (1024**3), 4)
    except Exception:
        pass
    return snap
