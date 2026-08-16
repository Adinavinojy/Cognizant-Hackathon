"""
Router: POST /sessions
Creates and returns a mock session object.
TODO(sessions-pair): Persist to DB and wire up session lifecycle (start / end).
"""

import uuid
from datetime import datetime

from fastapi import APIRouter

from app.schemas.sessions import SessionCreate, SessionOut

router = APIRouter()


@router.post("", response_model=SessionOut, status_code=201)
def create_session(payload: SessionCreate) -> SessionOut:
    """
    STUB — returns a mock session.
    TODO(sessions-pair): Persist MockSession to DB, validate user_id and role_id exist.
    """
    return SessionOut(
        session_id=uuid.uuid4(),
        user_id=payload.user_id,
        role_id=payload.role_id,
        started_at=datetime.utcnow(),
        ended_at=None,
        status="active",
    )
