"""Tests for the LLM judge module."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from pipeline.judge import (
    _default_rubrics,
    build_revision_prompt,
    evaluate_artifact,
    load_reference,
    load_rubrics,
)


class TestLoadRubrics:
    def test_default_rubrics_structure(self):
        rubrics = _default_rubrics()
        assert "pass_threshold" in rubrics
        assert "criteria" in rubrics
        assert rubrics["pass_threshold"] == 7
        assert "factual_accuracy" in rubrics["criteria"]
        assert "math_correctness" in rubrics["criteria"]
        assert "clarity" in rubrics["criteria"]
        assert "code_quality" in rubrics["criteria"]

    @patch("pipeline.judge.RUBRICS_PATH")
    def test_load_rubrics_from_file(self, mock_path):
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = json.dumps({
            "pass_threshold": 8,
            "criteria": {"test": {"weight": 1.0, "description": "test"}},
        })
        rubrics = load_rubrics()
        assert rubrics["pass_threshold"] == 8

    @patch("pipeline.judge.RUBRICS_PATH")
    def test_load_rubrics_fallback_to_defaults(self, mock_path):
        mock_path.exists.return_value = False
        rubrics = load_rubrics()
        assert rubrics["pass_threshold"] == 7


class TestLoadReference:
    @patch("pipeline.judge.REFERENCE_DIR")
    def test_load_existing_reference(self, mock_dir):
        ref_data = {
            "name": "CMA-ES",
            "key_facts": ["fact1"],
            "forbidden_claims": ["claim1"],
        }
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.read_text.return_value = json.dumps(ref_data)
        mock_dir.__truediv__ = MagicMock(return_value=mock_path)

        result = load_reference("cma-es")
        assert result == ref_data

    @patch("pipeline.judge.REFERENCE_DIR")
    def test_load_missing_reference(self, mock_dir):
        mock_path = MagicMock()
        mock_path.exists.return_value = False
        mock_dir.__truediv__ = MagicMock(return_value=mock_path)

        result = load_reference("nonexistent")
        assert result is None


class TestEvaluateArtifact:
    @patch("pipeline.judge.get_provider")
    @patch("pipeline.judge.generate_with_retry")
    @patch("pipeline.judge.load_reference")
    @patch("pipeline.judge.load_rubrics")
    def test_evaluate_passes(
        self, mock_rubrics, mock_ref, mock_generate, mock_provider
    ):
        mock_rubrics.return_value = _default_rubrics()
        mock_ref.return_value = {
            "name": "CMA-ES",
            "key_facts": ["CMA-ES is derivative-free"],
            "forbidden_claims": ["CMA-ES requires gradients"],
        }
        mock_provider.return_value = MagicMock()
        mock_generate.return_value = {
            "passed": True,
            "overall_score": 8,
            "criteria_scores": {
                "factual_accuracy": 9,
                "math_correctness": 8,
                "clarity": 8,
                "code_quality": 7,
            },
            "critiques": [],
            "revision_instructions": [],
        }

        result = evaluate_artifact("cma-es", "overview", {"markdown": "content"})
        assert result["passed"] is True
        assert result["overall_score"] == 8

    @patch("pipeline.judge.get_provider")
    @patch("pipeline.judge.generate_with_retry")
    @patch("pipeline.judge.load_reference")
    @patch("pipeline.judge.load_rubrics")
    def test_evaluate_handles_exception(
        self, mock_rubrics, mock_ref, mock_generate, mock_provider
    ):
        mock_rubrics.return_value = _default_rubrics()
        mock_ref.return_value = None
        mock_provider.return_value = MagicMock()
        mock_generate.side_effect = RuntimeError("API error")

        result = evaluate_artifact("cma-es", "overview", {"markdown": "content"})
        assert result["passed"] is False
        assert result["overall_score"] == 0


class TestBuildRevisionPrompt:
    def test_builds_prompts(self):
        judge_result = {
            "overall_score": 5,
            "critiques": ["Variable undefined"],
            "revision_instructions": ["Define the variable"],
        }
        system, user = build_revision_prompt("overview", {"key": "val"}, judge_result)
        assert "Revise" in system
        assert "Variable undefined" in user
        assert "Define the variable" in user
        assert "5/10" in user
