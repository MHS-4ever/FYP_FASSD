#!/usr/bin/env python3
"""Phase 9E-P1 Gradio local demo over Phase 9C inference + P6 partial contract."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_APP_DIR = Path(__file__).resolve().parent
for _p in (_APP_DIR, _APP_DIR.parent / "partial_redesign"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from app_config import APP_NAME, APP_PHASE, get_analyze_audio_file, safety_banner
from report_formatting import (
    build_app_analyze_response,
    gradio_segment_table,
    gradio_user_summary,
)

try:
    import gradio as gr
except ImportError:  # pragma: no cover
    gr = None  # type: ignore


def analyze_upload(audio_path: str | None) -> tuple[str, dict[str, Any], list[list[Any]], dict[str, Any]]:
    if not audio_path:
        empty = {
            "processing_status": "error",
            "error_message": "No audio file provided.",
            "manual_review_required": True,
        }
        return "Upload an audio file to analyze.", empty, [], json.dumps(empty, indent=2)

    analyze_fn = get_analyze_audio_file()
    phase9c = analyze_fn(audio_path=audio_path, device="auto", return_debug=True)
    app_resp = build_app_analyze_response(
        file_name=Path(audio_path).name,
        phase9c_result=phase9c,
        return_top_segments=True,
    )
    summary = gradio_user_summary(app_resp)
    table = gradio_segment_table(app_resp)
    return summary, app_resp, table, app_resp.get("partial_fabrication", {})


def build_demo() -> Any:
    if gr is None:
        raise ImportError("gradio is not installed. Install with: pip install gradio")

    with gr.Blocks(title=APP_NAME) as demo:
        gr.Markdown(
            f"# {APP_NAME}\n\n"
            "**Experimental forensic evidence indicators for audio authenticity review.**\n\n"
            f"Phase: {APP_PHASE} · Partial module: experimental_manual_review_only · "
            "Conclusive authenticity decision: **no**"
        )
        with gr.Row():
            audio_input = gr.Audio(type="filepath", label="Upload audio")
        analyze_btn = gr.Button("Analyze", variant="primary")
        summary_out = gr.Markdown(label="User-facing summary")
        with gr.Row():
            json_out = gr.JSON(label="Full app JSON response")
            partial_json_out = gr.JSON(label="partial_fabrication section")
        segment_table = gr.Dataframe(
            headers=["rank", "start_sec", "end_sec", "probability", "manual_review_recommended"],
            label="Top candidate segments (experimental)",
            interactive=False,
        )
        gr.Markdown(
            "### Limitations\n\n"
            "- Experimental partial-fabrication evidence indicator only.\n"
            "- Manual forensic review is recommended.\n"
            "- Conclusive authenticity decision: no.\n"
            "- Known false negatives and false positives remain in held-out testing (see P6 metadata)."
        )
        gr.Markdown(f"```json\n{json.dumps(safety_banner(), indent=2)}\n```")
        analyze_btn.click(
            analyze_upload,
            inputs=[audio_input],
            outputs=[summary_out, json_out, segment_table, partial_json_out],
        )
    return demo


if __name__ == "__main__":
    demo_app = build_demo()
    demo_app.launch(server_name="127.0.0.1")
