"""
Router: /auth
Endpoints for signup and simple login.
"""

import uuid
from datetime import datetime
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.auth import SignupRequest, LoginRequest, AuthResponse, UserOut

log = logging.getLogger(__name__)
router = APIRouter()

# ---------------------------------------------------------------------------
# STUB: fake JWT token
# ---------------------------------------------------------------------------
_FAKE_TOKEN = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    ".eyJzdWIiOiJtb2NrLXVzZXItaWQiLCJleHAiOjk5OTk5OTk5OTl9"
    ".STUBSIGNATURE"
)

@router.post("/signup", response_model=AuthResponse, status_code=201)
def signup(payload: SignupRequest, db: Session = Depends(get_db)) -> AuthResponse:
    """
    Registers a new user.
    """
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        user_id=uuid.uuid4(),
        name=payload.name,
        email=payload.email,
        password_hash="stub_hash",
        role=payload.role,
        created_at=datetime.utcnow()
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    user_out = UserOut.model_validate(new_user)
    return AuthResponse(access_token=_FAKE_TOKEN, user=user_out)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    """
    Simple no-auth login for prototyping.
    Finds the user by email, or creates a new one if it doesn't exist.
    """
    user = db.query(User).filter(User.email == payload.email).first()
    
    if not user:
        # Auto-create for seamless simple login experience
        user = User(
            user_id=uuid.uuid4(),
            name=payload.name or payload.email.split("@")[0],
            email=payload.email,
            password_hash="stub_hash",
            role="candidate",
            created_at=datetime.utcnow()
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    user_out = UserOut.model_validate(user)
    return AuthResponse(access_token=_FAKE_TOKEN, user=user_out)
