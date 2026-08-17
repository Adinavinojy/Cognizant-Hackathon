import logging
from typing import Optional
from app.schemas import Question
from app.services.question_generation import GenerationError, generate_question
from app.services.vector_store import get_question as get_bank_question

logger = logging.getLogger(__name__)


def get_next_question_with_fallback(role: str, topic: Optional[str] = None, difficulty: str = "Medium") -> Question:
    """
    Tries AI generation first.
    Falls back to the ChromaDB question bank if Gemini fails, times out,
    or returns an empty response.
    """
    # 1. Attempt AI Generation
    try:
        logger.info(f"Attempting Gemini generation for role='{role}', topic='{topic}'...")
        question = generate_question(role=role, topic=topic or "General", difficulty=difficulty)
        
        # Guard against empty/malformed text
        if question and question.question_text.strip() and question.reference_answer.strip():
            logger.info("Successfully generated question via Gemini.")
            return question
        else:
            raise GenerationError("Gemini returned empty question text or reference answer.")

    except (GenerationError, Exception) as e:
        logger.warning(f"Generation failed ({e}). Executing fallback to ChromaDB Question Bank...")

    # 2. Deterministic Fallback to ChromaDB Bank
    try:
        bank_question = get_bank_question(role=role, topic=topic)
        logger.info(f"Successfully retrieved fallback question from bank (ID: {bank_question.id}).")
        return bank_question
    except Exception as fallback_error:
        logger.error(f"Fallback retrieval failed: {fallback_error}")
        raise RuntimeError(f"Both AI generation and Question Bank fallback failed: {fallback_error}")