"""Phase 9A Gradio skeleton for local supervisor/demo testing."""

from __future__ import annotations

import gradio as gr

from src.inference_pipeline import run_inference_pipeline


def analyze(audio_path: str | None, case_id: str) -> tuple[str, dict]:
    result = run_inference_pipeline(audio_path=audio_path or "", case_id=case_id or None)
    summary = result.get("forensic_summary", "No summary available")
    return summary, result


def build_demo() -> gr.Blocks:
    with gr.Blocks(title="Audio Forensic Prototype - Phase 9A Skeleton") as demo:
        gr.Markdown(
            "## Experimental Forensic Prototype (Phase 9A Skeleton)\n"
            "Full inference is pending Phase 9B/9C."
        )
        with gr.Row():
            audio_input = gr.Audio(type="filepath", label="Upload audio")
            case_id_input = gr.Textbox(label="Optional case_id", placeholder="CASE-0001")
        run_btn = gr.Button("Analyze (placeholder)")
        summary_output = gr.Textbox(label="Forensic summary placeholder")
        json_output = gr.JSON(label="Structured response placeholder")
        run_btn.click(analyze, inputs=[audio_input, case_id_input], outputs=[summary_output, json_output])
    return demo


if __name__ == "__main__":
    # Do not auto-launch from imports. User runs manually later.
    demo_app = build_demo()
    demo_app.launch()
