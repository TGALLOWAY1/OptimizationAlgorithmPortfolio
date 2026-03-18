"""Main evaluation orchestrator — validates, judges, and promotes artifacts."""

import json
import logging
import re
import time
from pathlib import Path
from typing import Any

from pipeline.code_runner import validate_code_artifact
from pipeline.judge import evaluate_artifact
from pipeline.retry_loop import retry_loop
from pipeline.schema_validate import validate_schema
from pipeline.validator import validate_artifact as run_static_checks

logger = logging.getLogger(__name__)

CANDIDATES_DIR = Path("build/generated_candidates")
VALIDATED_DIR = Path("build/validated_artifacts")
CONTENT_DIR = Path("content/techniques")
METRICS_PATH = Path("content/evaluation_metrics.json")
LOG_DIR = Path("build/logs/evaluation")

# Artifact types that contain executable Python code
CODE_ARTIFACT_TYPES = {"implementation"}

# Placeholder patterns that indicate incomplete content
PLACEHOLDER_PATTERNS = [
    re.compile(r"\bTODO\b", re.IGNORECASE),
    re.compile(r"\bTBD\b", re.IGNORECASE),
    re.compile(r"\bFIXME\b", re.IGNORECASE),
    re.compile(r"\bXXX\b"),
    re.compile(r"\[INSERT\b", re.IGNORECASE),
    re.compile(r"\bPLACEHOLDER\b", re.IGNORECASE),
]


def run_deterministic_checks(artifact_type: str, data: dict[str, Any]) -> dict[str, Any]:
    """Run deterministic static checks on an artifact.

    Checks include:
        - Placeholder detection (TODO, TBD, FIXME)
        - LaTeX delimiter balance (for math-heavy artifacts)
        - Content validation rules from validator.py
        - Duplicated paragraphs
        - Mismatched algorithm names

    Args:
        artifact_type: The artifact type.
        data: The artifact content.

    Returns:
        Dict with passed (bool) and errors (list[str]).
    """
    errors: list[str] = []

    # Check for placeholders in all string fields
    for key, value in data.items():
        if isinstance(value, str):
            for pattern in PLACEHOLDER_PATTERNS:
                if pattern.search(value):
                    errors.append(
                        f"Placeholder detected in field '{key}': "
                        f"matched pattern '{pattern.pattern}'"
                    )

    # LaTeX delimiter balance check for math-heavy artifacts
    if artifact_type in ("math_deep_dive", "overview", "implementation"):
        markdown = data.get("markdown", "")
        _check_latex_balance(markdown, errors)

    # Duplicated paragraph check
    markdown = data.get("markdown", "")
    if markdown:
        _check_duplicated_paragraphs(markdown, errors)

    # Run existing content validators
    static_errors = run_static_checks(artifact_type, data)
    errors.extend(static_errors)

    return {"passed": len(errors) == 0, "errors": errors}


def _check_latex_balance(text: str, errors: list[str]) -> None:
    """Check that LaTeX delimiters are balanced."""
    # Check inline math $...$  (ignore $$...$$)
    # Count single $ that aren't part of $$
    single_dollar_count = 0
    i = 0
    while i < len(text):
        if text[i] == "$":
            if i + 1 < len(text) and text[i + 1] == "$":
                # This is a $$ delimiter, find closing $$
                i += 2
                while i < len(text) - 1:
                    if text[i] == "$" and text[i + 1] == "$":
                        i += 2
                        break
                    i += 1
                else:
                    errors.append("Unbalanced display math delimiter ($$)")
                continue
            single_dollar_count += 1
        i += 1

    if single_dollar_count % 2 != 0:
        errors.append("Unbalanced inline math delimiter ($)")

    # Check \( ... \) balance
    open_paren = text.count("\\(")
    close_paren = text.count("\\)")
    if open_paren != close_paren:
        errors.append(
            f"Unbalanced LaTeX parenthesis delimiters: "
            f"{open_paren} opening vs {close_paren} closing"
        )


