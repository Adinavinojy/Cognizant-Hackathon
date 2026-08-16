"""
Router: /auth
Stub endpoints for signup and login.
TODO(auth-pair): Replace mock logic with real password hashing (bcrypt/argon2)
                 and JWT signing against the database.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter

from app.schemas.auth import SignupRequest, LoginRequest, AuthResponse, UserOut

router = APIRouter()

# ---------------------------------------------------------------------------
# STUB: fake JWT token — auth pair will replace with python-jose signing
# ---------------------------------------------------------------------------
_FAKE_TOKEN = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    ".eyJzdWIiOiJtb2NrLXVzZXItaWQiLCJleHAiOjk5OTk5OTk5OTl9"
    ".STUBSIGNATURE"
)


def _mock_user(email: str, name: str, role: str = "candidate") -> UserOut:
    """Return a plausible-looking user object without hitting the database."""
    return UserOut(
        user_id=uuid.uuid4(),
        name=name,
        email=email,
        role=role,
        created_at=datetime.utcnow(),
    )


@router.post("/signup", response_model=AuthResponse, status_code=201)
def signup(payload: SignupRequest) -> AuthResponse:
    """
    STUB — registers a new user.
    TODO(auth-pair): hash payload.password, persist user to DB, return real JWT.
    """
    user = _mock_user(email=payload.email, name=payload.name, role=payload.role)
    return AuthResponse(access_token=_FAKE_TOKEN, user=user)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest) -> AuthResponse:
    """
    STUB — authenticates a user.
    TODO(auth-pair): look up user by email, verify password hash, sign real JWT.
    """
    user = _mock_user(email=payload.email, name="Mock User")
    return AuthResponse(access_token=_FAKE_TOKEN, user=user)
