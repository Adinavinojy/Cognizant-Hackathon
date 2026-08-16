"""
Pydantic schemas for /dashboard and /study-plan endpoints.
"""

from datetime import datetime
from uuid import UUID
from typing import List, Optional

from pydantic import BaseModel


class TopicProgressOut(BaseModel):
    id: UUID
    user_id: UUID
    topic_id: UUID
    avg_score: Optional[float] = None
    attempts_count: int
    last_updated: datetime

    model_config = {"from_attributes": True}


class StudyPlanOut(BaseModel):
    id: UUID
    user_id: UUID
    topic_id: UUID
    priority_rank: int
    recommended_resources: Optional[List[str]] = None
    generated_at: datetime

    model_config = {"from_attributes": True}
