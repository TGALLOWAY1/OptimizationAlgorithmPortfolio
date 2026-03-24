"""Generate the use case matrix via Gemini and save it under generated outputs."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline.llm_client import get_provider, generate_with_retry, load_config, load_topic
from pipeline.paths import PROMPTS_DIR, USE_CASE_MATRIX_PATH
from pipeline.runtime import ensure_supported_python

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

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
    """Generate use case matrix and save to the generated artifact root."""
    output_path = USE_CASE_MATRIX_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists() and not force:
        logger.info("Use case matrix already exists, skipping (use --force to regenerate)")
        return json.loads(output_path.read_text())

    topic = load_topic()
    config = load_config()
    techniques = config["techniques"]
    technique_list = "\n".join(f"- {t}" for t in techniques)

    prompt_path = PROMPTS_DIR / "use_case_matrix_prompt.md"
    prompt = (
        prompt_path.read_text()
        .replace("{{topic_name}}", topic["name"])
        .replace("{{domain}}", topic["domain"])
        .replace("{{technique_list}}", technique_list)
    )

    system_prompt = (
        f"You are an expert in {topic['domain']}. "
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
    ensure_supported_python()
    main(force=args.force)
