from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class User(BaseModel):
    id: str
    full_name: str
    email: EmailStr
    hashed_password: str  
    last_login: Optional[datetime]
    last_logout: Optional[datetime]
    is_email_verified: bool = False
    otp: Optional[str] = None
    otp_created_at: Optional[datetime] = None

class Admin(BaseModel):
    email: EmailStr
    password: str
    exists: Optional[bool] = False

