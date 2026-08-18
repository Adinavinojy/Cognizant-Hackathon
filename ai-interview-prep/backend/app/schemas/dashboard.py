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


class SessionHistoryOut(BaseModel):
    session_id: UUID
    started_at: datetime
    mode: str
    overall_score: Optional[float] = None
    question_count: int

    model_config = {"from_attributes": True}


class DashboardStatsOut(BaseModel):
    total_sessions: int
    highest_score: Optional[float] = None
    average_score: Optional[float] = None
    history: List[SessionHistoryOut] = []


class SkillItem(BaseModel):
    topic_name: str
    avg_score: float
    attempts: int


class DashboardSkillsOut(BaseModel):
    strengths: List[SkillItem] = []      # > 0.70
    average: List[SkillItem] = []        # 0.40 - 0.70
    weaknesses: List[SkillItem] = []     # < 0.40


class StudyPlanOut(BaseModel):
    id: UUID
    user_id: UUID
    topic_id: UUID
    priority_rank: int
    recommended_resources: Optional[List[str]] = None
    generated_at: datetime

    model_config = {"from_attributes": True}
