"""Tests for the schema validation stage."""

from pipeline.schema_validate import validate_schema


class TestValidateSchema:
    def test_valid_plan_passes(self):
        data = {
            "technique_name": "CMA-ES",
            "slug": "cma-es",
            "aliases": ["CMA-ES"],
            "problem_type": "continuous",
            "notation_conventions": ["x"],
            "assumptions": ["differentiable"],
            "target_audience": "researchers",
            "artifacts_required": ["overview"],
        }
        result = validate_schema("plan", data)
        assert result["passed"] is True
        assert result["errors"] == []

    def test_missing_required_field_fails(self):
        data = {
            "slug": "cma-es",
            "aliases": ["CMA-ES"],
        }
        result = validate_schema("plan", data)
        assert result["passed"] is False
        assert len(result["errors"]) > 0

    def test_unknown_artifact_type_fails(self):
        result = validate_schema("nonexistent_type", {"key": "value"})
        assert result["passed"] is False
        assert any("No schema" in e for e in result["errors"])

    def test_valid_overview_passes(self):
        data = {
            "technique_slug": "gradient-descent",
            "artifact_type": "overview",
            "title": "Gradient Descent",
            "summary": "An optimization method.",
            "markdown": "x " * 800,
            "use_cases": ["training"],
            "strengths": ["simple"],
            "limitations": ["slow"],
            "comparisons": ["vs SGD"],
        }
        result = validate_schema("overview", data)
        assert result["passed"] is True

    def test_short_markdown_fails(self):
        data = {
            "technique_slug": "gradient-descent",
            "artifact_type": "overview",
            "title": "GD",
            "summary": "Short.",
            "markdown": "too short",
            "use_cases": ["x"],
            "strengths": ["x"],
            "limitations": ["x"],
            "comparisons": ["x"],
        }
        result = validate_schema("overview", data)
        assert result["passed"] is False

    def test_extra_fields_fail(self):
        data = {
            "technique_name": "CMA-ES",
            "slug": "cma-es",
            "aliases": ["CMA-ES"],
            "problem_type": "continuous",
            "notation_conventions": ["x"],
            "assumptions": ["a"],
            "target_audience": "researchers",
            "artifacts_required": ["overview"],
            "extra_field": "not allowed",
        }
        result = validate_schema("plan", data)
        assert result["passed"] is False
