# app/models/__init__.py
# Import all models here so Alembic's autogenerate can discover them.

from app.models.user import User  # noqa: F401
from app.models.role_topic import JobRole, Topic  # noqa: F401
from app.models.question import Question  # noqa: F401
from app.models.session import MockSession, SessionQuestion  # noqa: F401
from app.models.answer import Answer  # noqa: F401
from app.models.score import Score  # noqa: F401
from app.models.progress import TopicProgress, StudyPlan  # noqa: F401
