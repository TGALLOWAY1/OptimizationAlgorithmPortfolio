"""Tests for the generator module — slugify and idempotency."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from pipeline.generator import slugify


class TestSlugify:
    def test_basic(self):
        assert slugify("Bayesian Optimization") == "bayesian-optimization"

    def test_special_chars(self):
        assert slugify("CMA-ES") == "cma-es"

    def test_extra_spaces(self):
        assert slugify("  Gradient  Descent  ") == "gradient-descent"

    def test_mixed_case(self):
        assert slugify("Nelder-Mead Simplex") == "nelder-mead-simplex"


class TestIdempotency:
    @patch("pipeline.generator.get_provider")
    def test_plan_skips_if_exists(self, mock_get_provider, tmp_path):
        """Plan generation should skip when plan.json already exists."""
        from pipeline import generator

        # Temporarily override CONTENT_DIR
        original = generator.CONTENT_DIR
        generator.CONTENT_DIR = tmp_path

        slug_dir = tmp_path / "test-technique"
        slug_dir.mkdir()
        plan_data = {
            "technique_name": "Test",
            "slug": "test-technique",
            "aliases": ["T"],
            "problem_type": "test",
            "notation_conventions": ["x"],
            "assumptions": ["a"],
            "target_audience": "testers",
            "artifacts_required": ["overview"],
        }
        (slug_dir / "plan.json").write_text(json.dumps(plan_data))

        result = generator.generate_plan("Test Technique", force=False)
        # Provider should NOT have been called
        mock_get_provider.assert_not_called()
        assert result == plan_data

        generator.CONTENT_DIR = original
