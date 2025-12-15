import os
import json
from datetime import datetime
from fastapi import UploadFile, File, Form, Body
from app.repository.job_repository import JobRepository
from app.views.response_formatter import format_response
from app.repository.resume_repository import ResumeRepository
from app.repository.match_result_repository import MatchResultRepository
from app.services.agent import (
    generate_job_details,
    generate_search_keywords,
    parse_resume_with_gemini,
    check_match, 
)
from app.services.agent.candidate_finder_agent import find_candidates,find_candidates_via_apollo,find_local_candidates
from app.services.agent.resume_parser_agent import (
    extract_text_from_pdf,
    extract_text_from_docx
)
from fastapi import HTTPException
from app.config.config import settings
from app.services.utils.log import logger
# # -------------------- PATH SETUP --------------------
UPLOAD_FOLDER = settings.UPLOAD_FOLDER
REQUIREMENT_FOLDER = settings.REQUIREMENT_FOLDER
RESUME_FOLDER = settings.RESUME_FOLDER
MATCH_RESULT = settings.MATCH_RESULT

async def create_job_summary_controller(
    title: str,
    summary: str,
    experience: str,
    location: str,
    employment_type: str,
):
    """
    Generates a detailed job requirement (preview) but does NOT store it in DB.
    Used for frontend preview before posting.
    """
    try:
        # Step 1: Generate job details
        job_details = generate_job_details(
            summary_text=summary,
            title=title,
            experience=experience,
            location=location,
            employment_type=employment_type
        )

        # Step 2: Generate search keywords
        search_data = generate_search_keywords(job_details)
        job_details.update(search_data)

        # Step 3: Return formatted response
        return format_response(
            data=job_details,
            message="✅ Job requirement preview generated successfully"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating job preview: {str(e)}"
        )
# -------------------- 2️⃣ FETCH DETAILED JOB DESCRIPTION --------------------
async def list_all_jobs(job_id: str):
    """
    Fetch job details from MongoDB using job_id (for preview/display).
    """
    try:
        job = await JobRepository.find_by_id(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        return format_response(job, message="✅ Job details fetched successfully")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching job details: {str(e)}")
    



# -------------------- 3️⃣ POST JOB TO DATABASE --------------------
async def post_job_to_db_controller(job_data: dict):
    """
    Saves the generated job requirement to DB and writes it to a file.
    Handles wrapped responses like:
    - {"status": "success", "message": "...", "data": {...}}
    - {"additionalProp1": {"status": "...", "message": "...", "data": {...}}}
    - {"anyKey": {"data": {...}}}
    """
    try:
        logger.debug(f"{job_data}")
        os.makedirs(REQUIREMENT_FOLDER, exist_ok=True)

        print("DEBUG incoming job_data keys:", list(job_data.keys()))

        job_info = None

        # ✅ Case 1: Directly has 'data'
        if "data" in job_data:
            job_info = job_data["data"]

        # ✅ Case 2: Find the first nested object that has 'data'
        elif any(isinstance(v, dict) and "data" in v for v in job_data.values()):
            for v in job_data.values():
                if isinstance(v, dict) and "data" in v:
                    job_info = v["data"]
                    break

        # ✅ Case 3: Handle any single nested dict (like {"additionalProp1": {...}})
        elif len(job_data) == 1:
            first_val = next(iter(job_data.values()))
            if isinstance(first_val, dict):
                job_info = first_val.get("data", first_val)

        # ✅ Default fallback
        if job_info is None:
            job_info = job_data

        # ✅ Validate essential field
        title = job_info.get("title")
        if not title:
            raise ValueError(f"Missing title in job data. Keys received: {list(job_info.keys())}")

        # ✅ Handle default experience & filename
        experience = job_info.get("experience", "N/A")
        filename = f"{title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        file_path = os.path.join(REQUIREMENT_FOLDER, filename)

        # ✅ Helper: Safe join
        def safe_join(value):
            if isinstance(value, list):
                return ", ".join(str(v) for v in value)
            return str(value or "")

        # ✅ Write to text file
        requirement_text = (
            f"Title: {job_info.get('title')}\n"
            f"Description: {job_info.get('description')}\n"
            f"Responsibilities: {safe_join(job_info.get('responsibilities'))}\n"
            f"Requirements: {safe_join(job_info.get('requirements'))}\n"
            f"Skills: {safe_join(job_info.get('skills'))}\n"
            f"Qualifications: {safe_join(job_info.get('qualifications'))}\n"
            f"Location: {job_info.get('location')}\n"
            f"Employment Type: {job_info.get('employment_type')}\n"
            f"Experience: {job_info.get('experience')}\n"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(requirement_text)

        job_record = {
            **job_info,
            "file_path": file_path,
            "created_at": datetime.utcnow()
        }

        job_id = await JobRepository.create_job(job_record)

        return format_response(
            {"job_id": job_id, "file_path": file_path},
            message="✅ Job requirement saved successfully"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error posting job: {str(e)}")


async def get_job_details_controller(job_id: str):
    """
    Fetch job requirement by ID.
    Reads the saved text file and returns a structured preview (not just the file path).
    """

    # Fetch job record from MongoDB
    job = await JobRepository.find_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="❌ Job not found in database")

    file_path = job.get("file_path")
    if not file_path:
        raise HTTPException(status_code=400, detail="⚠️ Job file path missing for this job")

    # Construct absolute file path
    abs_path = os.path.join(REQUIREMENT_FOLDER, os.path.basename(file_path))

    # Verify that file exists
    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="❌ Job file not found on server")

    # Read file content
    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"⚠️ Error reading job file: {str(e)}")

    # Parse the text into structured data
    parsed_data = parse_job_text(content)

    return format_response(
        data=parsed_data,
        message="✅ Job requirement preview generated successfully"
    )


