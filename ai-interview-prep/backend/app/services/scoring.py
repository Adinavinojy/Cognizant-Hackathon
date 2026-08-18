"""
Multi-Signal Scoring Service
============================
Implements three independent scoring signals that are each fault-isolated:

  Signal 1 — Embedding Similarity (OFFLINE / never-fail)
    Uses sentence-transformers (all-MiniLM-L6-v2) locally.
    No external API call. Returns a safe default on any failure.

  Signal 2 — Concept Overlap (OFFLINE)
    Extracts key noun-phrase concepts from the reference answer using spaCy.
    Returns (score, missing_concepts, connecting_concepts).

  Signal 3 — LLM Judge (ONLINE, optional)
    Prompts Gemini to rate correctness/clarity/structure and generate:
      - a plain-English explanation of the reference answer
      - short tips the student can act on
    Returns None on any failure — fusion redistributes weights.

  Fusion
    Weighted average across available signals.
    If LLM is down: similarity × 0.45 + concept × 0.55
    If all three available: similarity × 0.30 + concept × 0.35 + llm × 0.35
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Optional

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Signal 1: Embedding model — loaded once at import time, cached forever
# ---------------------------------------------------------------------------
_EMBED_MODEL = None
_EMBED_MODEL_NAME = "all-MiniLM-L6-v2"


def _get_embed_model():
    """
    Lazy-loads the sentence-transformer model exactly once.
    Returns None (never raises) so Signal 1 can always return a safe default.
    """
    global _EMBED_MODEL
    if _EMBED_MODEL is not None:
        return _EMBED_MODEL
    try:
        from sentence_transformers import SentenceTransformer
        _EMBED_MODEL = SentenceTransformer(_EMBED_MODEL_NAME)
        log.info("Embedding model '%s' loaded successfully.", _EMBED_MODEL_NAME)
    except Exception as exc:  # noqa: BLE001
        log.warning(
            "Could not load embedding model '%s': %s. "
            "Signal 1 will return the safe default (0.5).",
            _EMBED_MODEL_NAME, exc,
        )
        _EMBED_MODEL = None
    return _EMBED_MODEL


# ---------------------------------------------------------------------------
# Signal 1 — Embedding Similarity
# ---------------------------------------------------------------------------
_SIMILARITY_SAFE_DEFAULT = 0.5   # neutral mid-point when model unavailable


def compute_similarity(text_a: str, text_b: str) -> float:
    """
    Embed both texts and return cosine similarity in [0, 1].

    Guaranteed to return a float — never raises.
    Falls back to _SIMILARITY_SAFE_DEFAULT if the model is unavailable.

    Manually reproducible:
        from sentence_transformers import SentenceTransformer, util
        m = SentenceTransformer('all-MiniLM-L6-v2')
        score = util.cos_sim(m.encode(text_a), m.encode(text_b)).item()
    """
    try:
        model = _get_embed_model()
        if model is None:
            return _SIMILARITY_SAFE_DEFAULT

        from sentence_transformers import util as st_util
        emb_a = model.encode(text_a, convert_to_tensor=True)
        emb_b = model.encode(text_b, convert_to_tensor=True)
        score = float(st_util.cos_sim(emb_a, emb_b).item())
        # Clamp to [0, 1] — cosine can be slightly negative for very dissimilar texts
        return max(0.0, min(1.0, score))
    except Exception as exc:  # noqa: BLE001
        log.warning("compute_similarity failed: %s. Returning safe default.", exc)
        return _SIMILARITY_SAFE_DEFAULT


# ---------------------------------------------------------------------------
# Signal 2 — Concept Overlap (spaCy, offline)
# ---------------------------------------------------------------------------
_SPACY_NLP = None


def _get_spacy_nlp():
    """Lazy-loads spaCy en_core_web_sm. Returns None on failure."""
    global _SPACY_NLP
    if _SPACY_NLP is not None:
        return _SPACY_NLP
    try:
        import spacy
        _SPACY_NLP = spacy.load("en_core_web_sm")
        log.info("spaCy en_core_web_sm loaded successfully.")
    except Exception as exc:  # noqa: BLE001
        log.warning(
            "spaCy model unavailable: %s. "
            "Concept-match will use simple word-overlap fallback.",
            exc,
        )
        _SPACY_NLP = None
    return _SPACY_NLP


def _extract_concepts_spacy(text: str) -> list[str]:
    """
    Extracts key noun-phrase chunks from *text* using spaCy.
    Returns a deduplicated list of lower-cased concept strings.
    """
    nlp = _get_spacy_nlp()
    if nlp is None:
        return []
    doc = nlp(text)
    seen: set[str] = set()
    concepts: list[str] = []
    for chunk in doc.noun_chunks:
        c = chunk.text.strip().lower()
        # Filter out very short / pronoun-only chunks
        if len(c) > 2 and c not in seen:
            seen.add(c)
            concepts.append(c)
    return concepts


def _extract_concepts_fallback(text: str) -> list[str]:
    """
    Simple stopword-filtered word set — used when spaCy is unavailable.
    Returns a deduplicated list of content words (length > 3, not stop words).
    """
    STOP = {
        "the", "and", "for", "that", "this", "with", "are", "was",
        "have", "has", "not", "can", "will", "from", "its", "also",
        "more", "one", "all", "been", "when", "they", "which", "each",
        "than", "then", "into", "over", "also", "used", "use", "uses",
    }
    words = re.findall(r"[a-z]{4,}", text.lower())
    seen: set[str] = set()
    result: list[str] = []
    for w in words:
        if w not in STOP and w not in seen:
            seen.add(w)
            result.append(w)
    return result


def concept_match(
    answer_text: str,
    reference_answer: str,
) -> tuple[float, list[str], list[str]]:
    """
    Extracts key concepts from *reference_answer* and checks coverage in *answer_text*.

    Returns:
        (concept_match_score, missing_concepts, connecting_concepts)

        concept_match_score  — float in [0, 1]: fraction of reference concepts present.
        missing_concepts     — list of reference concepts ABSENT from the student answer.
        connecting_concepts  — list of reference concepts PRESENT in the student answer.

    The missing list becomes the core of the student-facing hint.
    """
    try:
        # Extract concepts from reference
        ref_concepts = _extract_concepts_spacy(reference_answer)
        if not ref_concepts:
            ref_concepts = _extract_concepts_fallback(reference_answer)

        if not ref_concepts:
            # No extractable concepts — return neutral score
            return 0.5, [], []

        answer_lower = answer_text.lower()

        missing: list[str] = []
        connecting: list[str] = []

        for concept in ref_concepts:
            # Check for the concept phrase or any of its individual content words
            concept_words = [w for w in concept.split() if len(w) > 3]
            phrase_present = concept in answer_lower
            words_present = any(w in answer_lower for w in concept_words) if concept_words else False

            if phrase_present or words_present:
                connecting.append(concept)
            else:
                missing.append(concept)

        score = len(connecting) / len(ref_concepts)
        return round(score, 4), missing, connecting

    except Exception as exc:  # noqa: BLE001
        log.warning("concept_match failed: %s. Returning neutral result.", exc)
        return 0.5, [], []


# ---------------------------------------------------------------------------
# Signal 3 — LLM Judge (Gemini, optional)
# ---------------------------------------------------------------------------

def llm_judge(
    answer_text: str,
    reference_answer: str,
    question_text: str,
) -> dict | None:
    """
    Asks Gemini to:
      1. Rate answer correctness / clarity / structure → fused numeric score [0,1]
      2. Write a simple plain-English explanation of the reference answer
      3. Give 2–3 short, actionable tips the student can use immediately

    Returns a dict with keys:
        llm_score        float in [0, 1]
        explanation      str  — simple explanation of the reference answer
        tips             list[str] — short actionable bullets

    Returns None (never raises) if Gemini is unavailable.
    """
    try:
        from app.config import settings
        from google import genai
        from google.genai import types as genai_types
        from app.services.question_generation import FALLBACK_MODELS

        api_key = settings.GEMINI_API_KEY
        if not api_key:
            log.info("GEMINI_API_KEY not set — LLM judge skipped.")
            return None

        prompt = f"""You are an expert technical interviewer evaluating a student's answer.

