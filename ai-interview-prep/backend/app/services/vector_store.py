"""
Vector Store Service — Persistent ChromaDB Integration
======================================================
Stores and retrieves questions with metadata (role_id, topic_id, difficulty).
Supports retrieval-grounded generation for Pod 1.
"""

import os
import random
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.schemas import Question

try:
    import chromadb
    from chromadb.config import Settings
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False

# Persistent DB directory
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "chroma_db"
DATA_DIR.mkdir(parents=True, exist_ok=True)

_chroma_client = None
_collection = None

# Fallback in-memory store if ChromaDB is not installed or empty
_memory_store: List[Dict[str, Any]] = []


def get_collection():
    global _chroma_client, _collection
    if not HAS_CHROMADB:
        return None
    if _collection is None:
        _chroma_client = chromadb.PersistentClient(path=str(DATA_DIR))
        _collection = _chroma_client.get_or_create_collection(
            name="question_bank",
            metadata={"hnsw:space": "cosine"}
        )
    return _collection


def ingest_questions(questions: List[Dict[str, Any]]) -> None:
    """
    Ingest a list of question dicts into ChromaDB vector store.
    Each dict should contain: question_id, role_id, topic_id, question_text, reference_answer, difficulty.
    """
    global _memory_store
    _memory_store.extend(questions)

    collection = get_collection()
    if not collection or not questions:
        return

    ids = []
    documents = []
    metadatas = []

    for q in questions:
        q_id = str(q.get("question_id"))
        text = f"Question: {q.get('question_text', '')}\nReference Answer: {q.get('reference_answer', '')}"
        
        metadata = {
            "question_id": q_id,
            "role_id": str(q.get("role_id", "")),
            "topic_id": str(q.get("topic_id", "")),
            "difficulty": str(q.get("difficulty", "medium")),
            "source": str(q.get("source", "bank")),
            "reference_answer": str(q.get("reference_answer", "")),
            "question_text": str(q.get("question_text", ""))
        }

        ids.append(q_id)
        documents.append(text)
        metadatas.append(metadata)

    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )


def search_questions(
    query: str,
    role_id: Optional[str] = None,
    topic_id: Optional[str] = None,
    top_k: int = 3
) -> List[Dict[str, Any]]:
    """
    Search ChromaDB vector store with optional role_id and topic_id metadata filtering.
    Returns list of question dictionary objects.
    """
    collection = get_collection()

    if collection is not None and collection.count() > 0:
        where_filter = {}
        if role_id and topic_id:
            where_filter = {"$and": [{"role_id": str(role_id)}, {"topic_id": str(topic_id)}]}
        elif role_id:
            where_filter = {"role_id": str(role_id)}
        elif topic_id:
            where_filter = {"topic_id": str(topic_id)}

        kwargs = {"query_texts": [query], "n_results": min(top_k, collection.count())}
        if where_filter:
            kwargs["where"] = where_filter

        try:
            results = collection.query(**kwargs)
            matches = []
            if results and results.get("metadatas") and len(results["metadatas"]) > 0:
                for meta in results["metadatas"][0]:
                    matches.append(meta)
            if matches:
                return matches
        except Exception as exc:
            print(f"ChromaDB search error: {exc}. Falling back to memory store.")

    # Fallback to memory store filtering
    results = []
    for q in _memory_store:
        if role_id and str(q.get("role_id")) != str(role_id):
            continue
        if topic_id and str(q.get("topic_id")) != str(topic_id):
            continue
        results.append(q)
        if len(results) >= top_k:
            break
    
    if not results:
        results = _memory_store[:top_k]

    return results


def ingest_documents(documents: List[dict]) -> None:
    ingest_questions(documents)


def search(query: str, top_k: int = 5) -> List[dict]:
    return search_questions(query, top_k=top_k)


class VectorStoreService:
    def __init__(self, db_path: Path = DATA_DIR):
        self.db_path = db_path

    def get_question(self, role: str, topic: Optional[str] = None, limit: int = 5) -> List[Question]:
        collection = get_collection()
        if not collection:
            return []
        where_filter = {"role_id": role} if not topic else {"$and": [{"role_id": role}, {"topic_id": topic}]}
        results = collection.get(where=where_filter, limit=limit)
        if not results["ids"] and topic:
            results = collection.get(where={"role_id": role}, limit=1)
        if not results["ids"]:
            return []
        return [
            Question(
                id=results["ids"][i],
                role=results["metadatas"][i].get("role_id", role),
                topic=results["metadatas"][i].get("topic_id", topic or ""),
                difficulty=results["metadatas"][i].get("difficulty", "medium"),
                question_text=results["documents"][i],
                reference_answer=results["metadatas"][i].get("reference_answer", "")
            )
            for i in range(len(results["ids"]))
        ]

    def get_grounding_examples(self, role: str, topic: str, n_results: int = 3) -> List[Question]:
        results = search_questions("interview question", role_id=role, topic_id=topic, top_k=n_results)
        return [
            Question(
                id=str(r.get("question_id", "")),
                role=str(r.get("role_id", role)),
                topic=str(r.get("topic_id", topic)),
                difficulty=str(r.get("difficulty", "medium")),
                question_text=str(r.get("question_text", "")),
                reference_answer=str(r.get("reference_answer", ""))
            )
            for r in results
        ]

    def get_random_questions(self, role: str, topic: Optional[str] = None, count: int = 1) -> List[Question]:
        results = search_questions("interview question", role_id=role, topic_id=topic, top_k=50)
        if not results:
            return []
        random.shuffle(results)
        selected = results[:count]
        return [
            Question(
                id=str(q.get("question_id", "")),
                role=str(q.get("role_id", role)),
                topic=str(q.get("topic_id", topic or "")),
                difficulty=str(q.get("difficulty", "medium")),
                question_text=str(q.get("question_text", "")),
                reference_answer=str(q.get("reference_answer", ""))
            )
            for q in selected
        ]


# Singleton instance
vector_store = VectorStoreService()


def get_question(role: str, topic: Optional[str] = None) -> Any:
    return vector_store.get_question(role, topic)

