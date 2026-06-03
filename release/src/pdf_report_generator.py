"""Phase 9E-P2: PDF (or HTML fallback) report export — presentation only."""

from __future__ import annotations

import html
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.app_report_formatting import (
    APP_NAME,
    RESEARCH_PROJECT_NAME,
    build_evidence_axis_cards,
    build_user_result_summary,
    gradio_segments_table_title,
    load_partial_module_metadata,
    repo_root,
)


def _default_report_output_dir() -> Path:
    out = repo_root() / "reports" / "phase9" / "app" / "sample_outputs" / "reports"
    out.mkdir(parents=True, exist_ok=True)
    return out


def _segments_for_report(app_response: dict[str, Any]) -> list[list[str]]:
    from src.app_report_formatting import gradio_suspicious_segments_table

    rows = gradio_suspicious_segments_table(app_response)
    return [[str(c) for c in row] for row in rows]


def _write_html_report(
    app_response: dict[str, Any],
    output_path: Path,
    *,
    waveform_image_path: str | None,
    summary: dict[str, Any],
    cards: list[dict[str, Any]],
) -> str:
    meta = load_partial_module_metadata()
    pf = app_response.get("partial_fabrication") or {}
    segments = _segments_for_report(app_response)
    seg_rows = "".join(
        "<tr>"
        + "".join(f"<td>{html.escape(str(c))}</td>" for c in row)
        + "</tr>"
        for row in segments
    )
    if not seg_rows:
        seg_rows = "<tr><td colspan='4'>No segments listed</td></tr>"

    card_blocks = "".join(
        f"<li><b>{html.escape(c['axis_name'])}</b>: {html.escape(c['status'])} — "
        f"{html.escape(c.get('user_text', ''))}</li>"
        for c in cards
    )
    img_block = ""
    if waveform_image_path and Path(waveform_image_path).is_file():
        rel = Path(waveform_image_path).name
        img_block = f'<img src="{html.escape(rel)}" alt="Waveform" style="max-width:100%;"/>'

    th = pf.get("thresholds") or meta.get("thresholds", {})
    th_lines = "".join(f"<li>{html.escape(k)}: {html.escape(str(v))}</li>" for k, v in th.items())
    lims = "".join(
        f"<li>{html.escape(str(x))}</li>" for x in (app_response.get("limitations") or [])[:10]
    )
    seg_title = html.escape(gradio_segments_table_title(app_response))
    cascade_note = html.escape(
        "The current release app maps the Phase 9C segment partial axis into the P6 report "
        "contract. The full P5B file-gate cascade is not used in this app path yet."
    )

    body = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"/><title>{html.escape(APP_NAME)} Report</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #1e293b; }}
