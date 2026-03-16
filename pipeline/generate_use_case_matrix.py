"""Generate the use case matrix via Gemini and save to content/use_case_matrix.json."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline.llm_client import get_provider, generate_with_retry

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

CONTENT_DIR = Path(__file__).resolve().parents[1] / "content"
PROMPTS_DIR = Path(__file__).parent / "prompts"

USE_CASE_MATRIX_SCHEMA = {
    "type": "object",
    "required": ["title", "description", "problem_spaces", "matrix"],
    "properties": {
        "title": {"type": "string", "minLength": 1},
        "description": {"type": "string", "minLength": 1},
        "problem_spaces": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "label", "description"],
                "properties": {
                    "id": {"type": "string"},
                    "label": {"type": "string"},
                    "description": {"type": "string"},
                },
            },
            "minItems": 1,
        },
        "matrix": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "additionalProperties": {
                    "type": "string",
                    "enum": ["ideal", "suitable", "unsuitable"],
                },
            },
        },
    },
}


def main(force: bool = False) -> dict:
    """Generate use case matrix and save to content/use_case_matrix.json."""
    output_path = CONTENT_DIR / "use_case_matrix.json"
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)

    if output_path.exists() and not force:
        logger.info("Use case matrix already exists, skipping (use --force to regenerate)")
        return json.loads(output_path.read_text())

    prompt_path = PROMPTS_DIR / "use_case_matrix_prompt.md"
    prompt = prompt_path.read_text()

    system_prompt = (
        "You are an expert in optimization algorithms. "
        "Respond with valid JSON only, no markdown fences or extra text."
    )

    provider = get_provider("overview")  # Use gemini via overview mapping
    result = generate_with_retry(
        provider, system_prompt, prompt, USE_CASE_MATRIX_SCHEMA
    )

    output_path.write_text(json.dumps(result, indent=2))
    logger.info("Saved use case matrix to %s", output_path)
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Regenerate even if exists")
    args = parser.parse_args()
    main(force=args.force)
