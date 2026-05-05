"""Editor Agent — improves clarity and resolves reviewer feedback in the draft."""

from __future__ import annotations

import logging
from typing import Any

from pipeline.agents.base import AgentResult, ContentAgent, PipelineContext
from pipeline.content_pipeline.prompts import render_prompt

logger = logging.getLogger(__name__)


class EditorAgent(ContentAgent):
    id = "editor"
    name = "Editor Agent"
    description = (
        "Improves clarity, structure, and concision while preserving technical "
        "meaning and resolving reviewer feedback."
    )

    STAGE_ID = "editor"
    ARTIFACT_TYPE = "agent_editor"
    SCHEMA_KEY = "edited_draft"
    PROMPT_FILE = "editor"

    SYSTEM_PROMPT = (
        "You are a meticulous editor who tightens technical prose without "
        "altering its meaning. You resolve reviewer issues and report the "
        "edits you made. Respond with valid JSON only."
    )

    def run(
        self, stage_input: dict[str, Any], context: PipelineContext
    ) -> AgentResult:
        draft = context.previous_outputs.get("draft") or {}
        review = context.previous_outputs.get("technical_review") or {}
        brief = context.previous_outputs.get("intake")
        markdown = draft.get("markdown")
        if not markdown:
            return AgentResult(
                success=False,
                errors=("editor stage requires a draft markdown in context",),
            )
        user_prompt = render_prompt(
            self.PROMPT_FILE,
            draft_markdown=markdown,
            review_json=review,
            brief_json=brief or {},
        )
        try:
            payload, metadata = self._call_llm(self.SYSTEM_PROMPT, user_prompt)
        except RuntimeError as exc:
            logger.warning("[run=%s stage=%s] LLM call failed: %s", context.run_id, self.STAGE_ID, exc)
            return AgentResult(success=False, errors=(str(exc),))
        return AgentResult(success=True, output=payload, metadata=metadata)
