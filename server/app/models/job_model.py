# models/job_model.py
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class Job(BaseModel):
    id: str
    title: str
    description: str
    responsibilities: Optional[List[str]] = []
    requirements: Optional[List[str]] = []
    skills: Optional[List[str]] = []
    qualifications: Optional[List[str]] = []
    location: Optional[str] = None
    employment_type: Optional[str] = None
    min_experience: Optional[int] = None
    max_experience: Optional[int] = None
    recruiter_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
