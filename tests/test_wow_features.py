"""Tests for wow factor features: SSE streaming, knowledge graph, playground config."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import jsonschema

from flask import Flask

from api.math_tutor import math_tutor_bp
from api.study_plan import study_plan_bp
from pipeline.schemas import KNOWLEDGE_GRAPH_SCHEMA, PLAYGROUND_CONFIG_SCHEMA


def _create_test_app(*blueprints):
    app = Flask(__name__)
    app.config["TESTING"] = True
    for bp in blueprints:
        app.register_blueprint(bp)
    return app


# ── SSE Streaming Tests ──────────────────────────────────────


class TestMathTutorStreaming:
    @pytest.fixture
    def client(self):
        app = _create_test_app(math_tutor_bp)
        with app.test_client() as c:
            yield c

    def test_stream_missing_text_returns_400(self, client):
        resp = client.post("/api/math_tutor/stream", json={})
        assert resp.status_code == 400

    def test_stream_empty_text_returns_400(self, client):
        resp = client.post("/api/math_tutor/stream", json={"selected_text": "   "})
        assert resp.status_code == 400

    @patch("api.math_tutor.get_provider")
    def test_stream_returns_sse_content_type(self, mock_provider, client):
        mock_prov = MagicMock()
        mock_prov.generate_stream.return_value = iter(["Hello ", "world"])
        mock_provider.return_value = mock_prov

        resp = client.post("/api/math_tutor/stream", json={
            "selected_text": "$x^2$",
            "context": "We minimize $f(x) = x^2$."
        })
        assert resp.status_code == 200
        assert resp.content_type == "text/event-stream"

    @patch("api.math_tutor.get_provider")
    def test_stream_yields_tokens_and_done(self, mock_provider, client):
        mock_prov = MagicMock()
        mock_prov.generate_stream.return_value = iter(["chunk1", "chunk2"])
        mock_provider.return_value = mock_prov

        resp = client.post("/api/math_tutor/stream", json={
            "selected_text": "$x^2$",
            "context": "context"
        })
        data = resp.get_data(as_text=True)
        assert "chunk1" in data
        assert "chunk2" in data
        assert '"done": true' in data

    @patch("api.math_tutor.get_provider")
    def test_stream_handles_provider_error(self, mock_provider, client):
        mock_prov = MagicMock()
        mock_prov.generate_stream.side_effect = RuntimeError("API down")
        mock_provider.return_value = mock_prov

        resp = client.post("/api/math_tutor/stream", json={
            "selected_text": "$x^2$",
            "context": "context"
        })
        data = resp.get_data(as_text=True)
        assert "error" in data


class TestStudyPlanStreaming:
    @pytest.fixture
    def client(self):
        app = _create_test_app(study_plan_bp)
        with app.test_client() as c:
            yield c

    def test_stream_missing_fields_returns_400(self, client):
        resp = client.post("/api/study_plan/stream", json={"background": "CS degree"})
        assert resp.status_code == 400

    @patch("api.study_plan._get_available_techniques")
    @patch("api.study_plan.get_provider")
    def test_stream_returns_sse(self, mock_provider, mock_techniques, client):
        mock_techniques.return_value = [{"slug": "test", "name": "Test"}]
        mock_prov = MagicMock()
        mock_prov.generate_stream.return_value = iter(['{"roadmap":', '[], "rationale": "ok"}'])
        mock_provider.return_value = mock_prov

        resp = client.post("/api/study_plan/stream", json={
            "background": "CS degree",
            "goals": "learn optimization"
        })
        assert resp.status_code == 200
        assert resp.content_type == "text/event-stream"


# ── Knowledge Graph Schema Tests ─────────────────────────────


class TestKnowledgeGraphSchema:
    def test_valid_graph(self):
        valid = {
            "nodes": [
                {"slug": "gradient-descent", "label": "Gradient Descent", "category": "gradient-based", "summary": "Iterative first-order optimizer."},
                {"slug": "genetic-algorithm", "label": "Genetic Algorithm", "category": "evolutionary", "summary": "Population-based search."},
            ],
            "edges": [
                {"source": "gradient-descent", "target": "genetic-algorithm", "relationship": "gradient-free alternative", "strength": 0.6},
            ],
        }
        jsonschema.validate(instance=valid, schema=KNOWLEDGE_GRAPH_SCHEMA)

    def test_missing_nodes_fails(self):
        invalid = {"edges": []}
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=invalid, schema=KNOWLEDGE_GRAPH_SCHEMA)

    def test_invalid_category_fails(self):
        invalid = {
            "nodes": [{"slug": "x", "label": "X", "category": "unknown", "summary": "s"}],
            "edges": [],
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=invalid, schema=KNOWLEDGE_GRAPH_SCHEMA)

    def test_edge_strength_bounds(self):
        invalid = {
            "nodes": [{"slug": "a", "label": "A", "category": "evolutionary", "summary": "s"}],
            "edges": [{"source": "a", "target": "a", "relationship": "self", "strength": 1.5}],
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=invalid, schema=KNOWLEDGE_GRAPH_SCHEMA)

    def test_all_valid_categories(self):
        for cat in ["evolutionary", "gradient-based", "probabilistic", "direct-search"]:
            valid = {
                "nodes": [{"slug": "x", "label": "X", "category": cat, "summary": "s"}],
                "edges": [{"source": "x", "target": "x", "relationship": "r", "strength": 0.5}],
            }
            jsonschema.validate(instance=valid, schema=KNOWLEDGE_GRAPH_SCHEMA)


# ── Playground Config Schema Tests ───────────────────────────


class TestPlaygroundConfigSchema:
    def test_valid_config(self):
        valid = {
            "parameters": [
                {"name": "learningRate", "label": "Learning Rate", "min": 0.001, "max": 1.0, "default": 0.01, "step": 0.001},
            ],
            "objective_function": "rosenbrock",
            "visualization_type": "contour_trajectory",
        }
        jsonschema.validate(instance=valid, schema=PLAYGROUND_CONFIG_SCHEMA)

    def test_missing_parameters_fails(self):
        invalid = {"objective_function": "sphere", "visualization_type": "contour_trajectory"}
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=invalid, schema=PLAYGROUND_CONFIG_SCHEMA)

    def test_invalid_objective_function_fails(self):
        invalid = {
            "parameters": [{"name": "x", "label": "X", "min": 0, "max": 1, "default": 0.5, "step": 0.1}],
            "objective_function": "banana",
            "visualization_type": "contour_trajectory",
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=invalid, schema=PLAYGROUND_CONFIG_SCHEMA)

    def test_invalid_visualization_type_fails(self):
        invalid = {
            "parameters": [{"name": "x", "label": "X", "min": 0, "max": 1, "default": 0.5, "step": 0.1}],
            "objective_function": "sphere",
            "visualization_type": "pie_chart",
        }
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=invalid, schema=PLAYGROUND_CONFIG_SCHEMA)

    def test_all_valid_objective_functions(self):
        for fn in ["rosenbrock", "rastrigin", "sphere", "ackley"]:
            valid = {
                "parameters": [{"name": "x", "label": "X", "min": 0, "max": 1, "default": 0.5, "step": 0.1}],
                "objective_function": fn,
                "visualization_type": "contour_trajectory",
            }
            jsonschema.validate(instance=valid, schema=PLAYGROUND_CONFIG_SCHEMA)

    def test_parameter_with_description(self):
        valid = {
            "parameters": [
                {"name": "lr", "label": "LR", "min": 0, "max": 1, "default": 0.01, "step": 0.001, "description": "Step size"},
            ],
            "objective_function": "sphere",
            "visualization_type": "convergence_curve",
        }
        jsonschema.validate(instance=valid, schema=PLAYGROUND_CONFIG_SCHEMA)


# ── Generator Function Tests ─────────────────────────────────


class TestGenerateKnowledgeGraph:
    @patch("pipeline.generator.generate_with_retry")
    @patch("pipeline.generator.get_provider")
    def test_generates_knowledge_graph(self, mock_get_provider, mock_generate):
        from pipeline.generator import generate_knowledge_graph

        mock_get_provider.return_value = MagicMock()
        mock_generate.return_value = {
            "nodes": [{"slug": "gd", "label": "GD", "category": "gradient-based", "summary": "s"}],
            "edges": [{"source": "gd", "target": "gd", "relationship": "r", "strength": 0.5}],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("pipeline.generator.GENERATED_ROOT", Path(tmpdir)):
                result = generate_knowledge_graph(
                    {"gradient-descent": {"technique_name": "Gradient Descent"}},
                    force=True,
                )
                assert result.status == "generated"
                assert "nodes" in result.payload
                assert "edges" in result.payload
                assert (Path(tmpdir) / "knowledge_graph.json").exists()


class TestGeneratePlaygroundConfig:
    @patch("pipeline.generator.generate_with_retry")
    @patch("pipeline.generator.get_provider")
    def test_generates_playground_config(self, mock_get_provider, mock_generate):
        from pipeline.generator import generate_playground_config

        mock_get_provider.return_value = MagicMock()
        mock_generate.return_value = {
            "parameters": [{"name": "lr", "label": "LR", "min": 0, "max": 1, "default": 0.01, "step": 0.001}],
            "objective_function": "rosenbrock",
            "visualization_type": "contour_trajectory",
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("pipeline.generator.CONTENT_DIR", Path(tmpdir)):
                result = generate_playground_config(
                    "gradient-descent",
                    "Gradient Descent",
                    {"technique_name": "Gradient Descent", "slug": "gradient-descent"},
                    force=True,
                )
                assert result.status == "generated"
                assert "parameters" in result.payload
                assert (Path(tmpdir) / "gradient-descent" / "playground_config.json").exists()


# ── LLM Provider Streaming Tests ─────────────────────────────


class TestLLMProviderStreaming:
    def test_openai_provider_has_generate_stream(self):
        from pipeline.llm_client import OpenAIProvider
        assert hasattr(OpenAIProvider, "generate_stream")

    def test_gemini_provider_has_generate_stream(self):
        from pipeline.llm_client import GeminiProvider
        assert hasattr(GeminiProvider, "generate_stream")

    def test_base_provider_has_generate_stream(self):
        from pipeline.llm_client import LLMProvider
        assert hasattr(LLMProvider, "generate_stream")
