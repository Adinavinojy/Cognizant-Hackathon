"""
Question Generation Service — Gemini LLM + Vector Store Retrieval
==================================================================
Retrieves exemplar questions from ChromaDB vector store for a role/topic,
then prompts Gemini LLM to generate grounded interview questions and follow-ups.
Includes fail-safe fallback if LLM is unavailable.
"""

import json
import os
import re
import time
import uuid
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.schemas import Question
from app.services.vector_store import search_questions, vector_store


class GenerationError(Exception):
    """Raised when all generation attempts fail."""
    pass


class GeneratedQuestionPayload(BaseModel):
    role: str = Field(description="Target engineering role")
    topic: str = Field(description="Specific technical topic")
    difficulty: str = Field(description="Difficulty level: Easy, Medium, or Hard")
    question_text: str = Field(description="Clear interview question")
    reference_answer: str = Field(description="Comprehensive reference answer")


# List of models in order of priority
FALLBACK_MODELS = [
    "gemini-2.5-flash",
    "gemini-1.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-flash-lite-latest",
]

# Gemini SDK check
try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False


def _get_genai_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if HAS_GENAI and api_key:
        try:
            return genai.Client(api_key=api_key)
        except Exception as e:
            print(f"GenAI Client init warning: {e}")
    return None


def generate_questions(role_id: str, topic_id: str, count: int = 1) -> List[dict]:
    """
    Retrieve exemplars from vector store and prompt LLM to produce a new grounded question.
    Falls back to exemplar/bank lookup if LLM generation fails.
    """
    exemplars = search_questions("interview question candidate assessment", role_id=role_id, topic_id=topic_id, top_k=3)
    
    client = _get_genai_client()
    if client and exemplars:
        try:
            exemplar_text = "\n".join(
                [f"- Question: {ex.get('question_text')}\n  Reference Answer: {ex.get('reference_answer')}" for ex in exemplars]
            )

            prompt = (
                f"You are an expert technical interviewer.\n"
                f"Below are reference interview questions for topic '{topic_id}' and role '{role_id}':\n"
                f"{exemplar_text}\n\n"
                f"Generate {count} NEW interview question(s) grounded strictly in the domain of the examples provided above.\n"
                f"Respond ONLY with a JSON array of objects having keys: 'question_text', 'reference_answer', 'difficulty' ('easy'|'medium'|'hard')."
            )

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            if response and response.text:
                cleaned = response.text.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned.split("```json")[1].split("```")[0].strip()
                elif cleaned.startswith("```"):
                    cleaned = cleaned.split("```")[1].split("```")[0].strip()
                
                parsed = json.loads(cleaned)
                if isinstance(parsed, dict):
                    parsed = [parsed]
                
                results = []
                for item in parsed[:count]:
                    results.append({
                        "question_id": str(uuid.uuid4()),
                        "role_id": str(role_id),
                        "topic_id": str(topic_id),
                        "question_text": item.get("question_text", ""),
                        "reference_answer": item.get("reference_answer", ""),
                        "difficulty": item.get("difficulty", "medium"),
                        "source": "generated"
                    })
                if results:
                    return results
        except Exception as exc:
            print(f"LLM Question Generation failed: {exc}. Using fallback bank lookup.")

    # Fallback: Return from exemplars or default template
    if exemplars:
        ex = exemplars[0]
        return [{
            "question_id": str(uuid.uuid4()),
            "role_id": str(role_id),
            "topic_id": str(topic_id),
            "question_text": ex.get("question_text", "Explain key trade-offs in distributed systems."),
            "reference_answer": ex.get("reference_answer", "Key trade-offs include latency vs consistency and throughput vs durability."),
            "difficulty": ex.get("difficulty", "medium"),
            "source": "bank_fallback"
        }]

    return [{
        "question_id": str(uuid.uuid4()),
        "role_id": str(role_id),
        "topic_id": str(topic_id),
        "question_text": "What are the core principles of object-oriented design and modular architecture?",
        "reference_answer": "Encapsulation, Abstraction, Inheritance, Polymorphism, and Low Coupling / High Cohesion.",
        "difficulty": "medium",
        "source": "bank_fallback"
    }]


def generate_question(role: str, topic: str, difficulty: str = "Medium") -> Question:
    """
    Attempts to generate a single question object with retry support across models.
    """
    client = _get_genai_client()
    if not client:
        # Fallback to local vector store
        examples = vector_store.get_grounding_examples(role=role, topic=topic, n_results=1)
        if examples:
            return examples[0]
        return Question(
            id=str(uuid.uuid4()),
            role=role,
            topic=topic,
            difficulty=difficulty,
            question_text="How do you detect a cycle in a singly linked list?",
            reference_answer="Use Floyd's Cycle-Finding Algorithm (Fast and Slow Pointers)."
        )

    res_list = generate_questions(role_id=role, topic_id=topic, count=1)
    if res_list:
        item = res_list[0]
        return Question(
            id=item["question_id"],
            role=role,
            topic=topic,
            difficulty=item.get("difficulty", difficulty),
            question_text=item.get("question_text", ""),
            reference_answer=item.get("reference_answer", "")
        )
    
    raise GenerationError("Unable to generate question.")


def generate_follow_up(
    answer_text: str,
    original_question_text: str,
    missing_keywords: Optional[List[str]] = None,
    role_id: Optional[str] = None,
    topic_id: Optional[str] = None
) -> dict:
    """
    Given a student's answer and missing_keywords from scoring, generate one targeted
    follow-up question probing that gap.
    """
    missing_str = ", ".join(missing_keywords) if missing_keywords else "depth and practical examples"

    client = _get_genai_client()
    if client:
        try:
            prompt = (
                f"A candidate answered the question: '{original_question_text}'\n"
                f"Candidate's Answer: '{answer_text}'\n"
                f"Missing concepts/keywords identified: {missing_str}\n\n"
                f"Generate ONE focused, follow-up interview question probing the candidate specifically on the missing concepts ({missing_str}).\n"
                f"Respond ONLY with a JSON object having keys: 'question_text', 'reference_answer', 'difficulty'."
            )

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            if response and response.text:
                cleaned = response.text.strip()
                if cleaned.startswith("```json"):
                    cleaned = cleaned.split("```json")[1].split("```")[0].strip()
                elif cleaned.startswith("```"):
                    cleaned = cleaned.split("```")[1].split("```")[0].strip()
                
                item = json.loads(cleaned)
                return {
                    "question_id": str(uuid.uuid4()),
                    "role_id": str(role_id or "00000000-0000-0000-0000-000000000001"),
                    "topic_id": str(topic_id or "00000000-0000-0000-0000-000000000001"),
                    "question_text": item.get("question_text", ""),
                    "reference_answer": item.get("reference_answer", ""),
                    "difficulty": item.get("difficulty", "medium"),
                    "source": "followup"
                }
        except Exception as exc:
            print(f"LLM Follow-up Generation failed: {exc}. Using fallback template.")

    # Fallback follow-up
    return {
        "question_id": str(uuid.uuid4()),
        "role_id": str(role_id or "00000000-0000-0000-0000-000000000001"),
        "topic_id": str(topic_id or "00000000-0000-0000-0000-000000000001"),
        "question_text": f"Could you elaborate further on how you would address {missing_str} in your solution?",
        "reference_answer": f"The response should specifically outline practical considerations regarding {missing_str}.",
        "difficulty": "medium",
        "source": "followup_fallback"
    }

