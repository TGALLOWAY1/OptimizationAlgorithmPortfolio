"""Multi-provider LLM client with OpenAI, Gemini, and Nano Banana Pro support."""

import json
import logging
import os
import time
from abc import ABC, abstractmethod
from pathlib import Path

import jsonschema

try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:
    genai = None
    genai_types = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent / "config.json"


def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return json.load(f)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str, schema: dict) -> dict:
        """Generate structured JSON output matching the given schema."""


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider using the Responses API."""

    def __init__(self, model: str, api_key_env: str):
        api_key = os.environ.get(api_key_env)
        if not api_key:
            raise ValueError(f"Environment variable {api_key_env} is not set")
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate(self, system_prompt: str, user_prompt: str, schema: dict) -> dict:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
        text = response.choices[0].message.content
        return json.loads(text)


class GeminiProvider(LLMProvider):
    """Google Gemini provider with native JSON schema enforcement."""

    def __init__(self, model: str, api_key_env: str):
        api_key = os.environ.get(api_key_env)
        if not api_key:
            raise ValueError(f"Environment variable {api_key_env} is not set")
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def generate(self, system_prompt: str, user_prompt: str, schema: dict) -> dict:
        combined_prompt = f"{system_prompt}\n\n{user_prompt}"
        response = self.client.models.generate_content(
            model=self.model,
            contents=combined_prompt,
            config=genai_types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
            ),
        )
        return json.loads(response.text)


class NanoBananaProvider:
    """Generates infographic images via Nano Banana Pro (Gemini 3 Image)."""

    def __init__(self, model: str, api_key_env: str):
        api_key = os.environ.get(api_key_env)
        if not api_key:
            raise ValueError(f"Environment variable {api_key_env} is not set")
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def generate_image(self, prompt: str, output_path: str) -> str:
        """Call Nano Banana Pro to generate an infographic image.

        Returns the path to the saved PNG file.
        """
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                response_modalities=["IMAGE"],
            ),
        )
        # Extract image bytes from response
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                image_bytes = part.inline_data.data
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(image_bytes)
                return output_path
        raise RuntimeError("No image data in Nano Banana Pro response")


# --- Provider cache ---
_providers: dict[str, LLMProvider | NanoBananaProvider] = {}


def get_provider(
    artifact_type: str, override: str | None = None
) -> LLMProvider | NanoBananaProvider:
    """Return the correct provider for a given artifact type.

    Args:
        artifact_type: The artifact type (e.g., "overview", "infographic_image").
        override: Optional provider name override (e.g., "openai", "gemini").
    """
    config = load_config()
    if override:
        provider_name = override
    else:
        provider_name = config["artifact_provider_map"].get(artifact_type)
        if not provider_name:
            raise ValueError(f"No provider mapped for artifact type: {artifact_type}")

    if provider_name in _providers:
        return _providers[provider_name]

    provider_config = config["providers"].get(provider_name)
    if not provider_config:
        raise ValueError(f"Unknown provider: {provider_name}")

    if provider_name == "nano_banana":
        provider = NanoBananaProvider(
            model=provider_config["model"],
            api_key_env=provider_config["api_key_env"],
        )
    elif provider_name == "openai":
        provider = OpenAIProvider(
            model=provider_config["model"],
            api_key_env=provider_config["api_key_env"],
        )
    elif provider_name == "gemini":
        provider = GeminiProvider(
            model=provider_config["model"],
            api_key_env=provider_config["api_key_env"],
        )
    else:
        raise ValueError(f"Unknown provider: {provider_name}")

    _providers[provider_name] = provider
    return provider


def generate_with_retry(
    provider: LLMProvider,
    system_prompt: str,
    user_prompt: str,
    schema: dict,
    max_retries: int = 3,
) -> dict:
    """Generate content with retry logic for API and schema validation failures."""
    for attempt in range(1, max_retries + 1):
        try:
            result = provider.generate(system_prompt, user_prompt, schema)
            jsonschema.validate(instance=result, schema=schema)
            return result
        except jsonschema.ValidationError as e:
            logger.warning(
                "Schema validation failed (attempt %d/%d): %s",
                attempt,
                max_retries,
                e.message,
            )
        except Exception as e:
            logger.warning(
                "API call failed (attempt %d/%d): %s", attempt, max_retries, e
            )
        if attempt < max_retries:
            wait = 2**attempt
            logger.info("Retrying in %ds...", wait)
            time.sleep(wait)
    raise RuntimeError(f"Failed after {max_retries} attempts")


def generate_image_with_retry(
    provider: NanoBananaProvider,
    prompt: str,
    output_path: str,
    max_retries: int = 3,
) -> str:
    """Generate an image with retry logic."""
    for attempt in range(1, max_retries + 1):
        try:
            return provider.generate_image(prompt, output_path)
        except Exception as e:
            logger.warning(
                "Image generation failed (attempt %d/%d): %s",
                attempt,
                max_retries,
                e,
            )
        if attempt < max_retries:
            wait = 2**attempt
            logger.info("Retrying in %ds...", wait)
            time.sleep(wait)
    raise RuntimeError(f"Image generation failed after {max_retries} attempts")
