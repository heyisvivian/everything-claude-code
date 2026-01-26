"""
CV Generator Module - Generates professional PDF CVs from structured data.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, ListFlowable, ListItem
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
import os
from datetime import datetime


def create_styles():
    """Create custom paragraph styles for the CV."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name='CVName',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#1a1a2e'),
        spaceAfter=4,
        alignment=TA_CENTER
    ))

    styles.add(ParagraphStyle(
        name='CVContact',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#4a4a4a'),
        alignment=TA_CENTER,
        spaceAfter=12
    ))

    styles.add(ParagraphStyle(
        name='CVSection',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#1a1a2e'),
        spaceBefore=14,
        spaceAfter=6,
        borderColor=colors.HexColor('#1a1a2e'),
        borderWidth=0,
        borderPadding=0
    ))

    styles.add(ParagraphStyle(
        name='CVSummary',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#333333'),
        alignment=TA_JUSTIFY,
        spaceAfter=8,
        leading=14
    ))

    styles.add(ParagraphStyle(
        name='CVJobTitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#1a1a2e'),
        fontName='Helvetica-Bold',
        spaceBefore=6,
        spaceAfter=2
    ))

    styles.add(ParagraphStyle(
        name='CVCompany',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#4a4a4a'),
        fontName='Helvetica-Oblique',
        spaceAfter=4
    ))

    styles.add(ParagraphStyle(
        name='CVBullet',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#333333'),
        leftIndent=15,
        bulletIndent=5,
        spaceAfter=3,
        leading=13
    ))

    styles.add(ParagraphStyle(
        name='CVSkills',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#333333'),
        spaceAfter=4
    ))

    styles.add(ParagraphStyle(
        name='CVEducation',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#333333'),
        spaceAfter=2
    ))

    return styles


def generate_cv_pdf(tailored_cv: dict, output_path: str) -> str:
    """
    Generate a professional PDF CV from tailored CV data.

    Args:
        tailored_cv: Dictionary with tailored CV content
        output_path: Path to save the generated PDF

    Returns:
        Path to the generated PDF file
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=0.6*inch,
        leftMargin=0.6*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )

    styles = create_styles()
    story = []

    # Name
    name = tailored_cv.get("name", "")
    if name:
        story.append(Paragraph(name, styles['CVName']))

    # Contact Info
    contact = tailored_cv.get("contact", {})
    contact_parts = []
    if contact.get("email"):
        contact_parts.append(contact["email"])
    if contact.get("phone"):
        contact_parts.append(contact["phone"])
    if contact.get("location"):
        contact_parts.append(contact["location"])
    if contact.get("linkedin"):
        contact_parts.append(contact["linkedin"])

    if contact_parts:
        contact_text = " | ".join(contact_parts)
        story.append(Paragraph(contact_text, styles['CVContact']))

    # Horizontal line
    story.append(HRFlowable(
        width="100%",
        thickness=1,
        color=colors.HexColor('#1a1a2e'),
        spaceAfter=10
    ))

    # Professional Summary
    summary = tailored_cv.get("summary")
    if summary:
        story.append(Paragraph("PROFESSIONAL SUMMARY", styles['CVSection']))
        story.append(Paragraph(summary, styles['CVSummary']))

    # Experience
    experience = tailored_cv.get("experience", [])
    if experience:
        story.append(Paragraph("EXPERIENCE", styles['CVSection']))

        for job in experience:
            # Job title and dates on same line
            title = job.get("title", "")
            dates = job.get("dates", "")
            title_text = f"<b>{title}</b>"
            if dates:
                title_text += f" <font color='#666666'>({dates})</font>"
            story.append(Paragraph(title_text, styles['CVJobTitle']))

            # Company and location
            company = job.get("company", "")
            location = job.get("location", "")
            company_text = company
            if location:
                company_text += f" - {location}"
            if company_text:
                story.append(Paragraph(company_text, styles['CVCompany']))

            # Bullets
            bullets = job.get("bullets", [])
            for bullet in bullets:
                story.append(Paragraph(f"• {bullet}", styles['CVBullet']))

    # Skills
    skills = tailored_cv.get("skills", [])
    if skills:
        story.append(Paragraph("SKILLS", styles['CVSection']))
        skills_text = " • ".join(skills)
        story.append(Paragraph(skills_text, styles['CVSkills']))

    # Education
    education = tailored_cv.get("education", [])
    if education:
        story.append(Paragraph("EDUCATION", styles['CVSection']))

        for edu in education:
            degree = edu.get("degree", "")
            institution = edu.get("institution", "")
            dates = edu.get("dates", "")
            details = edu.get("details", "")

            edu_text = f"<b>{degree}</b>"
            if institution:
                edu_text += f" - {institution}"
            if dates:
                edu_text += f" ({dates})"
            story.append(Paragraph(edu_text, styles['CVEducation']))

            if details:
                story.append(Paragraph(details, styles['CVBullet']))

    # Certifications
    certifications = tailored_cv.get("certifications", [])
    if certifications:
        story.append(Paragraph("CERTIFICATIONS", styles['CVSection']))
        for cert in certifications:
            story.append(Paragraph(f"• {cert}", styles['CVBullet']))

    # Projects
    projects = tailored_cv.get("projects", [])
    if projects:
        story.append(Paragraph("PROJECTS", styles['CVSection']))

        for project in projects:
            name = project.get("name", "")
            description = project.get("description", "")
            technologies = project.get("technologies", [])

            if name:
                story.append(Paragraph(f"<b>{name}</b>", styles['CVJobTitle']))
            if description:
                story.append(Paragraph(description, styles['CVBullet']))
            if technologies:
                tech_text = "Technologies: " + ", ".join(technologies)
                story.append(Paragraph(tech_text, styles['CVBullet']))

    # Languages
    languages = tailored_cv.get("languages", [])
    if languages:
        story.append(Paragraph("LANGUAGES", styles['CVSection']))
        lang_text = " • ".join(languages)
        story.append(Paragraph(lang_text, styles['CVSkills']))

    # Build PDF
    doc.build(story)

    return output_path


def generate_filename(tailored_cv: dict) -> str:
    """Generate a descriptive filename for the tailored CV."""
    name = tailored_cv.get("name", "CV").replace(" ", "_")
    job_info = tailored_cv.get("job_info", {})
    company = job_info.get("company", "").replace(" ", "_")
    title = job_info.get("title", "").replace(" ", "_")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if company and title:
        filename = f"{name}_{company}_{title}_{timestamp}.pdf"
    elif company:
        filename = f"{name}_{company}_{timestamp}.pdf"
    else:
        filename = f"{name}_tailored_{timestamp}.pdf"

    # Clean up filename
    filename = "".join(c for c in filename if c.isalnum() or c in "._-")

    return filename
