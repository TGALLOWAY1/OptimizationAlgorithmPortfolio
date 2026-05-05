"""Run the multi-agent content pipeline against a sample input.

Examples
--------

End-to-end smoke run with stubbed agents (no API key required)::

    python examples/run_content_pipeline.py --dry-run

End-to-end run against real LLMs (needs ``GEMINI_API_KEY`` set)::

    python examples/run_content_pipeline.py --input examples/sample_input.json

Resume a previously interrupted run::

    python examples/run_content_pipeline.py --resume 20260505T120000Z-abc123
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from pipeline.agents import build_default_registry
from pipeline.agents.base import (
    AgentMetadata,
    AgentResult,
    ContentAgent,
    PipelineContext,
)
from pipeline.content_pipeline.pipeline import ContentPipeline
from pipeline.content_pipeline.quality_gates import (
    DraftGate,
    FinalQAGate,
    IntakeGate,
    OutlineGate,
    TechnicalReviewGate,
)
from pipeline.content_pipeline.registry import AgentRegistry, StageDefinition
from pipeline.content_pipeline.state import PipelineStatus

DEFAULT_INPUT = Path("examples/sample_input.json")
DEFAULT_OUTPUT_ROOT = Path("outputs/runs")


def _stub_agent(stage_id: str, name: str, payload: dict):
    class _Stub(ContentAgent):
        id = stage_id
        STAGE_ID = stage_id
        ARTIFACT_TYPE = f"agent_{stage_id}"
        SCHEMA_KEY = stage_id  # not used in stub
        PROMPT_FILE = stage_id  # not used in stub

        def __init__(self):
            self.name = name
            self.description = f"Stub {name} for --dry-run"

        def run(self, stage_input, context: PipelineContext) -> AgentResult:
            return AgentResult(
                success=True,
                output=payload,
                metadata=AgentMetadata(model="stub", duration_ms=1),
            )

    return _Stub()


def _build_dry_run_registry() -> AgentRegistry:
    """Return a registry whose agents return canned outputs.

    Each output is shaped to satisfy the corresponding schema in
    :mod:`pipeline.schemas` and the cross-stage quality gates.
    """
    brief = {
        "topic": "Multi-agent orchestration for AI-native product workflows",
        "audience": "technical product managers and engineering leads",
        "content_type": "blog_post",
        "technical_depth": "intermediate",
        "goals": [
            "explain why one-shot LLM calls fail at production content workflows",
            "show a concrete staged-agent pattern readers can adopt",
        ],
        "requested_artifacts": ["blog_post", "linkedin_post", "x_thread"],
        "raw_input_summary": "Article comparing one-shot LLM use to a staged multi-agent pipeline.",
        "key_terms": ["orchestration", "agents", "PRD", "pipeline"],
    }
    research = {
        "notes": [
            {
                "claim": "One-shot LLM calls couple unrelated cognitive tasks.",
                "supporting_points": [
                    "research, drafting, and review have different failure modes",
                    "single prompts cannot easily expose intermediate state",
                ],
                "needs_verification": False,
            },
            {
                "claim": "Staged pipelines yield observable, testable artifacts.",
                "supporting_points": [
                    "each stage's output is a structured payload",
                    "schemas double as contracts between stages",
                ],
                "needs_verification": False,
            },
        ],
        "assumptions": ["readers already use LLMs day-to-day"],
        "open_questions": ["how do teams measure staged-pipeline ROI?"],
    }
    sections = [
        {
            "heading": "The cost of one-shot LLM workflows",
            "purpose": "Frame the problem with a concrete failure mode.",
            "key_points": [
                "one prompt does too much",
                "no observability into intermediate state",
            ],
            "section_type": "intro",
        },
        {
            "heading": "What changes when you split the work",
            "purpose": "Walk through a staged-pipeline pattern.",
            "key_points": [
                "each agent owns one responsibility",
                "schemas become contracts",
                "quality gates block weak outputs",
            ],
            "section_type": "explanation",
        },
        {
            "heading": "Applying it to your team",
            "purpose": "Give the reader a starting pattern.",
            "key_points": ["start with intake + outline", "add gates incrementally"],
            "section_type": "cta",
        },
    ]
    outline = {
        "title": "From One-Shot to Orchestrated: A Better Way to Use LLMs in Product Work",
        "hook": "Most teams treat LLMs as a single magic box. The teams that ship reliably split the box into stages.",
        "sections": sections,
        "estimated_word_count": 900,
        "target_format": "blog_post",
    }
    draft_markdown = (
        "## The cost of one-shot LLM workflows\n\n"
        "Most teams reach for an LLM the same way they reach for a calculator: paste in a prompt, copy out a result. "
        "That works for a quick answer. It does not work for a content workflow that has to ship reliably, week after week. "
        "When research, drafting, and review all happen in one prompt, you cannot inspect any of them. "
        "When the output is wrong, you cannot tell which step caused it. When you want to improve quality, you cannot target the failing layer. "
        "One prompt is a black box; a workflow has to be observable. The black-box problem compounds at scale: the more content you ship, the more you depend on lucky outputs and the less you can debug the unlucky ones. "
        "Teams discover this the hard way, usually when a piece slips through with a hallucinated benchmark or a confident but wrong claim, and there is nowhere to look to ask which step failed.\n\n"
        "## What changes when you split the work\n\n"
        "A staged pipeline names each cognitive task and gives it its own agent: intake, research, outline, draft, review, edit, repurpose, QA. "
        "Each agent reads structured input and produces a structured payload. Schemas become contracts: a draft must cite the outline it followed, a review must list issues with severities. "
        "Quality gates between stages block weak outputs from reaching downstream agents. The pipeline is observable because every step writes a typed artifact to disk. "
        "When something fails, you see exactly where. The schema contracts also let you swap implementations: a flash model for cheap stages, a pro model for the ones that matter, a stub for tests. "
        "Each stage is independently improvable; you can replace the drafting prompt without touching review. That is what makes the system feel less like a script and more like infrastructure.\n\n"
        "## Applying it to your team\n\n"
        "Start small. Build an intake agent that turns a free-text request into a structured brief. Add an outline agent next. "
        "Once both work, add a quality gate between them — does the brief specify an audience? a goal? Reject runs that do not. "
        "Layer in research, drafting, and review only once the upstream contracts hold. The pipeline grows in the order it should: contract first, agent second. "
        "The first version of this pattern can ship in a week. The first version that catches a hallucination at the gate, before it reaches a human reviewer, will pay for itself in saved cycles within a month. "
        "Teams that adopt this pattern stop debating prompts in Slack and start debating schemas in pull requests, which is exactly the upgrade you want.\n"
    )
    draft = {
        "markdown": draft_markdown,
        "word_count": len(draft_markdown.split()),
        "sections_covered": [s["heading"] for s in sections],
    }
    review = {
        "issues": [
            {
                "severity": "minor",
                "location": "Applying it to your team",
                "description": "Could mention specific tooling examples.",
                "suggested_fix": "Reference Prefect, LangGraph, or similar if relevant.",
            }
        ],
        "blocking_issues_count": 0,
        "overall_assessment": "Solid first draft; one minor suggestion.",
    }
    edited = {
        "markdown": draft_markdown.replace(
            "Layer in research, drafting, and review only once the upstream contracts hold.",
            "Layer in research, drafting, and review only once the upstream contracts hold. Frameworks like LangGraph or Prefect can manage the wiring once the shape is clear.",
        ),
        "word_count": len(draft_markdown.split()) + 16,
        "changes_made": [
            "Added a tooling pointer in the closing section in response to reviewer minor."
        ],
        "resolved_issues": ["Could mention specific tooling examples."],
    }
    repurposed = {
        "linkedin_post": (
            "Most teams treat LLMs as a single magic box. The teams that ship reliably "
            "split the box into stages — intake, research, outline, draft, review, edit, "
            "repurpose, QA — and put quality gates between them. Each agent owns one "
            "task. Each output is a typed artifact you can inspect. The result is a "
            "workflow you can debug instead of a black box you have to retry. Start "
            "with a structured intake and an outline; add gates between them; layer "
            "the rest in once the upstream contracts hold."
        ),
        "x_thread": [
            "Most teams treat LLMs as a single magic box. The teams that ship reliably split the box into stages.",
            "Intake, research, outline, draft, review, edit, repurpose, QA. Each step has its own agent and its own typed output.",
            "Schemas become contracts. A weak intake fails the gate before it pollutes downstream stages. You see where things break.",
            "Start tiny: intake -> outline + a gate between them. Add the rest only after the contract holds. Pipelines grow shape-first.",
        ],
        "youtube_description": (
            "How a multi-agent content pipeline beats one-shot LLM calls. "
            "Chapters: 1) The cost of one-shot LLM workflows. 2) What changes when "
            "you split the work. 3) Applying it to your team. Built for technical "
            "PMs and engineering leads who already use LLMs day-to-day."
        ),
        "short_form_script": (
            "Stop pasting prompts and praying. Split the work. Intake. Outline. "
            "Draft. Review. Each stage is a contract. Each output is something you "
            "can inspect. That's the difference between demos and shipping."
        ),
        "newsletter_blurb": (
            "If your LLM workflow is one big prompt, you are stuck debugging a black "
            "box. This week: how to split the work into staged agents with contracts "
            "between them — and the smallest version of the pattern that still pays "
            "off. Five-minute read."
        ),
        "readme_excerpt": (
            "## Background\n\nThis project ships a multi-agent content pipeline: "
            "intake, research, outline, draft, technical review, edit, repurposing, "
            "and publishing QA. Each stage has its own agent, its own JSON Schema, "
            "and an optional quality gate that can reject the stage's output and "
            "trigger a bounded revision pass."
        ),
    }
    publishing_qa = {
        "findings": [],
        "qa_score": 92,
        "publishable": True,
        "blocking_issues": [],
    }

    stages = [
        StageDefinition(
            stage_id="intake",
            agent=_stub_agent("intake", "Intake (stub)", brief),
            gate=IntakeGate(),
        ),
        StageDefinition(
            stage_id="research",
            agent=_stub_agent("research", "Research (stub)", research),
        ),
        StageDefinition(
            stage_id="outline",
            agent=_stub_agent("outline", "Outline (stub)", outline),
            gate=OutlineGate(),
        ),
        StageDefinition(
            stage_id="draft",
            agent=_stub_agent("draft", "Drafting (stub)", draft),
            gate=DraftGate(),
        ),
        StageDefinition(
            stage_id="technical_review",
            agent=_stub_agent("technical_review", "Technical Review (stub)", review),
            gate=TechnicalReviewGate(),
        ),
        StageDefinition(
            stage_id="editor",
            agent=_stub_agent("editor", "Editor (stub)", edited),
        ),
        StageDefinition(
            stage_id="repurposing",
            agent=_stub_agent("repurposing", "Repurposing (stub)", repurposed),
            optional=True,
        ),
        StageDefinition(
            stage_id="publishing_qa",
            agent=_stub_agent("publishing_qa", "Publishing QA (stub)", publishing_qa),
            gate=FinalQAGate(),
            optional=True,
        ),
    ]
    return AgentRegistry(stages)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--resume", type=str, default=None)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Use stub agents (no LLM calls). Useful for smoke verification.",
    )
    parser.add_argument("--auto-approve", action="store_true", default=True)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    pipeline_input = json.loads(args.input.read_text())
    registry = _build_dry_run_registry() if args.dry_run else build_default_registry()
    pipeline = ContentPipeline(registry=registry, output_root=args.output_root)
    run = pipeline.run(
        pipeline_input=pipeline_input,
        resume_run_id=args.resume,
        auto_approve=args.auto_approve,
    )

    print(f"\nRun id:      {run.run_id}")
    print(f"Status:      {run.status.value}")
    print(f"Output dir:  {args.output_root / run.run_id}")
    if run.artifacts:
        print("Artifacts:")
        for name, path in sorted(run.artifacts.items()):
            print(f"  {name}: {path}")
    return 0 if run.status is PipelineStatus.COMPLETED else 1


if __name__ == "__main__":
    raise SystemExit(main())
