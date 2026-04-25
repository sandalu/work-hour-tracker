from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime
import io

def generate_pdf(entries, total_hours, remaining_hours, fortnight_start, fortnight_end, academic_start, on_break, limit=48):
    """Generate a PDF work hour report"""
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()
    elements = []

    # ── Title ──────────────────────────────────────────────────────
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Normal'],
        fontSize=22,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#1e293b'),
        alignment=TA_CENTER,
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=11,
        fontName='Helvetica',
        textColor=colors.HexColor('#64748b'),
        alignment=TA_CENTER,
        spaceAfter=4
    )

    label_style = ParagraphStyle(
        'Label',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica',
        textColor=colors.HexColor('#64748b'),
        alignment=TA_CENTER
    )

    section_style = ParagraphStyle(
        'Section',
        parent=styles['Normal'],
        fontSize=13,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=16,
        spaceAfter=8
    )

    normal_style = ParagraphStyle(
        'Normal2',
        parent=styles['Normal'],
        fontSize=10,
        fontName='Helvetica',
        textColor=colors.HexColor('#334155'),
    )

    elements.append(Paragraph("🕐 Work Hour Tracker", title_style))
    elements.append(Paragraph("Australian Student Visa — Work Hour Report", subtitle_style))
    elements.append(Paragraph(f"Generated on {datetime.now().strftime('%d %b %Y at %I:%M %p')}", label_style))
    elements.append(Spacer(1, 0.4*cm))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e2e8f0')))
    elements.append(Spacer(1, 0.4*cm))

    # ── Summary Info ───────────────────────────────────────────────
    elements.append(Paragraph("Report Summary", section_style))

    summary_data = [
        ['Academic Start Date', academic_start],
        ['Fortnight Period', f"{fortnight_start} → {fortnight_end}"],
        ['Fortnightly Limit', f"{limit} hours"],
        ['Hours Worked', f"{total_hours:.2f} hours"],
        ['Hours Remaining', f"{remaining_hours:.2f} hours"],
        ['Status', "🏖️ Semester Break" if on_break else f"{'⚠️ Near Limit' if total_hours >= limit * 0.8 else '✅ Within Limit'}"],
    ]

    summary_table = Table(summary_data, colWidths=[6*cm, 10*cm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
        ('BACKGROUND', (1, 0), (1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#64748b')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1e293b')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ROUNDEDCORNERS', [4]),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 0.4*cm))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e2e8f0')))

    # ── Work History ───────────────────────────────────────────────
    elements.append(Paragraph("Work History", section_style))

    if entries:
        table_data = [['Date Worked', 'Job / Company', 'Hours', 'Logged On', 'Type']]

        for entry in entries:
            is_break = entry.get('is_break', False)
            table_data.append([
                entry.get('work_date', entry.get('date', '')),
                entry.get('job', ''),
                f"{entry.get('hours', 0):.2f}hrs",
                entry.get('date', ''),
                '🏖️ Break' if is_break else '📚 Semester'
            ])

        col_widths = [3.5*cm, 5*cm, 2.5*cm, 3.5*cm, 2.5*cm]
        history_table = Table(table_data, colWidths=col_widths)
        history_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('PADDING', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

            # Data rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('PADDING', (0, 1), (-1, -1), 8),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#334155')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),
            ('ALIGN', (4, 1), (4, -1), 'CENTER'),
        ]))
        elements.append(history_table)
    else:
        elements.append(Paragraph("No entries found for this period.", normal_style))

    elements.append(Spacer(1, 0.6*cm))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e2e8f0')))
    elements.append(Spacer(1, 0.2*cm))
    elements.append(Paragraph(
        "This report was generated by Work Hour Tracker — a tool to help international students track their work hours in compliance with Australian student visa conditions.",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#94a3b8'), alignment=TA_CENTER)
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer