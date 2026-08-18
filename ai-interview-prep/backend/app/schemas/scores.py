"""
Pydantic schemas for /scores endpoint.

ScoreOut is the canonical "Scored Answer" object consumed by:
  - Dashboard pod   → reads fused_score, per-signal scores, missing_concepts
  - AI Pipeline pod → reads missing_concepts to build adaptive follow-up questions
  - Frontend        → displays similarity_percentage, reference_answer,
                      answer_explanation, and hint
"""

from uuid import UUID
from typing import List, Optional

from pydantic import BaseModel


class AnswerHint(BaseModel):
    """
    Student-facing hint block shown alongside the scored answer.
    - connecting_keywords: concepts that link the student's answer to the
      reference (present in both) — useful to show what they DID get right.
    - missing_keywords: key concepts absent from the student's answer —
      these drive the adaptive follow-up question in the AI Pipeline pod.
    - tips_and_tricks: LLM-generated short advice bullets the student can
      act on immediately (e.g. "mention trade-offs", "cite a real example").
    """
    connecting_keywords: List[str] = []
    missing_keywords: List[str] = []
    tips_and_tricks: List[str] = []


class ScoreOut(BaseModel):
    # ── Identifiers ─────────────────────────────────────────────────────────
    score_id: UUID
    answer_id: UUID
    session_id: Optional[UUID] = None      # set by the router; used by Dashboard

    # ── Per-signal scores (all in [0, 1]) ────────────────────────────────────
    similarity_score: Optional[float] = None
    llm_judge_score: Optional[float] = None
    concept_match_score: Optional[float] = None

    # ── Derived / fused ──────────────────────────────────────────────────────
    fused_score: Optional[float] = None
    human_calibrated_score: Optional[float] = None  # filled by human reviewers

    # ── Similarity as an easy-to-read percentage (0–100) ─────────────────────
    # Manually computable: round(similarity_score * 100, 1)
    similarity_percentage: Optional[float] = None

    # ── Reference answer + plain-English explanation ─────────────────────────
    reference_answer: Optional[str] = None
    answer_explanation: Optional[str] = None   # LLM-generated simple explanation

    # ── Hint block (keywords + tips) ─────────────────────────────────────────
    hint: Optional[AnswerHint] = None

    # ── Legacy flat field — kept for backwards-compat with FollowUpRequest ───
    feedback_text: Optional[str] = None
    missing_keywords: Optional[List[str]] = None  # mirrors hint.missing_keywords

    model_config = {"from_attributes": True}