def parse_job_text(text: str):
    """
    Parse the text content of the job file into structured key-value pairs.
    """
    sections = {}
    current_key = None

    # Define recognized section headers
    keys = [
        "Title", "Description", "Responsibilities", "Requirements",
        "Skills", "Qualifications", "Location", "Employment Type", "Experience"
    ]

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        # Detect new section headers like "Title:" or "Description:"
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()

            if key in keys:
                current_key = key
                if value:
                    sections[key] = value
                else:
                    sections[key] = []
                continue

        # Add subsequent lines to the current section
        if current_key:
            if isinstance(sections[current_key], list):
                cleaned_line = line.lstrip("-• ").strip()
                sections[current_key].append(cleaned_line)
            else:
                sections[current_key] += f" {line}"

    # Convert parsed text into clean structured JSON
    return {
        "title": sections.get("Title", ""),
        "description": sections.get("Description", ""),
        "responsibilities": sections.get("Responsibilities", []),
        "requirements": sections.get("Requirements", []),
        "skills": sections.get("Skills", []),
        "qualifications": sections.get("Qualifications", []),
        "location": sections.get("Location", ""),
        "employment_type": sections.get("Employment Type", ""),
        "experience": sections.get("Experience", "")
    }

async def parse_resume_controller(
    resume: UploadFile = File(...),
    job_id: str = Form(...),
):
    """
    Parses a resume (PDF/DOCX), compares it with a selected existing job requirement
    (chosen from DB or /uploads/requirements), and stores the structured results in MongoDB.
    """

    try:
        # ✅ Validate file type
        if not resume.filename.lower().endswith((".pdf", ".docx")):
            return format_response(None, message="Resume must be a .pdf or .docx file")

        # ✅ Fetch selected job from DB
        job_data = await JobRepository.find_by_id(job_id)
        
        if not job_data:
            return format_response(None, message="Selected job not found in database")

        requirement_path = job_data.get("file_path")
        if not requirement_path or not os.path.exists(requirement_path):
            return format_response(None, message="Requirement file not found on server")

        # ✅ Save uploaded resume
        os.makedirs(RESUME_FOLDER, exist_ok=True)
        resume_path = os.path.join(RESUME_FOLDER, resume.filename)
        with open(resume_path, "wb") as buffer:
            buffer.write(await resume.read())

        # ✅ Read requirement file content
        with open(requirement_path, "r", encoding="utf-8") as f:
            requirement_text = f.read().strip()

        # ✅ Extract and parse resume
        resume_text = (
            extract_text_from_pdf(resume_path)
            if resume.filename.lower().endswith(".pdf")
            else extract_text_from_docx(resume_path)
        )

        parsed_resume = parse_resume_with_gemini(resume_text)
        match_result = check_match(requirement_text, parsed_resume)

        # ✅ Determine LinkedIn verification
        linkedin_verified = bool(
            parsed_resume.get("linkedin_url") and "linkedin.com" in parsed_resume["linkedin_url"].lower()
        )

        # ✅ Save parsed resume to DB
        resume_record = {
            "file_name": resume.filename,
            "file_path": resume_path,
            "file_type": "pdf" if resume.filename.lower().endswith(".pdf") else "docx",
            "parsed_data": parsed_resume,
            "skills": parsed_resume.get("skills", []),
            "raw_text": resume_text,
            "uploaded_at": datetime.utcnow(),
        }
        resume_id = await ResumeRepository.create_resume(resume_record)

        # ✅ Save match result to DB
        match_record = {
            "resume_id": resume_id,
            "job_id": job_id,
            "status": match_result.get("status", "unknown"),
            "reason": match_result.get("reason", ""),
            "accuracy": match_result.get("accuracy", 0),
            "raw_response": match_result,
            "linked_verified": linkedin_verified,
            "created_at": datetime.utcnow(),
        }
        await MatchResultRepository.create_match_result(match_record)

        return format_response(
            data={
                "parsed_resume": parsed_resume,
                "match_result": match_result,
                "linkedin_verified": linkedin_verified,
                "resume_id": resume_id,
                "job_id": job_id,
            },
            message="✅ Resume parsed and matched successfully"
        )

    except Exception as e:
        return format_response(None, message=f"❌ Error while parsing resume: {str(e)}")


       
