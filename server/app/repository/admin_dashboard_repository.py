from datetime import datetime
from bson import ObjectId
from fastapi import HTTPException
from app.config.database import db


class AdminDashboardRepository:
    """
    Repository for fetching and managing combined candidate/job/match data
    for the HR Admin Dashboard.
    """

    @staticmethod
    async def get_dashboard_data(
        job_title: str = None,
        linkedin_verified: bool = None,
        min_accuracy: float = None
    ):
        """
        Fetch combined data of resumes, match results, and jobs with optional filters.
        Ordered by LinkedIn verified first and highest accuracy.

        Args:
            job_title (str, optional): Filter by job title keyword
            linkedin_verified (bool, optional): Filter LinkedIn verified candidates
            min_accuracy (float, optional): Minimum accuracy threshold

        Returns:
            List[dict]: Candidate + job + match data
        """
        try:
            # Fetch all match results with resume and job references
            pipeline = [
                {
                    "$lookup": {
                        "from": "resumes",
                        "localField": "resume_id",
                        "foreignField": "_id",
                        "as": "resume_info"
                    }
                },
                {"$unwind": "$resume_info"},
                {
                    "$lookup": {
                        "from": "jobs",
                        "localField": "job_id",
                        "foreignField": "_id",
                        "as": "job_info"
                    }
                },
                {"$unwind": "$job_info"},
            ]

            results = await db.match_results.aggregate(pipeline).to_list(length=500)

            # Apply filters
            filtered = []
            for item in results:
                job = item.get("job_info", {})
                resume = item.get("resume_info", {})
                match = item

                # --- Filtering ---
                if job_title and job_title.lower() not in job.get("title", "").lower():
                    continue
                if linkedin_verified is not None and match.get("linkedin_verified") != linkedin_verified:
                    continue
                if min_accuracy is not None and match.get("accuracy", 0) < min_accuracy:
                    continue

                # --- Formatting ---
                filtered.append({
                    "candidate_name": resume.get("parsed_data", {}).get("name") or "N/A",
                    "resume_file": resume.get("file_name"),
                    "job_title": job.get("title"),
                    "requirement_file": job.get("file_path"),
                    "match_result": match.get("raw_response", {}),
                    "accuracy": match.get("accuracy"),
                    "linkedin_verified": match.get("linkedin_verified", False),
                    "status": match.get("status"),
                    "reason": match.get("reason"),
                    "uploaded_at": resume.get("uploaded_at"),
                    "job_created_at": job.get("created_at"),
                })

            # --- Sorting ---
            filtered.sort(
                key=lambda x: (
                    1 if x.get("linkedin_verified") else 0,
                    x.get("accuracy", 0)
                ),
                reverse=True
            )

            return filtered

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching dashboard data: {str(e)}")

    # -----------------------------------------------------------------
    @staticmethod
    async def update_candidate_status(candidate_id: str, new_status: str):
        """
        Updates a candidate’s match result status (accept/reject).
        """
        try:
            result = await db.match_results.update_one(
                {"_id": ObjectId(candidate_id)},
                {"$set": {"status": new_status, "updated_at": datetime.utcnow()}}
            )

            if result.matched_count == 0:
                raise HTTPException(status_code=404, detail="Candidate not found")

            return {"message": f"Candidate status updated to '{new_status}'."}

        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error updating candidate status: {str(e)}")
