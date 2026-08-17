from pathlib import Path
from typing import List, Optional
import chromadb
from app.schemas import Question

# Resolve database storage path relative to project backend root
CHROMA_DB_PATH = Path(__file__).resolve().parent.parent.parent / "chroma_db"


class VectorStoreService:
    def __init__(self, db_path: Path = CHROMA_DB_PATH):
        self.client = chromadb.PersistentClient(path=str(db_path))
        self.collection = self.client.get_or_create_collection(
            name="question_bank",
            metadata={"hnsw:space": "cosine"}
        )

    def get_question(self, role: str, topic: Optional[str] = None,limit: int=5) -> Question:
        """
        Retrieves a question filtered by role and topic.
        Returns an exact schemas.Question object.
        """
        where_filter = {"role": role}
        if topic:
            where_filter = {"$and": [{"role": role}, {"topic": topic}]}

        results = self.collection.get(where=where_filter, limit=limit)

        # Fallback to role-only match if topic returns no rows
        if not results["ids"] and topic:
            results = self.collection.get(where={"role": role}, limit=1)

        if not results["ids"]:
            raise ValueError(f"No questions found for role='{role}' and topic='{topic}'.")

        return [
        Question(
            id=results["ids"][i],
            role=results["metadatas"][i]["role"],
            topic=results["metadatas"][i]["topic"],
            difficulty=results["metadatas"][i]["difficulty"],
            question_text=results["documents"][i],
            reference_answer=results["metadatas"][i]["reference_answer"]
        )
        for i in range(len(results["ids"]))
    ]
    
    def get_grounding_examples(self, role: str, topic: str, n_results: int = 3) -> List[Question]:
        """
        Retrieves top N Chroma examples to pass as context into Gemini prompts.
        """
        results = self.collection.get(
            where={"$and": [{"role": role}, {"topic": topic}]},
            limit=n_results
        )

        if not results["ids"]:
            results = self.collection.get(where={"role": role}, limit=n_results)

        examples = []
        for i in range(len(results["ids"])):
            examples.append(
                Question(
                    id=results["ids"][i],
                    role=results["metadatas"][i]["role"],
                    topic=results["metadatas"][i]["topic"],
                    difficulty=results["metadatas"][i]["difficulty"],
                    question_text=results["documents"][i],
                    reference_answer=results["metadatas"][i]["reference_answer"]
                )
            )
        return examples

    def get_random_questions(self, role: str, topic: Optional[str] = None, count: int = 1) -> List[Question]:
        """
        Retrieves random questions from ChromaDB filtered by role and topic.
        """
        import random
        
        where_filter = {"role": role}
        if topic:
            where_filter = {"$and": [{"role": role}, {"topic": topic}]}

        results = self.collection.get(where=where_filter, limit=50)

        if not results["ids"] and topic:
            results = self.collection.get(where={"role": role}, limit=50)

        if not results["ids"]:
            return []

        # Bundle parallel lists, shuffle, and take 'count' elements
        bundled = list(zip(results["ids"], results["metadatas"], results["documents"]))
        random.shuffle(bundled)
        selected = bundled[:count]

        return [
            Question(
                id=q_id,
                role=q_meta["role"],
                topic=q_meta["topic"],
                difficulty=q_meta.get("difficulty"),
                question_text=q_doc,
                reference_answer=q_meta.get("reference_answer")
            )
            for q_id, q_meta, q_doc in selected
        ]


# Singleton instance for endpoint and service imports
vector_store = VectorStoreService()


def get_question(role: str, topic: Optional[str] = None) -> Question:
    """Standard Pod 1 function interface."""
    return vector_store.get_question(role, topic)