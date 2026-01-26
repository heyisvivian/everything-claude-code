"""
Job Application Tool - FastAPI Backend
Tailors CVs for job applications using AI.
"""

import os
import uuid
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from cv_parser import parse_cv
from cv_tailor import process_job_url
from cv_generator import generate_cv_pdf, generate_filename

# Configuration
UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
OUTPUT_DIR = Path(__file__).parent.parent / "outputs"
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

# Ensure directories exist
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# In-memory storage for session data
sessions = {}

app = FastAPI(
    title="Job Application Tool",
    description="AI-powered CV tailoring for job applications",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_api_key() -> str:
    """Get the Anthropic API key from environment."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="ANTHROPIC_API_KEY environment variable not set"
        )
    return api_key


@app.post("/api/upload-cv")
async def upload_cv(file: UploadFile = File(...)):
    """
    Upload and parse a CV PDF file.

    Returns a session ID and parsed CV data.
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    try:
        api_key = get_api_key()

        # Generate session ID
        session_id = str(uuid.uuid4())

        # Save uploaded file
        file_path = UPLOAD_DIR / f"{session_id}.pdf"
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        # Parse the CV
        parsed_cv = parse_cv(str(file_path), api_key)

        # Store in session
        sessions[session_id] = {
            "parsed_cv": parsed_cv,
            "original_filename": file.filename,
            "upload_time": datetime.now().isoformat(),
            "applications": []
        }

        return {
            "session_id": session_id,
            "parsed_cv": parsed_cv,
            "message": "CV uploaded and parsed successfully"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing CV: {str(e)}")


@app.post("/api/tailor")
async def tailor_cv(
    session_id: str = Form(...),
    job_url: str = Form(...),
    output_language: str = Form("english")
):
    """
    Tailor a CV for a specific job posting URL.

    Returns the tailored CV data and a download ID.
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found. Please upload your CV first.")

    if output_language not in ["english", "french"]:
        output_language = "english"

    try:
        api_key = get_api_key()
        session = sessions[session_id]
        parsed_cv = session["parsed_cv"]

        # Process the job URL and tailor the CV
        result = process_job_url(job_url, parsed_cv, api_key, output_language)

        # Generate PDF
        tailored_cv = result["tailored_cv"]
        filename = generate_filename(tailored_cv)
        output_path = OUTPUT_DIR / filename
        generate_cv_pdf(tailored_cv, str(output_path))

        # Generate download ID
        download_id = str(uuid.uuid4())

        # Store application record
        application = {
            "download_id": download_id,
            "job_url": job_url,
            "job_analysis": result["job_analysis"],
            "tailored_cv": tailored_cv,
            "output_filename": filename,
            "created_at": datetime.now().isoformat()
        }
        session["applications"].append(application)

        return {
            "download_id": download_id,
            "filename": filename,
            "job_analysis": result["job_analysis"],
            "tailored_cv": tailored_cv,
            "message": "CV tailored successfully"
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error tailoring CV: {str(e)}")


@app.get("/api/download/{download_id}")
async def download_cv(download_id: str):
    """
    Download a generated tailored CV PDF.
    """
    # Find the application with this download ID
    for session in sessions.values():
        for app in session.get("applications", []):
            if app["download_id"] == download_id:
                output_path = OUTPUT_DIR / app["output_filename"]
                if output_path.exists():
                    return FileResponse(
                        path=str(output_path),
                        filename=app["output_filename"],
                        media_type="application/pdf"
                    )

    raise HTTPException(status_code=404, detail="Download not found")


@app.get("/api/history/{session_id}")
async def get_history(session_id: str):
    """
    Get application history for a session.
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    return {
        "original_filename": session["original_filename"],
        "upload_time": session["upload_time"],
        "applications": [
            {
                "download_id": app["download_id"],
                "job_url": app["job_url"],
                "company": app["job_analysis"].get("company", {}).get("name", "Unknown"),
                "job_title": app["job_analysis"].get("job", {}).get("title", "Unknown"),
                "created_at": app["created_at"]
            }
            for app in session["applications"]
        ]
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    api_key_set = bool(os.environ.get("ANTHROPIC_API_KEY"))
    return {
        "status": "healthy",
        "api_key_configured": api_key_set
    }


# Serve frontend static files
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
