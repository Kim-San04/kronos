import os
from datetime import datetime

def generate_pdf(target, output_path: str):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer,
            Table, TableStyle, HRFlowable
        )

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=2*cm,
            rightMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )

        styles = getSampleStyleSheet()
        CYAN = colors.HexColor("#00bcd4")
        DARK = colors.HexColor("#0a0a0a")
        GRAY = colors.HexColor("#444444")

        title_style = ParagraphStyle(
            "KronosTitle",
            parent=styles["Title"],
            textColor=CYAN,
            fontSize=22,
            spaceAfter=6
        )
        h2_style = ParagraphStyle(
            "KronosH2",
            parent=styles["Heading2"],
            textColor=CYAN,
            fontSize=13,
            spaceBefore=12,
            spaceAfter=4
        )
        body_style = ParagraphStyle(
            "KronosBody",
            parent=styles["Normal"],
            fontSize=9,
            leading=13
        )

        story = []

        # Header
        name = getattr(
            target, "domain",
            getattr(target, "name", "Target")
        )
        story.append(Paragraph("◆ KRONOS — OSINT Intelligence Report", title_style))
        story.append(Paragraph(
            f"Target: <b>{name}</b> — Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            body_style
        ))
        story.append(HRFlowable(width="100%", color=CYAN, thickness=1, spaceAfter=12))

        # Risk score
        story.append(Paragraph("Risk Score", h2_style))
        score = target.risk_score
        color = (
            colors.red if score >= 70
            else colors.orange if score >= 40
            else colors.green
        )
        risk_table = Table(
            [[f"{score}/100"]],
            colWidths=[4*cm]
        )
        risk_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), color),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 20),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [color]),
        ]))
        story.append(risk_table)
        story.append(Spacer(1, 10))

        # AI Summary
        if target.ai_summary:
            story.append(Paragraph("Executive Summary", h2_style))
            story.append(Paragraph(target.ai_summary, body_style))
            story.append(Spacer(1, 8))

        # Correlations
        if target.correlations:
            story.append(Paragraph("Key Findings & Correlations", h2_style))
            for c in target.correlations:
                story.append(Paragraph(f"• {c}", body_style))
            story.append(Spacer(1, 8))

        # Data sections
        _add_person_data(story, target, h2_style, body_style)
        _add_company_data(story, target, h2_style, body_style)

        doc.build(story)

    except ImportError:
        _fallback_txt(target, output_path)


def _add_person_data(story, target, h2_style, body_style):
    from reportlab.platypus import Paragraph, Spacer

    if not hasattr(target, "emails_found"):
        return

    if target.emails_found:
        story.append(Paragraph("Emails Found", h2_style))
        for e in target.emails_found:
            story.append(Paragraph(f"• {e}", body_style))
        story.append(Spacer(1, 6))

    if target.social_profiles:
        story.append(Paragraph("Social Profiles", h2_style))
        for platform, url in target.social_profiles.items():
            story.append(Paragraph(f"• {platform}: {url}", body_style))
        story.append(Spacer(1, 6))

    if target.breaches:
        story.append(Paragraph("Data Breaches", h2_style))
        for b in target.breaches:
            story.append(Paragraph(
                f"• {b.get('Name', '?')} ({b.get('BreachDate', '')[:4]})",
                body_style
            ))
        story.append(Spacer(1, 6))

    if target.locations:
        story.append(Paragraph("Locations", h2_style))
        for loc in target.locations:
            story.append(Paragraph(
                f"• {loc.get('source')}: {loc.get('location')}",
                body_style
            ))
        story.append(Spacer(1, 6))


def _add_company_data(story, target, h2_style, body_style):
    from reportlab.platypus import Paragraph, Spacer

    if not hasattr(target, "subdomains"):
        return

    if target.subdomains:
        story.append(Paragraph("Subdomains", h2_style))
        for sub in target.subdomains[:30]:
            story.append(Paragraph(f"• {sub}", body_style))
        if len(target.subdomains) > 30:
            story.append(Paragraph(
                f"  ... and {len(target.subdomains) - 30} more",
                body_style
            ))
        story.append(Spacer(1, 6))

    if target.cves:
        story.append(Paragraph("CVEs Detected", h2_style))
        for cve in target.cves:
            story.append(Paragraph(f"• {cve}", body_style))
        story.append(Spacer(1, 6))

    if target.exposed_secrets:
        story.append(Paragraph("Exposed Secrets", h2_style))
        for s in target.exposed_secrets:
            story.append(Paragraph(
                f"• [{s.get('type')}] {s.get('repo')}/{s.get('file')}",
                body_style
            ))
        story.append(Spacer(1, 6))

    if target.employees:
        story.append(Paragraph("Identified Employees", h2_style))
        for emp in target.employees[:20]:
            line = emp.get("username", emp.get("name", "?"))
            if emp.get("email"):
                line += f" — {emp['email']}"
            story.append(Paragraph(f"• {line}", body_style))
        story.append(Spacer(1, 6))


def _fallback_txt(target, output_path):
    txt_path = output_path.replace(".pdf", ".txt")
    name = getattr(target, "domain", getattr(target, "name", "target"))
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"KRONOS Report — {name}\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write(f"Risk Score: {target.risk_score}/100\n\n")
        if target.ai_summary:
            f.write(f"Summary:\n{target.ai_summary}\n\n")
        for c in target.correlations:
            f.write(f"- {c}\n")
