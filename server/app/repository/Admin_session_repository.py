from datetime import datetime
from app.config.database import db  

class AdminSessionRepository:
    @staticmethod
    async def create_session(session_data: dict):
        result = await db.admin_sessions.insert_one(session_data)
        return result.inserted_id

    @staticmethod
    async def update_session_by_email(admin_email: str, update_data: dict):
        """
        Update the latest active session for the admin (where logout_time is None)
        """
        session = await db.admin_sessions.find_one(
            {"user_id": admin_email, "logout_time": None},
            sort=[("_id", -1)]  # get latest session
        )
        if not session:
            return None
        await db.admin_sessions.update_one(
            {"_id": session["_id"]},
            {"$set": update_data}
        )
        return await db.admin_sessions.find_one({"_id": session["_id"]})

    @staticmethod
    async def find_active_sessions(admin_email: str):
        return await db.admin_sessions.find(
            {"user_id": admin_email, "logout_time": None}
        ).to_list(length=100)
