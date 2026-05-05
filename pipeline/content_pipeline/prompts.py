"""Prompt-template helper for the multi-agent content pipeline.

Mirrors the ``{{var}}`` substitution style used by ``pipeline.generator``.
"""

from __future__ import annotations

import json
from typing import Any

from pipeline.paths import PROMPTS_DIR

CONTENT_PROMPTS_DIR = PROMPTS_DIR / "content_pipeline"


def _stringify(value: Any) -> str:
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    return json.dumps(value, indent=2, sort_keys=False, ensure_ascii=False)


def render_prompt(template_name: str, **variables: Any) -> str:
    """Load ``content_pipeline/<template_name>.md`` and substitute ``{{var}}`` placeholders.

    Missing variables resolve to an empty string so optional placeholders
    (e.g. ``gate_feedback`` on the first attempt) do not require callers to
    pass them explicitly.
    """
    template_path = CONTENT_PROMPTS_DIR / f"{template_name}.md"
    template = template_path.read_text()
    rendered = template
    for key, value in variables.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", _stringify(value))
    # Wipe any unfilled placeholders rather than leaking literal ``{{x}}`` to the model.
    while "{{" in rendered and "}}" in rendered:
        start = rendered.index("{{")
        end = rendered.index("}}", start) + 2
        rendered = rendered[:start] + rendered[end:]
    return rendered
