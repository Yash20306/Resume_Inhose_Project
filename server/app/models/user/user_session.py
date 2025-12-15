from datetime import datetime
from typing import Optional

from bson import ObjectId
from pydantic import BaseModel


class UserSession(BaseModel):
    user_id: str  # Refers to the user
    login_time: datetime
    logout_time: Optional[datetime] = None
    token: str  # JWT token for the session