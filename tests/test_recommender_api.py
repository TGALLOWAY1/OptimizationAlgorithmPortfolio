"""Tests for the Algorithm Recommender API endpoint."""

import json
from unittest.mock import patch, MagicMock

import pytest

from pipeline.recommender_api import app, get_recommendations


@pytest.fixture
def client():
    """Flask test client."""
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


MOCK_RECOMMENDATIONS = [
    {
        "algorithm": "Bayesian Optimization",
        "justification": "Ideal for expensive black-box evaluations with a small budget.",
        "confidence_score": 92,
        "url_slug": "bayesian-optimization",
    },
    {
        "algorithm": "CMA-ES",
        "justification": "Strong for noisy continuous optimization problems.",
        "confidence_score": 78,
        "url_slug": "cma-es",
    },
]


class TestRecommendEndpoint:
    def test_missing_query_returns_400(self, client):
        resp = client.post("/api/recommend", json={})
        assert resp.status_code == 400
        assert "query" in resp.get_json()["error"].lower()

    def test_empty_query_returns_400(self, client):
        resp = client.post("/api/recommend", json={"query": "   "})
        assert resp.status_code == 400

    def test_no_json_body_returns_400(self, client):
        resp = client.post("/api/recommend", content_type="application/json", data="")
        assert resp.status_code == 400

    def test_query_too_long_returns_400(self, client):
        resp = client.post("/api/recommend", json={"query": "x" * 2001})
        assert resp.status_code == 400
        assert "2000" in resp.get_json()["error"]

    @patch("pipeline.recommender_api.get_recommendations")
    def test_successful_recommendation(self, mock_get, client):
        mock_get.return_value = MOCK_RECOMMENDATIONS
        resp = client.post(
            "/api/recommend",
            json={"query": "I have a noisy black-box objective with a small budget"},
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["algorithm"] == "Bayesian Optimization"
        assert data[0]["confidence_score"] == 92
        assert data[0]["url_slug"] == "bayesian-optimization"

    @patch("pipeline.recommender_api.get_recommendations")
    def test_llm_failure_returns_500(self, mock_get, client):
        mock_get.side_effect = RuntimeError("LLM unavailable")
        resp = client.post(
            "/api/recommend",
            json={"query": "some valid query"},
        )
        assert resp.status_code == 500
        assert "error" in resp.get_json()


class TestGetRecommendations:
    @patch("pipeline.recommender_api.generate_with_retry")
    @patch("pipeline.recommender_api.get_provider")
    @patch("pipeline.recommender_api._load_prompt_template")
    @patch("pipeline.recommender_api._load_use_case_matrix")
    def test_calls_llm_with_query_and_matrix(
        self, mock_matrix, mock_prompt, mock_provider, mock_generate
    ):
        mock_matrix.return_value = {"algorithms": ["Bayesian Optimization"]}
        mock_prompt.return_value = "System prompt with {{use_case_matrix}}"
        mock_provider.return_value = MagicMock()
        mock_generate.return_value = {"recommendations": MOCK_RECOMMENDATIONS}

        result = get_recommendations("noisy black-box")

        mock_matrix.assert_called_once()
        mock_provider.assert_called_once_with("recommender")
        assert mock_generate.call_count == 1

        # Verify the matrix was injected into the system prompt
        call_args = mock_generate.call_args
        system_prompt = call_args.kwargs.get("system_prompt") or call_args[1].get("system_prompt") or call_args[0][1]
        assert "Bayesian Optimization" in system_prompt

        assert result == MOCK_RECOMMENDATIONS

    @patch("pipeline.recommender_api.generate_with_retry")
    @patch("pipeline.recommender_api.get_provider")
    @patch("pipeline.recommender_api._load_prompt_template")
    @patch("pipeline.recommender_api._load_use_case_matrix")
    def test_empty_matrix_still_works(
        self, mock_matrix, mock_prompt, mock_provider, mock_generate
    ):
        mock_matrix.return_value = {}
        mock_prompt.return_value = "Prompt {{use_case_matrix}}"
        mock_provider.return_value = MagicMock()
        mock_generate.return_value = {"recommendations": MOCK_RECOMMENDATIONS}

        result = get_recommendations("some query")
        assert len(result) == 2


class TestProviderMapping:
    def test_recommender_mapped_in_config(self):
        from pipeline.llm_client import load_config

        config = load_config()
        assert "recommender" in config["artifact_provider_map"]
