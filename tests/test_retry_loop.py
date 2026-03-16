"""Tests for the artifact retry loop module."""

from unittest.mock import MagicMock, patch

from pipeline.retry_loop import retry_loop, revise_artifact


class TestRetryLoop:
    @patch("pipeline.retry_loop.evaluate_artifact")
    @patch("pipeline.retry_loop.validate_schema")
    def test_passes_on_first_attempt(self, mock_schema, mock_judge):
        mock_schema.return_value = {"passed": True, "errors": []}
        mock_judge.return_value = {
            "passed": True,
            "overall_score": 8,
            "criteria_scores": {},
            "critiques": [],
            "revision_instructions": [],
        }

        result = retry_loop("cma-es", "overview", {"markdown": "content"})
        assert result["status"] == "passed"
        assert result["attempts"] == 1

    @patch("pipeline.retry_loop.revise_artifact")
    @patch("pipeline.retry_loop.evaluate_artifact")
    @patch("pipeline.retry_loop.validate_schema")
    def test_retries_on_judge_failure(self, mock_schema, mock_judge, mock_revise):
        mock_schema.return_value = {"passed": True, "errors": []}
        # Fail first, pass second
        mock_judge.side_effect = [
            {
                "passed": False,
                "overall_score": 4,
                "critiques": ["Needs improvement"],
                "revision_instructions": ["Fix it"],
            },
            {
                "passed": True,
                "overall_score": 8,
                "criteria_scores": {},
                "critiques": [],
                "revision_instructions": [],
            },
        ]
        mock_revise.return_value = {"markdown": "improved content"}

        result = retry_loop("cma-es", "overview", {"markdown": "content"})
        assert result["status"] == "passed"
        assert result["attempts"] == 2
        assert mock_revise.call_count == 1

    @patch("pipeline.retry_loop.revise_artifact")
    @patch("pipeline.retry_loop.evaluate_artifact")
    @patch("pipeline.retry_loop.validate_schema")
    def test_persistent_failure_after_max_attempts(
        self, mock_schema, mock_judge, mock_revise
    ):
        mock_schema.return_value = {"passed": True, "errors": []}
        mock_judge.return_value = {
            "passed": False,
            "overall_score": 3,
            "critiques": ["Bad content"],
            "revision_instructions": ["Rewrite"],
        }
        mock_revise.return_value = {"markdown": "still bad"}

        result = retry_loop(
            "cma-es", "overview", {"markdown": "bad"}, max_attempts=3
        )
        assert result["status"] == "persistent_failure"
        assert result["attempts"] == 3

    @patch("pipeline.retry_loop.validate_schema")
    def test_schema_failure_records_history(self, mock_schema):
        mock_schema.return_value = {
            "passed": False,
            "errors": ["Missing field"],
        }

        result = retry_loop(
            "cma-es", "overview", {"incomplete": True}, max_attempts=1
        )
        assert result["status"] == "persistent_failure"
        assert any(
            h.get("stage") == "schema_invalid"
            for h in result["judge_history"]
        )


class TestReviseArtifact:
    @patch("pipeline.retry_loop.get_provider")
    @patch("pipeline.retry_loop.generate_with_retry")
    def test_revise_calls_provider(self, mock_generate, mock_provider):
        mock_provider.return_value = MagicMock()
        mock_generate.return_value = {
            "technique_slug": "cma-es",
            "artifact_type": "overview",
            "title": "CMA-ES",
            "summary": "Revised summary.",
            "markdown": "x " * 800,
            "use_cases": ["optimization"],
            "strengths": ["powerful"],
            "limitations": ["complex"],
            "comparisons": ["vs DE"],
        }

        judge_result = {
            "critiques": ["Too brief"],
            "revision_instructions": ["Expand the summary"],
        }

        result = revise_artifact(
            "cma-es", "overview", {"markdown": "short"}, judge_result
        )
        assert mock_generate.called
        assert result["summary"] == "Revised summary."
