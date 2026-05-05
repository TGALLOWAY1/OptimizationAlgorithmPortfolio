"""Tests for content-pipeline quality gates."""

from __future__ import annotations

from pipeline.content_pipeline.quality_gates import (
    DraftGate,
    FinalQAGate,
    IntakeGate,
    OutlineGate,
    TechnicalReviewGate,
)


class TestIntakeGate:
    def test_passes_with_complete_brief(self):
        gate = IntakeGate()
        result = gate.evaluate(
            {
                "topic": "Multi-agent orchestration",
                "audience": "PMs",
                "content_type": "blog_post",
                "goals": ["explain X", "show Y"],
            }
        )
        assert result.passed
        assert result.failures == ()

    def test_fails_when_audience_missing(self):
        result = IntakeGate().evaluate(
            {"topic": "X", "audience": "", "content_type": "blog_post", "goals": ["g"]}
        )
        assert not result.passed
        assert any("audience" in f for f in result.failures)

    def test_fails_when_goals_empty(self):
        result = IntakeGate().evaluate(
            {"topic": "X", "audience": "PMs", "content_type": "blog_post", "goals": []}
        )
        assert not result.passed
        assert any("goals" in f for f in result.failures)


class TestOutlineGate:
    def _outline(self, **overrides):
        base = {
            "title": "T",
            "hook": "H",
            "sections": [
                {"heading": "Intro", "section_type": "intro"},
                {"heading": "How", "section_type": "explanation"},
                {"heading": "End", "section_type": "conclusion"},
            ],
        }
        base.update(overrides)
        return base

    def test_passes_with_three_sections_and_explanation(self):
        result = OutlineGate().evaluate(self._outline())
        assert result.passed

    def test_fails_when_too_few_sections(self):
        outline = self._outline(sections=[{"heading": "Only", "section_type": "intro"}])
        result = OutlineGate().evaluate(outline)
        assert not result.passed
        assert any("3" in f for f in result.failures)

    def test_fails_without_explanation_section(self):
        outline = self._outline(
            sections=[
                {"heading": "Intro", "section_type": "intro"},
                {"heading": "Mid", "section_type": "example"},
                {"heading": "End", "section_type": "cta"},
            ]
        )
        result = OutlineGate().evaluate(outline)
        assert not result.passed
        assert any("explanation" in f for f in result.failures)

    def test_warns_when_first_section_is_not_intro(self):
        outline = self._outline(
            sections=[
                {"heading": "Mid", "section_type": "explanation"},
                {"heading": "More", "section_type": "deep_dive"},
                {"heading": "End", "section_type": "conclusion"},
            ]
        )
        result = OutlineGate().evaluate(outline)
        assert result.passed
        assert any("intro" in w.lower() for w in result.warnings)


class TestDraftGate:
    def _draft(self, words: int = 400, sections=None, markdown: str | None = None):
        text = markdown or " ".join(["word"] * words)
        return {
            "markdown": text,
            "word_count": len(text.split()),
            "sections_covered": sections or ["A", "B", "C"],
        }

    def _outline(self):
        return {
            "outline": {
                "sections": [
                    {"heading": "A"},
                    {"heading": "B"},
                    {"heading": "C"},
                ]
            }
        }

    def test_passes_with_sufficient_length_and_coverage(self):
        result = DraftGate().evaluate(self._draft(), self._outline())
        assert result.passed

    def test_fails_when_too_short(self):
        result = DraftGate().evaluate(self._draft(words=50), self._outline())
        assert not result.passed
        assert any("too short" in f for f in result.failures)

    def test_fails_on_placeholder_text(self):
        markdown = "Here we go. TODO finish this section. The end."
        draft = self._draft(markdown=markdown, sections=["A", "B", "C"])
        # bump word count above the minimum so only the placeholder fails
        draft["markdown"] = markdown + " " + " ".join(["word"] * 400)
        draft["word_count"] = len(draft["markdown"].split())
        result = DraftGate().evaluate(draft, self._outline())
        assert not result.passed
        assert any("placeholder" in f.lower() for f in result.failures)

    def test_fails_on_low_section_coverage(self):
        draft = self._draft(sections=["A"])
        result = DraftGate().evaluate(draft, self._outline())
        assert not result.passed
        assert any("outline sections" in f for f in result.failures)


class TestTechnicalReviewGate:
    def test_passes_with_no_critical_issues(self):
        result = TechnicalReviewGate().evaluate(
            {
                "issues": [
                    {"severity": "minor", "location": "intro", "description": "x"}
                ],
                "blocking_issues_count": 0,
                "overall_assessment": "ok",
            }
        )
        assert result.passed

    def test_fails_on_critical_issue(self):
        result = TechnicalReviewGate().evaluate(
            {
                "issues": [
                    {"severity": "critical", "location": "intro", "description": "wrong"}
                ],
                "blocking_issues_count": 1,
                "overall_assessment": "bad",
            }
        )
        assert not result.passed
        assert any("critical" in f for f in result.failures)


class TestFinalQAGate:
    def test_passes_when_publishable_and_score_above_threshold(self):
        result = FinalQAGate().evaluate(
            {
                "findings": [],
                "qa_score": 90,
                "publishable": True,
                "blocking_issues": [],
            }
        )
        assert result.passed

    def test_fails_when_not_publishable(self):
        result = FinalQAGate().evaluate(
            {
                "findings": [],
                "qa_score": 50,
                "publishable": False,
                "blocking_issues": ["weak hook"],
            }
        )
        assert not result.passed
        assert any("weak hook" in f for f in result.failures)

    def test_fails_on_low_score_even_if_publishable_flag_true(self):
        result = FinalQAGate().evaluate(
            {
                "findings": [],
                "qa_score": 40,
                "publishable": True,
                "blocking_issues": [],
            }
        )
        assert not result.passed
        assert any("score" in f.lower() for f in result.failures)
