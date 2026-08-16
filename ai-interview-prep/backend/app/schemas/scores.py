"""
Pydantic schemas for /scores endpoint.
"""

from uuid import UUID
from typing import List, Optional

from pydantic import BaseModel


class ScoreOut(BaseModel):
    score_id: UUID
    answer_id: UUID
    similarity_score: Optional[float] = None
    llm_judge_score: Optional[float] = None
    concept_match_score: Optional[float] = None
    fused_score: Optional[float] = None
    human_calibrated_score: Optional[float] = None
    feedback_text: Optional[str] = None
    missing_keywords: Optional[List[str]] = None

    model_config = {"from_attributes": True}
