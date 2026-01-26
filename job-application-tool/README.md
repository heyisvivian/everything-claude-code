# Job Application Tool

AI-powered CV tailoring tool that analyzes job postings and generates customized CVs optimized for each role.

## Features

- **PDF CV Upload**: Upload your existing CV in PDF format
- **Job URL Analysis**: Paste a job posting URL - the tool scrapes and analyzes both the job requirements and company information
- **AI-Powered Tailoring**: Uses Claude AI to rewrite your CV, emphasizing relevant skills and experience
- **Professional PDF Output**: Generates a clean, professional PDF CV ready for submission
- **Application History**: Track all the jobs you've applied to

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Set Your API Key

```bash
# Windows
set ANTHROPIC_API_KEY=your-api-key-here

# Mac/Linux
export ANTHROPIC_API_KEY=your-api-key-here
```

### 3. Run the Server

```bash
cd backend
uvicorn main:app --reload
```

### 4. Open the App

Navigate to http://localhost:8000 in your browser.

## How It Works

1. **Upload CV**: Drag and drop your PDF CV or click to browse
2. **CV Parsing**: AI extracts and structures your CV content (experience, skills, education, etc.)
3. **Enter Job URL**: Paste the URL of the job posting you're applying for
4. **Job Analysis**: AI scrapes the posting and analyzes:
   - Company name, industry, and culture
   - Job requirements (must-have and nice-to-have skills)
   - Key responsibilities and keywords
5. **CV Tailoring**: AI rewrites your CV to:
   - Highlight relevant experience and achievements
   - Incorporate job-specific keywords naturally
   - Reorder sections by relevance
   - Adjust tone to match company culture
6. **Download**: Get your tailored CV as a professional PDF

## Project Structure

```
job-application-tool/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── cv_parser.py         # PDF parsing logic
│   ├── cv_tailor.py         # AI-powered CV customization
│   ├── cv_generator.py      # PDF generation
│   └── requirements.txt
├── frontend/
│   ├── index.html           # Main UI
│   ├── styles.css           # Styling
│   └── app.js               # Frontend logic
├── uploads/                 # Temporary CV storage
├── outputs/                 # Generated tailored CVs
└── README.md
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/upload-cv` | POST | Upload and parse a PDF CV |
| `/api/tailor` | POST | Tailor CV for a job posting URL |
| `/api/download/{id}` | GET | Download a generated CV |
| `/api/history/{session_id}` | GET | Get application history |
| `/api/health` | GET | Health check |

## Tech Stack

- **Backend**: FastAPI (Python)
- **PDF Parsing**: pdfplumber
- **AI**: Claude API (Anthropic)
- **PDF Generation**: ReportLab
- **Web Scraping**: BeautifulSoup4
- **Frontend**: Vanilla HTML/CSS/JavaScript

## Configuration

The tool requires an Anthropic API key set as the `ANTHROPIC_API_KEY` environment variable.

All CV data is processed locally and stored temporarily. Generated PDFs are saved in the `outputs/` directory.

## Tips for Best Results

1. **Use a text-based PDF**: Scanned image PDFs may not parse correctly
2. **Include detailed experience**: The more details in your CV, the better the AI can tailor it
3. **Use direct job URLs**: LinkedIn, company career pages, and job boards all work
4. **Review the output**: Always review and verify the tailored CV before submitting

## Troubleshooting

**"ANTHROPIC_API_KEY not configured"**
- Ensure you've set the environment variable before starting the server

**"Could not fetch the job posting"**
- Some websites block scraping. Try copying the job description and creating a simple HTML file locally

**"Could not extract text from PDF"**
- Your PDF may be image-based (scanned). Convert it to text-based PDF first

## License

MIT
