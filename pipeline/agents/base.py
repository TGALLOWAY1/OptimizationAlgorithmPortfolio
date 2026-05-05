"""Shared types and base class for content-pipeline agents."""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pipeline.llm_client import generate_with_retry, get_provider
from pipeline.schemas import SCHEMAS

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AgentMetadata:
    """Lightweight per-call telemetry returned alongside an :class:`AgentResult`."""

    model: str | None = None
    duration_ms: int = 0
    retry_count: int = 0


@dataclass(frozen=True)
class AgentResult:
    """Outcome of a single agent invocation.

    Payloads are plain dicts validated by jsonschema, matching the rest of the
    repo. A failed result still carries :attr:`metadata` when available so the
    run record can show where time was spent.
    """

    success: bool
    output: dict[str, Any] | None = None
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    metadata: AgentMetadata | None = None


@dataclass
class PipelineContext:
    """Mutable execution context passed to every agent."""

    run_id: str
    output_dir: Path
    input: dict[str, Any]
    previous_outputs: dict[str, dict[str, Any]] = field(default_factory=dict)
    gate_feedback: list[str] = field(default_factory=list)


class ContentAgent(ABC):
    """Base class every content-pipeline agent inherits from.

    Concrete agents declare four class-level metadata attributes — ``STAGE_ID``,
    ``ARTIFACT_TYPE`` (the key in ``config.json``'s ``artifact_provider_map``),
    ``SCHEMA_KEY`` (the key in ``schemas.SCHEMAS``), and ``PROMPT_FILE`` (the
    template name under ``pipeline/prompts/content_pipeline/``) — and implement
    :meth:`run`. The :meth:`_call_llm` helper wires the standard provider call
    with retry and schema validation.
    """

    id: str
    name: str
    description: str

    STAGE_ID: str
    ARTIFACT_TYPE: str
    SCHEMA_KEY: str
    PROMPT_FILE: str

    @abstractmethod
    def run(
        self, stage_input: dict[str, Any], context: PipelineContext
    ) -> AgentResult:  # pragma: no cover - abstract
        """Execute the agent and return an :class:`AgentResult`."""

    def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> tuple[dict[str, Any], AgentMetadata]:
        """Invoke the configured provider with retry + schema validation."""
        provider = get_provider(self.ARTIFACT_TYPE)
        schema = SCHEMAS[self.SCHEMA_KEY]
        start = time.monotonic()
        try:
            payload = generate_with_retry(provider, system_prompt, user_prompt, schema)
        finally:
            duration_ms = int((time.monotonic() - start) * 1000)
        metadata = AgentMetadata(
            model=getattr(provider, "model", None),
            duration_ms=duration_ms,
        )
        return payload, metadata
