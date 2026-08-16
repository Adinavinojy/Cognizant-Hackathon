"""
Router: GET /dashboard/{user_id} and GET /study-plan/{user_id}
Returns mock topic progress and study plan rows.
TODO(dashboard-pair): Replace mock data with real DB queries once scoring pipeline is live.
"""

import uuid
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter

from app.schemas.dashboard import TopicProgressOut, StudyPlanOut

router = APIRouter()

# ---------------------------------------------------------------------------
# Stable topic UUIDs used by both endpoints for consistency in dev
# ---------------------------------------------------------------------------
_TOPICS = [
    (uuid.UUID("22222222-2222-2222-2222-222222222222"), "Operating Systems"),
    (uuid.UUID("33333333-3333-3333-3333-333333333333"), "System Design"),
    (uuid.UUID("44444444-4444-4444-4444-444444444444"), "Databases"),
    (uuid.UUID("55555555-5555-5555-5555-555555555555"), "Algorithms"),
    (uuid.UUID("66666666-6666-6666-6666-666666666666"), "Behavioural"),
]


@router.get("/dashboard/{user_id}", response_model=List[TopicProgressOut])
def get_dashboard(user_id: uuid.UUID) -> List[TopicProgressOut]:
    """
    STUB — returns mock topic progress rows for the given user.
    TODO(dashboard-pair): Query topic_progress table filtered by user_id.
    """
    mock_scores = [0.82, 0.55, 0.71, 0.63, 0.90]
    mock_attempts = [5, 2, 4, 3, 7]

    return [
        TopicProgressOut(
            id=uuid.uuid4(),
            user_id=user_id,
            topic_id=topic_id,
            avg_score=score,
            attempts_count=attempts,
            last_updated=datetime.utcnow() - timedelta(days=idx),
        )
        for idx, ((topic_id, _name), score, attempts) in enumerate(
            zip(_TOPICS, mock_scores, mock_attempts)
        )
    ]


@router.get("/study-plan/{user_id}", response_model=List[StudyPlanOut])
def get_study_plan(user_id: uuid.UUID) -> List[StudyPlanOut]:
    """
    STUB — returns a mock prioritised study plan for the given user.
    TODO(dashboard-pair): Run study plan generation from services once scoring is live.
    """
    resources_by_topic = {
        "Databases": [
            "https://use-the-index-luke.com",
            "CMU 15-445 lectures",
        ],
        "System Design": [
            "Designing Data-Intensive Applications (Kleppmann)",
            "https://github.com/donnemartin/system-design-primer",
        ],
        "Algorithms": [
            "LeetCode Top 100 Liked Questions",
            "CLRS Chapter 6-9",
        ],
        "Operating Systems": [
            "Operating System Concepts (Silberschatz)",
            "https://pages.cs.wisc.edu/~remzi/OSTEP/",
        ],
        "Behavioural": [
            "STAR method guide",
            "Glassdoor company-specific questions",
        ],
    }

    # Prioritise topics with lower avg_score first (simulated)
    prioritised = [
        (_TOPICS[1], 1),  # System Design — score 0.55
        (_TOPICS[3], 2),  # Algorithms    — score 0.63
        (_TOPICS[2], 3),  # Databases     — score 0.71
        (_TOPICS[0], 4),  # OS            — score 0.82
        (_TOPICS[4], 5),  # Behavioural   — score 0.90
    ]

    return [
        StudyPlanOut(
            id=uuid.uuid4(),
            user_id=user_id,
            topic_id=topic_id,
            priority_rank=rank,
            recommended_resources=resources_by_topic.get(name, []),
            generated_at=datetime.utcnow(),
        )
        for (topic_id, name), rank in prioritised
    ]
