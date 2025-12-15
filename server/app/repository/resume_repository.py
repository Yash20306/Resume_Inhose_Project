from datetime import datetime
from app.config.database import db
from bson import ObjectId
from fastapi import HTTPException


class ResumeRepository:
    """
    Handles CRUD operations for resumes in MongoDB.
    """

    @staticmethod
    async def create_resume(resume_data: dict):
        """
        Saves parsed resume data to the 'resumes' collection.
        """
        try:
            resume_data["uploaded_at"] = datetime.utcnow()
            result = await db.resumes.insert_one(resume_data)
            return str(result.inserted_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save resume: {str(e)}")

    @staticmethod
    async def find_all(limit: int = 100):
        """
        Returns all stored resumes.
        """
        try:
            resumes = await db.resumes.find().sort("uploaded_at", -1).to_list(length=limit)
            for r in resumes:
                r["_id"] = str(r["_id"])
            return resumes
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to fetch resumes: {str(e)}")
        

    @staticmethod
    async def find_by_id(resume_id: str):
        """
        Finds a resume by its MongoDB ObjectId.
        """
        try:
            resume = await db.resumes.find_one({"_id": ObjectId(resume_id)})
            if not resume:
                raise HTTPException(status_code=404, detail="Resume not found")

            resume["_id"] = str(resume["_id"])
            return resume
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid resume ID or database error: {str(e)}")


    @staticmethod
    async def find_by_email(email: str):
        """
        Finds a resume by email if available.
        """
        try:
            resume = await db.resumes.find_one({"email": email})
            if resume:
                resume["_id"] = str(resume["_id"])
            return resume
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to fetch resume: {str(e)}")

    @staticmethod
    async def delete_resume(resume_id: str):
        """
        Deletes a resume document by its ID.
        """
        try:
            result = await db.resumes.delete_one({"_id": ObjectId(resume_id)})
            if result.deleted_count == 0:
                raise HTTPException(status_code=404, detail="Resume not found")
            return True
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid resume ID format: {str(e)}")
