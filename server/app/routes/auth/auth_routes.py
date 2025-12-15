from fastapi import APIRouter, Body
from app.controllers.auth.auth_controller import AuthController
from app.schemas.auth.user_schema import UserCreate, VerifyEmailSchema, OTPRequest , UserLogin
from app.views.response_formatter import format_response
from pydantic import BaseModel
from app.schemas.auth.user_schema import AdminLogin

router = APIRouter(prefix="", tags=["Auth"])  

@router.post("/register")
async def register(user: UserCreate):
    result = await AuthController.register(user)
    return format_response(result, message="User registered successfully")

@router.post("/login")
async def login(user: UserLogin):
    result = await AuthController.login(user)
    return format_response(result, message="Login successful")

@router.post("/admin/login")
async def admin_login(admin_data: AdminLogin):
    """
    Admin login endpoint using predefined credentials.
    """
    result = await AuthController.admin_login(admin_data)
    return format_response(result, message=result.get("message", "Admin login processed"))

@router.post("/verify-otp")
async def verify_otp(data: VerifyEmailSchema):
    result = await AuthController.verify_email_otp(data)
    return format_response(result, message="Email verified successfully. Mobile verified automatically.")


class ResendOtpSchema(BaseModel):
    email: str

@router.post("/resend-otp")
async def resend_otp(data: ResendOtpSchema = Body(...)):
    result = await AuthController.resend_otp(data.email)
    return format_response(result, message="OTP resent successfully. Please check your email.")
