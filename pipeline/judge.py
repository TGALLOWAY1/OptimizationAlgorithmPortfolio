"""LLM judge for evaluating and improving artifacts using rubric-based scoring."""

import json
import logging
import re
from typing import Any

import jsonschema

from pipeline.judge_tools import dispatch_tool, tool_declarations
from pipeline.llm_client import generate_with_retry, get_provider
from pipeline.paths import REFERENCE_DIR, RUBRICS_PATH

logger = logging.getLogger(__name__)

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


def _build_tool_using_judge_prompt(
    technique_slug: str,
    artifact_type: str,
    artifact_data: dict[str, Any],
    rubrics: dict[str, Any],
) -> tuple[str, str]:
    """Build prompts for the tool-using judge.

    The reference data is fetched on demand via the ``lookup_reference`` tool
    rather than embedded inline, which saves tokens and forces the judge to
    actively ground its claims.
    """
    threshold = rubrics.get("pass_threshold", DEFAULT_PASS_THRESHOLD)
    criteria_desc = "\n".join(
        f"- {name}: {info['description']}"
        for name, info in rubrics.get("criteria", {}).items()
    )
    schema_hint = json.dumps(JUDGE_OUTPUT_SCHEMA, indent=2)

    system_prompt = (
        "You are a strict educational content evaluator with access to "
        "verification tools. Before scoring, use the tools to:\n"
        f"  1. Call lookup_reference('{technique_slug}') to fetch canonical "
        "facts and forbidden claims for this technique.\n"
        "  2. For implementation artifacts, call run_python_code on the "
        "python_examples to confirm they execute without errors.\n"
        "  3. For implementation artifacts, call verify_imports on the "
        "runtime_dependencies to detect hallucinated imports.\n"
        "  4. For math-heavy artifacts, call check_equation on questionable "
        "LaTeX expressions to catch malformed equations.\n\n"
        "Once you have enough evidence, score each rubric criterion from "
        f"1-10. Set passed=true only if overall_score >= {threshold}. "
        "Provide specific critiques and actionable revision instructions.\n\n"
        "Final answer MUST be a single JSON object matching this schema "
        "(no markdown fences, no commentary):\n"
        f"{schema_hint}"
    )

    user_prompt = (
        f"## Technique: {technique_slug}\n"
        f"## Artifact Type: {artifact_type}\n\n"
        f"## Evaluation Criteria\n{criteria_desc}\n"
        f"## Pass Threshold: {threshold}/10\n\n"
        f"## Artifact Content\n```json\n{json.dumps(artifact_data, indent=2)[:8000]}\n```\n\n"
        "Use the available tools to verify the artifact, then return your "
        "final evaluation as JSON."
    )

    return system_prompt, user_prompt


def _parse_judge_json(text: str) -> dict[str, Any] | None:
    """Best-effort extraction of the judge's final JSON object from raw text."""
    if not text:
        return None
    candidates: list[str] = [text.strip()]

    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    if fenced:
        candidates.append(fenced.group(1))

    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace > first_brace:
        candidates.append(text[first_brace : last_brace + 1])

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def _judge_failure_payload(
    reason: str, tool_calls: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    """Standard shape for a failed judge run so callers can rely on it."""
    return {
        "passed": False,
        "overall_score": 0,
        "criteria_scores": {},
        "critiques": [reason],
        "revision_instructions": [],
        "tool_calls": tool_calls or [],
    }


def evaluate_artifact(
    technique_slug: str,
    artifact_type: str,
    artifact_data: dict[str, Any],
    provider_override=None,
    use_tools: bool = True,
    max_tool_iterations: int = 5,
) -> dict[str, Any]:
    """Evaluate an artifact using the LLM judge.

    Args:
        technique_slug: The technique identifier.
        artifact_type: The artifact type being evaluated.
        artifact_data: The artifact content to evaluate.
        provider_override: Optional provider name override.
        use_tools: When True, run the judge as a tool-using agent that can
            execute code, verify imports, check LaTeX, and look up canonical
            references before scoring. When False, fall back to the legacy
            one-shot path that embeds the reference inline.
        max_tool_iterations: Maximum tool-use turns before the judge must
            commit to a final score.

    Returns:
        Judge output dict with passed, overall_score, criteria_scores,
        critiques, revision_instructions, and (when ``use_tools`` is True)
        ``tool_calls`` documenting each tool invocation.
    """
    rubrics = load_rubrics()
    provider = get_provider("judge", override=provider_override)

    if use_tools and hasattr(provider, "generate_with_tools"):
        system_prompt, user_prompt = _build_tool_using_judge_prompt(
            technique_slug, artifact_type, artifact_data, rubrics
        )
        try:
            loop_result = provider.generate_with_tools(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                tools=tool_declarations(),
                dispatch=dispatch_tool,
                max_iterations=max_tool_iterations,
            )
        except Exception as e:
            logger.error(
                "Tool-using judge failed for %s/%s: %s",
                technique_slug,
                artifact_type,
                e,
            )
            return _judge_failure_payload(f"Tool-using judge raised: {e}")

        parsed = _parse_judge_json(loop_result.get("text", ""))
        tool_calls = loop_result.get("tool_calls", [])
        if parsed is None:
            return _judge_failure_payload(
                "Judge did not return valid JSON after tool use",
                tool_calls=tool_calls,
            )
        try:
            jsonschema.validate(instance=parsed, schema=JUDGE_OUTPUT_SCHEMA)
        except jsonschema.ValidationError as e:
            return _judge_failure_payload(
                f"Judge JSON failed schema validation: {e.message}",
                tool_calls=tool_calls,
            )
        parsed["tool_calls"] = tool_calls
        parsed["iterations"] = loop_result.get("iterations", 1)
        return parsed

    # Legacy one-shot path (no tools)
    reference = load_reference(technique_slug)
    system_prompt, user_prompt = _build_judge_prompt(
        artifact_type, artifact_data, rubrics, reference
    )
    try:
        result = generate_with_retry(
            provider, system_prompt, user_prompt, JUDGE_OUTPUT_SCHEMA
        )
        result.setdefault("tool_calls", [])
        return result
    except Exception as e:
        logger.error(
            "Judge evaluation failed for %s/%s: %s",
            technique_slug,
            artifact_type,
            e,
        )
        return _judge_failure_payload(f"Judge evaluation failed: {e}")


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
