"""Content-pipeline agents and the default registry that wires them together."""

from __future__ import annotations

from pipeline.agents.base import (
    AgentMetadata,
    AgentResult,
    ContentAgent,
    PipelineContext,
)
from pipeline.agents.drafting_agent import DraftingAgent
from pipeline.agents.editor_agent import EditorAgent
from pipeline.agents.intake_agent import IntakeAgent
from pipeline.agents.outline_agent import OutlineAgent
from pipeline.agents.publishing_qa_agent import PublishingQAAgent
from pipeline.agents.repurposing_agent import RepurposingAgent
from pipeline.agents.research_agent import ResearchAgent
from pipeline.agents.technical_reviewer_agent import TechnicalReviewerAgent

__all__ = [
    "AgentMetadata",
    "AgentResult",
    "ContentAgent",
    "DraftingAgent",
    "EditorAgent",
    "IntakeAgent",
    "OutlineAgent",
    "PipelineContext",
    "PublishingQAAgent",
    "RepurposingAgent",
    "ResearchAgent",
    "TechnicalReviewerAgent",
    "build_default_registry",
]


def build_default_registry():
    """Return the production :class:`AgentRegistry` with all 8 stages wired up.

    Imported lazily to avoid a circular import: ``pipeline.content_pipeline.registry``
    depends on agent and gate types defined in this package.
    """
    from pipeline.content_pipeline.quality_gates import (
        DraftGate,
        FinalQAGate,
        IntakeGate,
        OutlineGate,
        TechnicalReviewGate,
    )
    from pipeline.content_pipeline.registry import AgentRegistry, StageDefinition

    stages = [
        StageDefinition(
            stage_id="intake",
            agent=IntakeAgent(),
            gate=IntakeGate(),
        ),
        StageDefinition(
            stage_id="research",
            agent=ResearchAgent(),
            gate=None,
        ),
        StageDefinition(
            stage_id="outline",
            agent=OutlineAgent(),
            gate=OutlineGate(),
        ),
        StageDefinition(
            stage_id="draft",
            agent=DraftingAgent(),
            gate=DraftGate(),
        ),
        StageDefinition(
            stage_id="technical_review",
            agent=TechnicalReviewerAgent(),
            gate=TechnicalReviewGate(),
        ),
        StageDefinition(
            stage_id="editor",
            agent=EditorAgent(),
            gate=None,
        ),
        StageDefinition(
            stage_id="repurposing",
            agent=RepurposingAgent(),
            gate=None,
            optional=True,
        ),
        StageDefinition(
            stage_id="publishing_qa",
            agent=PublishingQAAgent(),
            gate=FinalQAGate(),
            optional=True,
        ),
    ]
    return AgentRegistry(stages)
