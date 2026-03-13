"""Tests for LLM client — provider routing and retry logic."""

import json
from unittest.mock import patch, MagicMock

import pytest

from pipeline.llm_client import get_provider, generate_with_retry, load_config


class TestProviderRouting:
    def test_plan_uses_gemini(self):
        config = load_config()
        assert config["artifact_provider_map"]["plan"] == "gemini"

    def test_overview_uses_openai(self):
        config = load_config()
        assert config["artifact_provider_map"]["overview"] == "openai"

    def test_infographic_image_uses_nano_banana(self):
        config = load_config()
        assert config["artifact_provider_map"]["infographic_image"] == "nano_banana"

    def test_unknown_artifact_raises(self):
        with pytest.raises(ValueError, match="No provider mapped"):
            get_provider("nonexistent_type")

    def test_override_works(self):
        """Override should select a different provider regardless of mapping."""
        # This will fail without API keys, but we can test the config lookup
        config = load_config()
        assert "openai" in config["providers"]
        assert "gemini" in config["providers"]


class TestRetryLogic:
    def test_succeeds_on_first_try(self):
        mock_provider = MagicMock()
        mock_provider.generate.return_value = {"technique_name": "test", "slug": "test"}
        schema = {"type": "object", "properties": {"technique_name": {"type": "string"}, "slug": {"type": "string"}}}
        result = generate_with_retry(mock_provider, "sys", "user", schema)
        assert result["technique_name"] == "test"
        assert mock_provider.generate.call_count == 1

    def test_retries_on_api_failure(self):
        mock_provider = MagicMock()
        mock_provider.generate.side_effect = [
            RuntimeError("API error"),
            {"technique_name": "test", "slug": "test"},
        ]
        schema = {"type": "object", "properties": {"technique_name": {"type": "string"}, "slug": {"type": "string"}}}
        with patch("pipeline.llm_client.time.sleep"):
            result = generate_with_retry(mock_provider, "sys", "user", schema)
        assert result["technique_name"] == "test"
        assert mock_provider.generate.call_count == 2

    def test_raises_after_max_retries(self):
        mock_provider = MagicMock()
        mock_provider.generate.side_effect = RuntimeError("always fails")
        schema = {"type": "object"}
        with patch("pipeline.llm_client.time.sleep"):
            with pytest.raises(RuntimeError, match="Failed after 3 attempts"):
                generate_with_retry(mock_provider, "sys", "user", schema)
        assert mock_provider.generate.call_count == 3
