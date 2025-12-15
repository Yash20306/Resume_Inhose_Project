from datetime import datetime
from typing import Optional, Dict, List
from pydantic import BaseModel, Field

class Resume(BaseModel):
    id: str
    user_id: Optional[str] = None
    job_id: Optional[str] = None
    file_name: str
    file_path: str
    file_type: str
    parsed_data: Optional[Dict] = None
    skills: Optional[List[str]] = []
    raw_text: Optional[str] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
