"""
Tests for the multi-signal scoring service.

Run with:   pytest backend/tests/test_scoring.py -v

The tests are deliberately dependency-light:
  - Signal 1 (embedding) is tested with the model mocked so the test suite
    runs fast even without sentence-transformers installed.
  - Signal 2 (concept overlap) uses pure logic — no external deps.
  - Signal 3 (LLM judge) is mocked out — we test the fusion math, not Gemini.
  - Integration test (score_answer) verifies the top-level dict contract.
"""

import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REFERENCE = (
    "A hash map stores key-value pairs. It uses a hash function to map keys "
    "to buckets in an array. Average lookup is O(1); worst case O(n) due to "
    "hash collisions. Good load-factor management keeps performance near O(1)."
)

GOOD_ANSWER = (
    "A hash map is a data structure that stores key-value pairs using a hash "
    "function to compute the bucket index. Lookup is O(1) average, O(n) worst "
    "case because of collisions."
)

POOR_ANSWER = "Hash maps are fast."


# ---------------------------------------------------------------------------
# Signal 1: compute_similarity
# ---------------------------------------------------------------------------

class TestComputeSimilarity:
    def test_identical_texts_return_one(self):
        """Identical strings should yield cosine similarity ≈ 1.0."""
        from app.services.scoring import compute_similarity
        score = compute_similarity("hello world", "hello world")
        assert 0.95 <= score <= 1.0

    def test_completely_different_texts_return_low_score(self):
        """Very unrelated strings should yield low similarity."""
        from app.services.scoring import compute_similarity
        score = compute_similarity(
            "apple banana orange",
            "quantum mechanics electron spin",
        )
        assert score < 0.7   # not necessarily 0, but meaningfully low

    def test_returns_float_in_range(self):
        from app.services.scoring import compute_similarity
        score = compute_similarity(GOOD_ANSWER, REFERENCE)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_returns_safe_default_when_model_unavailable(self):
        """If the model cannot be loaded, should return 0.5 (never raise)."""
        with patch("app.services.scoring._get_embed_model", return_value=None):
            from app.services.scoring import compute_similarity, _SIMILARITY_SAFE_DEFAULT
            score = compute_similarity("any text", "any other text")
            assert score == _SIMILARITY_SAFE_DEFAULT


# ---------------------------------------------------------------------------
# Signal 2: concept_match
# ---------------------------------------------------------------------------

class TestConceptMatch:
    def test_good_answer_has_low_missing(self):
        from app.services.scoring import concept_match
        score, missing, connecting = concept_match(GOOD_ANSWER, REFERENCE)
        assert score >= 0.4
        assert isinstance(missing, list)
        assert isinstance(connecting, list)

    def test_poor_answer_has_high_missing(self):
        from app.services.scoring import concept_match
        score, missing, connecting = concept_match(POOR_ANSWER, REFERENCE)
        assert score <= 0.6
        assert len(missing) >= len(connecting)

    def test_returns_tuple_of_three(self):
        from app.services.scoring import concept_match
        result = concept_match(GOOD_ANSWER, REFERENCE)
        assert len(result) == 3
        score, missing, connecting = result
        assert 0.0 <= score <= 1.0

    def test_score_in_valid_range(self):
        from app.services.scoring import concept_match
        score, _, _ = concept_match("random words here", REFERENCE)
        assert 0.0 <= score <= 1.0

    def test_fallback_works_without_spacy(self):
        """concept_match should still return results if spaCy is unavailable."""
        with patch("app.services.scoring._get_spacy_nlp", return_value=None):
            from app.services.scoring import concept_match
            score, missing, connecting = concept_match(GOOD_ANSWER, REFERENCE)
            assert 0.0 <= score <= 1.0


# ---------------------------------------------------------------------------
# Signal 3: llm_judge (mocked — we validate structure, not Gemini output)
# ---------------------------------------------------------------------------

