from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime


class MatchResultCreate(BaseModel):
    job_id: str
    resume_id: str
    status: str = Field(..., description="pass or fail")
    reason: Optional[str] = None
    accuracy: Optional[float] = None
    raw_response: Optional[Dict] = None
    linkedin_verified: bool = False
    file_path: Optional[str] = None


class MatchResultResponse(BaseModel):
    id: str
    job_id: str
    resume_id: str
    status: str
    reason: Optional[str]
    accuracy: Optional[float]
    linkedin_verified: bool
    file_path: Optional[str]
    created_at: datetime
