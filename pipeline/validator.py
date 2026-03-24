"""Content validation rules beyond JSON schema checks."""

import json
import os
import re
from pathlib import Path
from typing import Any, Iterator

OFF_TOPIC_HINTS = {
    "technical co-founder",
    "startup",
    "venture capital",
    "go-to-market",
    "seed round",
    "product roadmap",
    "customer acquisition",
}

# Default hints for the original optimization algorithms topic.
# Additional hints can be added via the "technique_hints" key in config.json.
_DEFAULT_TECHNIQUE_HINTS: dict[str, set[str]] = {
    "bayesian-optimization": {"bayesian optimization", "gaussian process", "acquisition function", "surrogate model"},
    "genetic-algorithm": {"genetic algorithm", "population", "mutation", "crossover"},
    "simulated-annealing": {"simulated annealing", "temperature", "cooling schedule", "metropolis"},
    "particle-swarm-optimization": {"particle swarm optimization", "particle", "velocity", "personal best", "global best"},
    "gradient-descent": {"gradient descent", "gradient", "learning rate", "step size"},
    "nelder-mead-simplex": {"nelder-mead", "simplex", "reflection", "expansion", "contraction"},
    "cma-es": {"cma-es", "covariance matrix adaptation", "evolution strategy", "covariance matrix"},
    "differential-evolution": {"differential evolution", "mutation factor", "trial vector", "crossover rate"},
}

_DEFAULT_DISALLOWED_TERMS: dict[str, set[str]] = {
    "gradient-descent": {"bfgs", "l-bfgs"},
}


def _load_technique_hints() -> dict[str, set[str]]:
    """Load technique hints from config.json, merging with defaults."""
    hints = dict(_DEFAULT_TECHNIQUE_HINTS)
    config_path = Path(__file__).parent / "config.json"
    try:
        config = json.loads(config_path.read_text())
        for slug, terms in config.get("technique_hints", {}).items():
            hints[slug] = set(terms)
    except (json.JSONDecodeError, OSError):
        pass
    return hints


def _load_disallowed_terms() -> dict[str, set[str]]:
    """Load disallowed terms from config.json, merging with defaults."""
    terms = dict(_DEFAULT_DISALLOWED_TERMS)
    config_path = Path(__file__).parent / "config.json"
    try:
        config = json.loads(config_path.read_text())
        for slug, bad_terms in config.get("implementation_disallowed_terms", {}).items():
            terms[slug] = set(bad_terms)
    except (json.JSONDecodeError, OSError):
        pass
    return terms


TECHNIQUE_HINTS = _load_technique_hints()
IMPLEMENTATION_DISALLOWED_TERMS = _load_disallowed_terms()


def iter_string_fields(value: Any, path: str = "") -> Iterator[tuple[str, str]]:
    """Yield every string field from a nested dict/list payload."""
    if isinstance(value, str):
        yield path or "root", value
        return
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            yield from iter_string_fields(child, child_path)
        return
    if isinstance(value, list):
        for index, child in enumerate(value):
            child_path = f"{path}[{index}]" if path else f"[{index}]"
            yield from iter_string_fields(child, child_path)


def _has_leading_heading(markdown: str) -> bool:
    return bool(re.match(r"^\s*#{1,2}\s+\S+", markdown))


