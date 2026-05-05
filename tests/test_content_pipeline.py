"""Tests for the ContentPipeline orchestrator.

Pipeline-level tests inject a fake :class:`AgentRegistry` populated with stub
:class:`ContentAgent` subclasses. This avoids stacking eight ``@patch``
decorators per test and lets us script per-stage behavior precisely.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pipeline.agents.base import (
    AgentMetadata,
    AgentResult,
    ContentAgent,
    PipelineContext,
)
from pipeline.content_pipeline.pipeline import ContentPipeline
from pipeline.content_pipeline.quality_gates import QualityGate, QualityGateResult
from pipeline.content_pipeline.registry import AgentRegistry, StageDefinition
from pipeline.content_pipeline.state import (
    PipelineStatus,
    StageStatus,
    load_run,
    save_run,
)


def _stub_agent_class(stage_id: str, payload: dict | None, fail: bool = False):
    """Create a one-off ContentAgent subclass returning a fixed result."""

    class _Stub(ContentAgent):
        STAGE_ID = stage_id
        ARTIFACT_TYPE = f"agent_{stage_id}"
        SCHEMA_KEY = stage_id
        PROMPT_FILE = stage_id

        def __init__(self):
            self.id = stage_id
            self.name = f"{stage_id} (stub)"
            self.description = ""
            self.calls = 0

        def run(self, stage_input, context: PipelineContext) -> AgentResult:
            self.calls += 1
            if fail:
                return AgentResult(
                    success=False,
                    errors=("synthetic stub failure",),
                    metadata=AgentMetadata(model="stub", duration_ms=1),
                )
            return AgentResult(
                success=True,
                output=payload,
                metadata=AgentMetadata(model="stub", duration_ms=1),
            )

    return _Stub


class _AlternatingGate(QualityGate):
    """Fails on its first N evaluations, then passes."""

    id = "alt_gate"
    description = "fails N times then passes"

    def __init__(self, stage_id: str, fail_n: int):
        self.stage_id = stage_id
        self._remaining = fail_n
        self.calls = 0

    def _check(self, payload, previous_outputs):
        self.calls += 1
        if self._remaining > 0:
            self._remaining -= 1
            return ["alt failure"], []
        return [], []


class _AlwaysFailGate(QualityGate):
    id = "always_fail"
    description = "always fails"

    def __init__(self, stage_id: str):
        self.stage_id = stage_id

    def _check(self, payload, previous_outputs):
        return ["fixed failure"], []


def _minimal_registry(*overrides: StageDefinition) -> AgentRegistry:
    """Build a 3-stage registry by default; overrides replace by stage_id."""
    base_payloads = {
        "intake": {"topic": "T", "audience": "A", "content_type": "blog_post", "goals": ["g"]},
        "outline": {"title": "T"},
        "draft": {"markdown": "x", "word_count": 1, "sections_covered": []},
    }
    stages = [
        StageDefinition(
            stage_id="intake",
            agent=_stub_agent_class("intake", base_payloads["intake"])(),
        ),
        StageDefinition(
            stage_id="outline",
            agent=_stub_agent_class("outline", base_payloads["outline"])(),
        ),
        StageDefinition(
            stage_id="draft",
            agent=_stub_agent_class("draft", base_payloads["draft"])(),
        ),
    ]
    by_id = {s.stage_id: s for s in stages}
    for override in overrides:
        by_id[override.stage_id] = override
    return AgentRegistry([by_id[s.stage_id] for s in stages])


class TestHappyPath:
    def test_completes_and_persists(self, tmp_path: Path):
        registry = _minimal_registry()
        pipeline = ContentPipeline(registry=registry, output_root=tmp_path)
        run = pipeline.run(pipeline_input={"raw_input": "hello"})

        assert run.status is PipelineStatus.COMPLETED
        assert all(s.status is StageStatus.SUCCEEDED for s in run.stages)
        assert (tmp_path / run.run_id / "run.json").exists()
        for stage_id in ("intake", "outline", "draft"):
            assert (tmp_path / run.run_id / f"{stage_id}.json").exists()

    def test_run_json_round_trips(self, tmp_path: Path):
        registry = _minimal_registry()
        pipeline = ContentPipeline(registry=registry, output_root=tmp_path)
        run = pipeline.run(pipeline_input={"raw_input": "hello"})

        loaded = load_run(run.run_id, tmp_path)
        assert loaded.run_id == run.run_id
        assert loaded.status is PipelineStatus.COMPLETED
        assert [s.stage_id for s in loaded.stages] == [
            s.stage_id for s in run.stages
        ]
        assert all(s.status is StageStatus.SUCCEEDED for s in loaded.stages)


class TestHardFailure:
    def test_required_stage_failure_marks_pipeline_failed(self, tmp_path: Path):
        registry = _minimal_registry(
            StageDefinition(
                stage_id="outline",
                agent=_stub_agent_class("outline", None, fail=True)(),
            )
        )
        pipeline = ContentPipeline(registry=registry, output_root=tmp_path)
        run = pipeline.run(pipeline_input={"raw_input": "hello"})

        assert run.status is PipelineStatus.FAILED
        statuses = {s.stage_id: s.status for s in run.stages}
        assert statuses["intake"] is StageStatus.SUCCEEDED
        assert statuses["outline"] is StageStatus.FAILED
        # Downstream stage should never have run
        assert statuses["draft"] is StageStatus.PENDING


class TestOptionalStage:
    def test_optional_stage_failure_is_skipped(self, tmp_path: Path):
        registry = _minimal_registry(
            StageDefinition(
                stage_id="draft",
                agent=_stub_agent_class("draft", None, fail=True)(),
                optional=True,
            )
        )
        pipeline = ContentPipeline(registry=registry, output_root=tmp_path)
        run = pipeline.run(pipeline_input={"raw_input": "hello"})

        statuses = {s.stage_id: s.status for s in run.stages}
        assert run.status is PipelineStatus.COMPLETED
        assert statuses["draft"] is StageStatus.SKIPPED


class TestGateRevision:
    def test_alternating_gate_succeeds_after_one_revision(self, tmp_path: Path):
        gate = _AlternatingGate(stage_id="outline", fail_n=1)
        agent = _stub_agent_class(
            "outline", {"title": "T"}
        )()
        registry = _minimal_registry(
            StageDefinition(
                stage_id="outline",
                agent=agent,
                gate=gate,
                max_revisions=1,
            )
        )
        pipeline = ContentPipeline(registry=registry, output_root=tmp_path)
        run = pipeline.run(pipeline_input={"raw_input": "hello"})

        assert run.status is PipelineStatus.COMPLETED
        outline_stage = run.stage("outline")
        assert outline_stage.status is StageStatus.SUCCEEDED
        assert outline_stage.retries == 1
        assert agent.calls == 2  # one initial + one revision
        assert gate.calls == 2

    def test_budget_exhausted_marks_failed(self, tmp_path: Path):
        gate = _AlwaysFailGate(stage_id="outline")
        registry = _minimal_registry(
            StageDefinition(
                stage_id="outline",
                agent=_stub_agent_class("outline", {"title": "T"})(),
                gate=gate,
                max_revisions=1,
            )
        )
        pipeline = ContentPipeline(registry=registry, output_root=tmp_path)
        run = pipeline.run(pipeline_input={"raw_input": "hello"})

        assert run.status is PipelineStatus.FAILED
        outline_stage = run.stage("outline")
        assert outline_stage.status is StageStatus.FAILED
        assert outline_stage.retries == 1


class TestResume:
    def test_resume_skips_already_succeeded_stages(self, tmp_path: Path):
        intake_agent = _stub_agent_class(
            "intake",
            {
                "topic": "T",
                "audience": "A",
                "content_type": "blog_post",
                "goals": ["g"],
            },
        )()
        outline_agent = _stub_agent_class("outline", {"title": "T"})()
        draft_agent = _stub_agent_class(
            "draft", {"markdown": "x", "word_count": 1, "sections_covered": []}
        )()

        registry = AgentRegistry(
            [
                StageDefinition(stage_id="intake", agent=intake_agent),
                StageDefinition(stage_id="outline", agent=outline_agent),
                StageDefinition(stage_id="draft", agent=draft_agent),
            ]
        )
        pipeline = ContentPipeline(registry=registry, output_root=tmp_path)
        run = pipeline.run(pipeline_input={"raw_input": "hello"})

        assert intake_agent.calls == 1
        assert outline_agent.calls == 1
        assert draft_agent.calls == 1

        # Build a fresh pipeline with fresh stub-agent instances and resume.
        intake_agent_2 = _stub_agent_class("intake", {"topic": "T2"})()
        outline_agent_2 = _stub_agent_class("outline", {"title": "T2"})()
        draft_agent_2 = _stub_agent_class(
            "draft",
            {"markdown": "y", "word_count": 1, "sections_covered": []},
        )()
        registry_2 = AgentRegistry(
            [
                StageDefinition(stage_id="intake", agent=intake_agent_2),
                StageDefinition(stage_id="outline", agent=outline_agent_2),
                StageDefinition(stage_id="draft", agent=draft_agent_2),
            ]
        )
        pipeline_2 = ContentPipeline(registry=registry_2, output_root=tmp_path)
        resumed = pipeline_2.run(
            pipeline_input={"raw_input": "hello"},
            resume_run_id=run.run_id,
        )
        assert resumed.status is PipelineStatus.COMPLETED
        # Agents from a fully-completed run are skipped; nothing is re-invoked.
        assert intake_agent_2.calls == 0
        assert outline_agent_2.calls == 0
        assert draft_agent_2.calls == 0
