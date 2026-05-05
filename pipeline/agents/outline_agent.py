"""Outline Agent — turns the brief and research notes into a structured outline."""

from __future__ import annotations

import logging
from typing import Any

from pipeline.agents.base import AgentResult, ContentAgent, PipelineContext
from pipeline.content_pipeline.prompts import render_prompt

logger = logging.getLogger(__name__)


class OutlineAgent(ContentAgent):
    id = "outline"
    name = "Outline Agent"
    description = "Converts a brief and research notes into a structured outline."

    STAGE_ID = "outline"
    ARTIFACT_TYPE = "agent_outline"
    SCHEMA_KEY = "content_outline"
    PROMPT_FILE = "outline"

    SYSTEM_PROMPT = (
        "You are an experienced editor who builds outlines for technical content. "
        "You produce ordered, audience-appropriate outlines with explicit section "
        "purposes and key points. Respond with valid JSON only."
    )

    def run(
        self, stage_input: dict[str, Any], context: PipelineContext
    ) -> AgentResult:
        brief = context.previous_outputs.get("intake")
        research = context.previous_outputs.get("research")
        if not brief:
            return AgentResult(
                success=False,
                errors=("outline stage requires an intake output in context",),
            )
        if not research:
            return AgentResult(
                success=False,
                errors=("outline stage requires a research output in context",),
            )
        user_prompt = render_prompt(
            self.PROMPT_FILE,
            brief_json=brief,
            research_json=research,
            gate_feedback="\n".join(f"- {f}" for f in context.gate_feedback),
        )
        try:
            payload, metadata = self._call_llm(self.SYSTEM_PROMPT, user_prompt)
        except RuntimeError as exc:
            logger.warning("[run=%s stage=%s] LLM call failed: %s", context.run_id, self.STAGE_ID, exc)
            return AgentResult(success=False, errors=(str(exc),))
        return AgentResult(success=True, output=payload, metadata=metadata)
