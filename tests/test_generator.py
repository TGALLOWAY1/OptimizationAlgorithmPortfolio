"""Tests for the generator module — slugify and idempotency."""

import json
from unittest.mock import patch, MagicMock

from pipeline.generator import ARTIFACT_VERSION, slugify


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
        """Plan generation should skip only when the manifest hash matches."""
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
        prompt_text = generator._load_prompt(generator.PROMPT_MAP["plan"])
        input_hash = generator._compute_input_hash(
            "plan",
            prompt_text=prompt_text,
            schema=generator.SCHEMAS["plan"],
            config_slice=generator._config_slice("plan"),
            material_inputs={"technique_name": "Test Technique", "slug": "test-technique"},
        )
        (slug_dir / "manifest.json").write_text(json.dumps({
            "artifact_version": ARTIFACT_VERSION,
            "artifacts": {
                "plan": {
                    "file": "plan.json",
                    "input_hash": input_hash,
                }
            },
        }))

        result = generator.generate_plan("Test Technique", force=False)
        # Provider should NOT have been called
        mock_get_provider.assert_not_called()
        assert result.payload == plan_data
        assert result.status == "skipped"

        generator.CONTENT_DIR = original

    @patch("pipeline.generator.get_provider")
    @patch("pipeline.generator.generate_with_retry")
    def test_plan_regenerates_when_manifest_missing(
        self,
        mock_generate_with_retry,
        mock_get_provider,
        tmp_path,
    ):
        """Existing artifacts should regenerate when no manifest metadata exists."""
        from pipeline import generator

        original = generator.CONTENT_DIR
        generator.CONTENT_DIR = tmp_path

        slug_dir = tmp_path / "test-technique"
        slug_dir.mkdir()
        (slug_dir / "plan.json").write_text(json.dumps({"stale": True}))

        provider = MagicMock()
        mock_get_provider.return_value = provider
        fresh_plan = {
            "technique_name": "Test Technique",
            "slug": "test-technique",
            "aliases": ["T"],
            "problem_type": "test",
            "notation_conventions": ["x"],
            "assumptions": ["a"],
            "target_audience": "testers",
            "artifacts_required": ["overview"],
        }
        mock_generate_with_retry.return_value = fresh_plan

        result = generator.generate_plan("Test Technique", force=False)

        assert result.status == "generated"
        assert result.payload == fresh_plan
        assert json.loads((slug_dir / "manifest.json").read_text())["artifacts"]["plan"]["file"] == "plan.json"

        generator.CONTENT_DIR = original
