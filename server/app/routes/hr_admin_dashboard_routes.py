from fastapi import APIRouter, HTTPException, Path, Query
from app.views.response_formatter import format_response
from app.controllers.hr_admin_dashboard_controller import (
    get_all_candidates_controller,
    get_candidate_detail_controller,
    update_candidate_status_controller,
)

router = APIRouter(prefix="/hr-admin", tags=["HR Admin Dashboard"])


# -------------------- 🧾 FETCH ALL CANDIDATES --------------------
@router.get("/candidates")
async def get_all_candidates():
    """
    📋 Fetch ALL candidates for the HR/Admin dashboard.

    Includes:
    - Candidate Name
    - Requirement (Job Title)
    - Resume Info
    - Match Result
    - Accuracy
    - LinkedIn Verification
    - Status (Accepted / Rejected / Pending)

    ⚙️ Ordered by:
    1️⃣ LinkedIn Verified (True first)
    2️⃣ Accuracy (Descending)

    🧭 Note:
    - Filtering and searching handled on the frontend.
    """
    try:
        data = await get_all_candidates_controller()
        return format_response(data, message="✅ All candidates fetched successfully")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching candidates: {str(e)}")


# -------------------- 👤 FETCH SINGLE CANDIDATE DETAIL --------------------
@router.get("/candidates/{match_result_id}")
async def get_candidate_detail(
    match_result_id: str = Path(..., description="MongoDB ID of the match result"),
):
    """
    👤 Fetch detailed information about a specific candidate.

    Returns:
    - Candidate Personal Info (from Resume)
    - Job Requirement Details
    - Match Result Data
    - AI Accuracy, Status, and LinkedIn Verification

    💡 Used when HR clicks on a candidate row to view their detailed profile.
    """
    try:
        data = await get_candidate_detail_controller(match_result_id)
        return format_response(data, message="✅ Candidate details fetched successfully")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching candidate detail: {str(e)}")


# -------------------- ✅ ACCEPT / ❌ REJECT CANDIDATE --------------------
@router.put("/candidates/{matchResultId}/status")
async def update_candidate_status(
    matchResultId: str = Path(..., description="MongoDB ID of the match result"),
    status: str = Query(
        ...,
        description="Decision: accepted or rejected",
        enum=["accepted", "rejected"],   # 👈 clean dropdown instead of regex
        example="accepted"
    ),
):
    """
    🔄 Update candidate’s hiring status (✅ Accept / ❌ Reject).

    On status update:
    - Updates the candidate status in the database.
    - Triggers Gemini-powered AI email generation.
    - Automatically sends a personalized email to the candidate:
        - Acceptance email if status = accepted
        - Rejection email if status = rejected

    📧 The email includes:
    - Candidate name
    - Job title
    - Professional HR message
    - Link to their match analysis page
    """
    try:
        data = await update_candidate_status_controller(matchResultId, status)
        return format_response(data, message=f"✅ Candidate marked as {status}")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating candidate status: {str(e)}")
