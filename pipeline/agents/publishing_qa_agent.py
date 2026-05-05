"""Publishing QA Agent — final quality gate before content is shipped."""

from __future__ import annotations

import logging
from typing import Any

from pipeline.agents.base import AgentResult, ContentAgent, PipelineContext
from pipeline.content_pipeline.prompts import render_prompt

logger = logging.getLogger(__name__)


class PublishingQAAgent(ContentAgent):
    id = "publishing_qa"
    name = "Publishing QA Agent"
    description = (
        "Reviews the edited long-form draft and the repurposed assets together "
        "and reports whether the package is publishable."
    )

    STAGE_ID = "publishing_qa"
    ARTIFACT_TYPE = "agent_publishing_qa"
    SCHEMA_KEY = "publishing_qa"
    PROMPT_FILE = "publishing_qa"

    SYSTEM_PROMPT = (
        "You are the final quality gate before publishing. You produce a "
        "structured findings list with severities, a 0-100 QA score, and a "
        "publishable boolean. Respond with valid JSON only."
    )

    def run(
        self, stage_input: dict[str, Any], context: PipelineContext
    ) -> AgentResult:
        edited = context.previous_outputs.get("editor") or {}
        repurposed = context.previous_outputs.get("repurposing") or {}
        outline = context.previous_outputs.get("outline")
        brief = context.previous_outputs.get("intake")
        markdown = edited.get("markdown")
        if not markdown:
            return AgentResult(
                success=False,
                errors=("publishing_qa stage requires edited draft markdown in context",),
            )
        user_prompt = render_prompt(
            self.PROMPT_FILE,
            edited_markdown=markdown,
            repurposed_json=repurposed,
            brief_json=brief or {},
            outline_json=outline or {},
        )
        try:
            payload, metadata = self._call_llm(self.SYSTEM_PROMPT, user_prompt)
        except RuntimeError as exc:
            logger.warning("[run=%s stage=%s] LLM call failed: %s", context.run_id, self.STAGE_ID, exc)
            return AgentResult(success=False, errors=(str(exc),))
        return AgentResult(success=True, output=payload, metadata=metadata)
