"""Drafting Agent — produces the first full draft from outline + brief + research."""

from __future__ import annotations

import logging
from typing import Any

from pipeline.agents.base import AgentResult, ContentAgent, PipelineContext
from pipeline.content_pipeline.prompts import render_prompt

logger = logging.getLogger(__name__)


class DraftingAgent(ContentAgent):
    id = "draft"
    name = "Drafting Agent"
    description = "Generates the first full Markdown draft from the outline."

    STAGE_ID = "draft"
    ARTIFACT_TYPE = "agent_draft"
    SCHEMA_KEY = "draft"
    PROMPT_FILE = "draft"

    SYSTEM_PROMPT = (
        "You are a senior technical writer. You produce a clear first draft "
        "that follows the supplied outline exactly, matches the audience and "
        "depth in the brief, and avoids placeholder text. Respond with valid JSON only."
    )

    def run(
        self, stage_input: dict[str, Any], context: PipelineContext
    ) -> AgentResult:
        brief = context.previous_outputs.get("intake")
        outline = context.previous_outputs.get("outline")
        research = context.previous_outputs.get("research")
        if not (brief and outline):
            return AgentResult(
                success=False,
                errors=("draft stage requires intake and outline outputs in context",),
            )
        user_prompt = render_prompt(
            self.PROMPT_FILE,
            brief_json=brief,
            outline_json=outline,
            research_json=research or {},
            gate_feedback="\n".join(f"- {f}" for f in context.gate_feedback),
        )
        try:
            payload, metadata = self._call_llm(self.SYSTEM_PROMPT, user_prompt)
        except RuntimeError as exc:
            logger.warning("[run=%s stage=%s] LLM call failed: %s", context.run_id, self.STAGE_ID, exc)
            return AgentResult(success=False, errors=(str(exc),))
        return AgentResult(success=True, output=payload, metadata=metadata)
