# app/models/admin_dashboard_model.py
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class AdminDashboardModel(BaseModel):
    candidate_id: str
    candidate_name: str
    resume_id: str
    job_id: str
    job_title: str
    requirement_file: Optional[str] = None
    resume_file: Optional[str] = None
    match_result_file: Optional[str] = None
    accuracy_score: Optional[float] = None
    linkedin_verified: bool = False
    status: Optional[str] = Field(default="Pending", description="Accepted / Rejected / Pending")
    created_at: datetime = Field(default_factory=datetime.utcnow)
