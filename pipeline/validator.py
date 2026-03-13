"""Content validation rules beyond JSON schema checks."""

import os
import re
from pathlib import Path


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
    if validator is None:
        return []
    return validator(data)
