"""
Job Application Tool - FastAPI Backend
Tailors CVs for job applications using AI.
Generates both English and French versions with salary info.
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
HISTORY_FILE = Path(__file__).parent.parent / "history.json"

# Ensure directories exist
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# In-memory storage for session data
sessions = {}


def load_history() -> dict:
    """Load persistent history from JSON file."""
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"applications": []}
    return {"applications": []}


def save_history(history: dict):
    """Save history to JSON file."""
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


app = FastAPI(
    title="Job Application Tool",
    description="AI-powered CV tailoring for job applications",
    version="2.0.0"
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
    job_url: str = Form(...)
):
    """
    Tailor a CV for a specific job posting URL.
    Generates BOTH English and French versions.
    Returns download IDs for both, plus salary info.
    """
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found. Please upload your CV first.")

    try:
        api_key = get_api_key()
        session = sessions[session_id]
        parsed_cv = session["parsed_cv"]

        # Process the job URL and tailor both CVs
        result = process_job_url(job_url, parsed_cv, api_key)

        # Generate English PDF
        tailored_cv_en = result["tailored_cv_english"]
        filename_en = generate_filename(tailored_cv_en, "english")
        output_path_en = OUTPUT_DIR / filename_en
        generate_cv_pdf(tailored_cv_en, str(output_path_en), "english")

        # Generate French PDF
        tailored_cv_fr = result["tailored_cv_french"]
        filename_fr = generate_filename(tailored_cv_fr, "french")
        output_path_fr = OUTPUT_DIR / filename_fr
        generate_cv_pdf(tailored_cv_fr, str(output_path_fr), "french")

        # Generate download IDs
        download_id_en = str(uuid.uuid4())
        download_id_fr = str(uuid.uuid4())

        # Store application record
        application = {
            "id": str(uuid.uuid4()),
            "job_url": job_url,
            "job_analysis": result["job_analysis"],
            "salary_info": result["salary_info"],
            "tailoring_notes": result["tailoring_notes"],
            "english": {
                "download_id": download_id_en,
                "filename": filename_en
            },
            "french": {
                "download_id": download_id_fr,
                "filename": filename_fr
            },
            "created_at": datetime.now().isoformat()
        }
        session["applications"].append(application)

        # Save to persistent history
        history = load_history()
        history["applications"].append({
            "id": application["id"],
            "job_url": job_url,
            "company": result["job_analysis"].get("company", {}).get("name", "Unknown"),
            "job_title": result["job_analysis"].get("job", {}).get("title", "Unknown"),
            "location": result["job_analysis"].get("job", {}).get("location", "Unknown"),
            "salary_info": result["salary_info"],
            "download_id_en": download_id_en,
            "download_id_fr": download_id_fr,
            "filename_en": filename_en,
            "filename_fr": filename_fr,
            "created_at": application["created_at"]
        })
        save_history(history)

        return {
            "download_id_en": download_id_en,
            "download_id_fr": download_id_fr,
            "filename_en": filename_en,
            "filename_fr": filename_fr,
            "job_analysis": result["job_analysis"],
            "salary_info": result["salary_info"],
            "tailoring_notes": result["tailoring_notes"],
            "message": "CVs tailored successfully in English and French"
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
    # Check session applications
    for session in sessions.values():
        for app in session.get("applications", []):
            if app["english"]["download_id"] == download_id:
                output_path = OUTPUT_DIR / app["english"]["filename"]
                if output_path.exists():
                    return FileResponse(
                        path=str(output_path),
                        filename=app["english"]["filename"],
                        media_type="application/pdf"
                    )
            if app["french"]["download_id"] == download_id:
                output_path = OUTPUT_DIR / app["french"]["filename"]
                if output_path.exists():
                    return FileResponse(
                        path=str(output_path),
                        filename=app["french"]["filename"],
                        media_type="application/pdf"
                    )

    # Check persistent history
    history = load_history()
    for app in history.get("applications", []):
        if app.get("download_id_en") == download_id:
            output_path = OUTPUT_DIR / app["filename_en"]
            if output_path.exists():
                return FileResponse(
                    path=str(output_path),
                    filename=app["filename_en"],
                    media_type="application/pdf"
                )
        if app.get("download_id_fr") == download_id:
            output_path = OUTPUT_DIR / app["filename_fr"]
            if output_path.exists():
                return FileResponse(
                    path=str(output_path),
                    filename=app["filename_fr"],
                    media_type="application/pdf"
                )

    raise HTTPException(status_code=404, detail="Download not found")


@app.get("/api/history")
async def get_all_history():
    """
    Get all application history (persistent).
    """
    history = load_history()
    return {
        "applications": history.get("applications", [])
    }


@app.get("/api/history/{session_id}")
async def get_session_history(session_id: str):
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
                "id": app["id"],
                "job_url": app["job_url"],
                "company": app["job_analysis"].get("company", {}).get("name", "Unknown"),
                "job_title": app["job_analysis"].get("job", {}).get("title", "Unknown"),
                "location": app["job_analysis"].get("job", {}).get("location", "Unknown"),
                "salary_info": app.get("salary_info", {}),
                "download_id_en": app["english"]["download_id"],
                "download_id_fr": app["french"]["download_id"],
                "created_at": app["created_at"]
            }
            for app in session["applications"]
        ]
    }


@app.delete("/api/history/{application_id}")
async def delete_application(application_id: str):
    """
    Delete an application from history.
    """
    history = load_history()
    history["applications"] = [
        app for app in history["applications"]
        if app.get("id") != application_id
    ]
    save_history(history)
    return {"message": "Application deleted"}


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
