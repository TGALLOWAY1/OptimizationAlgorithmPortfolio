"""Multi-agent content orchestration pipeline.

This package composes specialized agents (intake, research, outline, draft,
technical review, edit, repurposing, publishing QA) into an explicit pipeline
with quality gates between stages, structured run state, and on-disk artifacts.

It is independent of `pipeline.generate`, which orchestrates per-technique
artifact generation for the optimization-algorithm site. Both share the same
LLM client, schemas, and prompt-template idioms.
"""

from pipeline.content_pipeline.pipeline import ContentPipeline
from pipeline.content_pipeline.quality_gates import QualityGateResult
from pipeline.content_pipeline.state import (
    ContentPipelineRun,
    PipelineStatus,
    StageRun,
    StageStatus,
    load_run,
    save_run,
)

__all__ = [
    "ContentPipeline",
    "ContentPipelineRun",
    "PipelineStatus",
    "QualityGateResult",
    "StageRun",
    "StageStatus",
    "load_run",
    "save_run",
]
