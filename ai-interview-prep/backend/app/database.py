"""
SQLAlchemy engine and session dependency.
Import `get_db` into routers to obtain a database session.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
db_url = settings.DATABASE_URL

if "sqlite" in db_url:
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False},
    )
else:
    try:
        engine = create_engine(
            db_url,
            pool_pre_ping=True,
        )
        # Verify connection
        with engine.connect() as conn:
            pass
    except Exception as exc:
        print(f"PostgreSQL connection error: {exc}. Falling back to SQLite.")
        sqlite_file = "interview_prep.db"
        engine = create_engine(
            f"sqlite:///{sqlite_file}",
            connect_args={"check_same_thread": False},
        )

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)



# ---------------------------------------------------------------------------
# Base class for all ORM models
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------
def get_db():
    """Yields a database session and ensures it is closed after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
