# app/schemas/admin_dashboard_schema.py
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class CandidateResume(BaseModel):
    resume_id: str
    candidate_name: str
    resume_file: Optional[str] = None
    linkedin_verified: bool = False
    accuracy_score: Optional[float] = None
    status: str = "Pending"


class JobRequirement(BaseModel):
    job_id: str
    job_title: str
    requirement_file: Optional[str] = None


class MatchResultSchema(BaseModel):
    match_result_file: Optional[str] = None
    accuracy_score: Optional[float] = None
    linkedin_verified: bool = False


class AdminDashboardResponse(BaseModel):
    candidate_name: str
    job_title: str
    resume_file: Optional[str]
    requirement_file: Optional[str]
    match_result_file: Optional[str]
    accuracy_score: Optional[float]
    linkedin_verified: bool
    status: str
    created_at: datetime


class AdminDashboardListResponse(BaseModel):
    total_candidates: int
    candidates: List[AdminDashboardResponse]
