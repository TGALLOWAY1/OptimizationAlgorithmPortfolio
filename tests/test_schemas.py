"""Tests for JSON schema validation."""

import pytest
import jsonschema

from pipeline.schemas import SCHEMAS


def _make_valid_plan():
    return {
        "technique_name": "Gradient Descent",
        "slug": "gradient-descent",
        "aliases": ["GD", "Steepest Descent"],
        "problem_type": "continuous optimization",
        "notation_conventions": ["f(x) for objective function"],
        "assumptions": ["differentiable objective"],
        "target_audience": "graduate CS students",
        "artifacts_required": ["overview", "math_deep_dive"],
    }


def _make_valid_overview():
    return {
        "technique_slug": "gradient-descent",
        "artifact_type": "overview",
        "title": "Gradient Descent Overview",
        "summary": "A fundamental optimization method.",
        "markdown": "x " * 800,  # 800 words
        "use_cases": ["neural network training"],
        "strengths": ["simple to implement"],
        "limitations": ["slow convergence"],
        "comparisons": ["faster than random search"],
    }


class TestPlanSchema:
    def test_valid_plan_passes(self):
        jsonschema.validate(_make_valid_plan(), SCHEMAS["plan"])

    def test_missing_required_field_fails(self):
        plan = _make_valid_plan()
        del plan["technique_name"]
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(plan, SCHEMAS["plan"])

    def test_empty_aliases_fails(self):
        plan = _make_valid_plan()
        plan["aliases"] = []
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(plan, SCHEMAS["plan"])

    def test_extra_field_fails(self):
        plan = _make_valid_plan()
        plan["extra"] = "not allowed"
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(plan, SCHEMAS["plan"])


class TestOverviewSchema:
    def test_valid_overview_passes(self):
        jsonschema.validate(_make_valid_overview(), SCHEMAS["overview"])

    def test_short_markdown_fails(self):
        overview = _make_valid_overview()
        overview["markdown"] = "too short"
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(overview, SCHEMAS["overview"])

    def test_wrong_artifact_type_fails(self):
        overview = _make_valid_overview()
        overview["artifact_type"] = "wrong"
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(overview, SCHEMAS["overview"])
