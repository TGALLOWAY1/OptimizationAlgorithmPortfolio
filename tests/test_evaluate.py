"""Tests for the main evaluation orchestrator."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from pipeline.evaluate import (
    _check_duplicated_paragraphs,
    _check_latex_balance,
    evaluate_single_artifact,
    evaluate_technique,
    promote_artifact,
    run_deterministic_checks,
    save_metrics,
)


class TestDeterministicChecks:
    def test_clean_artifact_passes(self):
        data = {
            "summary": "A clean summary without placeholders.",
            "markdown": "word " * 900,
        }
        result = run_deterministic_checks("overview", data)
        assert result["passed"] is True

    def test_todo_placeholder_detected(self):
        data = {
            "summary": "TODO: fill this in later.",
            "markdown": "word " * 900,
        }
        result = run_deterministic_checks("overview", data)
        assert result["passed"] is False
        assert any("placeholder" in e.lower() for e in result["errors"])

    def test_tbd_placeholder_detected(self):
        data = {
            "summary": "This section is TBD.",
            "markdown": "word " * 900,
        }
        result = run_deterministic_checks("overview", data)
        assert result["passed"] is False

    def test_fixme_placeholder_detected(self):
        data = {
            "markdown": "Content with FIXME markers " + "word " * 900,
        }
        result = run_deterministic_checks("math_deep_dive", data)
        assert result["passed"] is False


class TestLatexBalance:
    def test_balanced_inline_math(self):
        errors = []
        _check_latex_balance("The equation $x^2$ is simple.", errors)
        assert len(errors) == 0

    def test_unbalanced_inline_math(self):
        errors = []
        _check_latex_balance("The equation $x^2 is missing delimiter.", errors)
        assert any("inline math" in e.lower() for e in errors)

    def test_balanced_display_math(self):
        errors = []
        _check_latex_balance("Display: $$x^2 + y^2 = r^2$$", errors)
        assert len(errors) == 0

    def test_balanced_paren_delimiters(self):
        errors = []
        _check_latex_balance("Equation \\(x^2\\) here.", errors)
        assert len(errors) == 0

    def test_unbalanced_paren_delimiters(self):
        errors = []
        _check_latex_balance("Equation \\(x^2 missing close.", errors)
        assert any("parenthesis" in e.lower() for e in errors)


class TestDuplicatedParagraphs:
    def test_no_duplicates(self):
        errors = []
        text = "First paragraph with enough content to be meaningful.\n\nSecond paragraph that is different."
        _check_duplicated_paragraphs(text, errors)
        assert len(errors) == 0

    def test_detects_duplicates(self):
        errors = []
        para = "This is a duplicated paragraph with enough content to trigger detection."
        text = f"{para}\n\n{para}"
        _check_duplicated_paragraphs(text, errors)
        assert any("duplicated" in e.lower() for e in errors)


class TestEvaluateSingleArtifact:
    def test_schema_failure_returns_schema_invalid(self):
        result = evaluate_single_artifact(
            "cma-es", "overview", {"bad": "data"}, skip_judge=True
        )
        assert result["status"] == "schema_invalid"

    def test_static_check_failure(self):
        data = {
            "technique_slug": "cma-es",
            "artifact_type": "overview",
            "title": "CMA-ES",
            "summary": "TODO: write this",
            "markdown": "x " * 800,
            "use_cases": ["optimization"],
            "strengths": ["good"],
            "limitations": ["complex"],
            "comparisons": ["vs DE"],
        }
        result = evaluate_single_artifact(
            "cma-es", "overview", data, skip_judge=True
        )
        assert result["status"] == "static_check_failed"

    def test_passes_with_skip_judge(self):
        data = {
            "technique_slug": "cma-es",
            "artifact_type": "overview",
            "title": "CMA-ES Overview",
            "summary": "A valid summary.",
            "markdown": "word " * 900,
            "use_cases": ["optimization"],
            "strengths": ["powerful"],
            "limitations": ["complex"],
            "comparisons": ["vs DE"],
        }
        result = evaluate_single_artifact(
            "cma-es", "overview", data, skip_judge=True
        )
        assert result["status"] == "passed"


class TestPromoteArtifact:
    def test_promotes_to_content_dir(self, tmp_path):
        from pipeline import evaluate

        original = evaluate.CONTENT_DIR
        evaluate.CONTENT_DIR = tmp_path

        data = {"key": "value"}
        path = promote_artifact("cma-es", "overview", data)

        assert path.exists()
        assert json.loads(path.read_text()) == data

        evaluate.CONTENT_DIR = original


class TestSaveMetrics:
    def test_saves_full_metrics_file(self, tmp_path):
        from pipeline import evaluate

        original_runs = evaluate.RUNS_DIR
        original_full = evaluate.EVALUATION_LATEST_FULL_PATH
        original_partial = evaluate.EVALUATION_LATEST_PARTIAL_PATH
        evaluate.RUNS_DIR = tmp_path / "runs"
        evaluate.EVALUATION_LATEST_FULL_PATH = tmp_path / "latest-full.json"
        evaluate.EVALUATION_LATEST_PARTIAL_PATH = tmp_path / "latest-partial.json"

        metrics = {
            "evaluated_at": "2026-03-22T12:00:00+00:00",
            "scope": {"type": "full"},
            "techniques": {"cma-es": {"artifacts": {}}},
        }
        paths = save_metrics(metrics)

        assert paths["run_path"].exists()
        assert paths["latest_path"].exists()
        assert paths["latest_path"] == evaluate.EVALUATION_LATEST_FULL_PATH
        assert json.loads(paths["latest_path"].read_text())["scope"]["type"] == "full"

        evaluate.RUNS_DIR = original_runs
        evaluate.EVALUATION_LATEST_FULL_PATH = original_full
        evaluate.EVALUATION_LATEST_PARTIAL_PATH = original_partial

    def test_saves_partial_metrics_file(self, tmp_path):
        from pipeline import evaluate

        original_runs = evaluate.RUNS_DIR
        original_full = evaluate.EVALUATION_LATEST_FULL_PATH
        original_partial = evaluate.EVALUATION_LATEST_PARTIAL_PATH
        evaluate.RUNS_DIR = tmp_path / "runs"
        evaluate.EVALUATION_LATEST_FULL_PATH = tmp_path / "latest-full.json"
        evaluate.EVALUATION_LATEST_PARTIAL_PATH = tmp_path / "latest-partial.json"

        metrics = {
            "evaluated_at": "2026-03-22T12:00:00+00:00",
            "scope": {"type": "partial"},
            "techniques": {"cma-es": {"artifacts": {}}},
        }
        paths = save_metrics(metrics)

        assert paths["latest_path"] == evaluate.EVALUATION_LATEST_PARTIAL_PATH
        assert json.loads(paths["latest_path"].read_text())["scope"]["type"] == "partial"

        evaluate.RUNS_DIR = original_runs
        evaluate.EVALUATION_LATEST_FULL_PATH = original_full
        evaluate.EVALUATION_LATEST_PARTIAL_PATH = original_partial


class TestEvaluateTechnique:
    @patch("pipeline.evaluate.save_evaluation_log")
    @patch("pipeline.evaluate.promote_artifact")
    @patch("pipeline.evaluate.evaluate_single_artifact")
    def test_evaluates_all_artifacts(
        self, mock_eval, mock_promote, mock_log
    ):
        mock_eval.return_value = {
            "status": "passed",
            "artifact": {"key": "val"},
            "stages": [],
            "attempts": 1,
            "duration_seconds": 0.5,
        }
        mock_log.return_value = Path("/tmp/log.json")

        artifacts = {
            "overview": {"technique_slug": "cma-es"},
            "math_deep_dive": {"technique_slug": "cma-es"},
        }
        result = evaluate_technique(
            "cma-es", ["overview", "math_deep_dive"], artifacts, skip_judge=True
        )

        assert result["overall_passed"] is True
        assert result["artifacts"]["overview"]["status"] == "passed"
        assert mock_promote.call_count == 2

    @patch("pipeline.evaluate.save_evaluation_log")
    @patch("pipeline.evaluate.evaluate_single_artifact")
    def test_missing_artifact_fails(self, mock_eval, mock_log):
        mock_log.return_value = Path("/tmp/log.json")

        result = evaluate_technique(
            "cma-es", ["overview"], {}, skip_judge=True
        )
        assert result["overall_passed"] is False
        assert result["artifacts"]["overview"]["status"] == "missing"