QUESTION:
{question_text}

REFERENCE ANSWER (the ideal answer):
{reference_answer}

STUDENT'S ANSWER:
{answer_text}

Your task — respond with valid JSON containing exactly these four keys:

  "correctness_score":  a float 0.0–1.0 rating how factually correct the student's answer is
  "clarity_score":      a float 0.0–1.0 rating how clearly and coherently the answer is written
  "structure_score":    a float 0.0–1.0 rating how well the answer is organised and complete
  "explanation":        a SHORT, simple, plain-English explanation of the reference answer
                        (2–4 sentences; imagine explaining to a junior developer)
  "tips":               a JSON array of 2–3 short, specific, actionable tips the student
                        can use to improve their answer RIGHT NOW
                        (e.g. "Mention the CAP theorem to ground your answer",
                               "Add a concrete example of when you'd use a hash map vs a tree")

Return ONLY valid JSON. No markdown fences. No extra text.
"""

        client = genai.Client(api_key=api_key)

        for model_name in FALLBACK_MODELS:
            for _attempt in range(2):
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=genai_types.GenerateContentConfig(
                            response_mime_type="application/json",
                            temperature=0.3,   # low temp → more consistent scoring
                        ),
                    )
                    if response.text:
                        raw = re.sub(r"^```json\s*|\s*```$", "", response.text.strip())
                        data = json.loads(raw)

                        correctness = float(data.get("correctness_score", 0.5))
                        clarity     = float(data.get("clarity_score", 0.5))
                        structure   = float(data.get("structure_score", 0.5))

                        # Weighted blend of the three LLM sub-dimensions
                        llm_score = round(
                            correctness * 0.50 + clarity * 0.25 + structure * 0.25,
                            4,
                        )
                        llm_score = max(0.0, min(1.0, llm_score))

                        explanation = str(data.get("explanation", "")).strip()
                        tips_raw    = data.get("tips", [])
                        tips = [str(t).strip() for t in tips_raw if str(t).strip()]

                        return {
                            "llm_score":   llm_score,
                            "explanation": explanation,
                            "tips":        tips,
                        }

                except Exception as exc:  # noqa: BLE001
                    log.debug("LLM judge attempt failed (%s): %s", model_name, exc)
                    time.sleep(1.0)
                    continue

        log.warning("All LLM judge models failed. Score will be fused without LLM signal.")
        return None

    except Exception as exc:  # noqa: BLE001
        log.warning("llm_judge raised unexpectedly: %s. Skipping.", exc)
        return None


# ---------------------------------------------------------------------------
# Fusion
# ---------------------------------------------------------------------------

def fuse_scores(
    similarity: float,
    concept: float,
    llm: Optional[float],
) -> float:
    """
    Weighted average of available signals.

    Weights when all three signals are present:
        similarity × 0.30 + concept × 0.35 + llm × 0.35

    Weights when LLM is unavailable (None):
        similarity × 0.45 + concept × 0.55
    """
    if llm is not None:
        fused = similarity * 0.30 + concept * 0.35 + llm * 0.35
    else:
        fused = similarity * 0.45 + concept * 0.55
    return round(max(0.0, min(1.0, fused)), 4)


# ---------------------------------------------------------------------------
# Top-level orchestrator
# ---------------------------------------------------------------------------

def score_answer(
    answer_text: str,
    reference_answer: str,
    question_text: str,
) -> dict:
    """
    Runs the full multi-signal scoring pipeline and returns a result dict
    ready to be unpacked into a ScoreOut / Score DB row.

    Keys returned:
        similarity_score        float [0,1]
        similarity_percentage   float [0,100]  (= round(similarity_score*100, 1))
        concept_match_score     float [0,1]
        llm_judge_score         float|None
        fused_score             float [0,1]
        missing_concepts        list[str]
        connecting_concepts     list[str]
        reference_answer        str   (echoed back for client convenience)
        answer_explanation      str   (LLM explanation, or empty string)
        tips                    list[str]
        feedback_text           str   (human-readable summary sentence)

    Each signal is caught individually — a failure in one degrades the score
    gracefully rather than breaking the entire pipeline.
    """
    # ── Signal 1: Embedding Similarity ──────────────────────────────────────
    try:
        similarity = compute_similarity(answer_text, reference_answer)
    except Exception as exc:
        log.warning("Signal 1 (similarity) failed unexpectedly: %s", exc)
        similarity = _SIMILARITY_SAFE_DEFAULT

    # ── Signal 2: Concept Overlap ────────────────────────────────────────────
    try:
        concept_score, missing_concepts, connecting_concepts = concept_match(
            answer_text, reference_answer
        )
    except Exception as exc:
        log.warning("Signal 2 (concept_match) failed unexpectedly: %s", exc)
        concept_score       = 0.5
        missing_concepts    = []
        connecting_concepts = []

    # ── Signal 3: LLM Judge ─────────────────────────────────────────────────
    llm_result      = llm_judge(answer_text, reference_answer, question_text)
    llm_score       = llm_result["llm_score"]       if llm_result else None
    explanation     = llm_result["explanation"]      if llm_result else ""
    tips            = llm_result["tips"]             if llm_result else []

    # ── Fusion ───────────────────────────────────────────────────────────────
    fused = fuse_scores(similarity, concept_score, llm_score)

    # ── Similarity percentage (manually calculable) ──────────────────────────
    # Students/reviewers can reproduce this with:  round(similarity_score * 100, 1)
    similarity_pct = round(similarity * 100, 1)

    # ── Human-readable feedback summary ──────────────────────────────────────
    if fused >= 0.80:
        quality = "Excellent"
    elif fused >= 0.60:
        quality = "Good"
    elif fused >= 0.40:
        quality = "Partial"
    else:
        quality = "Needs improvement"

    missing_summary = (
        f" Key missing concepts: {', '.join(missing_concepts[:3])}."
        if missing_concepts
        else " All key concepts were covered."
    )
    feedback_text = (
        f"{quality} answer (fused score: {round(fused * 100, 1)}%).{missing_summary}"
    )

    return {
        "similarity_score":      round(similarity, 4),
        "similarity_percentage": similarity_pct,
        "concept_match_score":   concept_score,
        "llm_judge_score":       llm_score,
        "fused_score":           fused,
        "missing_concepts":      missing_concepts,
        "connecting_concepts":   connecting_concepts,
        "reference_answer":      reference_answer,
        "answer_explanation":    explanation,
        "tips":                  tips,
        "feedback_text":         feedback_text,
    }
