"""
CV Tailor Module - Analyzes job postings and tailors CVs using AI.
Generates both English and French versions.
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
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5,fr;q=0.3",
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        raise ValueError(f"Could not fetch the job posting: {str(e)}")

    soup = BeautifulSoup(response.text, "lxml")

    for element in soup(["script", "style", "nav", "footer", "header"]):
        element.decompose()

    main_content = soup.find("main") or soup.find("article") or soup.find("body")

    if main_content:
        text = main_content.get_text(separator="\n", strip=True)
    else:
        text = soup.get_text(separator="\n", strip=True)

    lines = [line.strip() for line in text.split("\n") if line.strip()]
    clean_text = "\n".join(lines)

    if len(clean_text) > 15000:
        clean_text = clean_text[:15000] + "\n...[truncated]"

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
    "emphasis": "What does this job posting emphasize most?",
    "language": "Language of the job posting (english/french/other)"
}}

Return ONLY valid JSON, no additional text.""".format(**job_content)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}]
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


def tailor_cv_bilingual(parsed_cv: dict, job_analysis: dict, api_key: str) -> dict:
    """
    Use Claude to tailor the CV content for the specific job in BOTH English and French.
    Returns both versions in a single API call for efficiency.
    """
    client = Anthropic(api_key=api_key)

    prompt = """You are an expert CV/resume writer fluent in both English and French.
Tailor this CV for the specific job posting and generate BOTH English and French versions.

IMPORTANT: Keep each CV to ONE PAGE worth of content. Be concise but impactful.

ORIGINAL CV:
{cv_json}

JOB ANALYSIS:
{job_json}

Your tasks:
1. Rewrite the professional summary to directly address this role
2. Reorder and rewrite experience bullets to highlight relevant skills (2-3 bullets per job MAX)
3. Emphasize skills that match the job requirements
4. Use keywords from the job posting naturally
5. For French version: Write natural, professional French (not translated-sounding)

Return a JSON object with BOTH versions:
{{
    "english": {{
        "name": "Keep original name",
        "contact": {{ "email": "...", "phone": "...", "linkedin": "...", "location": "..." }},
        "summary": "Tailored summary in English (2 sentences max)",
        "education": [
            {{
                "institution": "School name",
                "degree": "Degree name",
                "dates": "Aug 2023 - Jun 2024",
                "location": "City, Country",
                "details": "Key relevant coursework or achievements"
            }}
        ],
        "experience": [
            {{
                "company": "Company name",
                "title": "Job title",
                "dates": "Jan 2024 - Jul 2024",
                "duration": "6 months",
                "location": "City, Country",
                "bullets": ["Achievement 1 with metrics", "Achievement 2"]
            }}
        ],
        "leadership": [
            {{
                "name": "Project or Role name",
                "role": "Your role",
                "dates": "Start - End",
                "duration": "X months",
                "location": "City, Country",
                "bullets": ["Key achievement"]
            }}
        ],
        "skills": ["Skill1", "Skill2", "Skill3"],
        "languages": ["English (Fluent)", "French (B2)"],
        "certifications": []
    }},
    "french": {{
        "name": "Keep original name",
        "contact": {{ "email": "...", "phone": "...", "linkedin": "...", "location": "..." }},
        "summary": "Résumé professionnel adapté en français naturel (2 phrases max)",
        "education": [
            {{
                "institution": "Nom de l'école",
                "degree": "Nom du diplôme",
                "dates": "Aug 2023 - Jun 2024",
                "location": "Ville, Pays",
                "details": "Cours pertinents"
            }}
        ],
        "experience": [
            {{
                "company": "Nom de l'entreprise",
                "title": "Titre du poste en français",
                "dates": "Jan 2024 - Jul 2024",
                "duration": "6 mois",
                "location": "Ville, Pays",
                "bullets": ["Réalisation 1 avec métriques", "Réalisation 2"]
            }}
        ],
        "leadership": [...],
        "skills": ["Compétence1", "Compétence2"],
        "languages": ["Anglais (Courant)", "Français (B2)"],
        "certifications": []
    }},
    "tailoring_notes": {{
        "keywords_added": ["keyword1", "keyword2"],
        "emphasis_areas": ["What was emphasized"],
        "match_score": "85% - Strong match because..."
    }}
}}

IMPORTANT:
- Keep each CV to ONE PAGE - limit bullets, be concise
- Don't invent new experience or skills
- French version should sound natural, not translated
- Include duration for each role (e.g., "6 months", "2 years")
- Return ONLY valid JSON""".format(
        cv_json=json.dumps(parsed_cv, indent=2),
        job_json=json.dumps(job_analysis, indent=2)
    )

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=6000,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = response.content[0].text

    try:
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        result = json.loads(response_text.strip())

        # Add job info to both versions
        job_info = {
            "company": job_analysis.get("company", {}).get("name", "Unknown"),
            "title": job_analysis.get("job", {}).get("title", "Unknown"),
            "url": job_analysis.get("url", "")
        }

        if "english" in result:
            result["english"]["job_info"] = job_info
        if "french" in result:
            result["french"]["job_info"] = job_info

        return result
    except json.JSONDecodeError:
        raise ValueError("Failed to generate tailored CV. Please try again.")


def search_salary_info(job_title: str, company: str, location: str, api_key: str) -> dict:
    """
    Use Claude to search for salary information based on job details.
    """
    client = Anthropic(api_key=api_key)

    prompt = """Based on your knowledge, estimate the salary range for this position:

Job Title: {title}
Company: {company}
Location: {location}

Provide salary information in JSON format:
{{
    "estimated_range": {{
        "min": 45000,
        "max": 65000,
        "currency": "EUR"
    }},
    "confidence": "medium",
    "notes": "Brief explanation of the estimate",
    "sources": "Based on typical market rates for this role in this location"
}}

If you cannot provide a reasonable estimate, return:
{{
    "estimated_range": null,
    "confidence": "low",
    "notes": "Insufficient information to estimate salary"
}}

Return ONLY valid JSON.""".format(
        title=job_title,
        company=company,
        location=location
    )

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = response.content[0].text

        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        return json.loads(response_text.strip())
    except:
        return {
            "estimated_range": None,
            "confidence": "low",
            "notes": "Could not retrieve salary information"
        }


def process_job_url(url: str, parsed_cv: dict, api_key: str) -> dict:
    """
    Main function to process a job URL and tailor CVs in both languages.
    Also fetches salary information.
    """
    # Fetch the job posting
    job_content = fetch_job_posting(url)

    # Analyze the job posting
    job_analysis = analyze_job_posting(job_content, api_key)
    job_analysis["url"] = url

    # Tailor the CV in both languages
    tailored_result = tailor_cv_bilingual(parsed_cv, job_analysis, api_key)

    # Get salary estimate
    salary_info = search_salary_info(
        job_analysis.get("job", {}).get("title", ""),
        job_analysis.get("company", {}).get("name", ""),
        job_analysis.get("job", {}).get("location", ""),
        api_key
    )

    return {
        "job_analysis": job_analysis,
        "tailored_cv_english": tailored_result.get("english", {}),
        "tailored_cv_french": tailored_result.get("french", {}),
        "tailoring_notes": tailored_result.get("tailoring_notes", {}),
        "salary_info": salary_info
    }
