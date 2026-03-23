"""Tests for content validation rules."""

import os
import tempfile

from pipeline.validator import (
    validate_artifact,
    validate_infographic_image,
    validate_overview,
    validate_math_deep_dive,
    validate_implementation,
    validate_infographic_spec,
)


class TestOverviewValidator:
    def test_valid_overview(self):
        data = {
            "summary": "A good summary.",
            "markdown": "word " * 900,
        }
        assert validate_overview(data) == []

    def test_empty_summary(self):
        data = {"summary": "", "markdown": "word " * 900}
        errors = validate_overview(data)
        assert any("summary" in e.lower() for e in errors)

    def test_short_markdown(self):
        data = {"summary": "Fine", "markdown": "short"}
        errors = validate_overview(data)
        assert any("too short" in e.lower() for e in errors)


class TestMathDeepDiveValidator:
    def test_valid_math(self):
        data = {"markdown": "word " * 800 + " $x^2$ more words"}
        assert validate_math_deep_dive(data) == []

    def test_no_latex(self):
        data = {"markdown": "word " * 900}
        errors = validate_math_deep_dive(data)
        assert any("latex" in e.lower() for e in errors)


class TestImplementationValidator:
    def test_valid_implementation(self):
        data = {
            "markdown": "word " * 800 + " ```python\nprint()```",
            "pseudo_code": "FUNCTION optimize()\n  RETURN x",
            "python_examples": ["print('hello')"],
            "runtime_dependencies": ["math"],
        }
        assert validate_implementation(data) == []

    def test_no_pseudocode(self):
        data = {
            "markdown": "word " * 900,
            "pseudo_code": "no keywords here",
            "python_examples": ["print('hello')"],
            "runtime_dependencies": ["math"],
        }
        errors = validate_implementation(data)
        assert any("pseudocode" in e.lower() for e in errors)

    def test_runtime_dependencies_must_be_raw_imports(self):
        data = {
            "markdown": "word " * 900,
            "pseudo_code": "FUNCTION optimize()\n  RETURN x",
            "python_examples": ["print('hello')"],
            "runtime_dependencies": ["scipy.optimize - optimization toolkit"],
        }
        errors = validate_implementation(data)
        assert any("raw import name" in e.lower() for e in errors)


class TestInfographicSpecValidator:
    def test_valid_spec(self):
        data = {"panels": [{"title": "Panel 1"}], "layout": "vertical"}
        assert validate_infographic_spec(data) == []

    def test_no_panels(self):
        data = {"panels": [], "layout": "vertical"}
        errors = validate_infographic_spec(data)
        assert any("panels" in e.lower() for e in errors)


class TestInfographicImageValidator:
    def test_missing_image(self):
        errors = validate_infographic_image("/nonexistent/path.png")
        assert any("not found" in e.lower() for e in errors)

    def test_small_image(self):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(b"tiny")
            f.flush()
            errors = validate_infographic_image(f.name)
            assert any("too small" in e.lower() for e in errors)
            os.unlink(f.name)


class TestValidateArtifact:
    def test_unknown_type_returns_empty(self):
        assert validate_artifact("unknown_type", {}) == []
