"""
schemas.py — the ONE shared contract file for PrepIQ.

All 3 pods import from this file. Do not redefine these shapes locally
in your own pod's code — import them from here.

Any change to this file must be flagged to the other two pod merge-owners
before pushing (Varghese/Biju/Adina for ai-pipeline, Essa for scoring,
Paul for dashboard) — a silent change here breaks all three pods at once.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel
from sqlalchemy import Column, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base

# ---------------------------------------------------------------------------
# Contract 1: Question object
# Produced by: AI Pipeline pod (/questions/next)
# Consumed by: Data & Scoring pod, Dashboard pod
# ---------------------------------------------------------------------------

class Question(BaseModel):
    id: str
    role: str
    topic: str
    difficulty: str
    question_text: str
    reference_answer: str


# ---------------------------------------------------------------------------
# Contract 2: Scored answer
# Produced by: Data & Scoring pod (/answers/submit)
# Consumed by: Dashboard pod, AI Pipeline pod (missing_concepts, for follow-up)
# ---------------------------------------------------------------------------

class ScoredAnswer(BaseModel):
    session_id: str
    question_id: str
    user_answer: str
    cosine_score: float
    llm_judge_score: float
    final_score: float
    missing_concepts: List[str]
    topic: str
    timestamp: datetime


# ---------------------------------------------------------------------------
# Contract 3: SQLite schema (SQLAlchemy models)
# Owned by: Dashboard pod (Paul) — only Paul runs migrations against this.
# Read by: everyone, via SQLAlchemy.
# ---------------------------------------------------------------------------

Base = declarative_base()


class MockSession(Base):
    __tablename__ = "mock_sessions"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)


class Answer(Base):
    __tablename__ = "answers"

    session_id = Column(String, ForeignKey("mock_sessions.id"), primary_key=True)
    question_id = Column(String, primary_key=True)
    user_answer = Column(String, nullable=True)
    cosine_score = Column(Float, nullable=True)
    llm_judge_score = Column(Float, nullable=True)
    score = Column(Float, nullable=True)          # = final_score
    missing_concepts = Column(String, nullable=True)  # store as comma-separated string
    topic = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)