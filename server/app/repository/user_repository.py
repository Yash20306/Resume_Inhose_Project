from datetime import datetime, timedelta
from app.config.database import db
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException

class UserRepository:
    @staticmethod
    async def find_by_email(email: str):
        """
        Finds a user by email or ObjectId string.
        - If 'email' contains '@', search by email field.
        - Otherwise, treat it as an ObjectId.
        """
        try:
            if "@" in email:
                # Search by email field
                return await db.users.find_one({"email": email})
            else:
                # Search by ObjectId
                return await db.users.find_one({"_id": ObjectId(email)})
        except Exception as e:
            # Log or raise if needed
            print(f"Error in find_by_email: {e}")
            return None
            
    @staticmethod
    async def create_user(user: dict):
        result = await db.users.insert_one(user)
        return str(result.inserted_id)

    @staticmethod
    async def save_otp(email: str, otp: str):
        return await db.users.update_one(
            {"email": email},
            {"$set": {"otp": otp, "otp_created_at": datetime.utcnow()}}
        )

    @staticmethod
    async def verify_otp(email: str, otp: str):
        user = await db.users.find_one({"email": email})

        if not user or user.get("otp") != otp:
            return False

        otp_created = user.get("otp_created_at")
        if not otp_created or (datetime.utcnow() - otp_created).total_seconds() > 300:
            return False

        await db.users.update_one(
            {"email": email},
            {"$set": {"is_email_verified": True, "is_mobile_verified": True},
             "$unset": {"otp": "", "otp_created_at": ""}}
        )
        return True

    @staticmethod
    async def is_email_verified(email: str) -> bool:
        user = await db.users.find_one({"email": email})
        return bool(user and user.get("is_email_verified", False))
