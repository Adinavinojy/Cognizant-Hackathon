import json
import os
import re
import time
import uuid
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from app.schemas import Question
from app.services.vector_store import vector_store


class GenerationError(Exception):
    """Raised when all generation attempts fail."""
    pass


class GeneratedQuestionPayload(BaseModel):
    role: str = Field(description="Target engineering role")
    topic: str = Field(description="Specific technical topic")
    difficulty: str = Field(description="Difficulty level: Easy, Medium, or Hard")
    question_text: str = Field(description="Clear interview question")
    reference_answer: str = Field(description="Comprehensive reference answer")


# List of models in order of priority (lite/flash models experience less queue congestion)
FALLBACK_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-3.5-flash",
    "gemini-flash-latest",
    "gemini-3.7-flash",
]


def generate_question(role: str, topic: str, difficulty: str = "Medium") -> Question:
    """
    Attempts to generate a question across available models with automatic retry.
    Raises GenerationError only if all attempts are exhausted.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise GenerationError("GEMINI_API_KEY environment variable is not set.")

    # 1. Fetch ChromaDB grounding examples
    grounding_examples = vector_store.get_grounding_examples(role=role, topic=topic, n_results=2)
    examples_context = "\n\n".join(
        [
            f"Example {i+1}:\nQuestion: {eg.question_text}\nAnswer: {eg.reference_answer}"
            for i, eg in enumerate(grounding_examples)
        ]
    )

    prompt = f"""You are a technical interviewer. Generate 1 new interview question and reference answer.
Role: {role}
Topic: {topic}
Difficulty: {difficulty}

Grounded Examples:
{examples_context}

Return valid JSON with keys: "role", "topic", "difficulty", "question_text", "reference_answer"."""

    client = genai.Client(api_key=api_key)
    last_err = None

    # 2. Iterate through fallback models
    for model_name in FALLBACK_MODELS:
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.7,
                    ),
                )

                if response.text:
                    # Clean potential markdown wrapping
                    raw_text = re.sub(r"^```json\s*|\s*```$", "", response.text.strip())
                    data = json.loads(raw_text)

                    return Question(
                        id=str(uuid.uuid4()),
                        role=data.get("role", role),
                        topic=data.get("topic", topic),
                        difficulty=data.get("difficulty", difficulty),
                        question_text=data["question_text"],
                        reference_answer=data["reference_answer"],
                    )

            except Exception as e:
                last_err = e
                time.sleep(1.5)  # Brief pause between retries to let spikes subside
                continue

    raise GenerationError(f"All Gemini models busy: {last_err}")