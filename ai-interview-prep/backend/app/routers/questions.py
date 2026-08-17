"""
Router: GET /questions
Returns 3-5 real question objects filtered by role and topic from ChromaDB / Gemini generation.
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Query

from app.schemas.questions import QuestionOut
from app.services.vector_store import vector_store
from app.services.question_generation import generate_question, GenerationError

router = APIRouter()

# Default fallback UUIDs for frontend/database compatibility
_DEFAULT_ROLE_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
_DEFAULT_TOPIC_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")


def _to_uuid(raw_id: str) -> uuid.UUID:
    """Converts a string ID (such as numeric StackOverflow ID or UUID) into a valid UUID object."""
    try:
        return uuid.UUID(str(raw_id))
    except (ValueError, AttributeError):
        # Generate a deterministic UUID5 if the raw ID is numeric (e.g. from SEDE)
        return uuid.uuid5(uuid.NAMESPACE_DNS, str(raw_id))


@router.get("", response_model=List[QuestionOut])
def get_questions(
    role: Optional[str] = Query(None, description="Filter by role name, e.g. 'Backend Engineer'"),
    topic: Optional[str] = Query(None, description="Filter by topic name, e.g. 'Python / Data Structures'"),
    count: int = Query(3, ge=1, le=10, description="Number of questions to retrieve (3-5 typical)"),
) -> List[QuestionOut]:
    """
    Returns real questions filtered by role and topic.
    Attempts to fetch a fresh Gemini question first, then fills the remainder with 
    distinct random questions from the ChromaDB question bank.
    """
    role_filter = role or "Backend Engineer"
    topic_filter = topic or "Python / Data Structures"
    
    questions_out: List[QuestionOut] = []

    # 1. Attempt fresh Gemini generation for the leading question
    try:
        ai_q = generate_question(role=role_filter, topic=topic_filter)
        questions_out.append(
            QuestionOut(
                question_id=_to_uuid(ai_q.id),
                topic_id=_DEFAULT_TOPIC_ID,
                role_id=_DEFAULT_ROLE_ID,
                question_text=ai_q.question_text,
                reference_answer=ai_q.reference_answer,
                difficulty=ai_q.difficulty.lower(),
                source="gemini",
            )
        )
    except (GenerationError, Exception) as e:
        # Graceful fallback: log and continue to fill directly from bank
        pass

    # 2. Retrieve remaining questions from ChromaDB Question Bank
    needed = count - len(questions_out)
    if needed > 0:
        bank_questions = vector_store.get_random_questions(
            role=role_filter,
            topic=topic_filter,
            count=needed,
        )
        
        for bq in bank_questions:
            questions_out.append(
                QuestionOut(
                    question_id=_to_uuid(bq.id),
                    topic_id=_DEFAULT_TOPIC_ID,
                    role_id=_DEFAULT_ROLE_ID,
                    question_text=bq.question_text,
                    reference_answer=bq.reference_answer,
                    difficulty=bq.difficulty.lower(),
                    source="chromadb",
                )
            )

    return questions_out