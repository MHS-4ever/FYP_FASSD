"""Utility helpers for release skeleton."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import yaml


def make_case_id() -> str:
    return f"CASE-{uuid4().hex[:12].upper()}"


def safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_yaml_safe(path: str) -> dict:
    target = Path(path)
    if not target.exists():
        return {}
    data = yaml.safe_load(target.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}
