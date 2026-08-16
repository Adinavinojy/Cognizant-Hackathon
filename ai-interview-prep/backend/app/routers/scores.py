"""
Router: /scores
Placeholder router — individual score retrieval if needed by UI.
TODO(scoring-pair): Add GET /scores/{score_id} once DB persistence is wired.
"""

from fastapi import APIRouter

router = APIRouter()

# No endpoints defined yet — scores are returned inline by POST /sessions/{id}/answers.
# This file exists so the scores feature area has its own router from day one.
