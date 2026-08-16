"""
Pydantic schemas for answers (posted under /sessions/{id}/answers).
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AnswerCreate(BaseModel):
    question_id: UUID
    user_id: UUID
    answer_text: str


class AnswerOut(BaseModel):
    answer_id: UUID
    session_id: UUID
    question_id: UUID
    user_id: UUID
    answer_text: str
    submitted_at: datetime

    model_config = {"from_attributes": True}
