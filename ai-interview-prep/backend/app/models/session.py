"""
ORM models: mock_sessions and session_questions tables.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class MockSession(Base):
    __tablename__ = "mock_sessions"

    session_id: uuid.UUID = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: uuid.UUID = Column(
        UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True
    )
    role_id: uuid.UUID = Column(
        UUID(as_uuid=True), ForeignKey("job_roles.role_id"), nullable=False
    )
    started_at: datetime = Column(DateTime, nullable=False, default=datetime.utcnow)
    ended_at: datetime = Column(DateTime, nullable=True)
    status: str = Column(String(50), nullable=False, default="active")  # active | completed
    
    # Session Configuration
    mode: str = Column(String(50), nullable=False, default="normal") # normal | rapid
    question_count: int = Column(Integer, nullable=False, default=5)
    tech_stacks = Column(JSONB, nullable=True) # List of topic names/IDs tested in this session
    
    # Session Results
    overall_score: float = Column(Float, nullable=True)

    session_questions = relationship("SessionQuestion", back_populates="session")


class SessionQuestion(Base):
    __tablename__ = "session_questions"

    id: uuid.UUID = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: uuid.UUID = Column(
        UUID(as_uuid=True), ForeignKey("mock_sessions.session_id"), nullable=False, index=True
    )
    question_id: uuid.UUID = Column(
        UUID(as_uuid=True), ForeignKey("questions.question_id"), nullable=False
    )
    order_index: int = Column(Integer, nullable=False)
    
    # Track individual question status (especially for rapid mode)
    status: str = Column(String(50), nullable=False, default="unattempted") # unattempted | attempted | timed_out
    time_spent_seconds: int = Column(Integer, nullable=False, default=0)

    # Nullable FK — used when a question is a follow-up to a specific answer
    follow_up_of_answer_id: uuid.UUID = Column(
        UUID(as_uuid=True), ForeignKey("answers.answer_id"), nullable=True
    )

    session = relationship("MockSession", back_populates="session_questions")
