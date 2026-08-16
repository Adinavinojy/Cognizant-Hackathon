"""
Question Generation Service — STUB
=====================================
TODO(ML-generation pair): Implement real question generation using an LLM + retrieval.

Planned implementation:
  1. Given a role_id and topic_id, retrieve relevant chunks from vector_store.
  2. Pass chunks + topic metadata to an LLM (e.g. GPT-4 / Gemini) to generate
     contextual questions.
  3. Optionally generate follow-up questions conditioned on a previous answer.

This module is intentionally empty. Add your implementations below.
"""

from typing import List


def generate_questions(role_id: str, topic_id: str, count: int = 5) -> List[dict]:
    """
    TODO(ML-generation pair): Use LLM + vector retrieval to generate `count` questions
    for the given role and topic.

    Args:
        role_id: UUID string of the job role.
        topic_id: UUID string of the topic.
        count: Number of questions to generate.

    Returns:
        List of question dicts matching the questions schema.
    """
    raise NotImplementedError("question_generation.generate_questions is not yet implemented.")


def generate_follow_up(answer_text: str, original_question_text: str) -> dict:
    """
    TODO(ML-generation pair): Given a candidate answer, use an LLM to generate a
    targeted follow-up question that probes weak areas.

    Args:
        answer_text: The candidate's answer.
        original_question_text: The question that was answered.

    Returns:
        A question dict matching the questions schema.
    """
    raise NotImplementedError("question_generation.generate_follow_up is not yet implemented.")