def _common_technique_errors(artifact_type: str, data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    markdown = data.get("markdown", "")
    if artifact_type in {"overview", "math_deep_dive", "implementation"} and _has_leading_heading(markdown):
        errors.append("Markdown should not start with a redundant heading")

    technique_slug = data.get("technique_slug", "")
    if not technique_slug:
        return errors

    technique_terms = TECHNIQUE_HINTS.get(
        technique_slug,
        {technique_slug.replace("-", " ")},
    )

    for field_path, text in iter_string_fields(data):
        lower_text = text.lower()
        if len(lower_text) >= 80 and any(hint in lower_text for hint in OFF_TOPIC_HINTS):
            if not any(term in lower_text for term in technique_terms):
                errors.append(
                    f"Field '{field_path}' appears off-topic for {technique_slug}"
                )

    if artifact_type == "implementation":
        implementation_text = " ".join(
            [
                markdown,
                data.get("pseudo_code", ""),
                *data.get("python_examples", []),
                *[variation.get("code", "") for variation in data.get("code_variations", [])],
            ]
        ).lower()
        if not any(term in implementation_text for term in technique_terms):
            errors.append(
                f"Implementation content does not clearly reference {technique_slug}"
            )
        for bad_term in IMPLEMENTATION_DISALLOWED_TERMS.get(technique_slug, set()):
            if bad_term in implementation_text:
                errors.append(
                    f"Implementation content appears to rely on '{bad_term}', which does not match {technique_slug}"
                )

    return errors


def validate_overview(data: dict) -> list[str]:
    errors = []
    if not data.get("summary", "").strip():
        errors.append("Overview summary is empty")
    markdown = data.get("markdown", "")
    word_count = len(markdown.split())
    if word_count < 800:
        errors.append(f"Overview markdown too short: {word_count} words (min 800)")
    return errors


def validate_math_deep_dive(data: dict) -> list[str]:
    errors = []
    markdown = data.get("markdown", "")
    word_count = len(markdown.split())
    if word_count < 800:
        errors.append(
            f"Math deep dive markdown too short: {word_count} words (min 800)"
        )
    if "$" not in markdown and "\\(" not in markdown:
        errors.append("Math deep dive markdown contains no LaTeX delimiters")
    return errors


def validate_implementation(data: dict) -> list[str]:
    errors = []
    markdown = data.get("markdown", "")
    pseudo_code = data.get("pseudo_code", "")
    word_count = len(markdown.split())
    if word_count < 800:
        errors.append(
            f"Implementation markdown too short: {word_count} words (min 800)"
        )
    pseudocode_keywords = ["FUNCTION", "FOR", "WHILE", "IF", "RETURN"]
    has_pseudocode = any(kw in pseudo_code.upper() for kw in pseudocode_keywords) or any(
        kw in markdown.upper() for kw in pseudocode_keywords
    )
    if not has_pseudocode:
        errors.append("Implementation lacks pseudocode keywords")
    python_examples = data.get("python_examples", [])
    has_python = bool(python_examples) or "```python" in markdown
    if not has_python:
        errors.append("Implementation lacks Python code examples")
    runtime_dependencies = data.get("runtime_dependencies")
    if runtime_dependencies is None:
        errors.append("Implementation is missing runtime_dependencies")
    elif not isinstance(runtime_dependencies, list):
        errors.append("Implementation runtime_dependencies must be a list")
    else:
        for dep in runtime_dependencies:
            if not isinstance(dep, str) or not dep.strip():
                errors.append("Implementation runtime_dependencies must contain non-empty strings")
                continue
            if re.search(r"\s|-", dep):
                errors.append(
                    f"Runtime dependency '{dep}' must be a raw import name without spaces or descriptions"
                )
    return errors


def validate_infographic_spec(data: dict) -> list[str]:
    errors = []
    if not data.get("panels"):
        errors.append("Infographic spec has no panels")
    if not data.get("layout", "").strip():
        errors.append("Infographic spec has no layout")
    return errors


def validate_infographic_image(image_path: str) -> list[str]:
    errors = []
    if not os.path.exists(image_path):
        errors.append(f"Infographic image not found: {image_path}")
        return errors
    size = os.path.getsize(image_path)
    if size < 10240:  # 10KB minimum
        errors.append(
            f"Infographic image too small ({size} bytes), may be blank or corrupt"
        )
    return errors


VALIDATORS = {
    "overview": validate_overview,
    "math_deep_dive": validate_math_deep_dive,
    "implementation": validate_implementation,
    "infographic_spec": validate_infographic_spec,
}


def validate_artifact(artifact_type: str, data: dict) -> list[str]:
    """Run content validation for a given artifact type.

    Returns a list of error strings (empty if valid).
    """
    validator = VALIDATORS.get(artifact_type)
    errors = validator(data) if validator is not None else []
    errors.extend(_common_technique_errors(artifact_type, data))
    return errors
