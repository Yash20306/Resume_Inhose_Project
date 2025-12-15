from fastapi import HTTPException
from app.repository.resume_repository import ResumeRepository
from app.repository.match_result_repository import MatchResultRepository
from app.repository.job_repository import JobRepository
from app.services.agent.email_automation_agent import EmailAutomationService  # 👈 import this
from app.services.utils.log import logger



# -------------------- 🧾 FETCH ALL CANDIDATES (Dashboard List) --------------------
async def get_all_candidates_controller():
    """
    Fetch all candidates with resume + job + match result info.

    Sorting:
    - LinkedIn Verified first
    - Then by highest accuracy

    (No filters applied here — filtering handled on frontend)
    """
    try:
        resumes = await ResumeRepository.find_all()
        match_results = await MatchResultRepository.find_all()
        jobs = await JobRepository.find_all()

        # Create lookup maps for quick reference
        job_map = {str(job["_id"]): job for job in jobs}
        resume_map = {str(res["_id"]): res for res in resumes}

        combined_data = []
        
        for result in match_results:
            resume = resume_map.get(result.get("resume_id"))
            job = job_map.get(result.get("job_id"))

            if not resume or not job:
                continue
            logger.debug(f"result is {result}")

            candidate_name = (
                resume.get("parsed_data", {}).get("name")
                or resume.get("file_name", "Unnamed Candidate")
            )
            raw_response = result.get("raw_response", {})
            if not isinstance(raw_response, dict):
                raw_response = {}

            combined_data.append({
                "match_result_id": str(result["_id"]),
                "candidate_name": candidate_name,
                "requirement": job.get("title", "N/A"),
                "accuracy_score": raw_response.get("accuracy_score"),
                "linkedin_verified": raw_response.get("linkedin_verified", False),
                "status": raw_response.get("status", "pending"),
                "resume_path": resume.get("file_path"),
                "job_id": str(job["_id"]),
                "resume_id": str(resume["_id"]),
                "job_title":str(job["title"])
            })
        # ✅ Sort by LinkedIn verified first, then accuracy descending
        combined_data.sort(
            key=lambda x: (
                1 if x.get("linkedin_verified") else 0,
                x.get("accuracy", 0)
            ),
            reverse=True
        )

        return {
            "total": len(combined_data),
            "candidates": combined_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching candidate list: {str(e)}")


# -------------------- 👤 FETCH SINGLE CANDIDATE DETAIL --------------------
async def get_candidate_detail_controller(match_result_id: str):
    """
    Returns full details for a specific candidate:
    - Resume data
    - Job data
    - Match result data
    """
    try:
        match = await MatchResultRepository.find_by_id(match_result_id)
        if not match:
            raise HTTPException(status_code=404, detail="Candidate match result not found")

        resume = await ResumeRepository.find_by_id(match.get("resume_id"))
        job = await JobRepository.find_by_id(match.get("job_id"))

        candidate_name = resume.get("parsed_data", {}).get("name", "N/A")

        return {
            "candidate_name": candidate_name,
            "linkedin_verified": match.get("linked_verified", False),
            "accuracy": match.get("accuracy", 0),
            "status": match.get("status", "pending"),
            "resume_data": resume,
            "job_data": job,
            "match_result": match,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching candidate details: {str(e)}")


# -------------------- ✅ ACCEPT / ❌ REJECT CANDIDATE --------------------
async def update_candidate_status_controller(match_result_id: str, status: str):
    """
    HR/Admin can accept or reject a candidate.
    After updating status, an AI-generated email is automatically sent.
    """
    # ✅ Validate allowed status
    allowed_status = ["accepted", "rejected"]
    if status not in allowed_status:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of {allowed_status}"
        )

    try:
        # ✅ Step 1: Update status in DB
        updated = await MatchResultRepository.update_match_result(
            match_result_id, {"status": status}
        )
        if not updated:
            raise HTTPException(status_code=404, detail="Candidate not found")

        # ✅ Step 2: Trigger email automation based on HR selection
        email_response = await EmailAutomationService.send_candidate_status_email(
            match_result_id, status
        )

        # ✅ Step 3: Build response
        return {
            "match_result_id": match_result_id,
            "new_status": status,
            "email_status": email_response.get("message", "Email process completed")
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating candidate status: {str(e)}"
        )
