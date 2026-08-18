"""
Pydantic schemas for /sessions endpoint.
"""

from datetime import datetime
from uuid import UUID
from typing import Optional, List

from pydantic import BaseModel


from app.schemas.questions import QuestionOut

class SessionCreate(BaseModel):
    user_id: UUID
    role_id: UUID
    mode: str = "normal"
    question_count: int = 5
    tech_stacks: List[str] = []


class SessionQuestionOut(BaseModel):
    session_question_id: UUID
    order_index: int
    status: str
    time_spent_seconds: int
    question: QuestionOut

    model_config = {"from_attributes": True}


class SessionOut(BaseModel):
    session_id: UUID
    user_id: UUID
    role_id: UUID
    started_at: datetime
    ended_at: Optional[datetime] = None
    status: str
    mode: str
    question_count: int
    tech_stacks: Optional[List[str]] = []
    questions: List[SessionQuestionOut] = []

    model_config = {"from_attributes": True}
