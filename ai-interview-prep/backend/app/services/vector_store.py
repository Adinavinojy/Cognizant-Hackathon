"""
Vector Store Service — STUB
==============================
TODO(ML-generation pair): Wire up FAISS or ChromaDB for document retrieval.

Planned implementation:
  1. At startup (or via a management command), ingest question/answer pairs and
     supplementary material from the `ml/` folder.
  2. Expose `search(query, top_k)` → list of relevant document chunks.
  3. Used by question_generation.py to ground LLM prompts.

This module is intentionally empty. Add your implementations below.
"""

from typing import List


def ingest_documents(documents: List[dict]) -> None:
    """
    TODO(ML-generation pair): Embed and store documents in the vector store.

    Args:
        documents: List of dicts with at minimum 'text' and 'metadata' keys.
    """
    raise NotImplementedError("vector_store.ingest_documents is not yet implemented.")


def search(query: str, top_k: int = 5) -> List[dict]:
    """
    TODO(ML-generation pair): Embed query and return top_k most similar document chunks.

    Args:
        query: Natural language query string.
        top_k: Number of results to return.

    Returns:
        List of dicts: [{"text": ..., "metadata": {...}, "score": float}, ...]
    """
    raise NotImplementedError("vector_store.search is not yet implemented.")