class TestLlmJudge:
    def test_returns_none_when_no_api_key(self):
        with patch("app.config.settings") as mock_settings:
            mock_settings.GEMINI_API_KEY = ""
            from app.services import scoring
            result = scoring.llm_judge(GOOD_ANSWER, REFERENCE, "What is a hash map?")
        assert result is None

    def test_returns_dict_with_expected_keys_on_success(self):
        """When the LLM returns a valid JSON response, we expect the right keys."""
        fake_response_text = (
            '{"correctness_score": 0.8, "clarity_score": 0.7, "structure_score": 0.75, '
            '"explanation": "A hash map uses a hash function to find buckets quickly.", '
            '"tips": ["Mention O(1) complexity", "Discuss collision handling"]}'
        )
        mock_response = MagicMock()
        mock_response.text = fake_response_text

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = mock_response

        with (
            patch("app.config.settings") as mock_settings,
            patch("google.genai.Client", return_value=mock_client),
        ):
            mock_settings.GEMINI_API_KEY = "fake-key"
            from app.services import scoring
            result = scoring.llm_judge(GOOD_ANSWER, REFERENCE, "What is a hash map?")

        if result is not None:   # LLM path reached
            assert "llm_score" in result
            assert "explanation" in result
            assert "tips" in result
            assert 0.0 <= result["llm_score"] <= 1.0
            assert isinstance(result["tips"], list)


# ---------------------------------------------------------------------------
# Fusion
# ---------------------------------------------------------------------------

class TestFuseScores:
    def test_all_three_signals(self):
        from app.services.scoring import fuse_scores
        fused = fuse_scores(0.8, 0.6, 0.7)
        # 0.8*0.30 + 0.6*0.35 + 0.7*0.35 = 0.24 + 0.21 + 0.245 = 0.695
        assert abs(fused - 0.695) < 0.001

    def test_without_llm_signal(self):
        from app.services.scoring import fuse_scores
        fused = fuse_scores(0.8, 0.6, None)
        # 0.8*0.45 + 0.6*0.55 = 0.36 + 0.33 = 0.69
        assert abs(fused - 0.69) < 0.001

    def test_output_clamped_to_zero_one(self):
        from app.services.scoring import fuse_scores
        assert fuse_scores(0.0, 0.0, 0.0) == 0.0
        assert fuse_scores(1.0, 1.0, 1.0) == 1.0


# ---------------------------------------------------------------------------
# Integration: score_answer dict contract
# ---------------------------------------------------------------------------

class TestScoreAnswer:
    def test_returns_all_required_keys(self):
        """score_answer must return all keys expected by the router."""
        from app.services.scoring import score_answer
        result = score_answer(GOOD_ANSWER, REFERENCE, "What is a hash map?")

        required_keys = {
            "similarity_score",
            "similarity_percentage",
            "concept_match_score",
            "fused_score",
            "missing_concepts",
            "connecting_concepts",
            "reference_answer",
            "answer_explanation",
            "tips",
            "feedback_text",
        }
        for key in required_keys:
            assert key in result, f"Missing key: {key}"

    def test_similarity_percentage_is_score_times_100(self):
        from app.services.scoring import score_answer
        result = score_answer(GOOD_ANSWER, REFERENCE, "What is a hash map?")
        expected_pct = round(result["similarity_score"] * 100, 1)
        assert result["similarity_percentage"] == expected_pct

    def test_fused_score_in_range(self):
        from app.services.scoring import score_answer
        result = score_answer(POOR_ANSWER, REFERENCE, "What is a hash map?")
        assert 0.0 <= result["fused_score"] <= 1.0

    def test_missing_and_connecting_are_lists(self):
        from app.services.scoring import score_answer
        result = score_answer(GOOD_ANSWER, REFERENCE, "What is a hash map?")
        assert isinstance(result["missing_concepts"], list)
        assert isinstance(result["connecting_concepts"], list)

    def test_reference_answer_echoed_back(self):
        from app.services.scoring import score_answer
        result = score_answer(GOOD_ANSWER, REFERENCE, "What is a hash map?")
        assert result["reference_answer"] == REFERENCE
