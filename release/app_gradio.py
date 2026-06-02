"""Phase 9E Gradio — release app over Phase 9C inference + P6 partial contract."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.app_report_formatting import (
    APP_NAME,
    APP_PHASE,
    enrich_phase9c_response,
    gradio_segment_table,
    gradio_user_summary,
    safety_banner,
)
from src.inference_pipeline import analyze_audio_file

try:
    import gradio as gr
except ImportError:  # pragma: no cover
    gr = None  # type: ignore


def analyze(audio_path: str | None, case_id: str) -> tuple[str, dict[str, Any], list[list[Any]], dict[str, Any]]:
    if not audio_path:
        empty: dict[str, Any] = {
            "processing_status": "error",
            "error_message": "No audio file provided.",
            "manual_review_required": True,
        }
        return "Upload an audio file to analyze.", empty, [], {}

    phase9c = analyze_audio_file(
        audio_path=audio_path,
        case_id=case_id or None,
        device="auto",
        return_debug=True,
    )
    enriched = enrich_phase9c_response(
        phase9c,
        file_name=Path(audio_path).name,
        return_top_segments=True,
    )
    summary = gradio_user_summary(enriched)
    table = gradio_segment_table(enriched)
    partial_panel = enriched.get("partial_fabrication", {})
    return summary, enriched, table, partial_panel


def build_demo() -> Any:
    if gr is None:
        raise ImportError("gradio is not installed. Install with: pip install gradio")

    with gr.Blocks(title=APP_NAME) as demo:
        gr.Markdown(
            f"# {APP_NAME}\n\n"
            "**Experimental forensic evidence indicators for audio authenticity review.**\n\n"
            f"Phase: {APP_PHASE} · Release app path: `release/` · "
            "Partial module: experimental_manual_review_only · "
            "Conclusive authenticity decision: **no**"
        )
        with gr.Row():
            audio_input = gr.Audio(type="filepath", label="Upload audio")
            case_id_input = gr.Textbox(label="Optional case_id", placeholder="CASE-0001")
        run_btn = gr.Button("Analyze", variant="primary")
        summary_output = gr.Markdown(label="User-facing summary")
        with gr.Row():
            json_output = gr.JSON(label="Full structured response")
            partial_json_output = gr.JSON(label="partial_fabrication section")
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
            "- Known false negatives and false positives remain (see P6 package metadata)."
        )
        run_btn.click(
            analyze,
            inputs=[audio_input, case_id_input],
            outputs=[summary_output, json_output, segment_table, partial_json_output],
        )
    return demo


if __name__ == "__main__":
    demo_app = build_demo()
    demo_app.launch(server_name="127.0.0.1")
