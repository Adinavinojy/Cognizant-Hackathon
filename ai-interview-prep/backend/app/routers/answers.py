"""
Router: POST /sessions/{session_id}/answers
============================================
Accepts a submitted answer, runs the full multi-signal scoring pipeline,
persists both the Answer and Score rows to the database, and returns a
fully populated ScoreOut object.

ScoreOut contains everything the frontend needs to display:
  • similarity_percentage  — how close the student's answer is to the reference
  • reference_answer       — the ideal/correct answer for this question
  • answer_explanation     — a simple plain-English breakdown of the reference
  • hint                   — connecting keywords, missing keywords, tips & tricks
  • fused_score            — the combined score from all three signals
  • per-signal breakdown   — similarity, concept, llm scores individually

The three scoring signals (embedding, concept-overlap, LLM judge) are
independently fault-isolated: a failure in any one degrades the score
gracefully instead of breaking the endpoint.
"""

import uuid
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.answer import Answer
from app.models.score import Score
from app.models.question import Question
from app.models.progress import TopicProgress
from app.schemas.answers import AnswerCreate, AnswerOut, FollowUpRequest
from app.schemas.scores import ScoreOut, AnswerHint
from app.schemas.questions import QuestionOut
from app.services import scoring
from app.services.question_generation import generate_followup_question, GenerationError

log = logging.getLogger(__name__)
router = APIRouter()


