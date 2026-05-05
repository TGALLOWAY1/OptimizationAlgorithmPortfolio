"""Research Agent — surfaces claims, assumptions, and open questions."""

from __future__ import annotations

import logging
from typing import Any

from pipeline.agents.base import AgentResult, ContentAgent, PipelineContext
from pipeline.content_pipeline.prompts import render_prompt

logger = logging.getLogger(__name__)


class ResearchAgent(ContentAgent):
    id = "research"
    name = "Research Agent"
    description = (
        "Extracts research questions, supporting points, assumptions, and open "
        "questions. Marks claims that need external verification."
    )

    STAGE_ID = "research"
    ARTIFACT_TYPE = "agent_research"
    SCHEMA_KEY = "research_notes"
    PROMPT_FILE = "research"

    SYSTEM_PROMPT = (
        "You are a careful technical researcher. You list the claims a piece "
        "would need to support, mark which ones require external verification, "
        "and surface assumptions the draft will rest on. Respond with valid JSON only."
    )

    def run(
        self, stage_input: dict[str, Any], context: PipelineContext
    ) -> AgentResult:
        brief = context.previous_outputs.get("intake")
        if not brief:
            return AgentResult(
                success=False,
                errors=("research stage requires an intake output in context",),
            )
        user_prompt = render_prompt(
            self.PROMPT_FILE,
            brief_json=brief,
            gate_feedback="\n".join(f"- {f}" for f in context.gate_feedback),
        )
        try:
            payload, metadata = self._call_llm(self.SYSTEM_PROMPT, user_prompt)
        except RuntimeError as exc:
            logger.warning("[run=%s stage=%s] LLM call failed: %s", context.run_id, self.STAGE_ID, exc)
            return AgentResult(success=False, errors=(str(exc),))
        return AgentResult(success=True, output=payload, metadata=metadata)
