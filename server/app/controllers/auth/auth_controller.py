from datetime import datetime, timezone
from bson import ObjectId
from fastapi import HTTPException

from app.models.user.user_model import User
from app.repository.user_repository import UserRepository
from app.repository.user_session_repository import UserSessionRepository
from app.schemas.auth.user_schema import UserCreate, VerifyEmailSchema , AdminLogin , UserLogin
from app.services.auth.auth_service import AuthService


class AuthController:
    @staticmethod
    async def register(user_data: UserCreate):
        existing_user = await UserRepository.find_by_email(user_data.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        hashed_pw = AuthService.hash_password(user_data.password)

        user_dict = {
            "_id": ObjectId(),
            "full_name": user_data.full_name,
            "email": user_data.email,
            "hashed_password": hashed_pw,
            "is_email_verified": False,
            "is_mobile_verified": False,
            "created_at": datetime.now(timezone.utc),
        }

        inserted_id = await UserRepository.create_user(user_dict)

        try:
            await AuthService.create_and_send_otp(user_data.email)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to send OTP: {e}")

        return {
            "message": "User registered successfully. Please verify your email with the OTP sent.",
            "user_id": str(inserted_id),
        }

    @staticmethod
    async def login(user_data: UserLogin):
        user = await UserRepository.find_by_email(user_data.email)
        if not user or not AuthService.verify_password(user_data.password, user["hashed_password"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not user.get("is_email_verified", False):
            raise HTTPException(
                status_code=403,
                detail="Email not verified. Please verify your email before login."
            )

        user_id = str(user["_id"])
        token = AuthService.create_token({"sub": user_id})
        current_time = datetime.now(timezone.utc)

        session_dict = {
            "user_id": user_id,
            "login_time": current_time,
            "logout_time": None,
            "token": token,
        }
        session_id = await UserSessionRepository.create_session(session_dict)

        return {
            "access_token": token,
            "token_type": "bearer",
            "session_id": str(session_id),
        }

    @staticmethod
    async def verify_email_otp(data: VerifyEmailSchema):
        try:
            is_verified = await AuthService.verify_email_otp(data.email, data.otp)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error verifying OTP: {e}")

        if not is_verified:
            raise HTTPException(status_code=400, detail="Invalid or expired OTP")

        return {"message": "Email verified successfully. Mobile is also verified automatically."}

    @staticmethod
    async def resend_otp(email: str):
        user = await UserRepository.find_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user.get("is_email_verified", False):
            raise HTTPException(status_code=400, detail="Email already verified")

        try:
            await AuthService.create_and_send_otp(email)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to resend OTP: {e}")

        return {"message": "OTP resent successfully. Please check your email."}


    @staticmethod
    async def admin_login(admin_data: AdminLogin):
        """
        Admin login using predefined credentials.
        Returns JWT token if successful.
        """
        auth_result = await AuthService.admin_login(admin_data.email, admin_data.password)

        if not auth_result["is_authenticated"]:
            raise HTTPException(status_code=401, detail=auth_result["message"])

        # Create a JWT token for admin
        token = AuthService.create_token({"sub": admin_data.email, "role": "admin"})
        current_time = datetime.now(timezone.utc)

        # Store admin session in DB if required
        session_dict = {
            "user_id": admin_data.email,
            "login_time": current_time,
            "logout_time": None,
            "token": token,
            "role": "admin"
        }
        # Optional: create session in DB
        # session_id = await UserSessionRepository.create_session(session_dict)

        return {
            "access_token": token,
            "token_type": "bearer",
            "message": auth_result["message"],
            # "session_id": str(session_id),  # optional
        }

