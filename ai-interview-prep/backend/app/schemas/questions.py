"""
Pydantic schemas for /questions endpoint.
"""

from uuid import UUID
from typing import Optional

from pydantic import BaseModel


class QuestionOut(BaseModel):
    question_id: UUID
    topic_id: UUID
    role_id: UUID
    question_text: str
    reference_answer: Optional[str] = None
    difficulty: Optional[str] = None
    source: Optional[str] = None

    model_config = {"from_attributes": True}
