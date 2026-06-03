"""Phase 9E-P2 Gradio — user-facing local demo over Phase 9C inference + P6 partial contract."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.app_report_formatting import (
    APP_NAME,
    APP_SUBTITLE,
    RESEARCH_PROJECT_NAME,
    build_evidence_axis_cards,
    build_user_result_summary,
    enrich_phase9c_response,
    gradio_output_dir,
    gradio_segments_section_heading,
    gradio_suspicious_segments_table,
    release_root,
    render_audio_overview,
    render_evidence_cards_html,
    render_main_result_card,
    render_technical_details,
    save_json_report,
)
from src.app_visualization import generate_timeline_fallback, generate_waveform_highlight
from src.inference_pipeline import analyze_audio_file
from src.pdf_report_generator import generate_pdf_report

try:
    import gradio as gr
except ImportError:  # pragma: no cover
    gr = None  # type: ignore


def _empty_outputs() -> tuple[Any, ...]:
    return (
        "",
        "",
        "",
        "### Candidate segments for review",
        None,
        [],
        None,
        None,
        {},
        {},
        "",
    )


def analyze(
    audio_path: str | None,
    case_id: str,
) -> tuple[Any, ...]:
    if not audio_path:
        return _empty_outputs()

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

    summary = build_user_result_summary(enriched)
    cards = build_evidence_axis_cards(enriched)
    main_html = render_main_result_card(summary)
    overview_html = render_audio_overview(enriched)
    evidence_html = render_evidence_cards_html(cards)
    table = gradio_suspicious_segments_table(enriched)

    visual_dir = gradio_output_dir("visuals")
    json_dir = gradio_output_dir("json")
    report_dir = gradio_output_dir("reports")

    waveform_path: str | None = None
    try:
        waveform_path = generate_waveform_highlight(
            audio_path, enriched, output_dir=visual_dir
        )
    except Exception:
        try:
            waveform_path = generate_timeline_fallback(enriched, output_dir=visual_dir)
        except Exception:
            waveform_path = None

    json_path = save_json_report(enriched, output_dir=json_dir)
    pdf_path = generate_pdf_report(
        enriched, waveform_image_path=waveform_path, output_dir=report_dir
    )
    technical_md = render_technical_details(enriched)
    partial_panel = enriched.get("partial_fabrication", {})
    segments_heading = gradio_segments_section_heading(enriched)

    return (
        main_html,
        overview_html,
        evidence_html,
        segments_heading,
        waveform_path,
        table,
        pdf_path,
        json_path,
        enriched,
        partial_panel,
        technical_md,
    )


def build_demo() -> Any:
    if gr is None:
        raise ImportError("gradio is not installed. Install with: pip install gradio")

    with gr.Blocks(title=APP_NAME) as demo:
        gr.Markdown(
            f"# {APP_NAME}\n\n"
            f"*{APP_SUBTITLE}*\n\n"
            f"*Research project: {RESEARCH_PROJECT_NAME}*\n\n"
            "> **Experimental evidence indicators only. Manual review is recommended.**"
        )

        with gr.Row():
            with gr.Column(scale=2):
                gr.Markdown("### Upload audio")
                audio_input = gr.Audio(type="filepath", label="Audio file")
                case_id_input = gr.Textbox(label="Case ID (optional)", placeholder="CASE-0001")
                with gr.Row():
                    run_btn = gr.Button("Analyze", variant="primary")
                    clear_btn = gr.Button("Clear / New analysis")

        gr.Markdown("### Main result")
        main_result = gr.HTML(label="Result")

        gr.Markdown("### Audio overview")
        audio_overview = gr.HTML()

        gr.Markdown("### Evidence indicators")
        evidence_cards = gr.HTML()

        gr.Markdown("### Waveform & timeline")
        waveform_image = gr.Image(label="Waveform visualization", type="filepath")

        segments_heading = gr.Markdown("### Candidate segments for review")
        segment_table = gr.Dataframe(
            headers=["Rank", "Time range", "Evidence score", "Review recommendation"],
            label="Segments for review",
            interactive=False,
        )

        gr.Markdown("### Reports")
        with gr.Row():
            pdf_download = gr.File(label="Download PDF Report")
            json_download = gr.File(label="Download JSON Report")

        with gr.Accordion("Advanced details", open=False):
            technical_details = gr.Markdown(label="Technical details")
            with gr.Accordion("Partial-fabrication contract", open=False):
                partial_json_output = gr.JSON(label="partial_fabrication section")
            with gr.Accordion("Raw JSON", open=False):
                json_output = gr.JSON(label="Full structured response")

        gr.Markdown(
            "#### About this demo\n\n"
            "- Experimental partial-fabrication and multi-axis evidence indicators only.\n"
            "- Manual forensic review is recommended.\n"
            "- Conclusive authenticity decision: **no**.\n"
            "- Not operational deployment or legal-evidence ready."
        )

        outputs = [
            main_result,
            audio_overview,
            evidence_cards,
            segments_heading,
            waveform_image,
            segment_table,
            pdf_download,
            json_download,
            json_output,
            partial_json_output,
            technical_details,
        ]

        run_btn.click(
            analyze,
            inputs=[audio_input, case_id_input],
            outputs=outputs,
        )
        clear_btn.click(
            lambda: _empty_outputs(),
            inputs=[],
            outputs=outputs,
        )

    return demo


if __name__ == "__main__":
    demo_app = build_demo()
    demo_app.launch(
        server_name="127.0.0.1",
        allowed_paths=[str(release_root())],
    )
