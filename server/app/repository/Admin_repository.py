from datetime import datetime
from fastapi import HTTPException
from app.repository.Admin_session_repository import AdminSessionRepository
from app.config.config import settings

class AdminRepository:
    @staticmethod
    async def verify_admin(email: str, password: str) -> bool:
        """
        Check if provided email/password match the predefined admin credentials from settings.
        """
        return email == settings.ADMIN_EMAIL and password == settings.ADMIN_PASSWORD

    @staticmethod
    async def exists(email: str) -> bool:
        """
        Check if admin exists (predefined, so return True if email matches)
        """
        return email == settings.ADMIN_EMAIL

