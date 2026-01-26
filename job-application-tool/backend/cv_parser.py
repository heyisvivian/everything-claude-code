"""
CV Parser Module - Extracts and structures content from PDF CVs.
"""

import pdfplumber
from anthropic import Anthropic
import json
import os


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract all text content from a PDF file."""
    text_content = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                text_content.append(text)

    return "\n\n".join(text_content)


def parse_cv_with_ai(raw_text: str, api_key: str) -> dict:
    """
    Use Claude to structure the raw CV text into organized sections.
    Returns a dictionary with structured CV data.
    """
    client = Anthropic(api_key=api_key)

    prompt = """Analyze this CV/resume text and extract the information into a structured JSON format.

CV Text:
---
{cv_text}
---

Return a JSON object with the following structure (use null for missing sections):
{{
    "name": "Full name",
    "contact": {{
        "email": "email address",
        "phone": "phone number",
        "location": "city, country",
        "linkedin": "LinkedIn URL if present",
        "website": "personal website if present"
    }},
    "summary": "Professional summary or objective if present",
    "experience": [
        {{
            "title": "Job title",
            "company": "Company name",
            "location": "Location",
            "dates": "Start - End dates",
            "bullets": ["Achievement/responsibility 1", "Achievement/responsibility 2"]
        }}
    ],
    "education": [
        {{
            "degree": "Degree name",
            "institution": "School/University",
            "dates": "Graduation year or date range",
            "details": "GPA, honors, relevant coursework if mentioned"
        }}
    ],
    "skills": ["Skill 1", "Skill 2", "Skill 3"],
    "certifications": ["Certification 1", "Certification 2"],
    "languages": ["Language 1 (proficiency)", "Language 2 (proficiency)"],
    "projects": [
        {{
            "name": "Project name",
            "description": "Brief description",
            "technologies": ["Tech 1", "Tech 2"]
        }}
    ]
}}

Important:
- Extract ALL information from the CV, don't skip any sections
- Keep the original wording for experience bullets and descriptions
- If a section doesn't exist in the CV, set it to null or empty array
- Return ONLY valid JSON, no additional text""".format(cv_text=raw_text)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    response_text = response.content[0].text

    # Try to parse the JSON response
    try:
        # Handle potential markdown code blocks
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        parsed_cv = json.loads(response_text.strip())
        return parsed_cv
    except json.JSONDecodeError:
        # Return raw text if parsing fails
        return {
            "name": "Unknown",
            "raw_text": raw_text,
            "parse_error": "Could not structure CV automatically"
        }


def parse_cv(pdf_path: str, api_key: str) -> dict:
    """
    Main function to parse a CV from PDF to structured data.

    Args:
        pdf_path: Path to the PDF CV file
        api_key: Anthropic API key

    Returns:
        Dictionary with structured CV data
    """
    # Extract raw text
    raw_text = extract_text_from_pdf(pdf_path)

    if not raw_text.strip():
        raise ValueError("Could not extract any text from the PDF. The file may be image-based or corrupted.")

    # Structure with AI
    structured_cv = parse_cv_with_ai(raw_text, api_key)
    structured_cv["raw_text"] = raw_text

    return structured_cv
