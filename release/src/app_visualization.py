"""Phase 9E-P2: Waveform and timeline visualization (representation only; no inference changes)."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import numpy as np

from .audio_io import AudioLoadError, load_audio

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def format_time_mmss(seconds: float | None) -> str:
    if seconds is None:
        return "—"
    try:
        total = max(0, int(round(float(seconds))))
    except (TypeError, ValueError):
        return "—"
    minutes, secs = divmod(total, 60)
    return f"{minutes:02d}:{secs:02d}"


def _default_visual_output_dir() -> Path:
    out = _REPO_ROOT / "reports" / "phase9" / "app" / "sample_outputs" / "visuals"
    out.mkdir(parents=True, exist_ok=True)
    return out


def extract_candidate_segments(response: dict[str, Any]) -> list[dict[str, Any]]:
    segments: list[dict[str, Any]] = []
    pf = response.get("partial_fabrication") or {}
    cand = pf.get("candidate_segment") or {}
    if cand.get("start_sec") is not None and cand.get("end_sec") is not None:
        segments.append(
            {
                "rank": cand.get("rank", 1),
                "start_sec": float(cand["start_sec"]),
                "end_sec": float(cand["end_sec"]),
                "probability": cand.get("probability"),
            }
        )
    seen = {(s["start_sec"], s["end_sec"]) for s in segments}
    for row in pf.get("top_segments") or []:
        start = row.get("start_sec")
        end = row.get("end_sec")
        if start is None or end is None:
            continue
        key = (float(start), float(end))
        if key in seen:
            continue
        seen.add(key)
        segments.append(
            {
                "rank": row.get("rank"),
                "start_sec": float(start),
                "end_sec": float(end),
                "probability": row.get("probability"),
            }
        )
    for row in response.get("segment_candidates") or []:
        start = row.get("start_sec")
        end = row.get("end_sec")
        if start is None or end is None:
            continue
        key = (float(start), float(end))
        if key in seen:
            continue
        seen.add(key)
        segments.append(
            {
                "rank": row.get("candidate_rank", row.get("rank")),
                "start_sec": float(start),
                "end_sec": float(end),
                "probability": row.get("partial_probability", row.get("probability")),
            }
        )
    segments.sort(key=lambda s: (s.get("rank") or 999, s["start_sec"]))
    return segments


def _decimate(y: np.ndarray, max_points: int) -> tuple[np.ndarray, np.ndarray]:
    n = len(y)
    if n <= max_points:
        return np.arange(n, dtype=np.float64), y.astype(np.float64)
    step = max(1, n // max_points)
    idx = np.arange(0, n, step, dtype=np.int64)
    return idx.astype(np.float64), y[idx].astype(np.float64)


def generate_waveform_highlight(
    audio_path: str | None,
    response: dict[str, Any],
    output_dir: str | Path | None = None,
    max_points: int = 5000,
) -> str:
    """Render full waveform with highlighted candidate segment(s). Returns PNG path."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out_dir = Path(output_dir) if output_dir else _default_visual_output_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    png_path = out_dir / f"waveform_{uuid.uuid4().hex[:12]}.png"

    segments = extract_candidate_segments(response)
    audio_meta = response.get("audio_metadata") or {}
    duration = float(audio_meta.get("duration_sec") or 0.0)

    y: np.ndarray | None = None
    sr = 16000
    if audio_path:
        try:
            y, sr = load_audio(audio_path)
            duration = float(len(y) / sr) if sr > 0 else duration
        except (AudioLoadError, Exception):
            y = None

    fig, ax = plt.subplots(figsize=(10, 3.2), dpi=120)
    if y is not None and len(y) > 0 and duration > 0:
        t_idx, y_plot = _decimate(y, max_points)
        t_sec = t_idx / float(sr)
        ax.plot(t_sec, y_plot, color="#334155", linewidth=0.6, label="Audio waveform")
        highlighted = False
        for seg in segments:
            start = seg.get("start_sec")
            end = seg.get("end_sec")
            if start is None or end is None:
                continue
            ax.axvspan(
                float(start),
                float(end),
                color="#f97316",
                alpha=0.35,
                label="Highlighted suspicious segment" if not highlighted else None,
            )
            highlighted = True
        if not highlighted:
            ax.text(
                0.5,
                0.92,
                "No candidate segment highlighted",
                transform=ax.transAxes,
                ha="center",
                fontsize=9,
                color="#64748b",
            )
        ax.set_xlim(0.0, max(duration, t_sec[-1] if len(t_sec) else duration))
    else:
        ax.text(
            0.5,
            0.5,
            "Waveform unavailable — see timeline fallback",
            transform=ax.transAxes,
            ha="center",
            va="center",
            fontsize=10,
            color="#64748b",
        )
        ax.set_xlim(0.0, max(duration, 1.0))

    ax.set_xlabel("Time (seconds)")
    ax.set_ylabel("Amplitude")
    ax.set_title("Audio waveform")
    handles, labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(png_path, bbox_inches="tight")
    plt.close(fig)
    return str(png_path)


def generate_timeline_fallback(
    response: dict[str, Any],
    output_dir: str | Path | None = None,
) -> str:
    """Simple timeline image when waveform load/plot fails."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out_dir = Path(output_dir) if output_dir else _default_visual_output_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    png_path = out_dir / f"timeline_{uuid.uuid4().hex[:12]}.png"

    audio_meta = response.get("audio_metadata") or {}
    duration = float(audio_meta.get("duration_sec") or 1.0)
    segments = extract_candidate_segments(response)

    fig, ax = plt.subplots(figsize=(10, 1.8), dpi=120)
    ax.set_ylim(0, 1)
    ax.set_xlim(0, max(duration, 0.1))
    ax.axhline(0.5, color="#94a3b8", linewidth=4)
    if segments:
        for seg in segments:
            start = seg.get("start_sec")
            end = seg.get("end_sec")
            if start is None or end is None:
                continue
            ax.axvspan(float(start), float(end), color="#f97316", alpha=0.5)
            ax.text(
                (float(start) + float(end)) / 2,
                0.72,
                f"{format_time_mmss(start)} – {format_time_mmss(end)}",
                ha="center",
                fontsize=8,
            )
    else:
        ax.text(
            duration / 2,
            0.5,
            "No candidate segment highlighted",
            ha="center",
            va="center",
            fontsize=9,
            color="#64748b",
        )
    ax.set_xlabel("Time (seconds)")
    ax.set_title("Analysis timeline (fallback)")
    ax.set_yticks([])
    fig.tight_layout()
    fig.savefig(png_path, bbox_inches="tight")
    plt.close(fig)
    return str(png_path)
