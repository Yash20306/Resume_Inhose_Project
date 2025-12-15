from datetime import datetime
from app.config.database import db
from bson import ObjectId
from fastapi import HTTPException


class MatchResultRepository:
    """
    Handles CRUD operations for match results in MongoDB.
    """

    # -------------------- CREATE --------------------
    @staticmethod
    async def create_match_result(match_data: dict):
        """
        Saves the match result (comparison between resume & job).
        """
        try:
            match_data["created_at"] = datetime.utcnow()
            result = await db.match_results.insert_one(match_data)
            return str(result.inserted_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save match result: {str(e)}")

    # -------------------- READ ALL --------------------
    @staticmethod
    async def find_all(limit: int = 100):
            try:
                results = await db.match_results.find().sort("created_at", -1).to_list(length=limit)
                for result in results:
                    result["_id"] = str(result["_id"])
                return results
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to fetch match results: {str(e)}")

    # -------------------- READ BY JOB ID --------------------
    @staticmethod
    async def find_by_job_id(job_id: str):
        """
        Finds all match results for a given job ID.
        """
        try:
            results = await db.match_results.find({"job_id": ObjectId(job_id)}).to_list(length=100)
            for r in results:
                r["_id"] = str(r["_id"])
            return results
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid job ID format")

    # -------------------- READ BY ID (for HR dashboard) --------------------
    @staticmethod
    async def find_by_id(result_id: str):
        """
        Finds a single match result by its ID.
        """
        try:
            result = await db.match_results.find_one({"_id": ObjectId(result_id)})
            if not result:
                raise HTTPException(status_code=404, detail="Match result not found")
            result["_id"] = str(result["_id"])
            return result
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid match result ID format")

    # -------------------- UPDATE STATUS (accept/reject) --------------------
    @staticmethod
    async def update_match_result(result_id: str, update_data: dict):
        """
        Updates a match result (e.g., change status to accepted/rejected).
        """
        try:
            result = await db.match_results.update_one(
                {"_id": ObjectId(result_id)},
                {"$set": update_data}
            )
            if result.matched_count == 0:
                raise HTTPException(status_code=404, detail="Match result not found")
            return True
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to update match result: {str(e)}")

    # -------------------- DELETE --------------------
    @staticmethod
    async def delete_match_result(result_id: str):
        """
        Deletes a match result by its ID.
        """
        try:
            result = await db.match_results.delete_one({"_id": ObjectId(result_id)})
            if result.deleted_count == 0:
                raise HTTPException(status_code=404, detail="Match result not found")
            return True
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid match result ID format: {str(e)}")