@router.post("/{session_id}/answers", response_model=ScoreOut, status_code=201)
def submit_answer(
    session_id: uuid.UUID,
    payload: AnswerCreate,
    db: Session = Depends(get_db),
) -> ScoreOut:
    """
    Submit a student's answer and receive a fully scored result.

    **What happens internally:**
    1. The Question row is fetched (to get the reference answer).
    2. An Answer row is persisted to the database.
    3. The multi-signal scoring pipeline runs:
       - Signal 1: Embedding cosine similarity (offline, never fails)
       - Signal 2: Concept overlap with missing/connecting concept lists (offline)
       - Signal 3: LLM judge → score + plain-English explanation + tips (Gemini, optional)
       - Fusion: weighted average of all available signals
    4. A Score row is persisted to the database.
    5. The fully populated ScoreOut is returned.

    **Response fields of note:**
    - `similarity_percentage`: easy-to-read percentage (0–100).
      Manually reproducible as `round(similarity_score * 100, 1)`.
    - `reference_answer`: the ideal answer for this question.
    - `answer_explanation`: a simple, plain-English explanation of the reference answer.
    - `hint.connecting_keywords`: concepts the student DID mention correctly.
    - `hint.missing_keywords`: key concepts absent from the student's answer.
    - `hint.tips_and_tricks`: 2–3 short, actionable improvement tips from the LLM.
    """

    # ── 1. Fetch the question (needed for reference_answer + question_text) ──
    question: Question | None = db.get(Question, payload.question_id)
    if question is None:
        raise HTTPException(
            status_code=404,
            detail=f"Question {payload.question_id} not found.",
        )

    reference_answer = question.reference_answer or ""
    question_text    = question.question_text or ""

    # ── 2. Persist the Answer row ────────────────────────────────────────────
    answer_id = uuid.uuid4()
    db_answer = Answer(
        answer_id    = answer_id,
        session_id   = session_id,
        question_id  = payload.question_id,
        user_id      = payload.user_id,
        answer_text  = payload.answer_text,
        submitted_at = datetime.utcnow(),
    )
    db.add(db_answer)
    db.flush()   # get the answer_id in DB without committing yet

    # ── 3. Run the scoring pipeline ──────────────────────────────────────────
    try:
        result = scoring.score_answer(
            answer_text      = payload.answer_text,
            reference_answer = reference_answer,
            question_text    = question_text,
        )
    except Exception as exc:
        db.rollback()
        log.error("Scoring pipeline raised unexpectedly: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Scoring pipeline failed. Please try again.",
        ) from exc

    # ── 4. Persist the Score row ─────────────────────────────────────────────
    score_id = uuid.uuid4()
    db_score = Score(
        score_id               = score_id,
        answer_id              = answer_id,
        similarity_score       = result["similarity_score"],
        llm_judge_score        = result.get("llm_judge_score"),
        concept_match_score    = result["concept_match_score"],
        fused_score            = result["fused_score"],
        human_calibrated_score = None,        # filled by human reviewers later
        feedback_text          = result["feedback_text"],
        missing_keywords       = result["missing_concepts"],
    )
    db.add(db_score)
    db.commit()

    # ── 4b. Update Topic Progress ──────────────────────────────────────────────
    if question.topic_id:
        topic_progress = db.query(TopicProgress).filter(
            TopicProgress.user_id == payload.user_id,
            TopicProgress.topic_id == question.topic_id
        ).first()

        if not topic_progress:
            topic_progress = TopicProgress(
                id=uuid.uuid4(),
                user_id=payload.user_id,
                topic_id=question.topic_id,
                avg_score=result["fused_score"],
                attempts_count=1,
                last_updated=datetime.utcnow()
            )
            db.add(topic_progress)
        else:
            # Moving average to prevent wild swings
            current_avg = topic_progress.avg_score or 0.0
            new_score = result["fused_score"]
            topic_progress.avg_score = (current_avg * 0.8) + (new_score * 0.2)
            topic_progress.attempts_count += 1
            topic_progress.last_updated = datetime.utcnow()
        
        db.commit()

    # ── 4c. Update MockSession overall_score & status if all Qs answered ────
    try:
        from app.models.session import MockSession, SessionQuestion
        from sqlalchemy import func as sqlfunc

        session_obj = db.get(MockSession, session_id)
        if session_obj:
            # Count how many session_questions have a corresponding answer
            answered_count = db.query(sqlfunc.count(Answer.answer_id)).filter(
                Answer.session_id == session_id
            ).scalar() or 0

            total_qs = session_obj.question_count or 0

            if total_qs > 0 and answered_count >= total_qs:
                # All questions answered — compute mean fused_score across all answers
                from app.models.score import Score as ScoreModel
                avg_fused = db.query(sqlfunc.avg(ScoreModel.fused_score)).join(
                    Answer, ScoreModel.answer_id == Answer.answer_id
                ).filter(
                    Answer.session_id == session_id
                ).scalar()

                session_obj.overall_score = float(avg_fused) if avg_fused is not None else None
                session_obj.status = "completed"
                db.commit()
    except Exception as exc:
        log.warning("Could not update session overall_score: %s", exc)


    # ── 5. Build and return ScoreOut ─────────────────────────────────────────
    hint = AnswerHint(
        connecting_keywords = result["connecting_concepts"],
        missing_keywords    = result["missing_concepts"],
        tips_and_tricks     = result["tips"],
    )

    return ScoreOut(
        score_id               = score_id,
        answer_id              = answer_id,
        session_id             = session_id,
        # Per-signal scores
        similarity_score       = result["similarity_score"],
        concept_match_score    = result["concept_match_score"],
        llm_judge_score        = result.get("llm_judge_score"),
        # Fused
        fused_score            = result["fused_score"],
        human_calibrated_score = None,
        # Easy-to-read percentage
        similarity_percentage  = result["similarity_percentage"],
        # Reference answer + explanation
        reference_answer       = reference_answer,
        answer_explanation     = result["answer_explanation"],
        # Hint block
        hint                   = hint,
        # Legacy flat fields (kept for FollowUpRequest backwards-compat)
        feedback_text          = result["feedback_text"],
        missing_keywords       = result["missing_concepts"],
    )


@router.post("/{session_id}/answers/followup", response_model=QuestionOut)
def generate_followup(session_id: uuid.UUID, payload: FollowUpRequest) -> QuestionOut:
    """
    Generates an adaptive follow-up question based on the user's answer and
    their score. If Gemini is unavailable, returns 503 — this is a purely
    generative feature and has no offline fallback.
    """
    try:
        ai_q = generate_followup_question(payload)

        _DEFAULT_ROLE_ID  = uuid.UUID("11111111-1111-1111-1111-111111111111")
        _DEFAULT_TOPIC_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")

        return QuestionOut(
            question_id    = uuid.uuid4(),
            topic_id       = _DEFAULT_TOPIC_ID,
            role_id        = _DEFAULT_ROLE_ID,
            question_text  = ai_q.question_text,
            reference_answer = ai_q.reference_answer,
            difficulty     = ai_q.difficulty.lower() if ai_q.difficulty else "medium",
            source         = "gemini",
        )
    except GenerationError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Follow-up generation failed: {str(e)}",
        )
