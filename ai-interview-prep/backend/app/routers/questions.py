"""
Router: GET /questions
Returns 3-5 mock question objects filtered (loosely) by role and topic.
TODO(ml-generation-pair): Replace mock list with real retrieval from vector_store.
"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Query

from app.schemas.questions import QuestionOut

router = APIRouter()

# ---------------------------------------------------------------------------
# Seed UUIDs — kept stable so frontend can hard-code them in dev if needed
# ---------------------------------------------------------------------------
_ROLE_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
_TOPIC_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")

_MOCK_QUESTIONS: List[QuestionOut] = [
    QuestionOut(
        question_id=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        topic_id=_TOPIC_ID,
        role_id=_ROLE_ID,
        question_text="Explain the difference between a process and a thread.",
        reference_answer=(
            "A process is an independent program in execution with its own memory space. "
            "A thread is a lightweight unit of execution within a process that shares memory."
        ),
        difficulty="easy",
        source="seed",
    ),
    QuestionOut(
        question_id=uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
        topic_id=_TOPIC_ID,
        role_id=_ROLE_ID,
        question_text="What is the CAP theorem? Give a practical example.",
        reference_answer=(
            "CAP theorem states that a distributed system can guarantee at most two of: "
            "Consistency, Availability, Partition Tolerance. Example: Cassandra favours AP."
        ),
        difficulty="medium",
        source="seed",
    ),
    QuestionOut(
        question_id=uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),
        topic_id=_TOPIC_ID,
        role_id=_ROLE_ID,
        question_text="How would you design a URL shortener at scale?",
        reference_answer=(
            "Key components: hash function for URL → short code, distributed key-value store, "
            "CDN for redirect latency, rate limiting, analytics pipeline."
        ),
        difficulty="hard",
        source="seed",
    ),
    QuestionOut(
        question_id=uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd"),
        topic_id=_TOPIC_ID,
        role_id=_ROLE_ID,
        question_text="What is the difference between SQL and NoSQL databases?",
        reference_answer=(
            "SQL databases are relational with fixed schemas and ACID properties. "
            "NoSQL databases are flexible, schema-less and optimized for horizontal scaling."
        ),
        difficulty="easy",
        source="seed",
    ),
    QuestionOut(
        question_id=uuid.UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"),
        topic_id=_TOPIC_ID,
        role_id=_ROLE_ID,
        question_text="Describe how garbage collection works in Java.",
        reference_answer=(
            "JVM GC automatically manages heap memory by identifying and collecting unreachable "
            "objects. Common algorithms: Mark-and-Sweep, G1GC, ZGC."
        ),
        difficulty="medium",
        source="seed",
    ),
]


@router.get("", response_model=List[QuestionOut])
def get_questions(
    role: Optional[str] = Query(None, description="Filter by role name"),
    topic: Optional[str] = Query(None, description="Filter by topic name"),
) -> List[QuestionOut]:
    """
    STUB — returns a fixed list of mock questions.
    TODO(ml-generation-pair): Replace with vector_store retrieval + optional LLM follow-ups.
    The `role` and `topic` query params are accepted and logged but not yet used for filtering.
    """
    # Return all mock questions (frontend pair can use the full list for now)
    return _MOCK_QUESTIONS