def _check_duplicated_paragraphs(text: str, errors: list[str]) -> None:
    """Check for duplicated paragraphs in markdown text."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    # Only flag paragraphs with meaningful content (>50 chars)
    meaningful = [p for p in paragraphs if len(p) > 50]
    seen: set[str] = set()
    for para in meaningful:
        if para in seen:
            errors.append(
                f"Duplicated paragraph detected: '{para[:80]}...'"
            )
        seen.add(para)


def evaluate_single_artifact(
    technique_slug: str,
    artifact_type: str,
    artifact_data: dict[str, Any],
    provider_override=None,
    skip_judge: bool = False,
) -> dict[str, Any]:
    """Run the full evaluation pipeline on a single artifact.

    Stages:
        1. Schema validation
        2. Deterministic static checks
        3. Code execution (for implementation artifacts)
        4. LLM judge evaluation + retry loop

    Args:
        technique_slug: The technique identifier.
        artifact_type: The artifact type.
        artifact_data: The artifact content.
        provider_override: Optional provider override for the judge.
        skip_judge: If True, skip the LLM judge stage.

    Returns:
        Dict with status, artifact, stages (list of stage results), attempts.
    """
    start_time = time.time()
    stages: list[dict[str, Any]] = []

    # Stage 1: Schema validation
    schema_result = validate_schema(artifact_type, artifact_data)
    stages.append({"stage": "schema_validation", **schema_result})
    if not schema_result["passed"]:
        return _build_result(
            "schema_invalid", artifact_data, stages, 1, start_time
        )

    # Stage 2: Deterministic static checks
    static_result = run_deterministic_checks(artifact_type, artifact_data)
    stages.append({"stage": "static_checks", **static_result})
    if not static_result["passed"]:
        return _build_result(
            "static_check_failed", artifact_data, stages, 1, start_time
        )

    # Stage 3: Code execution (implementation artifacts only)
    if artifact_type in CODE_ARTIFACT_TYPES:
        code_result = validate_code_artifact(artifact_data)
        stages.append({"stage": "code_validation", **code_result})
        if not code_result["passed"]:
            return _build_result(
                "code_runtime_error", artifact_data, stages, 1, start_time
            )

    # Stage 4: LLM judge evaluation with retry loop
    if not skip_judge:
        loop_result = retry_loop(
            technique_slug, artifact_type, artifact_data,
            provider_override=provider_override,
        )
        stages.append({
            "stage": "judge_evaluation",
            "status": loop_result["status"],
            "attempts": loop_result["attempts"],
            "judge_history": loop_result["judge_history"],
        })

        return _build_result(
            loop_result["status"],
            loop_result["artifact"],
            stages,
            loop_result["attempts"],
            start_time,
        )

    return _build_result("passed", artifact_data, stages, 1, start_time)


def _build_result(
    status: str,
    artifact: dict[str, Any],
    stages: list[dict[str, Any]],
    attempts: int,
    start_time: float,
) -> dict[str, Any]:
    """Build a standardized evaluation result."""
    return {
        "status": status,
        "artifact": artifact,
        "stages": stages,
        "attempts": attempts,
        "duration_seconds": round(time.time() - start_time, 2),
    }


def promote_artifact(
    technique_slug: str,
    artifact_type: str,
    artifact_data: dict[str, Any],
) -> Path:
    """Promote a validated artifact to the content directory.

    Args:
        technique_slug: The technique identifier.
        artifact_type: The artifact type.
        artifact_data: The validated artifact content.

    Returns:
        Path to the promoted artifact file.
    """
    out_dir = CONTENT_DIR / technique_slug
    out_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = out_dir / f"{artifact_type}.json"
    artifact_path.write_text(json.dumps(artifact_data, indent=2))
    logger.info("Promoted %s/%s to %s", technique_slug, artifact_type, artifact_path)
    return artifact_path


def save_metrics(metrics: dict[str, Any]) -> Path:
    """Save evaluation metrics to content/evaluation_metrics.json."""
    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2))
    logger.info("Saved evaluation metrics to %s", METRICS_PATH)
    return METRICS_PATH


def save_evaluation_log(
    technique_slug: str,
    artifact_type: str,
    result: dict[str, Any],
) -> Path:
    """Save detailed evaluation log for a single artifact."""
    log_dir = LOG_DIR / technique_slug
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{artifact_type}.json"
    log_path.write_text(json.dumps(result, indent=2))
    return log_path


def evaluate_technique(
    technique_slug: str,
    artifact_types: list[str],
    artifacts: dict[str, dict[str, Any]],
    provider_override=None,
    skip_judge: bool = False,
) -> dict[str, Any]:
    """Evaluate all artifacts for a single technique.

    Args:
        technique_slug: The technique identifier.
        artifact_types: List of artifact types to evaluate.
        artifacts: Dict mapping artifact_type -> artifact_data.
        provider_override: Optional provider override.
        skip_judge: If True, skip the LLM judge stage.

    Returns:
        Dict with per-artifact evaluation results and overall status.
    """
    results: dict[str, Any] = {}
    all_passed = True

    for artifact_type in artifact_types:
        artifact_data = artifacts.get(artifact_type)
        if artifact_data is None:
            logger.warning(
                "No artifact data for %s/%s, skipping",
                technique_slug,
                artifact_type,
            )
            results[artifact_type] = {"status": "missing", "attempts": 0}
            all_passed = False
            continue

        result = evaluate_single_artifact(
            technique_slug,
            artifact_type,
            artifact_data,
            provider_override=provider_override,
            skip_judge=skip_judge,
        )
        results[artifact_type] = {
            "status": result["status"],
            "attempts": result["attempts"],
            "duration_seconds": result["duration_seconds"],
        }

        # Save detailed log
        save_evaluation_log(technique_slug, artifact_type, result)

        if result["status"] == "passed":
            promote_artifact(technique_slug, artifact_type, result["artifact"])
        else:
            all_passed = False
            logger.warning(
                "Artifact %s/%s failed evaluation: %s",
                technique_slug,
                artifact_type,
                result["status"],
            )

    return {
        "technique_slug": technique_slug,
        "overall_passed": all_passed,
        "artifacts": results,
    }
