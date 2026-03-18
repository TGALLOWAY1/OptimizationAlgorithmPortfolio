"""Artifact retry logic — revision loop with max attempts."""

import json
import logging
from typing import Any

from pipeline.judge import build_revision_prompt, evaluate_artifact
from pipeline.llm_client import generate_with_retry, get_provider
from pipeline.schema_validate import validate_schema
from pipeline.schemas import SCHEMAS

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3


def revise_artifact(
    technique_slug: str,
    artifact_type: str,
    artifact_data: dict[str, Any],
    judge_result: dict[str, Any],
    provider_override=None,
) -> dict[str, Any]:
    """Revise an artifact based on judge feedback.

    Args:
        technique_slug: The technique identifier.
        artifact_type: The artifact type.
        artifact_data: The current artifact content.
        judge_result: The judge evaluation output with revision instructions.
        provider_override: Optional provider name override.

    Returns:
        The revised artifact data.
    """
    system_prompt, user_prompt = build_revision_prompt(
        artifact_type, artifact_data, judge_result
    )

    provider = get_provider(artifact_type, override=provider_override)
    schema = SCHEMAS.get(artifact_type)
    if schema is None:
        raise ValueError(f"No schema for artifact type: {artifact_type}")

    return generate_with_retry(provider, system_prompt, user_prompt, schema)


def retry_loop(
    technique_slug: str,
    artifact_type: str,
    artifact_data: dict[str, Any],
    max_attempts: int = MAX_ATTEMPTS,
    provider_override=None,
) -> dict[str, Any]:
    """Run the evaluation-revision loop for an artifact.

    Attempts up to max_attempts total (initial + revisions).

    Args:
        technique_slug: The technique identifier.
        artifact_type: The artifact type.
        artifact_data: The initial artifact data.
        max_attempts: Maximum total attempts (default 3).
        provider_override: Optional provider name override.

    Returns:
        Dict with keys:
            artifact: The final artifact data.
            status: "passed" | "persistent_failure"
            attempts: Number of attempts made.
            judge_history: List of judge results per attempt.
    """
    current_data = artifact_data
    judge_history: list[dict[str, Any]] = []

    for attempt in range(1, max_attempts + 1):
        logger.info(
            "Evaluation attempt %d/%d for %s/%s",
            attempt,
            max_attempts,
            technique_slug,
            artifact_type,
        )

        # Schema validation first
        schema_result = validate_schema(artifact_type, current_data)
        if not schema_result["passed"]:
            logger.warning(
                "Schema validation failed on attempt %d: %s",
                attempt,
                schema_result["errors"],
            )
            judge_history.append({
                "attempt": attempt,
                "stage": "schema_invalid",
                "errors": schema_result["errors"],
            })
            if attempt < max_attempts:
                # Try to regenerate via revision
                judge_result = {
                    "overall_score": 0,
                    "critiques": [f"Schema validation failed: {e}" for e in schema_result["errors"]],
                    "revision_instructions": ["Fix the JSON structure to match the required schema."],
                }
                try:
                    current_data = revise_artifact(
                        technique_slug, artifact_type, current_data,
                        judge_result, provider_override,
                    )
                except Exception as e:
                    logger.error("Revision failed on attempt %d: %s", attempt, e)
                continue
            break

        # LLM judge evaluation
        judge_result = evaluate_artifact(
            technique_slug, artifact_type, current_data, provider_override
        )
        judge_history.append({
            "attempt": attempt,
            "stage": "judge",
            "result": judge_result,
        })

        if judge_result.get("passed", False):
            logger.info(
                "Artifact %s/%s passed evaluation on attempt %d with score %d/10",
                technique_slug,
                artifact_type,
                attempt,
                judge_result.get("overall_score", 0),
            )
            return {
                "artifact": current_data,
                "status": "passed",
                "attempts": attempt,
                "judge_history": judge_history,
            }

        logger.info(
            "Artifact %s/%s failed evaluation on attempt %d (score: %d/10)",
            technique_slug,
            artifact_type,
            attempt,
            judge_result.get("overall_score", 0),
        )

        # Revise if we have attempts remaining
        if attempt < max_attempts:
            try:
                current_data = revise_artifact(
                    technique_slug, artifact_type, current_data,
                    judge_result, provider_override,
                )
            except Exception as e:
                logger.error("Revision failed on attempt %d: %s", attempt, e)
                judge_history.append({
                    "attempt": attempt,
                    "stage": "revision_failed",
                    "error": str(e),
                })

    return {
        "artifact": current_data,
        "status": "persistent_failure",
        "attempts": max_attempts,
        "judge_history": judge_history,
    }
