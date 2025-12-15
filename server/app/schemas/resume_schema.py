from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime


class ResumeCreate(BaseModel):
    user_id: Optional[str] = None
    job_id: Optional[str] = None
    file_name: str
    file_path: str
    file_type: str
    parsed_data: Optional[Dict] = None
    skills: Optional[List[str]] = []
    raw_text: Optional[str] = None


class ResumeResponse(BaseModel):
    id: str
    user_id: Optional[str]
    job_id: Optional[str]
    file_name: str
    file_path: str
    file_type: str
    skills: Optional[List[str]] = []
    uploaded_at: datetime
