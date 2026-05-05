"""Tests for the eight content-pipeline agents.

Each agent invokes :func:`pipeline.llm_client.get_provider` and
:func:`pipeline.llm_client.generate_with_retry` through the helper on
:class:`pipeline.agents.base.ContentAgent`. We patch those at the ``base``
module level — exactly the same pattern other tests in this repo use for
``api.math_tutor`` and friends.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pipeline.agents.base import PipelineContext
from pipeline.agents.drafting_agent import DraftingAgent
from pipeline.agents.editor_agent import EditorAgent
from pipeline.agents.intake_agent import IntakeAgent
from pipeline.agents.outline_agent import OutlineAgent
from pipeline.agents.publishing_qa_agent import PublishingQAAgent
from pipeline.agents.repurposing_agent import RepurposingAgent
from pipeline.agents.research_agent import ResearchAgent
from pipeline.agents.technical_reviewer_agent import TechnicalReviewerAgent


def _ctx(previous=None) -> PipelineContext:
    return PipelineContext(
        run_id="test-run",
        output_dir=Path("/tmp/test-run"),
        input={"raw_input": "Article about staged agents."},
        previous_outputs=previous or {},
    )


def _mock_provider():
    provider = MagicMock()
    provider.model = "stub-model"
    return provider


class TestIntakeAgent:
    @patch("pipeline.agents.base.generate_with_retry")
    @patch("pipeline.agents.base.get_provider")
    def test_returns_payload_on_success(self, mock_get_provider, mock_generate):
        mock_get_provider.return_value = _mock_provider()
        mock_generate.return_value = {
            "topic": "T",
            "audience": "A",
            "content_type": "blog_post",
            "technical_depth": "intermediate",
            "goals": ["g"],
            "requested_artifacts": ["blog_post"],
            "raw_input_summary": "summary text",
        }
        agent = IntakeAgent()
        ctx = _ctx()
        result = agent.run({"raw_input": "Article about staged agents."}, ctx)
        assert result.success
        assert result.output["topic"] == "T"
        assert result.metadata.model == "stub-model"

    def test_fails_on_empty_raw_input(self):
        result = IntakeAgent().run({"raw_input": "   "}, _ctx())
        assert not result.success
        assert any("raw_input" in e for e in result.errors)

    @patch("pipeline.agents.base.generate_with_retry")
    @patch("pipeline.agents.base.get_provider")
    def test_returns_failure_on_runtime_error(self, mock_get_provider, mock_generate):
        mock_get_provider.return_value = _mock_provider()
        mock_generate.side_effect = RuntimeError("LLM exhausted retries")
        result = IntakeAgent().run({"raw_input": "x"}, _ctx())
        assert not result.success
        assert any("exhausted" in e for e in result.errors)


class TestResearchAgent:
    @patch("pipeline.agents.base.generate_with_retry")
    @patch("pipeline.agents.base.get_provider")
    def test_requires_intake_in_context(self, mock_get_provider, mock_generate):
        result = ResearchAgent().run({}, _ctx())
        assert not result.success
        mock_generate.assert_not_called()

    @patch("pipeline.agents.base.generate_with_retry")
    @patch("pipeline.agents.base.get_provider")
    def test_runs_with_intake_present(self, mock_get_provider, mock_generate):
        mock_get_provider.return_value = _mock_provider()
        mock_generate.return_value = {
            "notes": [
                {
                    "claim": "X is true",
                    "supporting_points": ["because Y"],
                    "needs_verification": True,
                }
            ],
            "assumptions": [],
            "open_questions": [],
        }
        ctx = _ctx(previous={"intake": {"topic": "X"}})
        result = ResearchAgent().run({}, ctx)
        assert result.success
        assert result.output["notes"][0]["needs_verification"] is True


class TestOutlineAgent:
    @patch("pipeline.agents.base.generate_with_retry")
    @patch("pipeline.agents.base.get_provider")
    def test_requires_intake_and_research(self, mock_get_provider, mock_generate):
        result = OutlineAgent().run({}, _ctx(previous={"intake": {"topic": "X"}}))
        assert not result.success
        mock_generate.assert_not_called()

    @patch("pipeline.agents.base.generate_with_retry")
    @patch("pipeline.agents.base.get_provider")
    def test_runs_with_full_context(self, mock_get_provider, mock_generate):
        mock_get_provider.return_value = _mock_provider()
        mock_generate.return_value = {
            "title": "T",
            "hook": "H",
            "sections": [
                {
                    "heading": "Intro",
                    "purpose": "introduce",
                    "key_points": ["a"],
                    "section_type": "intro",
                },
                {
                    "heading": "How",
                    "purpose": "explain",
                    "key_points": ["b"],
                    "section_type": "explanation",
                },
                {
                    "heading": "End",
                    "purpose": "wrap",
                    "key_points": ["c"],
                    "section_type": "conclusion",
                },
            ],
            "estimated_word_count": 800,
            "target_format": "blog_post",
        }
        ctx = _ctx(
            previous={
                "intake": {"topic": "X"},
                "research": {"notes": [], "assumptions": [], "open_questions": []},
            }
        )
        result = OutlineAgent().run({}, ctx)
        assert result.success
        assert len(result.output["sections"]) == 3


class TestDraftingAgent:
    @patch("pipeline.agents.base.generate_with_retry")
    @patch("pipeline.agents.base.get_provider")
    def test_runs(self, mock_get_provider, mock_generate):
        mock_get_provider.return_value = _mock_provider()
        mock_generate.return_value = {
            "markdown": "## Intro\n\nbody " * 100,
            "word_count": 200,
            "sections_covered": ["Intro"],
        }
        ctx = _ctx(
            previous={
                "intake": {"topic": "X"},
                "outline": {"sections": [{"heading": "Intro"}]},
                "research": {"notes": []},
            }
        )
        result = DraftingAgent().run({}, ctx)
        assert result.success


class TestTechnicalReviewerAgent:
    @patch("pipeline.agents.base.generate_with_retry")
    @patch("pipeline.agents.base.get_provider")
    def test_requires_draft_markdown(self, mock_get_provider, mock_generate):
        result = TechnicalReviewerAgent().run({}, _ctx(previous={"draft": {}}))
        assert not result.success
        mock_generate.assert_not_called()

    @patch("pipeline.agents.base.generate_with_retry")
    @patch("pipeline.agents.base.get_provider")
    def test_runs_with_draft(self, mock_get_provider, mock_generate):
        mock_get_provider.return_value = _mock_provider()
        mock_generate.return_value = {
            "issues": [],
            "blocking_issues_count": 0,
            "overall_assessment": "fine",
        }
        ctx = _ctx(previous={"draft": {"markdown": "## A\n\nx"}, "intake": {}, "research": {}})
        result = TechnicalReviewerAgent().run({}, ctx)
        assert result.success


class TestEditorAgent:
    @patch("pipeline.agents.base.generate_with_retry")
    @patch("pipeline.agents.base.get_provider")
    def test_runs(self, mock_get_provider, mock_generate):
        mock_get_provider.return_value = _mock_provider()
        mock_generate.return_value = {
            "markdown": "## A\n\nedited body " * 50,
            "word_count": 150,
            "changes_made": ["tightened intro"],
            "resolved_issues": [],
        }
        ctx = _ctx(
            previous={
                "draft": {"markdown": "## A\n\nx"},
                "technical_review": {"issues": []},
                "intake": {},
            }
        )
        result = EditorAgent().run({}, ctx)
        assert result.success


class TestRepurposingAgent:
    @patch("pipeline.agents.base.generate_with_retry")
    @patch("pipeline.agents.base.get_provider")
    def test_runs(self, mock_get_provider, mock_generate):
        mock_get_provider.return_value = _mock_provider()
        payload = {
            "linkedin_post": "x" * 80,
            "x_thread": ["tweet one", "tweet two"],
            "youtube_description": "y" * 80,
            "short_form_script": "z" * 60,
            "newsletter_blurb": "n" * 60,
            "readme_excerpt": "r" * 60,
        }
        mock_generate.return_value = payload
        ctx = _ctx(
            previous={
                "editor": {"markdown": "## A\n\nedited"},
                "outline": {},
                "intake": {},
            }
        )
        result = RepurposingAgent().run({}, ctx)
        assert result.success
        assert "linkedin_post" in result.output

    def test_fails_without_edited_markdown(self):
        result = RepurposingAgent().run({}, _ctx(previous={"editor": {}}))
        assert not result.success


class TestPublishingQAAgent:
    @patch("pipeline.agents.base.generate_with_retry")
    @patch("pipeline.agents.base.get_provider")
    def test_runs(self, mock_get_provider, mock_generate):
        mock_get_provider.return_value = _mock_provider()
        mock_generate.return_value = {
            "findings": [],
            "qa_score": 92,
            "publishable": True,
            "blocking_issues": [],
        }
        ctx = _ctx(
            previous={
                "editor": {"markdown": "## A\n\nedited"},
                "repurposing": {},
                "outline": {},
                "intake": {},
            }
        )
        result = PublishingQAAgent().run({}, ctx)
        assert result.success
        assert result.output["publishable"] is True
