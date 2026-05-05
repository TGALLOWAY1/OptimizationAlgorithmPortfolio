"""Technical Reviewer Agent — produces a structured review report on the draft."""

from __future__ import annotations

import logging
from typing import Any

from pipeline.agents.base import AgentResult, ContentAgent, PipelineContext
from pipeline.content_pipeline.prompts import render_prompt

logger = logging.getLogger(__name__)


class TechnicalReviewerAgent(ContentAgent):
    id = "technical_review"
    name = "Technical Reviewer Agent"
    description = (
        "Reviews the draft for technical accuracy, missing steps, vague claims, "
        "and unsupported assumptions."
    )

    STAGE_ID = "technical_review"
    ARTIFACT_TYPE = "agent_technical_review"
    SCHEMA_KEY = "review_report"
    PROMPT_FILE = "technical_review"

    SYSTEM_PROMPT = (
        "You are a careful senior engineer reviewing a technical draft. You "
        "find problems and label their severity precisely. You do not rewrite "
        "the prose. Respond with valid JSON only."
    )

    def run(
        self, stage_input: dict[str, Any], context: PipelineContext
    ) -> AgentResult:
        draft = context.previous_outputs.get("draft") or {}
        brief = context.previous_outputs.get("intake")
        research = context.previous_outputs.get("research") or {}
        markdown = draft.get("markdown")
        if not markdown:
            return AgentResult(
                success=False,
                errors=("technical_review stage requires a draft markdown in context",),
            )
        user_prompt = render_prompt(
            self.PROMPT_FILE,
            draft_markdown=markdown,
            brief_json=brief or {},
            research_json=research,
        )
        try:
            payload, metadata = self._call_llm(self.SYSTEM_PROMPT, user_prompt)
        except RuntimeError as exc:
            logger.warning("[run=%s stage=%s] LLM call failed: %s", context.run_id, self.STAGE_ID, exc)
            return AgentResult(success=False, errors=(str(exc),))
        return AgentResult(success=True, output=payload, metadata=metadata)
