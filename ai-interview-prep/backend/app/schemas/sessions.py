"""
Pydantic schemas for /sessions endpoint.
"""

from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel


class SessionCreate(BaseModel):
    user_id: UUID
    role_id: UUID


class SessionOut(BaseModel):
    session_id: UUID
    user_id: UUID
    role_id: UUID
    started_at: datetime
    ended_at: Optional[datetime] = None
    status: str

    model_config = {"from_attributes": True}
