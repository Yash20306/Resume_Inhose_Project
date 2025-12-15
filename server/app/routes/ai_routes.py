from fastapi import APIRouter, UploadFile, File, Form, Body , Path
from app.controllers.ai_controller import (
    parse_resume_controller,
    find_candidates_controller
)
from app.views.response_formatter import format_response
from app.repository.job_repository import JobRepository
from app.controllers.ai_controller import (
    create_job_summary_controller,
    get_job_details_controller,
    post_job_to_db_controller,
)
from app.services.utils.log import logger

# Create Router
router = APIRouter()


# -------------------- 1️⃣ JOB CREATION --------------------
# 1️⃣ Generate job preview (summary → detailed requirement)
@router.post("/summary")
async def generate_job_summary(
    title: str = Form(...),
    summary: str = Form(...),
    experience: str = Form(...),
    location: str = Form(...),
    employment_type: str = Form(...),
):
    """
    Generates a detailed job requirement (without saving to DB).
    Used for frontend preview.
    """
    return await create_job_summary_controller(
        title=title,
        summary=summary,
        experience=experience,
        location=location,
        employment_type=employment_type
    )

# 3️⃣ Post job to DB (when HR clicks 'Post')
@router.post("/post")
async def post_job_to_db(
    job_data: dict = Body(..., description="Full job data to store in DB")
):
    """
    Saves generated job requirement to DB and file.
    """
    logger.debug(f"data:{job_data}")
    return await post_job_to_db_controller(job_data)


# 2️⃣ Get job details (for preview / fetch existing job)
@router.get("/details/{job_id}")
async def get_job_details(job_id: str = Path(..., description="MongoDB Job ID")):
    """
    Fetch a saved job requirement by ID.
    """
    return await get_job_details_controller(job_id)


# -------------------- 2️⃣ GET ALL JOBS --------------------
@router.get("/jobs/list")
async def list_all_jobs():
    """
    Fetch all job listings from the database.
    Used by frontend to populate the dropdown for selecting requirement file.
    """
    try:
        jobs = await JobRepository.find_all()
        return format_response(
            data={"jobs": jobs},
            message=f"✅ {len(jobs)} job(s) fetched successfully"
        )
    except Exception as e:
        return format_response(None, message=f"❌ Error fetching jobs: {str(e)}")


# -------------------- 3️⃣ RESUME PARSING --------------------
@router.post("/resume/parse")
async def parse_resume(
    resume: UploadFile = File(...),
    job_id: str = Form(...)
):
    """
    Upload a resume (PDF/DOCX) and match it with a selected job requirement (by job_id).
    """
    result = await parse_resume_controller(
        resume=resume,
        job_id=job_id
    )
    return result


# -------------------- 4️⃣ FIND CANDIDATES --------------------
@router.post("/candidates/find")
async def find_candidates(
    requirement_file: UploadFile = File(...),
    global_search: bool = Body(False),
    top_n: int = Body(5)
):
    """
    Finds top candidate resumes from uploads/resumes against a given requirement.
    """
    result = await find_candidates_controller(
        requirement_file=requirement_file,
        global_search=global_search,
        top_n=top_n
    )
    return result
