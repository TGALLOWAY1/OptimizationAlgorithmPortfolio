"""ContentPipeline — sequential orchestrator for the multi-agent content flow."""

from __future__ import annotations

import json
import logging
import secrets
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.agents.base import PipelineContext
from pipeline.content_pipeline.registry import AgentRegistry, StageDefinition
from pipeline.content_pipeline.state import (
    ContentPipelineRun,
    PipelineStatus,
    StageRun,
    StageStatus,
    load_run,
    save_run,
    utc_now_iso,
)

logger = logging.getLogger(__name__)

DEFAULT_OUTPUT_ROOT = Path("outputs/runs")


class PipelineFailure(RuntimeError):
    """Raised when the pipeline cannot make progress and must stop."""


class ContentPipeline:
    """Compose the registered agents into a sequential, gated pipeline.

    Usage::

        pipeline = ContentPipeline(build_default_registry())
        run = pipeline.run({"raw_input": "..."})
    """

    def __init__(
        self,
        registry: AgentRegistry,
        output_root: Path | str = DEFAULT_OUTPUT_ROOT,
    ):
        self.registry = registry
        self.output_root = Path(output_root)

    # ------------------------------------------------------------------ run

    def run(
        self,
        pipeline_input: dict[str, Any],
        resume_run_id: str | None = None,
        auto_approve: bool = True,
    ) -> ContentPipelineRun:
        """Execute the pipeline end-to-end (or resume an interrupted run)."""
        if resume_run_id:
            run = load_run(resume_run_id, self.output_root)
            run.status = PipelineStatus.RUNNING
            logger.info("[run=%s] resuming pipeline", run.run_id)
        else:
            run = self._init_run(pipeline_input)
            logger.info("[run=%s] starting pipeline", run.run_id)

        run_dir = self.output_root / run.run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        context = PipelineContext(
            run_id=run.run_id,
            output_dir=run_dir,
            input=run.input,
            previous_outputs=self._load_previous_outputs(run, run_dir),
            gate_feedback=[],
        )

        save_run(run, run_dir)

        try:
            for stage_def in self.registry.iter_stages():
                stage_run = self._ensure_stage(run, stage_def)

                if (
                    stage_run.status is StageStatus.SUCCEEDED
                    and stage_run.output_path
                    and Path(stage_run.output_path).exists()
                ):
                    logger.info(
                        "[run=%s stage=%s] already succeeded; skipping",
                        run.run_id,
                        stage_def.stage_id,
                    )
                    context.previous_outputs[stage_def.stage_id] = json.loads(
                        Path(stage_run.output_path).read_text()
                    )
                    continue

                self._run_stage(run, stage_def, stage_run, context, run_dir)

                if (
                    stage_def.stage_id == "technical_review"
                    and not auto_approve
                    and (context.previous_outputs.get("technical_review", {})
                         .get("requires_human"))
                ):
                    run.status = PipelineStatus.WAITING_FOR_REVIEW
                    save_run(run, run_dir)
                    logger.info(
                        "[run=%s] paused for human review after technical_review",
                        run.run_id,
                    )
                    return run

            self._finalize_artifacts(run, run_dir)
            run.status = PipelineStatus.COMPLETED
            run.finished_at = utc_now_iso()
            save_run(run, run_dir)
            logger.info("[run=%s] pipeline completed", run.run_id)
            return run

        except PipelineFailure as exc:
            run.status = PipelineStatus.FAILED
            run.finished_at = utc_now_iso()
            save_run(run, run_dir)
            logger.warning("[run=%s] pipeline failed: %s", run.run_id, exc)
            return run

    # -------------------------------------------------------------- helpers

    def cancel(self, run_id: str) -> None:
        """Reserved for future use — cancellation requires an external signal."""
        raise NotImplementedError(
            "Pipeline cancellation is not yet implemented; the status is reserved."
        )

    def _init_run(self, pipeline_input: dict[str, Any]) -> ContentPipelineRun:
        now = datetime.now(timezone.utc)
        run_id = (
            now.strftime("%Y%m%dT%H%M%SZ")
            + "-"
            + secrets.token_hex(3)
        )
        stages = [
            StageRun(stage_id=s.stage_id, name=s.agent.name)
            for s in self.registry.iter_stages()
        ]
        return ContentPipelineRun(
            run_id=run_id,
            status=PipelineStatus.RUNNING,
            input=pipeline_input,
            stages=stages,
            started_at=now.isoformat(),
        )

    def _ensure_stage(
        self,
        run: ContentPipelineRun,
        stage_def: StageDefinition,
    ) -> StageRun:
        stage_run = run.stage(stage_def.stage_id)
        if stage_run is None:
            stage_run = StageRun(stage_id=stage_def.stage_id, name=stage_def.agent.name)
            run.stages.append(stage_run)
        return stage_run

    def _load_previous_outputs(
        self,
        run: ContentPipelineRun,
        run_dir: Path,
    ) -> dict[str, dict[str, Any]]:
        previous: dict[str, dict[str, Any]] = {}
        for stage in run.stages:
            if stage.status is StageStatus.SUCCEEDED and stage.output_path:
                path = Path(stage.output_path)
                if path.exists():
                    previous[stage.stage_id] = json.loads(path.read_text())
        return previous

    def _run_stage(
        self,
        run: ContentPipelineRun,
        stage_def: StageDefinition,
        stage_run: StageRun,
        context: PipelineContext,
        run_dir: Path,
    ) -> None:
        attempts_remaining = stage_def.max_revisions + 1
        while attempts_remaining > 0:
            attempts_remaining -= 1
            stage_run.status = StageStatus.RUNNING
            stage_run.started_at = utc_now_iso()
            stage_run.error = None
            save_run(run, run_dir)
            logger.info(
                "[run=%s stage=%s] starting (gate_feedback=%d)",
                run.run_id,
                stage_def.stage_id,
                len(context.gate_feedback),
            )

            stage_input = context.input if stage_def.stage_id == "intake" else {}
            result = stage_def.agent.run(stage_input, context)
            stage_run.finished_at = utc_now_iso()
            if result.metadata is not None:
                stage_run.metadata = asdict(result.metadata)

            if not result.success or result.output is None:
                error_msg = "; ".join(result.errors) or "agent reported failure"
                stage_run.error = error_msg
                if stage_def.optional:
                    stage_run.status = StageStatus.SKIPPED
                    logger.warning(
                        "[run=%s stage=%s] optional stage skipped: %s",
                        run.run_id,
                        stage_def.stage_id,
                        error_msg,
                    )
                    save_run(run, run_dir)
                    return
                stage_run.status = StageStatus.FAILED
                save_run(run, run_dir)
                raise PipelineFailure(
                    f"stage {stage_def.stage_id} failed: {error_msg}"
                )

            output_path = run_dir / f"{stage_def.stage_id}.json"
            output_path.write_text(json.dumps(result.output, indent=2))
            stage_run.output_path = str(output_path)
            context.previous_outputs[stage_def.stage_id] = result.output

            if stage_def.gate is not None:
                gate_result = stage_def.gate.evaluate(
                    result.output, context.previous_outputs
                )
                run.gate_results.append(asdict(gate_result))
                save_run(run, run_dir)
                if not gate_result.passed:
                    if attempts_remaining > 0:
                        stage_run.status = StageStatus.NEEDS_REVISION
                        stage_run.retries += 1
                        context.gate_feedback = list(gate_result.failures)
                        logger.warning(
                            "[run=%s stage=%s] gate %s failed: %s — revising",
                            run.run_id,
                            stage_def.stage_id,
                            gate_result.gate_id,
                            list(gate_result.failures),
                        )
                        save_run(run, run_dir)
                        continue
                    if stage_def.optional:
                        stage_run.status = StageStatus.SKIPPED
                        stage_run.error = (
                            f"gate {gate_result.gate_id} failed: "
                            f"{list(gate_result.failures)}"
                        )
                        logger.warning(
                            "[run=%s stage=%s] optional stage skipped after gate exhaustion",
                            run.run_id,
                            stage_def.stage_id,
                        )
                        save_run(run, run_dir)
                        return
                    stage_run.status = StageStatus.FAILED
                    stage_run.error = (
                        f"gate {gate_result.gate_id} failed after retries: "
                        f"{list(gate_result.failures)}"
                    )
                    save_run(run, run_dir)
                    raise PipelineFailure(stage_run.error)

            stage_run.status = StageStatus.SUCCEEDED
            context.gate_feedback = []
            save_run(run, run_dir)
            logger.info(
                "[run=%s stage=%s] succeeded (retries=%d)",
                run.run_id,
                stage_def.stage_id,
                stage_run.retries,
            )
            return

    def _finalize_artifacts(self, run: ContentPipelineRun, run_dir: Path) -> None:
        """Write derived markdown files alongside the JSON stage outputs."""
        artifacts: dict[str, str] = {}
        for stage in run.stages:
            if stage.output_path:
                artifacts[f"{stage.stage_id}.json"] = stage.output_path

        previous_outputs: dict[str, dict[str, Any]] = {}
        for stage in run.stages:
            if stage.status is StageStatus.SUCCEEDED and stage.output_path:
                previous_outputs[stage.stage_id] = json.loads(
                    Path(stage.output_path).read_text()
                )

        draft = previous_outputs.get("draft") or {}
        if draft.get("markdown"):
            path = run_dir / "draft.md"
            path.write_text(draft["markdown"])
            artifacts["draft.md"] = str(path)

        edited = previous_outputs.get("editor") or {}
        if edited.get("markdown"):
            path = run_dir / "edited-draft.md"
            path.write_text(edited["markdown"])
            artifacts["edited-draft.md"] = str(path)

        repurposed = previous_outputs.get("repurposing") or {}
        if repurposed:
            mapping = {
                "linkedin-post.md": repurposed.get("linkedin_post"),
                "x-thread.md": (
                    "\n\n".join(repurposed.get("x_thread") or [])
                    if repurposed.get("x_thread")
                    else None
                ),
                "youtube-description.md": repurposed.get("youtube_description"),
                "short-form-script.md": repurposed.get("short_form_script"),
                "newsletter-blurb.md": repurposed.get("newsletter_blurb"),
                "readme-excerpt.md": repurposed.get("readme_excerpt"),
            }
            for filename, content in mapping.items():
                if content:
                    path = run_dir / filename
                    path.write_text(content)
                    artifacts[filename] = str(path)

        run.artifacts = artifacts
