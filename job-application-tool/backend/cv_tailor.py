"""
CV Tailor Module - Analyzes job postings and tailors CVs using AI.
"""

import requests
from bs4 import BeautifulSoup
from anthropic import Anthropic
import json
import re
from urllib.parse import urlparse


def fetch_job_posting(url: str) -> dict:
    """
    Fetch and extract content from a job posting URL.

    Returns:
        Dictionary with job description and company info
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        raise ValueError(f"Could not fetch the job posting: {str(e)}")

    soup = BeautifulSoup(response.text, "lxml")

    # Remove script and style elements
    for element in soup(["script", "style", "nav", "footer", "header"]):
        element.decompose()

    # Extract main content
    main_content = soup.find("main") or soup.find("article") or soup.find("body")

    if main_content:
        text = main_content.get_text(separator="\n", strip=True)
    else:
        text = soup.get_text(separator="\n", strip=True)

    # Clean up the text
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    clean_text = "\n".join(lines)

    # Truncate if too long
    if len(clean_text) > 15000:
        clean_text = clean_text[:15000] + "\n...[truncated]"

    # Extract domain for company context
    domain = urlparse(url).netloc

    return {
        "url": url,
        "domain": domain,
        "content": clean_text
    }


def analyze_job_posting(job_content: dict, api_key: str) -> dict:
    """
    Use Claude to analyze the job posting and extract structured information.
    """
    client = Anthropic(api_key=api_key)

    prompt = """Analyze this job posting content and extract key information.

Job Posting URL: {url}
Domain: {domain}

Content:
---
{content}
---

Return a JSON object with:
{{
    "company": {{
        "name": "Company name",
        "industry": "Industry/sector",
        "description": "Brief company description if available",
        "culture": "Company culture hints from the posting",
        "size": "Company size if mentioned"
    }},
    "job": {{
        "title": "Job title",
        "department": "Department if mentioned",
        "location": "Location/remote status",
        "type": "Full-time/Part-time/Contract",
        "level": "Entry/Mid/Senior/Lead/Executive"
    }},
    "requirements": {{
        "must_have": ["Required skill/experience 1", "Required skill/experience 2"],
        "nice_to_have": ["Preferred skill 1", "Preferred skill 2"],
        "years_experience": "Years of experience required",
        "education": "Education requirements"
    }},
    "responsibilities": ["Key responsibility 1", "Key responsibility 2"],
    "keywords": ["Important keyword 1", "Important keyword 2"],
    "tone": "Formal/Casual/Technical - describe the tone of the posting",
    "emphasis": "What does this job posting emphasize most?"
}}

Return ONLY valid JSON, no additional text.""".format(**job_content)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    response_text = response.content[0].text

    try:
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        return json.loads(response_text.strip())
    except json.JSONDecodeError:
        return {"raw_content": job_content["content"], "parse_error": True}


def tailor_cv(parsed_cv: dict, job_analysis: dict, api_key: str, output_language: str = "english") -> dict:
    """
    Use Claude to tailor the CV content for the specific job.

    Args:
        parsed_cv: Structured CV data from cv_parser
        job_analysis: Analyzed job posting data
        api_key: Anthropic API key
        output_language: "english" or "french"

    Returns:
        Dictionary with tailored CV content
    """
    client = Anthropic(api_key=api_key)

    language_instruction = ""
    if output_language == "french":
        language_instruction = """
CRITICAL: Write ALL CV content in French. This includes:
- Professional summary in natural, professional French
- All experience bullets in French
- Skills translated to French where appropriate
- Use proper French business language and conventions
- The CV is for a French company, so use French throughout
"""
    else:
        language_instruction = """
Write all CV content in English.
"""

    prompt = """You are an expert CV/resume writer. Tailor this CV for the specific job posting.

ORIGINAL CV:
{cv_json}

JOB ANALYSIS:
{job_json}

{language_instruction}

Your task:
1. Rewrite the professional summary to directly address this role and company
2. Reorder and rewrite experience bullets to highlight relevant skills and achievements
3. Emphasize skills that match the job requirements
4. Use keywords from the job posting naturally throughout
5. Adjust the tone to match the company culture
6. Keep all information truthful - enhance presentation, don't fabricate

Return a JSON object with the tailored CV:
{{
    "name": "Keep original name",
    "contact": {{ /* Keep original contact info */ }},
    "summary": "Newly written professional summary tailored for this role (2-3 sentences)",
    "experience": [
        {{
            "title": "Original or slightly adjusted title",
            "company": "Original company",
            "location": "Original location",
            "dates": "Original dates",
            "bullets": ["Rewritten bullet emphasizing relevant achievements", "Another tailored bullet"]
        }}
    ],
    "education": [ /* Keep original education */ ],
    "skills": ["Reordered skills with most relevant first"],
    "certifications": [ /* Keep relevant certifications */ ],
    "languages": [ /* Keep original */ ],
    "projects": [ /* Keep relevant projects, rewrite descriptions to emphasize relevant tech */ ],
    "tailoring_notes": {{
        "keywords_added": ["keyword1", "keyword2"],
        "emphasis_areas": ["What was emphasized"],
        "match_score": "Estimated match percentage with reasoning"
    }}
}}

Important:
- Keep the CV to 1-2 pages worth of content
- Don't invent new experience or skills
- Make bullets achievement-focused with metrics where available
- Return ONLY valid JSON""".format(
        cv_json=json.dumps(parsed_cv, indent=2),
        job_json=json.dumps(job_analysis, indent=2),
        language_instruction=language_instruction
    )

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    response_text = response.content[0].text

    try:
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        tailored = json.loads(response_text.strip())
        tailored["job_info"] = {
            "company": job_analysis.get("company", {}).get("name", "Unknown"),
            "title": job_analysis.get("job", {}).get("title", "Unknown"),
            "url": job_analysis.get("url", "")
        }
        return tailored
    except json.JSONDecodeError:
        raise ValueError("Failed to generate tailored CV. Please try again.")


def process_job_url(url: str, parsed_cv: dict, api_key: str, output_language: str = "english") -> dict:
    """
    Main function to process a job URL and tailor a CV.

    Args:
        url: Job posting URL
        parsed_cv: Pre-parsed CV data
        api_key: Anthropic API key
        output_language: "english" or "french"

    Returns:
        Dictionary with job analysis and tailored CV
    """
    # Fetch the job posting
    job_content = fetch_job_posting(url)

    # Analyze the job posting
    job_analysis = analyze_job_posting(job_content, api_key)
    job_analysis["url"] = url

    # Tailor the CV
    tailored_cv = tailor_cv(parsed_cv, job_analysis, api_key, output_language)

    return {
        "job_analysis": job_analysis,
        "tailored_cv": tailored_cv
    }
