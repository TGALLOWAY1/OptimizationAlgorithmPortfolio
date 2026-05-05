"""Repurposing Agent — derives channel-specific assets from the edited draft."""

from __future__ import annotations

import logging
from typing import Any

from pipeline.agents.base import AgentResult, ContentAgent, PipelineContext
from pipeline.content_pipeline.prompts import render_prompt

logger = logging.getLogger(__name__)


class RepurposingAgent(ContentAgent):
    id = "repurposing"
    name = "Repurposing Agent"
    description = (
        "Converts the edited long-form draft into LinkedIn, X thread, YouTube, "
        "short-form, newsletter, and README assets."
    )

    STAGE_ID = "repurposing"
    ARTIFACT_TYPE = "agent_repurposing"
    SCHEMA_KEY = "repurposed_assets"
    PROMPT_FILE = "repurposing"

    SYSTEM_PROMPT = (
        "You are a multi-channel content adapter. You produce asset variants "
        "that match each channel's voice and length conventions while "
        "preserving the source's technical accuracy. Respond with valid JSON only."
    )

    def run(
        self, stage_input: dict[str, Any], context: PipelineContext
    ) -> AgentResult:
        edited = context.previous_outputs.get("editor") or {}
        outline = context.previous_outputs.get("outline")
        brief = context.previous_outputs.get("intake")
        markdown = edited.get("markdown")
        if not markdown:
            return AgentResult(
                success=False,
                errors=("repurposing stage requires edited draft markdown in context",),
            )
        user_prompt = render_prompt(
            self.PROMPT_FILE,
            edited_markdown=markdown,
            brief_json=brief or {},
            outline_json=outline or {},
        )
        try:
            payload, metadata = self._call_llm(self.SYSTEM_PROMPT, user_prompt)
        except RuntimeError as exc:
            logger.warning("[run=%s stage=%s] LLM call failed: %s", context.run_id, self.STAGE_ID, exc)
            return AgentResult(success=False, errors=(str(exc),))
        return AgentResult(success=True, output=payload, metadata=metadata)
