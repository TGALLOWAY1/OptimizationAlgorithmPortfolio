"""Tests for the new API endpoints: math_tutor, compare, study_plan, adapt_code."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from api.math_tutor import math_tutor_bp
from api.compare import compare_bp, _get_available_slugs, _load_technique_artifacts
from api.study_plan import study_plan_bp
from api.adapt_code import adapt_code_bp

from flask import Flask


def _create_test_app(*blueprints):
    app = Flask(__name__)
    app.config["TESTING"] = True
    for bp in blueprints:
        app.register_blueprint(bp)
    return app


# ── Math Tutor ──────────────────────────────────────────────


class TestMathTutorEndpoint:
    @pytest.fixture
    def client(self):
        app = _create_test_app(math_tutor_bp)
        with app.test_client() as c:
            yield c

    def test_missing_selected_text_returns_400(self, client):
        resp = client.post("/api/math_tutor", json={})
        assert resp.status_code == 400

    def test_empty_selected_text_returns_400(self, client):
        resp = client.post("/api/math_tutor", json={"selected_text": "   "})
        assert resp.status_code == 400

    def test_text_too_long_returns_400(self, client):
        resp = client.post("/api/math_tutor", json={"selected_text": "x" * 2001})
        assert resp.status_code == 400

    @patch("api.math_tutor.generate_with_retry")
    @patch("api.math_tutor.get_provider")
    def test_successful_explanation(self, mock_provider, mock_generate, client):
        mock_provider.return_value = MagicMock()
        mock_generate.return_value = {"explanation": "This is $x^2$."}
        resp = client.post("/api/math_tutor", json={
            "selected_text": "$x^2$",
            "context": "We minimize $f(x) = x^2$.",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert "explanation" in data

    @patch("api.math_tutor.generate_with_retry")
    @patch("api.math_tutor.get_provider")
    def test_llm_failure_returns_500(self, mock_provider, mock_generate, client):
        mock_provider.return_value = MagicMock()
        mock_generate.side_effect = RuntimeError("fail")
        resp = client.post("/api/math_tutor", json={
            "selected_text": "$x$",
            "context": "context",
        })
        assert resp.status_code == 500


# ── Compare ─────────────────────────────────────────────────


class TestCompareEndpoint:
    @pytest.fixture
    def client(self):
        app = _create_test_app(compare_bp)
        with app.test_client() as c:
            yield c

    def test_missing_slugs_returns_400(self, client):
        resp = client.post("/api/compare", json={})
        assert resp.status_code == 400

    def test_same_slugs_returns_400(self, client):
        resp = client.post("/api/compare", json={"slug_a": "gd", "slug_b": "gd"})
        assert resp.status_code == 400

    @patch("api.compare._load_technique_artifacts")
    def test_unknown_slug_returns_404(self, mock_load, client):
        mock_load.return_value = None
        resp = client.post("/api/compare", json={"slug_a": "fake-a", "slug_b": "fake-b"})
        assert resp.status_code == 404

    @patch("api.compare.generate_with_retry")
    @patch("api.compare.get_provider")
    @patch("api.compare._load_technique_artifacts")
    def test_successful_comparison(self, mock_load, mock_provider, mock_generate, client):
        mock_load.return_value = {"overview": {"summary": "test"}}
        mock_provider.return_value = MagicMock()
        mock_generate.return_value = {
            "algorithm_a": "A",
            "algorithm_b": "B",
            "pros_a": ["fast"],
            "pros_b": ["accurate"],
            "cons_a": ["slow convergence"],
            "cons_b": ["complex"],
            "best_for_a": "simple problems",
            "best_for_b": "complex problems",
            "summary": "A is simpler, B is more powerful.",
        }
        resp = client.post("/api/compare", json={"slug_a": "algo-a", "slug_b": "algo-b"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["algorithm_a"] == "A"


# ── Study Plan ──────────────────────────────────────────────


class TestStudyPlanEndpoint:
    @pytest.fixture
    def client(self):
        app = _create_test_app(study_plan_bp)
        with app.test_client() as c:
            yield c

    def test_missing_fields_returns_400(self, client):
        resp = client.post("/api/study_plan", json={"background": "CS"})
        assert resp.status_code == 400

    def test_empty_fields_returns_400(self, client):
        resp = client.post("/api/study_plan", json={"background": "", "goals": ""})
        assert resp.status_code == 400

    @patch("api.study_plan._get_available_techniques")
    def test_no_techniques_returns_404(self, mock_get, client):
        mock_get.return_value = []
        resp = client.post("/api/study_plan", json={
            "background": "CS student",
            "goals": "Learn optimization",
        })
        assert resp.status_code == 404

    @patch("api.study_plan.generate_with_retry")
    @patch("api.study_plan.get_provider")
    @patch("api.study_plan._get_available_techniques")
    def test_successful_plan(self, mock_get, mock_provider, mock_generate, client):
        mock_get.return_value = [{"slug": "gd", "name": "Gradient Descent"}]
        mock_provider.return_value = MagicMock()
        mock_generate.return_value = {
            "roadmap": [
                {"slug": "gd", "title": "Gradient Descent", "reason": "Foundational", "order": 1}
            ],
            "rationale": "Start with basics.",
        }
        resp = client.post("/api/study_plan", json={
            "background": "CS student",
            "goals": "Learn optimization",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["roadmap"]) == 1


# ── Adapt Code ──────────────────────────────────────────────


class TestAdaptCodeEndpoint:
    @pytest.fixture
    def client(self):
        app = _create_test_app(adapt_code_bp)
        with app.test_client() as c:
            yield c

    def test_missing_source_code_returns_400(self, client):
        resp = client.post("/api/adapt_code", json={"target_framework": "jax"})
        assert resp.status_code == 400

    def test_missing_target_framework_returns_400(self, client):
        resp = client.post("/api/adapt_code", json={"source_code": "x = 1"})
        assert resp.status_code == 400

    @patch("api.adapt_code.generate_with_retry")
    @patch("api.adapt_code.get_provider")
    def test_successful_adaptation(self, mock_provider, mock_generate, client):
        mock_provider.return_value = MagicMock()
        mock_generate.return_value = {
            "adapted_code": "import jax\nx = jax.numpy.array([1])",
            "notes": "Converted numpy to jax.",
        }
        resp = client.post("/api/adapt_code", json={
            "source_code": "import numpy as np\nx = np.array([1])",
            "target_framework": "jax",
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert "adapted_code" in data
