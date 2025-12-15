from datetime import datetime
from typing import Optional, Dict
from pydantic import BaseModel, Field

class MatchResult(BaseModel):
    id: str
    job_id: str
    resume_id: str
    status: str = Field(..., description="pass or fail")
    reason: Optional[str] = None
    accuracy: Optional[float] = None
    raw_response: Optional[Dict] = None
    linkedin_verified: bool = False
    file_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
