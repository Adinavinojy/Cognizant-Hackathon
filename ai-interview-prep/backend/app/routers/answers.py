"""
Router: POST /sessions/{session_id}/answers and POST /answers/submit
Accepts a submitted answer, runs the 3-signal scoring pipeline, persists Answer and Score records to DB,
updates student TopicProgress, and returns ScoreOut.
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.answer import Answer as AnswerModel
from app.models.question import Question as QuestionModel
from app.models.score import Score as ScoreModel
from app.models.progress import TopicProgress as TopicProgressModel
from app.schemas.answers import AnswerCreate, AnswerOut
from app.schemas.scores import ScoreOut
from app.services.scoring import score_answer

router = APIRouter()


class AnswerSubmitPayload(BaseModel):
    session_id: Optional[uuid.UUID] = None
    question_id: uuid.UUID
    user_id: uuid.UUID
    answer_text: str


def _process_answer_submission(
    session_id: uuid.UUID,
    question_id: uuid.UUID,
    user_id: uuid.UUID,
    answer_text: str,
    db: Session
) -> ScoreOut:
    # 1. Create and persist Answer ORM model
    answer_record = AnswerModel(
        answer_id=uuid.uuid4(),
        session_id=session_id,
        question_id=question_id,
        user_id=user_id,
        answer_text=answer_text,
        submitted_at=datetime.utcnow(),
    )
    db.add(answer_record)
    db.commit()
    db.refresh(answer_record)

    # 2. Look up question details for scoring
    question = db.query(QuestionModel).filter(QuestionModel.question_id == question_id).first()
    question_text = question.question_text if question else "Answer evaluation"
    reference_answer = question.reference_answer if question else ""
    topic_id = question.topic_id if question else None

    # 3. Run multi-signal scoring pipeline
    score_results = score_answer(
        answer_text=answer_text,
        reference_answer=reference_answer,
        question_text=question_text,
    )

    # 4. Create and persist Score ORM model
    score_record = ScoreModel(
        score_id=uuid.uuid4(),
        answer_id=answer_record.answer_id,
        similarity_score=score_results["similarity_score"],
        llm_judge_score=score_results["llm_judge_score"],
        concept_match_score=score_results["concept_match_score"],
        fused_score=score_results["fused_score"],
        human_calibrated_score=score_results["human_calibrated_score"],
        feedback_text=score_results["feedback_text"],
        missing_keywords=score_results["missing_keywords"],
    )
    db.add(score_record)
    db.commit()
    db.refresh(score_record)

    # 5. Update student TopicProgress statistics if topic_id is available
    if topic_id:
        tp = db.query(TopicProgressModel).filter(
            TopicProgressModel.user_id == user_id,
            TopicProgressModel.topic_id == topic_id
        ).first()

        new_fused = score_results["fused_score"] or 0.0
        if tp:
            old_count = tp.attempts_count or 0
            old_avg = tp.avg_score or 0.0
            tp.attempts_count = old_count + 1
            tp.avg_score = round(((old_avg * old_count) + (new_fused * 100.0)) / tp.attempts_count, 2)
            tp.last_updated = datetime.utcnow()
        else:
            tp = TopicProgressModel(
                id=uuid.uuid4(),
                user_id=user_id,
                topic_id=topic_id,
                avg_score=round(new_fused * 100.0, 2),
                attempts_count=1,
                last_updated=datetime.utcnow(),
            )
            db.add(tp)
        db.commit()

    # 6. Return ScoreOut matching existing schema
    return ScoreOut(
        score_id=score_record.score_id,
        answer_id=score_record.answer_id,
        similarity_score=score_record.similarity_score,
        llm_judge_score=score_record.llm_judge_score,
        concept_match_score=score_record.concept_match_score,
        fused_score=score_record.fused_score,
        human_calibrated_score=score_record.human_calibrated_score,
        feedback_text=score_record.feedback_text,
        missing_keywords=score_record.missing_keywords or [],
    )


@router.post("/{session_id}/answers", response_model=ScoreOut, status_code=status.HTTP_201_CREATED)
def submit_session_answer(
    session_id: uuid.UUID,
    payload: AnswerCreate,
    db: Session = Depends(get_db)
) -> ScoreOut:
    """Submit answer under session route /sessions/{session_id}/answers."""
    return _process_answer_submission(
        session_id=session_id,
        question_id=payload.question_id,
        user_id=payload.user_id,
        answer_text=payload.answer_text,
        db=db
    )


@router.post("/submit", response_model=ScoreOut, status_code=status.HTTP_201_CREATED)
def submit_answer_direct(
    payload: AnswerSubmitPayload,
    db: Session = Depends(get_db)
) -> ScoreOut:
    """Pod 2 direct owned endpoint: /answers/submit."""
    sess_id = payload.session_id or uuid.UUID("00000000-0000-0000-0000-000000000001")
    return _process_answer_submission(
        session_id=sess_id,
        question_id=payload.question_id,
        user_id=payload.user_id,
        answer_text=payload.answer_text,
        db=db
    )

