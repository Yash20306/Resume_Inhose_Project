from datetime import datetime

from app.config.database import db  
from bson import ObjectId


class UserSessionRepository:
    @staticmethod
    async def create_session(session_data: dict):
        result = await db.user_sessions.insert_one(session_data)
        return result.inserted_id

    @staticmethod
    async def update_session(user_id: str, session_id: str, update_data: dict):
        result = await db.user_sessions.update_one(
            {"user_id": user_id, "_id": ObjectId(session_id)}, {"$set": update_data}
        )
        return result.modified_count > 0

    @staticmethod
    async def find_session_by_id(user_id: str, session_id: str):
        return await db.user_sessions.find_one(
            {"user_id": user_id, "_id": ObjectId(session_id)}
        )

    @staticmethod
    async def find_sessions_by_user_id(user_id: str):
        return await db.user_sessions.find({"user_id": user_id}).to_list(length=100)

    @staticmethod
    async def find_active_sessions(user_id: str):
        return await db.user_sessions.find(
            {"user_id": user_id, "logout_time": None}
        ).to_list(length=100)
