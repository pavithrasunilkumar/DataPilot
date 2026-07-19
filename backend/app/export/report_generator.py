"""
PDF executive report generator.

Builds a structured report from what the platform has actually computed —
quality report, autonomous analysis (correlations/trends), and trained
model results if present. No charts are rasterized as images here (kept
deliberately simple); the report communicates findings as tables and text,
which is faster to generate and just as legible for an executive summary.
"""

import os
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from app.core.config import settings


def _styles():
    base = getSampleStyleSheet()
    base.add(ParagraphStyle(name="ReportTitle", fontSize=20, leading=24, spaceAfter=6, fontName="Helvetica-Bold"))
    base.add(ParagraphStyle(name="SectionHeading", fontSize=13, leading=16, spaceBefore=16, spaceAfter=8, fontName="Helvetica-Bold"))
    base.add(ParagraphStyle(name="Body", fontSize=10, leading=14))
    base.add(ParagraphStyle(name="Muted", fontSize=9, leading=12, textColor=colors.grey))
    return base


def generate_pdf_report(
    filename: str,
    quality_report: dict,
    autonomous_analysis: dict | None,
    trained_model_info: dict | None,
    domain: str | None,
) -> str:
    styles = _styles()
    output_path = os.path.join(settings.upload_dir, f"report_{os.urandom(4).hex()}.pdf")

    doc = SimpleDocTemplate(output_path, pagesize=letter, topMargin=0.7 * inch, bottomMargin=0.7 * inch)
    story = []

    story.append(Paragraph("DataPilot Executive Report", styles["ReportTitle"]))
    story.append(Paragraph(f"Dataset: {filename}", styles["Muted"]))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles["Muted"]))
    if domain:
        story.append(Paragraph(f"Detected domain: {domain.title()}", styles["Muted"]))
    story.append(Spacer(1, 12))

    # --- Data quality section ---
    story.append(Paragraph("Data Quality Summary", styles["SectionHeading"]))
    quality_table_data = [
        ["Metric", "Value"],
        ["Rows", str(quality_report.get("row_count", "—"))],
        ["Columns", str(quality_report.get("column_count", "—"))],
        ["Duplicate rows", f"{quality_report.get('duplicate_row_pct', 0)}%"],
        ["Quality score", f"{quality_report.get('quality_score', '—')} / 100"],
    ]
    story.append(_styled_table(quality_table_data))

    warnings = quality_report.get("warnings", [])
    if warnings:
        story.append(Spacer(1, 8))
        story.append(Paragraph("Warnings", styles["Body"]))
        for w in warnings[:10]:
            story.append(Paragraph(f"• {w}", styles["Body"]))

    # --- Autonomous analysis section ---
    if autonomous_analysis:
        story.append(Paragraph("Key Relationships & Trends", styles["SectionHeading"]))

        top_pairs = autonomous_analysis.get("correlations", {}).get("top_pairs", [])
        if top_pairs:
            story.append(Paragraph("Strongest correlations:", styles["Body"]))
            corr_table_data = [["Variable A", "Variable B", "Correlation"]]
            for pair in top_pairs[:6]:
                corr_table_data.append([pair["column_a"], pair["column_b"], f"{pair['correlation']:.2f}"])
            story.append(_styled_table(corr_table_data))

        trends = autonomous_analysis.get("trends", [])
        if trends:
            story.append(Spacer(1, 8))
            story.append(Paragraph("Detected trends:", styles["Body"]))
            trend_table_data = [["Column", "Direction", "Fit (R²)", "Periods"]]
            for t in trends[:6]:
                trend_table_data.append([t["column"], t["direction"], f"{t['r_squared']:.2f}", str(t["periods_available"])])
            story.append(_styled_table(trend_table_data))

        summary = autonomous_analysis.get("summary")
        if summary:
            story.append(Spacer(1, 8))
            story.append(Paragraph("Summary", styles["Body"]))
            story.append(Paragraph(summary, styles["Body"]))

    # --- ML model section ---
    if trained_model_info:
        story.append(Paragraph("Predictive Model Results", styles["SectionHeading"]))
        story.append(Paragraph(
            f"Target: {trained_model_info.get('target_column')} "
            f"({trained_model_info.get('task_type', '').replace('_', ' ')})",
            styles["Body"],
        ))
        chosen = trained_model_info.get("chosen_model")
        metrics = trained_model_info.get(f"{'boosted' if chosen == 'xgboost' else 'baseline'}_model", {}).get("metrics", {})
        metrics_table = [["Metric", "Value"]] + [[k.title(), str(v)] for k, v in metrics.items()]
        story.append(_styled_table(metrics_table))

        importance = trained_model_info.get("feature_importance", [])
        if importance:
            story.append(Spacer(1, 8))
            story.append(Paragraph("Top predictive features:", styles["Body"]))
            imp_table = [["Feature", "Importance"]] + [[f["feature"], f"{f['importance']:.3f}"] for f in importance[:8]]
            story.append(_styled_table(imp_table))

    doc.build(story)
    return output_path


def _styled_table(data: list[list[str]]) -> Table:
    table = Table(data, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1b1f26")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table
