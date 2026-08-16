"""
Router: POST /sessions/{session_id}/answers
Accepts a submitted answer and immediately returns a mock Score.
TODO(scoring-pair): Replace mock score with real scoring pipeline from services/scoring.py.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter

from app.schemas.answers import AnswerCreate, AnswerOut
from app.schemas.scores import ScoreOut

router = APIRouter()


@router.post("/{session_id}/answers", response_model=ScoreOut, status_code=201)
def submit_answer(session_id: uuid.UUID, payload: AnswerCreate) -> ScoreOut:
    """
    STUB — persists nothing; returns a plausible-looking score object.
    TODO(scoring-pair): Persist Answer to DB, call services.scoring.score_answer(),
                        persist Score to DB, return real scores.
    """
    answer_id = uuid.uuid4()

    # -----------------------------------------------------------------------
    # Placeholder scores — hardcoded floats so frontend can render feedback UI
    # -----------------------------------------------------------------------
    return ScoreOut(
        score_id=uuid.uuid4(),
        answer_id=answer_id,
        similarity_score=0.72,
        llm_judge_score=0.68,
        concept_match_score=0.75,
        fused_score=0.71,
        human_calibrated_score=None,  # filled in by human reviewers later
        feedback_text=(
            "Good answer! You covered the main concepts. Consider also mentioning "
            "trade-offs and real-world use cases to strengthen your response."
        ),
        missing_keywords=["trade-offs", "latency", "fault tolerance"],
    )
