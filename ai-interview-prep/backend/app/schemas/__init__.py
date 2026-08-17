# app/schemas/__init__.py
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Question:
    id: str
    role: str
    topic: str
    question_text: str
    difficulty: Optional[str] = None
    reference_answer: Optional[str] = None
