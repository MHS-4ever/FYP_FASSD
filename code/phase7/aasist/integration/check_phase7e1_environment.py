"""
Phase 7E1: Environment check for AASIST integration (no training).
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys
from pathlib import Path
from typing import Any

from _common import REPO_ROOT, collect_gpu_info, resolve_path, utc_now_iso, write_json, write_markdown

PACKAGES = (
    "torch",
    "numpy",
    "pandas",
    "librosa",
    "soundfile",
    "h5py",
    "yaml",
    "sklearn",
    "scipy",
)


def check_environment() -> dict[str, Any]:
    env: dict[str, Any] = {
        "timestamp_utc": utc_now_iso(),
        "repo_root": str(REPO_ROOT),
        "sys_executable": sys.executable,
        "python_version": sys.version,
        "cwd": os.getcwd(),
        "conda_env": os.environ.get("CONDA_DEFAULT_ENV"),
        "packages": {},
        "gpu": collect_gpu_info(),
        "verdict": "PASS",
        "issues": [],
    }

    for pkg in PACKAGES:
        spec = importlib.util.find_spec(pkg)
        entry: dict[str, Any] = {"installed": spec is not None}
        if spec is not None:
            try:
                mod = importlib.import_module(pkg)
                entry["version"] = getattr(mod, "__version__", "unknown")
            except Exception as e:  # noqa: BLE001
                entry["import_error"] = repr(e)
        env["packages"][pkg] = entry

    if not env["packages"]["torch"]["installed"]:
        env["verdict"] = "FAIL"
        env["issues"].append("torch_not_installed")
    elif not env["gpu"].get("cuda_available"):
        env["verdict"] = "FAIL"
        env["issues"].append("cuda_not_available")

    optional_missing = [p for p in ("librosa", "soundfile", "h5py") if not env["packages"][p]["installed"]]
    if optional_missing and env["verdict"] == "PASS":
        env["verdict"] = "PASS_WITH_WARNINGS"
        env["issues"].append(f"optional_missing:{','.join(optional_missing)}")

    return env


def _md(env: dict[str, Any]) -> list[str]:
    lines = [
        "# Phase 7E1 — Environment Check",
        "",
        f"**Generated:** {env['timestamp_utc']}  ",
        f"**Verdict:** `{env['verdict']}`  ",
        "",
        "## Python",
        "",
        f"| Item | Value |",
        f"|------|-------|",
        f"| Executable | `{env['sys_executable']}` |",
        f"| Version | `{env['python_version'].split()[0]}` |",
        f"| Conda env | `{env.get('conda_env') or '(not set)'}` |",
        f"| CWD | `{env['cwd']}` |",
        "",
        "## GPU / PyTorch",
        "",
        f"| Item | Value |",
        f"|------|-------|",
        f"| PyTorch | `{env['gpu'].get('torch_version', 'N/A')}` |",
        f"| CUDA | `{env['gpu'].get('cuda_available')}` |",
        f"| GPU | `{env['gpu'].get('gpu_name', 'N/A')}` |",
        f"| VRAM (total GB) | `{env['gpu'].get('gpu_total_memory_gb', 'N/A')}` |",
        "",
        "## Packages",
        "",
        "| Package | Installed | Version |",
        "|---------|-----------|---------|",
    ]
    for pkg, info in env["packages"].items():
        lines.append(f"| {pkg} | {info['installed']} | {info.get('version', '-')} |")
    if env.get("issues"):
        lines.extend(["", "## Issues", ""])
        for i in env["issues"]:
            lines.append(f"- {i}")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 7E1 environment check")
    parser.add_argument(
        "--output_dir",
        type=str,
        default="reports/phase7/phase7e_aasist_experiment/audit",
    )
    args = parser.parse_args()
    out = resolve_path(args.output_dir)
    env = check_environment()
    write_json(out / "phase7e1_environment_check.json", env)
    write_markdown(out / "phase7e1_environment_check.md", _md(env))
    print(f"Phase 7E1 environment verdict: {env['verdict']}")
    return 0 if env["verdict"] != "FAIL" else 1


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    raise SystemExit(main())
