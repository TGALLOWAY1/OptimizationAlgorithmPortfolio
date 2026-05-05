"""Stage registry for the content pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

from pipeline.agents.base import ContentAgent
from pipeline.content_pipeline.quality_gates import QualityGate


@dataclass(frozen=True)
class StageDefinition:
    """One stage in the pipeline.

    ``optional`` stages may fail without failing the whole pipeline (the stage
    is recorded as ``skipped`` instead). ``max_revisions`` bounds the number of
    gate-driven retries before a stage is marked failed.
    """

    stage_id: str
    agent: ContentAgent
    gate: QualityGate | None = None
    optional: bool = False
    max_revisions: int = 1


class AgentRegistry:
    """Ordered collection of stage definitions consumed by :class:`ContentPipeline`."""

    def __init__(self, stages: list[StageDefinition]):
        seen: set[str] = set()
        for stage in stages:
            if stage.stage_id in seen:
                raise ValueError(f"Duplicate stage_id in registry: {stage.stage_id}")
            seen.add(stage.stage_id)
        self._stages = list(stages)

    def get(self, stage_id: str) -> StageDefinition:
        for stage in self._stages:
            if stage.stage_id == stage_id:
                return stage
        raise KeyError(stage_id)

    def iter_stages(self) -> Iterator[StageDefinition]:
        return iter(self._stages)

    def __len__(self) -> int:
        return len(self._stages)