def find_local_candidates(job_details: dict, resumes_folder: str = RESUME_FOLDER) -> list:
    """
    Matches local resumes from the 'uploads' folder against the given job description.
    """
    matched = []

    if not os.path.exists(resumes_folder):
        return matched

    for file_name in os.listdir(resumes_folder):
        if not (file_name.lower().endswith(".pdf") or file_name.lower().endswith(".docx")):
            continue

        file_path = os.path.join(resumes_folder, file_name)
        try:
            text = extract_text_from_pdf(file_path) if file_name.lower().endswith(".pdf") else extract_text_from_docx(file_path)
            parsed_resume = parse_resume_with_gemini(text)
            match_result = check_match(job_details.get("description", ""), parsed_resume)

            matched.append({
                "file_name": file_name,
                "parsed_resume": parsed_resume,
                "match_result": match_result
            })
        except Exception as e:
            print(f"❌ Failed to process local resume {file_name}: {e}")

    matched.sort(
        key=lambda x: (
            1 if isinstance(x.get("match_result", {}), dict) and x["match_result"].get("status") == "pass" else 0
        ),
        reverse=True
    )

    return matched


def find_local_candidates(job_details: dict, resumes_folder: str = RESUME_FOLDER) -> list:
    """
    Matches local resumes from the 'uploads' folder against the given job description.
    """
    matched = []

    if not os.path.exists(resumes_folder):
        return matched

    for file_name in os.listdir(resumes_folder):
        if not (file_name.lower().endswith(".pdf") or file_name.lower().endswith(".docx")):
            continue

        file_path = os.path.join(resumes_folder, file_name)
        try:
            text = extract_text_from_pdf(file_path) if file_name.lower().endswith(".pdf") else extract_text_from_docx(file_path)
            parsed_resume = parse_resume_with_gemini(text)
            match_result = check_match(job_details.get("description", ""), parsed_resume)

            matched.append({
                "file_name": file_name,
                "parsed_resume": parsed_resume,
                "match_result": match_result
            })
        except Exception as e:
            print(f"❌ Failed to process local resume {file_name}: {e}")

    matched.sort(
        key=lambda x: (
            1 if isinstance(x.get("match_result", {}), dict) and x["match_result"].get("status") == "pass" else 0
        ),
        reverse=True
    )

    return matched


async def find_candidates_controller(
    requirement_file: UploadFile = File(...),
    global_search: bool = False,
    top_n: int = 5
):
    """
    Finds best candidate resumes from local 'uploads' folder or global search
    against an uploaded requirement file.
    """
    try:
        if not requirement_file.filename.endswith(".txt"):
            return format_response(
                None,
                message="Invalid file type. Please upload a .txt requirement file"
            )

        os.makedirs(REQUIREMENT_FOLDER, exist_ok=True)
        requirement_path = os.path.join(REQUIREMENT_FOLDER, requirement_file.filename)

        # Save uploaded requirement file
        with open(requirement_path, "wb") as f:
            f.write(await requirement_file.read())

        # Read requirement text
        with open(requirement_path, "r", encoding="utf-8") as f:
            requirement_text = f.read()

        job_details = {"description": requirement_text}

        # Decide search type
        if global_search:
            candidates = await find_candidates_via_apollo(job_details)
        else:
            candidates = find_local_candidates(job_details)

        top_candidates = candidates[:top_n]

        return format_response(
            {
                "total_candidates": len(top_candidates),
                "candidates": top_candidates
            },
            message=f"Top {len(top_candidates)} candidates found successfully"
        )

    except Exception as e:
        return format_response(
            None,
            message=f"Error occurred while finding candidates: {str(e)}"
        )
