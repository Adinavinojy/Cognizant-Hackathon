"""
FastAPI application entry point.
Mounts all feature routers and exposes GET /health.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, questions, sessions, answers, scores, dashboard

app = FastAPI(
    title="AI Interview Prep API",
    description="Backend for the AI Interview Preparation Companion (hackathon scaffold).",
    version="0.1.0",
)

# ---------------------------------------------------------------------------
# CORS — allow all origins during local development; tighten in production.
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(auth.router,      prefix="/auth",       tags=["auth"])
app.include_router(questions.router, prefix="/questions",  tags=["questions"])
app.include_router(sessions.router,  prefix="/sessions",   tags=["sessions"])
app.include_router(answers.router,   prefix="/sessions",   tags=["answers"])
app.include_router(scores.router,    prefix="/scores",     tags=["scores"])
app.include_router(dashboard.router, prefix="",            tags=["dashboard"])


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["health"])
def health_check() -> dict:
    """Liveness probe — always returns 200 OK."""
    return {"status": "ok"}
