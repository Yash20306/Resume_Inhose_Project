from pydantic import BaseModel, EmailStr
from typing import Optional


class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    """Used for user login — only email and password required"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    full_name: str    
    email: EmailStr
    is_email_verified: bool


class VerifyEmailSchema(BaseModel):
    email: EmailStr
    otp: str


class OTPRequest(BaseModel):
    email: EmailStr


class OTPResponse(BaseModel):
    email: EmailStr
    otp_expiry: Optional[int] = 5  
    message: str



class AdminLogin(BaseModel):
    email: EmailStr
    password: str


class AdminResponse(BaseModel):
    email: EmailStr
    is_authenticated: bool
    message: Optional[str] = None
