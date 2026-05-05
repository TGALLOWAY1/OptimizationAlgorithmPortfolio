"""Intake Agent — parses raw user input into a normalized ContentBrief."""

from __future__ import annotations

import logging
from typing import Any

from pipeline.agents.base import AgentResult, ContentAgent, PipelineContext
from pipeline.content_pipeline.prompts import render_prompt

logger = logging.getLogger(__name__)


class IntakeAgent(ContentAgent):
    id = "intake"
    name = "Intake Agent"
    description = "Parses raw input into a normalized ContentBrief."

    STAGE_ID = "intake"
    ARTIFACT_TYPE = "agent_intake"
    SCHEMA_KEY = "content_brief"
    PROMPT_FILE = "intake"

    SYSTEM_PROMPT = (
        "You are a senior technical-content strategist. You read raw inputs "
        "(ideas, transcripts, notes, drafts) and extract a normalized brief. "
        "Respond with valid JSON only."
    )

    def run(
        self, stage_input: dict[str, Any], context: PipelineContext
    ) -> AgentResult:
        raw_input = stage_input.get("raw_input", "").strip()
        if not raw_input:
            return AgentResult(
                success=False,
                errors=("intake stage requires non-empty raw_input",),
            )
        user_prompt = render_prompt(
            self.PROMPT_FILE,
            raw_input=raw_input,
            audience_hint=stage_input.get("audience_hint", ""),
            content_type_hint=stage_input.get("content_type_hint", ""),
            gate_feedback="\n".join(f"- {f}" for f in context.gate_feedback),
        )
        try:
            payload, metadata = self._call_llm(self.SYSTEM_PROMPT, user_prompt)
        except RuntimeError as exc:
            logger.warning("[run=%s stage=%s] LLM call failed: %s", context.run_id, self.STAGE_ID, exc)
            return AgentResult(success=False, errors=(str(exc),))
        return AgentResult(success=True, output=payload, metadata=metadata)
