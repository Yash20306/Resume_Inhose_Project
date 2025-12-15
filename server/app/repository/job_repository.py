from datetime import datetime
from bson import ObjectId
from fastapi import HTTPException
from app.config.database import db
from app.models.job_model import Job


class JobRepository:
    """
    Repository for handling CRUD operations on the 'jobs' collection.
    """

    @staticmethod
    async def create_job(job_data: dict):
        """
        Inserts a new job record into the database.
        """
        try:
            job_data["created_at"] = datetime.utcnow()
            job_data["is_active"] = True
            result = await db.jobs.insert_one(job_data)
            return str(result.inserted_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")

    @staticmethod
    async def find_by_id(job_id: str):
        """
        Finds a job by its ID.
        """
        try:
            job = await db.jobs.find_one({"_id": ObjectId(job_id)})
            if not job:
                raise HTTPException(status_code=404, detail="Job not found")
            job["_id"] = str(job["_id"])
            return job
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid job ID format or error: {str(e)}")

    @staticmethod
    async def find_all(limit: int = 100):
        """
        Fetches all jobs up to a specified limit.
        """
        try:
            jobs = await db.jobs.find().sort("created_at", -1).to_list(length=limit)
            for job in jobs:
                job["_id"] = str(job["_id"])
            return jobs
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch jobs: {str(e)}")

    @staticmethod
    async def find_latest():
        """
        Returns the most recently created job.
        """
        try:
            job = await db.jobs.find_one(sort=[("created_at", -1)])
            if not job:
                raise HTTPException(status_code=404, detail="No job found")
            job["_id"] = str(job["_id"])
            return job
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch latest job: {str(e)}")

    @staticmethod
    async def update_job(job_id: str, update_data: dict):
        """
        Updates an existing job record by ID.
        """
        try:
            result = await db.jobs.update_one(
                {"_id": ObjectId(job_id)},
                {"$set": update_data}
            )
            if result.matched_count == 0:
                raise HTTPException(status_code=404, detail="Job not found")
            return True
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to update job: {str(e)}")

    @staticmethod
    async def delete_job(job_id: str):
        """
        Deletes a job by its ID.
        """
        try:
            result = await db.jobs.delete_one({"_id": ObjectId(job_id)})
            if result.deleted_count == 0:
                raise HTTPException(status_code=404, detail="Job not found")
            return True
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to delete job: {str(e)}")
