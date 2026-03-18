"""LLM judge for evaluating and improving artifacts using rubric-based scoring."""

import json
import logging
from pathlib import Path
from typing import Any

from pipeline.llm_client import generate_with_retry, get_provider

logger = logging.getLogger(__name__)

RUBRICS_PATH = Path("content/rubrics.json")
REFERENCE_DIR = Path("content/reference")

# JSON Schema for judge output
JUDGE_OUTPUT_SCHEMA = {
    "type": "object",
    "required": [
        "passed",
        "overall_score",
        "criteria_scores",
        "critiques",
        "revision_instructions",
    ],
    "properties": {
        "passed": {"type": "boolean"},
        "overall_score": {"type": "integer", "minimum": 1, "maximum": 10},
        "criteria_scores": {
            "type": "object",
            "properties": {
                "factual_accuracy": {"type": "integer", "minimum": 1, "maximum": 10},
                "math_correctness": {"type": "integer", "minimum": 1, "maximum": 10},
                "clarity": {"type": "integer", "minimum": 1, "maximum": 10},
                "code_quality": {"type": "integer", "minimum": 1, "maximum": 10},
            },
        },
        "critiques": {
            "type": "array",
            "items": {"type": "string"},
        },
        "revision_instructions": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "additionalProperties": False,
}

DEFAULT_PASS_THRESHOLD = 7


def load_rubrics() -> dict[str, Any]:
    """Load evaluation rubrics from content/rubrics.json."""
    if not RUBRICS_PATH.exists():
        logger.warning("Rubrics file not found at %s, using defaults", RUBRICS_PATH)
        return _default_rubrics()
    return json.loads(RUBRICS_PATH.read_text())


def _default_rubrics() -> dict[str, Any]:
    """Return default rubrics when rubrics.json is not available."""
    return {
        "pass_threshold": DEFAULT_PASS_THRESHOLD,
        "criteria": {
            "factual_accuracy": {
                "weight": 0.3,
                "description": "Are all factual claims accurate and verifiable?",
            },
            "math_correctness": {
                "weight": 0.3,
                "description": "Are mathematical expressions, derivations, and notation correct?",
            },
            "clarity": {
                "weight": 0.25,
                "description": "Is the content clear, well-organized, and pedagogically effective?",
            },
            "code_quality": {
                "weight": 0.15,
                "description": "Is the code correct, readable, and well-documented?",
            },
        },
    }


def load_reference(technique_slug: str) -> dict[str, Any] | None:
    """Load canonical reference facts for a technique."""
    ref_path = REFERENCE_DIR / f"{technique_slug}.json"
    if not ref_path.exists():
        logger.warning("No reference file found for %s", technique_slug)
        return None
    return json.loads(ref_path.read_text())


def _build_judge_prompt(
    artifact_type: str,
    artifact_data: dict[str, Any],
    rubrics: dict[str, Any],
    reference: dict[str, Any] | None,
) -> tuple[str, str]:
    """Build system and user prompts for the judge LLM.

    Returns:
        Tuple of (system_prompt, user_prompt).
    """
    system_prompt = (
        "You are a strict educational content evaluator. "
        "Evaluate the provided artifact against the rubric criteria and reference facts. "
        "Score each criterion from 1-10. Set passed=true only if overall_score >= "
        f"{rubrics.get('pass_threshold', DEFAULT_PASS_THRESHOLD)}. "
        "Provide specific critiques and actionable revision instructions. "
        "Respond with valid JSON only."
    )

    criteria_desc = "\n".join(
        f"- {name}: {info['description']}"
        for name, info in rubrics.get("criteria", {}).items()
    )

    reference_section = ""
    if reference:
        key_facts = "\n".join(f"- {f}" for f in reference.get("key_facts", []))
        forbidden = "\n".join(f"- {f}" for f in reference.get("forbidden_claims", []))
        reference_section = (
            f"\n\n## Canonical Reference Facts\n{key_facts}"
            f"\n\n## Forbidden Claims (must NOT appear)\n{forbidden}"
        )

    user_prompt = (
        f"## Artifact Type: {artifact_type}\n\n"
        f"## Evaluation Criteria\n{criteria_desc}\n"
        f"## Pass Threshold: {rubrics.get('pass_threshold', DEFAULT_PASS_THRESHOLD)}/10\n"
        f"{reference_section}\n\n"
        f"## Artifact Content\n```json\n{json.dumps(artifact_data, indent=2)[:8000]}\n```\n\n"
        "Evaluate this artifact. Respond with JSON matching the judge output schema."
    )

    return system_prompt, user_prompt


def evaluate_artifact(
    technique_slug: str,
    artifact_type: str,
    artifact_data: dict[str, Any],
    provider_override=None,
) -> dict[str, Any]:
    """Evaluate an artifact using the LLM judge.

    Args:
        technique_slug: The technique identifier.
        artifact_type: The artifact type being evaluated.
        artifact_data: The artifact content to evaluate.
        provider_override: Optional provider name override.

    Returns:
        Judge output dict with passed, overall_score, criteria_scores,
        critiques, and revision_instructions.
    """
    rubrics = load_rubrics()
    reference = load_reference(technique_slug)

    system_prompt, user_prompt = _build_judge_prompt(
        artifact_type, artifact_data, rubrics, reference
    )

    provider = get_provider("judge", override=provider_override)
    try:
        result = generate_with_retry(
            provider, system_prompt, user_prompt, JUDGE_OUTPUT_SCHEMA
        )
        return result
    except Exception as e:
        logger.error("Judge evaluation failed for %s/%s: %s", technique_slug, artifact_type, e)
        return {
            "passed": False,
            "overall_score": 0,
            "criteria_scores": {},
            "critiques": [f"Judge evaluation failed: {e}"],
            "revision_instructions": [],
        }


def build_revision_prompt(
    artifact_type: str,
    artifact_data: dict[str, Any],
    judge_result: dict[str, Any],
) -> tuple[str, str]:
    """Build prompts to revise an artifact based on judge feedback.

    Args:
        artifact_type: The artifact type.
        artifact_data: The current artifact content.
        judge_result: The judge's evaluation output.

    Returns:
        Tuple of (system_prompt, user_prompt) for revision.
    """
    system_prompt = (
        "You are an expert in optimization algorithms. "
        "Revise the provided artifact based on the improvement instructions. "
        "Maintain the same JSON structure. Respond with valid JSON only."
    )

    critiques = "\n".join(f"- {c}" for c in judge_result.get("critiques", []))
    instructions = "\n".join(
        f"- {i}" for i in judge_result.get("revision_instructions", [])
    )

    user_prompt = (
        f"## Artifact Type: {artifact_type}\n\n"
        f"## Current Score: {judge_result.get('overall_score', 0)}/10\n\n"
        f"## Critiques\n{critiques}\n\n"
        f"## Revision Instructions\n{instructions}\n\n"
        f"## Current Artifact\n```json\n{json.dumps(artifact_data, indent=2)[:8000]}\n```\n\n"
        "Revise this artifact to address all critiques and instructions. "
        "Return the complete revised artifact as JSON."
    )

    return system_prompt, user_prompt
