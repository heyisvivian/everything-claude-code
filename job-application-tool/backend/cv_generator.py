"""
CV Generator Module - Generates professional one-page PDF CVs matching reference format.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from datetime import datetime


def create_styles():
    """Create custom paragraph styles for the compact one-page CV."""
    styles = getSampleStyleSheet()

    # Name - large, right aligned
    styles.add(ParagraphStyle(
        name='CVName',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.black,
        alignment=TA_RIGHT,
        spaceAfter=1,
        spaceBefore=0
    ))

    # Contact info - right aligned, smaller
    styles.add(ParagraphStyle(
        name='CVContact',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#0066cc'),
        alignment=TA_RIGHT,
        spaceAfter=6
    ))

    # Section headers - uppercase, underlined
    styles.add(ParagraphStyle(
        name='CVSection',
        parent=styles['Heading2'],
        fontSize=10,
        textColor=colors.black,
        spaceBefore=8,
        spaceAfter=4,
        fontName='Helvetica-Bold'
    ))

    # Date column style
    styles.add(ParagraphStyle(
        name='CVDate',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#333333'),
        alignment=TA_LEFT,
        leading=10
    ))

    # Duration style (italic, smaller)
    styles.add(ParagraphStyle(
        name='CVDuration',
        parent=styles['Normal'],
        fontSize=7,
        textColor=colors.HexColor('#666666'),
        fontName='Helvetica-Oblique',
        leading=9
    ))

    # Company/School name - bold
    styles.add(ParagraphStyle(
        name='CVCompany',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.black,
        fontName='Helvetica-Bold',
        leading=11
    ))

    # Job title - italic
    styles.add(ParagraphStyle(
        name='CVTitle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.black,
        fontName='Helvetica-Oblique',
        leading=11
    ))

    # Bullet points - compact
    styles.add(ParagraphStyle(
        name='CVBullet',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#333333'),
        leftIndent=8,
        bulletIndent=0,
        spaceBefore=1,
        spaceAfter=1,
        leading=10
    ))

    # Location - right aligned
    styles.add(ParagraphStyle(
        name='CVLocation',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.black,
        alignment=TA_RIGHT,
        leading=10
    ))

    # Skills label
    styles.add(ParagraphStyle(
        name='CVSkillLabel',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.black,
        fontName='Helvetica-Oblique',
        leading=10
    ))

    # Skills content
    styles.add(ParagraphStyle(
        name='CVSkillContent',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#333333'),
        leading=10
    ))

    return styles


def generate_cv_pdf(tailored_cv: dict, output_path: str, language: str = "english") -> str:
    """
    Generate a professional one-page PDF CV from tailored CV data.
    Matches the reference format with dates on left, content in middle, location on right.
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1*cm,
        bottomMargin=1*cm
    )

    styles = create_styles()
    story = []

    # === HEADER: Name and Contact ===
    name = tailored_cv.get("name", "")
    if name:
        story.append(Paragraph(name, styles['CVName']))

    contact = tailored_cv.get("contact", {})
    contact_parts = []
    if contact.get("phone"):
        contact_parts.append(contact["phone"])
    if contact.get("email"):
        contact_parts.append(contact["email"])
    contact_line = " | ".join(contact_parts)
    if contact_line:
        story.append(Paragraph(contact_line, styles['CVContact']))

    if contact.get("linkedin"):
        story.append(Paragraph(contact["linkedin"], styles['CVContact']))

    # === EDUCATION ===
    education = tailored_cv.get("education", [])
    if education:
        story.append(Paragraph("EDUCATION", styles['CVSection']))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.black, spaceAfter=4))

        for edu in education:
            # Create three-column layout: Date | Content | Location
            date_text = edu.get("dates", "")

            # Content column
            content_parts = []
            degree = edu.get("degree", "")
            institution = edu.get("institution", "")
            if institution and degree:
                content_parts.append(f"<b>{institution}</b> - <i>{degree}</i>")
            elif institution:
                content_parts.append(f"<b>{institution}</b>")

            details = edu.get("details", "")
            if details:
                content_parts.append(f"<font size=7>• {details}</font>")

            content_text = "<br/>".join(content_parts)
            location = edu.get("location", "")

            # Build table row
            table_data = [[
                Paragraph(date_text, styles['CVDate']),
                Paragraph(content_text, styles['CVBullet']),
                Paragraph(location, styles['CVLocation'])
            ]]

            t = Table(table_data, colWidths=[2.8*cm, 11.5*cm, 3*cm])
            t.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ]))
            story.append(t)

    # === PROFESSIONAL EXPERIENCE ===
    experience = tailored_cv.get("experience", [])
    if experience:
        story.append(Paragraph("PROFESSIONAL EXPERIENCE", styles['CVSection']))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.black, spaceAfter=4))

        for job in experience:
            dates = job.get("dates", "")
            duration = job.get("duration", "")
            company = job.get("company", "")
            title = job.get("title", "")
            location = job.get("location", "")
            bullets = job.get("bullets", [])

            # Date column with duration
            date_content = f"{dates}"
            if duration:
                date_content += f"<br/><i>{duration}</i>"

            # Content column
            content_parts = [f"<b>{company}</b>"]
            if title:
                content_parts.append(f"<i>{title}</i>")

            # Add bullets (limit to 2-3 for space)
            for bullet in bullets[:3]:
                content_parts.append(f"• {bullet}")

            content_text = "<br/>".join(content_parts)

            table_data = [[
                Paragraph(date_content, styles['CVDate']),
                Paragraph(content_text, styles['CVBullet']),
                Paragraph(location, styles['CVLocation'])
            ]]

            t = Table(table_data, colWidths=[2.8*cm, 11.5*cm, 3*cm])
            t.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            story.append(t)

    # === LEADERSHIP EXPERIENCE (if present) ===
    projects = tailored_cv.get("projects", [])
    leadership = tailored_cv.get("leadership", [])
    leadership_items = leadership if leadership else projects

    if leadership_items:
        label = "LEADERSHIP EXPERIENCE" if language == "english" else "EXPÉRIENCE DE LEADERSHIP"
        story.append(Paragraph(label, styles['CVSection']))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.black, spaceAfter=4))

        for item in leadership_items[:4]:  # Limit for space
            dates = item.get("dates", "")
            duration = item.get("duration", "")
            name = item.get("name", item.get("title", ""))
            role = item.get("role", item.get("description", ""))
            location = item.get("location", "")

            date_content = f"{dates}"
            if duration:
                date_content += f"<br/><i>{duration}</i>"

            content_parts = []
            if name and role:
                content_parts.append(f"<b>{name}</b> - <i>{role}</i>")
            elif name:
                content_parts.append(f"<b>{name}</b>")

            bullets = item.get("bullets", [])
            for bullet in bullets[:2]:
                content_parts.append(f"• {bullet}")

            content_text = "<br/>".join(content_parts)

            table_data = [[
                Paragraph(date_content, styles['CVDate']),
                Paragraph(content_text, styles['CVBullet']),
                Paragraph(location, styles['CVLocation'])
            ]]

            t = Table(table_data, colWidths=[2.8*cm, 11.5*cm, 3*cm])
            t.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ]))
            story.append(t)

    # === SKILLS & ADDITIONAL INFORMATION ===
    skills_label = "SKILLS & ADDITIONAL INFORMATION" if language == "english" else "COMPÉTENCES & INFORMATIONS"
    story.append(Paragraph(skills_label, styles['CVSection']))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.black, spaceAfter=4))

    # Language skills
    languages = tailored_cv.get("languages", [])
    if languages:
        lang_label = "Language Skills" if language == "english" else "Langues"
        lang_text = ", ".join(languages) if isinstance(languages, list) else languages
        table_data = [[
            Paragraph(f"<i>{lang_label}</i>", styles['CVSkillLabel']),
            Paragraph(f"• {lang_text}", styles['CVSkillContent'])
        ]]
        t = Table(table_data, colWidths=[2.8*cm, 14.5*cm])
        t.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ]))
        story.append(t)

    # IT/Technical skills
    skills = tailored_cv.get("skills", [])
    if skills:
        it_label = "IT Skills" if language == "english" else "Compétences IT"
        skills_text = ", ".join(skills[:15]) if isinstance(skills, list) else skills  # Limit for space
        table_data = [[
            Paragraph(f"<i>{it_label}</i>", styles['CVSkillLabel']),
            Paragraph(f"• {skills_text}", styles['CVSkillContent'])
        ]]
        t = Table(table_data, colWidths=[2.8*cm, 14.5*cm])
        t.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ]))
        story.append(t)

    # Certifications
    certifications = tailored_cv.get("certifications", [])
    if certifications:
        cert_label = "Certifications" if language == "english" else "Certifications"
        cert_text = ", ".join(certifications) if isinstance(certifications, list) else certifications
        table_data = [[
            Paragraph(f"<i>{cert_label}</i>", styles['CVSkillLabel']),
            Paragraph(f"• {cert_text}", styles['CVSkillContent'])
        ]]
        t = Table(table_data, colWidths=[2.8*cm, 14.5*cm])
        t.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ]))
        story.append(t)

    # Build PDF
    doc.build(story)
    return output_path


def generate_filename(tailored_cv: dict, language: str = "english") -> str:
    """Generate a descriptive filename for the tailored CV."""
    name = tailored_cv.get("name", "CV").replace(" ", "_")
    job_info = tailored_cv.get("job_info", {})
    company = job_info.get("company", "").replace(" ", "_").replace("/", "-")
    title = job_info.get("title", "").replace(" ", "_").replace("/", "-")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    lang_suffix = "EN" if language == "english" else "FR"

    if company and title:
        filename = f"{name}_{company}_{title}_{lang_suffix}_{timestamp}.pdf"
    elif company:
        filename = f"{name}_{company}_{lang_suffix}_{timestamp}.pdf"
    else:
        filename = f"{name}_tailored_{lang_suffix}_{timestamp}.pdf"

    # Clean up filename - remove invalid characters
    filename = "".join(c for c in filename if c.isalnum() or c in "._-")
    return filename
