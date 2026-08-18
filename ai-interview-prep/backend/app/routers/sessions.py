"""
Router: /sessions
Creates and returns a mock session object and generates questions adaptively.
"""

import uuid
import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.session import MockSession, SessionQuestion
from app.models.role_topic import JobRole, Topic
from app.models.progress import TopicProgress
from app.schemas.sessions import SessionCreate, SessionOut, SessionQuestionOut
from app.schemas.questions import QuestionOut as QuestionSchema
from app.services.question_generation import generate_question_batch, GenerationError

log = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=SessionOut, status_code=201)
def create_session(payload: SessionCreate, db: Session = Depends(get_db)) -> SessionOut:
    """
    Creates a MockSession, determines adaptive difficulty based on progress,
    generates a batch of questions, and saves them to the DB.
    """
    # 1. Validate Job Role
    role = db.query(JobRole).filter(JobRole.role_id == payload.role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="JobRole not found")
        
    role_name = role.role_name

    # 2. Determine topics to test
    topics_to_test = payload.tech_stacks
    if not topics_to_test:
        # Default to all topics for this role
        role_topics = db.query(Topic).filter(Topic.role_id == role.role_id).all()
        topics_to_test = [t.topic_name for t in role_topics]

    if not topics_to_test:
        raise HTTPException(status_code=400, detail="No topics provided and role has no default topics.")

    # 3. Read TopicProgress to determine adaptive difficulty
    topic_difficulties = []
    
    # We need to distribute `question_count` across `topics_to_test`
    # Simple round-robin distribution
    distribution = {t: 0 for t in topics_to_test}
    for i in range(payload.question_count):
        distribution[topics_to_test[i % len(topics_to_test)]] += 1

    for topic_name, count in distribution.items():
        if count == 0:
            continue
            
        # Get progress
        progress = db.query(TopicProgress).join(Topic).filter(
            TopicProgress.user_id == payload.user_id,
            Topic.topic_name == topic_name,
            TopicProgress.attempts_count > 0
        ).first()

        difficulty = "Easy" # Default for untested
        if progress and progress.avg_score is not None:
            if progress.avg_score >= 0.70:
                difficulty = "Hard"
            elif progress.avg_score >= 0.40:
                difficulty = "Medium"
            else:
                difficulty = "Easy"

        for _ in range(count):
            topic_difficulties.append({"topic": topic_name, "difficulty": difficulty})

    # 4. Generate the batch of questions
    try:
        generated_questions = generate_question_batch(role_name, topic_difficulties)
    except GenerationError as e:
        log.error("Failed to generate questions: %s", e)
        raise HTTPException(status_code=500, detail="Could not generate questions. Please try again.")

    if not generated_questions:
        raise HTTPException(status_code=500, detail="Generated empty question list.")

    # 5. Save MockSession
    new_session = MockSession(
        session_id=uuid.uuid4(),
        user_id=payload.user_id,
        role_id=payload.role_id,
        started_at=datetime.utcnow(),
        status="active",
        mode=payload.mode,
        question_count=payload.question_count,
        tech_stacks=payload.tech_stacks
    )
    db.add(new_session)
    db.commit()

    # 6. Save SessionQuestions
    # Note: For this prototype we store the question text/answer directly in the SessionQuestion or Question table.
    # Since we use `Question` schema from Pydantic but our DB has a questions table...
    # Wait, does `questions` table exist? Let's check `models.question` if it exists.
    # Actually, we should import `Question` model.
    # We will persist to `questions` and then link to `session_questions`.
    from app.models.question import Question
    
    session_questions_out = []
    
    for i, q in enumerate(generated_questions):
        # Find the topic_id for this question's topic string.
        # If the LLM used a slightly different topic name (e.g. "Caching" vs "Docker"),
        # create the topic on-the-fly so the FK constraint is never violated.
        topic_db = db.query(Topic).filter(
            Topic.topic_name == q.topic, Topic.role_id == payload.role_id
        ).first()
        if not topic_db:
            # Also try a case-insensitive match
            topic_db = db.query(Topic).filter(
                Topic.topic_name.ilike(q.topic), Topic.role_id == payload.role_id
            ).first()
        if not topic_db:
            # Create the topic on-the-fly so we never use a fake UUID
            topic_db = Topic(
                topic_id=uuid.uuid4(),
                role_id=payload.role_id,
                topic_name=q.topic
            )
            db.add(topic_db)
            db.flush()  # flush so topic_db.topic_id is populated before we reference it

        # Create Question in DB
        db_question = Question(
            question_id=uuid.UUID(q.id),
            role_id=payload.role_id,
            topic_id=topic_db.topic_id,
            difficulty=q.difficulty,
            question_text=q.question_text,
            reference_answer=q.reference_answer
        )
        db.add(db_question)
        
        # Create SessionQuestion link
        db_sq = SessionQuestion(
            id=uuid.uuid4(),
            session_id=new_session.session_id,
            question_id=db_question.question_id,
            order_index=i,
            status="unattempted",
            time_spent_seconds=0
        )
        db.add(db_sq)
        
        session_questions_out.append(
            SessionQuestionOut(
                session_question_id=db_sq.id,
                order_index=db_sq.order_index,
                status=db_sq.status,
                time_spent_seconds=db_sq.time_spent_seconds,
                question=db_question
            )
        )

    db.commit()

    return SessionOut(
        session_id=new_session.session_id,
        user_id=new_session.user_id,
        role_id=new_session.role_id,
        started_at=new_session.started_at,
        status=new_session.status,
        mode=new_session.mode,
        question_count=new_session.question_count,
        tech_stacks=new_session.tech_stacks,
        questions=session_questions_out
    )
