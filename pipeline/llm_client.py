"""Multi-provider LLM client with Gemini and Nano Banana Pro support."""

from __future__ import annotations

import json
import logging
import os
import time
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

import jsonschema

# Load .env from project root so API keys are available
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:
    genai = None
    genai_types = None

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent / "config.json"


def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return json.load(f)


def load_topic() -> dict:
    """Load the topic profile from config, with sensible defaults."""
    config = load_config()
    defaults = {
        "name": "Algorithm Portfolio",
        "domain": "algorithms",
        "expert_role": "algorithm expert",
        "curriculum_role": "curriculum designer",
    }
    return {**defaults, **config.get("topic", {})}


def _schema_for_gemini(schema: dict) -> dict:
    """Remove Gemini-unsupported schema fields (e.g. additionalProperties)."""
    result = {}
    for k, v in schema.items():
        if k == "additionalProperties":
            continue
        if isinstance(v, dict):
            result[k] = _schema_for_gemini(v)
        elif isinstance(v, list):
            result[k] = [
                _schema_for_gemini(x) if isinstance(x, dict) else x for x in v
            ]
        else:
            result[k] = v
    return result


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str, schema: dict) -> dict:
        """Generate structured JSON output matching the given schema."""

    def generate_stream(self, system_prompt: str, user_prompt: str) -> Iterator[str]:
        """Yield response tokens as they arrive. Override for streaming support."""
        result = self.generate(system_prompt, user_prompt, schema={})
        yield json.dumps(result)


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
        gemini_schema = _schema_for_gemini(schema)
        response = self.client.models.generate_content(
            model=self.model,
            contents=combined_prompt,
            config=genai_types.GenerateContentConfig(
                response_mime_type="application/json",
                response_json_schema=gemini_schema,
            ),
        )
        return json.loads(response.text)

    def generate_stream(self, system_prompt: str, user_prompt: str) -> Iterator[str]:
        """Stream response tokens from Gemini."""
        combined_prompt = f"{system_prompt}\n\n{user_prompt}"
        response = self.client.models.generate_content_stream(
            model=self.model,
            contents=combined_prompt,
        )
        for chunk in response:
            if chunk.text:
                yield chunk.text

    def generate_with_tools(
        self,
        system_prompt: str,
        user_prompt: str,
        tools: list[dict],
        dispatch: Callable[[str, dict], dict],
        max_iterations: int = 5,
    ) -> dict:
        """Run a tool-use loop and return the final text plus the tool-call history.

        The loop sends the system+user prompts to Gemini with the supplied tool
        declarations. On each turn the model can either return text (the final
        answer) or one or more ``function_call`` parts. Function calls are
        dispatched via ``dispatch(name, args)``; the return value is sent back
        to the model as a ``function_response`` and the loop continues.

        Returns a dict with ``text`` (final model output as a string),
        ``tool_calls`` (list of {name, args, result}), and ``iterations``.
        """
        function_decls = [
            genai_types.FunctionDeclaration(
                name=tool["name"],
                description=tool["description"],
                parameters=tool["parameters"],
            )
            for tool in tools
        ]
        gemini_tool = genai_types.Tool(function_declarations=function_decls)
        config = genai_types.GenerateContentConfig(
            system_instruction=system_prompt,
            tools=[gemini_tool],
        )

        contents: list[Any] = [
            genai_types.Content(
                role="user",
                parts=[genai_types.Part.from_text(text=user_prompt)],
            )
        ]
        tool_calls: list[dict] = []
        final_text = ""

        for iteration in range(1, max_iterations + 1):
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=config,
            )
            candidate = response.candidates[0]
            parts = list(candidate.content.parts or [])

            fn_calls = [p for p in parts if getattr(p, "function_call", None)]
            text_parts = [p.text for p in parts if getattr(p, "text", None)]

            if not fn_calls:
                final_text = "".join(text_parts).strip()
                return {
                    "text": final_text,
                    "tool_calls": tool_calls,
                    "iterations": iteration,
                }

            contents.append(candidate.content)

            response_parts = []
            for part in fn_calls:
                fn_call = part.function_call
                args = dict(fn_call.args) if fn_call.args else {}
                result = dispatch(fn_call.name, args)
                tool_calls.append({
                    "name": fn_call.name,
                    "args": args,
                    "result": result,
                    "iteration": iteration,
                })
                response_parts.append(
                    genai_types.Part.from_function_response(
                        name=fn_call.name,
                        response=result,
                    )
                )
            contents.append(
                genai_types.Content(role="user", parts=response_parts)
            )

        logger.warning(
            "Tool-use loop hit max_iterations=%d without a final answer",
            max_iterations,
        )
        return {
            "text": final_text,
            "tool_calls": tool_calls,
            "iterations": max_iterations,
            "max_iterations_reached": True,
        }


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
    artifact_type: str, override=None
) -> LLMProvider | NanoBananaProvider:
    """Return the correct provider for a given artifact type.

    Args:
        artifact_type: The artifact type (e.g., "overview", "infographic_image").
        override: Optional provider name override (e.g., "gemini").
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
    elif provider_name.startswith("gemini"):
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
