"""
Router: /dashboard
Endpoints for user statistics, session history, and skill breakdowns.
"""

import uuid
import logging
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.database import get_db
from app.models.session import MockSession
from app.models.progress import TopicProgress
from app.models.role_topic import Topic
from app.schemas.dashboard import (
    DashboardStatsOut, 
    SessionHistoryOut, 
    DashboardSkillsOut, 
    SkillItem
)

log = logging.getLogger(__name__)
router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/{user_id}/stats", response_model=DashboardStatsOut)
def get_dashboard_stats(user_id: uuid.UUID, db: Session = Depends(get_db)) -> DashboardStatsOut:
    """
    Returns aggregate statistics and a history of all sessions for a user.
    """
    sessions = db.query(MockSession).filter(
        MockSession.user_id == user_id,
        MockSession.status == "completed"
    ).order_by(desc(MockSession.started_at)).all()

    total_sessions = len(sessions)
    
    if total_sessions == 0:
        return DashboardStatsOut(
            total_sessions=0,
            highest_score=None,
            average_score=None,
            history=[]
        )

    # Calculate highest and average
    valid_scores = [s.overall_score for s in sessions if s.overall_score is not None]
    highest_score = max(valid_scores) if valid_scores else None
    average_score = sum(valid_scores) / len(valid_scores) if valid_scores else None

    # Format history
    history = [
        SessionHistoryOut(
            session_id=s.session_id,
            started_at=s.started_at,
            mode=s.mode,
            overall_score=s.overall_score,
            question_count=s.question_count
        )
        for s in sessions
    ]

    return DashboardStatsOut(
        total_sessions=total_sessions,
        highest_score=highest_score,
        average_score=average_score,
        history=history
    )


@router.get("/{user_id}/skills", response_model=DashboardSkillsOut)
def get_dashboard_skills(user_id: uuid.UUID, db: Session = Depends(get_db)) -> DashboardSkillsOut:
    """
    Returns the user's skills grouped into strengths, average, and weaknesses.
    """
    progress_rows = db.query(TopicProgress, Topic).join(
        Topic, TopicProgress.topic_id == Topic.topic_id
    ).filter(
        TopicProgress.user_id == user_id,
        TopicProgress.attempts_count > 0,
        TopicProgress.avg_score.isnot(None)
    ).all()

    strengths = []
    average = []
    weaknesses = []

    for progress, topic in progress_rows:
        item = SkillItem(
            topic_name=topic.topic_name,
            avg_score=progress.avg_score,
            attempts=progress.attempts_count
        )
        
        if progress.avg_score >= 0.70:
            strengths.append(item)
        elif progress.avg_score >= 0.40:
            average.append(item)
        else:
            weaknesses.append(item)

    # Sort descending by score within each bucket
    strengths.sort(key=lambda x: x.avg_score, reverse=True)
    average.sort(key=lambda x: x.avg_score, reverse=True)
    weaknesses.sort(key=lambda x: x.avg_score, reverse=True)

    return DashboardSkillsOut(
        strengths=strengths,
        average=average,
        weaknesses=weaknesses
    )
