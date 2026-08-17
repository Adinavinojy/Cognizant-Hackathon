# backend/test_gen.py
from dotenv import load_dotenv
load_dotenv()  # Loads GEMINI_API_KEY from backend/.env

from app.services.question_generation import generate_question, GenerationError

def test_pipeline():
    print("🚀 Testing Gemini Question Generation grounded in ChromaDB...")
    try:
        question = generate_question(
            role="Software Engineer",
            topic="Database Indexing",
            difficulty="Medium"
        )
        print("\n✅ Success! Generated Question Object:")
        print(f"ID: {question.id}")
        print(f"Role: {question.role}")
        print(f"Topic: {question.topic}")
        print(f"Difficulty: {question.difficulty}")
        print(f"\nQuestion:\n{question.question_text}")
        print(f"\nReference Answer:\n{question.reference_answer}")
    except GenerationError as err:
        print(f"\n❌ Generation failed loudly as expected on error:\n{err}")

if __name__ == "__main__":
    test_pipeline()