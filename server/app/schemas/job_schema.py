from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class JobCreate(BaseModel):
    title: str
    summary: str
    location: Optional[str] = None
    min_experience: Optional[int] = None
    max_experience: Optional[int] = None
    employment_type: Optional[str] = None


class JobGeneratedResponse(BaseModel):
    title: str
    description: str
    responsibilities: List[str]
    requirements: List[str]
    skills: List[str]
    qualifications: List[str]
    location: Optional[str]
    employment_type: Optional[str]
    min_experience: Optional[int]
    max_experience: Optional[int]


class JobResponse(BaseModel):
    id: str
    title: str
    description: str
    location: Optional[str]
    employment_type: Optional[str]
    is_active: bool
    created_at: datetime