h1 {{ font-size: 1.4rem; }} .muted {{ color: #64748b; font-size: 0.9rem; }}
.box {{ border: 1px solid #e2e8f0; padding: 12px; border-radius: 8px; margin: 12px 0; }}
table {{ border-collapse: collapse; width: 100%; }} th, td {{ border: 1px solid #e2e8f0; padding: 6px; }}
</style></head><body>
<h1>{html.escape(APP_NAME)}</h1>
<p class="muted">Research project: {html.escape(RESEARCH_PROJECT_NAME)}</p>
<div class="box">
<p><b>Case ID:</b> {html.escape(str(app_response.get('case_id') or '—'))}</p>
<p><b>File:</b> {html.escape(str(app_response.get('file_name') or '—'))}</p>
<p><b>Duration:</b> {html.escape(str((app_response.get('audio_metadata') or {}).get('duration_sec', '—')))} s</p>
<p><b>Generated:</b> {html.escape(str(app_response.get('generated_at') or datetime.now(timezone.utc).isoformat()))}</p>
</div>
<div class="box">
<h2>Main result</h2>
<p><b>{html.escape(summary.get('finding_title',''))}</b></p>
<p>{html.escape(summary.get('highlighted_segment_text',''))}</p>
<p>{html.escape(summary.get('recommendation_text',''))}</p>
</div>
<div class="box"><h2>Evidence axes</h2><ul>{card_blocks}</ul></div>
<div class="box"><h2>Visual evidence</h2>{img_block or '<p>Waveform image not available.</p>'}</div>
<div class="box"><h2>{seg_title}</h2>
<table><tr><th>Rank</th><th>Time range</th><th>Evidence score</th><th>Review recommendation</th></tr>
{seg_rows}</table></div>
<div class="box"><h2>Technical details</h2>
<p>{cascade_note}</p>
<p>Partial module status: {html.escape(str(pf.get('module_status', meta.get('status',''))))}</p>
<p>Segment candidate only: {html.escape(str(pf.get('segment_candidate_only', False)))}</p>
<ul>{th_lines}</ul>
<p>Package: partial_fabrication_experimental_p5b (experimental_manual_review_only)</p>
<ul>{lims}</ul></div>
<div class="box"><p><b>Safety note:</b> Experimental evidence indicators only. Manual forensic review is recommended.
Conclusive authenticity decision: no.</p></div>
</body></html>"""
    output_path.write_text(body, encoding="utf-8")
    if waveform_image_path and Path(waveform_image_path).is_file():
        import shutil

        dest = output_path.parent / Path(waveform_image_path).name
        if dest.resolve() != Path(waveform_image_path).resolve():
            shutil.copy2(waveform_image_path, dest)
    return str(output_path)


def _write_pdf_reportlab(
    app_response: dict[str, Any],
    output_path: Path,
    *,
    waveform_image_path: str | None,
    summary: dict[str, Any],
    cards: list[dict[str, Any]],
) -> str:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    meta = load_partial_module_metadata()
    pf = app_response.get("partial_fabrication") or {}
    styles = getSampleStyleSheet()
    story: list[Any] = []

    story.append(Paragraph(APP_NAME, styles["Title"]))
    story.append(Paragraph(f"Research project: {RESEARCH_PROJECT_NAME}", styles["Normal"]))
    story.append(Spacer(1, 0.2 * inch))

    audio_meta = app_response.get("audio_metadata") or {}
    story.append(Paragraph("<b>Case information</b>", styles["Heading2"]))
    for line in (
        f"Case ID: {app_response.get('case_id') or '—'}",
        f"File name: {app_response.get('file_name') or '—'}",
        f"Duration: {audio_meta.get('duration_sec', '—')} s",
        f"Generated at: {app_response.get('generated_at', '—')}",
    ):
        story.append(Paragraph(line, styles["Normal"]))
    story.append(Spacer(1, 0.15 * inch))

    story.append(Paragraph("<b>Main result</b>", styles["Heading2"]))
    for key in ("finding_title", "highlighted_segment_text", "recommendation_text"):
        story.append(Paragraph(str(summary.get(key, "")), styles["Normal"]))
    story.append(Spacer(1, 0.15 * inch))

    story.append(Paragraph("<b>Evidence axis summary</b>", styles["Heading2"]))
    for card in cards:
        story.append(
            Paragraph(
                f"<b>{card.get('axis_name')}</b>: {card.get('status')} — {card.get('user_text', '')}",
                styles["Normal"],
            )
        )
    story.append(Spacer(1, 0.15 * inch))

    if waveform_image_path and Path(waveform_image_path).is_file():
        story.append(Paragraph("<b>Visual evidence</b>", styles["Heading2"]))
        story.append(Image(waveform_image_path, width=6.5 * inch, height=2.0 * inch))
        story.append(Spacer(1, 0.15 * inch))

    seg_data = [["Rank", "Time range", "Evidence score", "Review recommendation"]]
    seg_data.extend(_segments_for_report(app_response))
    if len(seg_data) == 1:
        seg_data.append(["—", "—", "—", "—"])
    t = Table(seg_data, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(Paragraph(f"<b>{gradio_segments_table_title(app_response)}</b>", styles["Heading2"]))
    story.append(t)
    story.append(Spacer(1, 0.15 * inch))

    story.append(Paragraph("<b>Technical details</b>", styles["Heading2"]))
    story.append(
        Paragraph(
            "The current release app maps the Phase 9C segment partial axis into the P6 report "
            "contract. The full P5B file-gate cascade is not used in this app path yet.",
            styles["Normal"],
        )
    )
    th = pf.get("thresholds") or meta.get("thresholds", {})
    for k, v in th.items():
        story.append(Paragraph(f"{k}: {v}", styles["Normal"]))
    story.append(
        Paragraph(
            f"Partial module status: {pf.get('module_status', meta.get('status', ''))}",
            styles["Normal"],
        )
    )
    for lim in (app_response.get("limitations") or [])[:8]:
        story.append(Paragraph(f"• {lim}", styles["Bullet"]))

    story.append(Spacer(1, 0.2 * inch))
    story.append(
        Paragraph(
            "<b>Safety note:</b> Experimental evidence indicators only. "
            "Manual forensic review is recommended. Conclusive authenticity decision: no.",
            styles["Normal"],
        )
    )

    doc = SimpleDocTemplate(str(output_path), pagesize=letter)
    doc.build(story)
    return str(output_path)


def generate_pdf_report(
    app_response: dict[str, Any],
    waveform_image_path: str | None = None,
    output_dir: str | Path | None = None,
) -> str:
    """Generate PDF report, or HTML fallback if reportlab is unavailable."""
    out_dir = Path(output_dir) if output_dir else _default_report_output_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    case = app_response.get("case_id") or app_response.get("request_id") or "report"
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in str(case))[:40]
    stamp = uuid.uuid4().hex[:8]

    summary = build_user_result_summary(app_response)
    cards = build_evidence_axis_cards(app_response)

    try:
        import reportlab  # noqa: F401

        pdf_path = out_dir / f"{safe}_{stamp}_report.pdf"
        return _write_pdf_reportlab(
            app_response,
            pdf_path,
            waveform_image_path=waveform_image_path,
            summary=summary,
            cards=cards,
        )
    except ImportError:
        html_path = out_dir / f"{safe}_{stamp}_report.html"
        return _write_html_report(
            app_response,
            html_path,
            waveform_image_path=waveform_image_path,
            summary=summary,
            cards=cards,
        )
