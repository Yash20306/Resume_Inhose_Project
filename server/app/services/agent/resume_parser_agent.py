import json
import os
import pymupdf
from docx import Document
from app.config.config import settings


# -------------------- TEXT EXTRACTION --------------------

def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX resume."""
    doc = Document(file_path)
    return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF resume using PyMuPDF."""
    text = ""
    pdf = pymupdf.open(file_path)
    for page in pdf:
        text += page.get_text("text")
    pdf.close()
    return text.strip()


# -------------------- GEMINI AI RESUME PARSING --------------------

def parse_resume_with_gemini(resume_text: str) -> dict:
    """
    Parse raw resume text into detailed structured JSON using Gemini.
    """
    prompt = f"""
    You are an expert Resume Parsing AI.
    Analyze the resume text carefully and extract detailed structured information.

    Return STRICTLY in this JSON format:
    {{
      "name": "Full name of the candidate",
      "email": "Primary valid email address",
      "phone": "Primary phone number with country code if available",
      "linkedin": "LinkedIn profile URL if mentioned, else empty string",
      "skills": ["list", "of", "key", "technical and soft skills"],
      "education": [
        {{
          "degree": "e.g. B.Tech in Computer Science",
          "institute": "e.g. IIT Delhi",
          "year": "e.g. 2022"
        }}
      ],
      "experience": [
        {{
          "company": "Company Name",
          "role": "Job Title",
          "duration": "e.g. Jan 2021 - Dec 2023",
          "responsibilities": ["list", "of", "main", "responsibilities"]
        }}
      ],
      "certifications": ["List of relevant certifications, if any"],
      "projects": [
        {{
          "title": "Project title",
          "description": "Brief description of the project"
        }}
      ],
      "summary": "Brief professional summary (if available)"
    }}

    Ensure output is valid JSON without any commentary or markdown fences.

    Resume Text:
    {resume_text}
    """

    response = settings.llm.invoke(prompt)
    text = response.content.strip()

    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(text)
    except Exception:
        return {"raw_response": text}


# -------------------- GEMINI AI MATCHING --------------------

def check_match(requirement_text: str, parsed_resume: dict) -> dict:
    """
    Compare job requirement with parsed resume using Gemini.
    Returns detailed structured JSON including accuracy score and analysis.
    """
    prompt = f"""
    You are a job matching assistant.
    Compare the following job requirement with the parsed resume data and provide
    a structured, detailed evaluation.

    Consider:
    - Skill relevance
    - Experience alignment
    - Education suitability
    - Project/Certification relevance
    - Presence of verified links (e.g. LinkedIn)
    - Overall match confidence (accuracy score)

    Respond STRICTLY in this JSON format:
    {{
      "status": "pass" or "fail",
      "accuracy_score": 0-100,
      "reason": "Summary of why candidate passed or failed",
      "strengths": ["key areas where candidate matches well"],
      "weaknesses": ["key areas where candidate falls short"],
      "linked_profile_verified": true or false,
      "detailed_comparison": {{
        "skills_match": "percentage of matching skills",
        "experience_match": "evaluation summary",
        "education_match": "evaluation summary",
        "project_relevance": "short summary"
      }},
      "recommendation": "short recruiter recommendation (1-2 sentences)"
    }}

    Job Requirement:
    {requirement_text}

    Resume Data:
    {json.dumps(parsed_resume, indent=2)}

    Return ONLY the JSON. Do not include any explanations or markdown formatting.
    """

    response = settings.llm.invoke(prompt)
    text = response.content.strip()

    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(text)
    except Exception:
        return {"raw_response": text}


# -------------------- MAIN PIPELINE FUNCTION --------------------

def process_resume_and_match(resume_path: str, requirement_path: str) -> dict:
    """
    Complete workflow:
      1. Extract resume text (.docx or .pdf)
      2. Parse resume using Gemini
      3. Compare with requirement text
    """
    if resume_path.endswith(".docx"):
        resume_text = extract_text_from_docx(resume_path)
    elif resume_path.endswith(".pdf"):
        resume_text = extract_text_from_pdf(resume_path)
    else:
        raise ValueError("Unsupported resume format. Must be .docx or .pdf")

    parsed_resume = parse_resume_with_gemini(resume_text)

    with open(requirement_path, "r", encoding="utf-8") as f:
        requirement_text = f.read()

    match_result = check_match(requirement_text, parsed_resume)

    return {
        "parsed_resume": parsed_resume,
        "match_result": match_result
    }
