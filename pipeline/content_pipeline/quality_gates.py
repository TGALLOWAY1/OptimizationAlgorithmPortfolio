"""Quality gates evaluated between pipeline stages.

A gate inspects the dict payload a stage produced (and optionally the
previous-outputs context) and returns a :class:`QualityGateResult`. The
orchestrator uses ``passed`` to decide whether to advance, retry the stage with
the gate's failures fed back as feedback, or fail the pipeline.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

PLACEHOLDER_PATTERNS = (
    re.compile(r"\bTODO\b"),
    re.compile(r"\bTBD\b"),
    re.compile(r"\[(insert|placeholder|example needed|fill in)[^\]]*\]", re.IGNORECASE),
)


@dataclass(frozen=True)
class QualityGateResult:
    """Outcome of a single gate evaluation."""

    gate_id: str
    stage_id: str
    passed: bool
    failures: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


class QualityGate(ABC):
    """Abstract base class for content-pipeline quality gates."""

    id: str
    description: str
    stage_id: str

    def evaluate(
        self,
        payload: dict[str, Any],
        previous_outputs: dict[str, dict[str, Any]] | None = None,
    ) -> QualityGateResult:
        """Run the gate and produce a structured result.

        ``previous_outputs`` is the orchestrator's view of every prior stage
        output keyed by stage id. Most gates ignore it; gates that need
        cross-stage context (e.g. :class:`DraftGate` checking outline coverage)
        read from it.
        """
        failures, warnings = self._check(payload, previous_outputs or {})
        return QualityGateResult(
            gate_id=self.id,
            stage_id=self.stage_id,
            passed=not failures,
            failures=tuple(failures),
            warnings=tuple(warnings),
        )

    @abstractmethod
    def _check(
        self,
        payload: dict[str, Any],
        previous_outputs: dict[str, dict[str, Any]],
    ) -> tuple[list[str], list[str]]:  # pragma: no cover - abstract
        """Return ``(failures, warnings)``."""


class IntakeGate(QualityGate):
    id = "intake_gate"
    description = "ContentBrief must name an audience, content_type, and goals."
    stage_id = "intake"

    def _check(
        self,
        payload: dict[str, Any],
        previous_outputs: dict[str, dict[str, Any]],
    ) -> tuple[list[str], list[str]]:
        failures: list[str] = []
        warnings: list[str] = []
        if not (payload.get("audience") or "").strip():
            failures.append("Brief is missing audience")
        if not (payload.get("content_type") or "").strip():
            failures.append("Brief is missing content_type")
        goals = payload.get("goals") or []
        if not goals:
            failures.append("Brief has no goals")
        if not (payload.get("topic") or "").strip():
            failures.append("Brief is missing topic")
        return failures, warnings


class OutlineGate(QualityGate):
    id = "outline_gate"
    description = (
        "Outline must have a title, a hook, at least three sections, "
        "and at least one technical-explanation section."
    )
    stage_id = "outline"

    def _check(
        self,
        payload: dict[str, Any],
        previous_outputs: dict[str, dict[str, Any]],
    ) -> tuple[list[str], list[str]]:
        failures: list[str] = []
        warnings: list[str] = []
        if not (payload.get("title") or "").strip():
            failures.append("Outline is missing a title")
        if not (payload.get("hook") or "").strip():
            failures.append("Outline is missing a hook")
        sections = payload.get("sections") or []
        if len(sections) < 3:
            failures.append(f"Outline has only {len(sections)} sections (minimum 3)")
        types = {s.get("section_type") for s in sections}
        if not (types & {"explanation", "deep_dive"}):
            failures.append("Outline has no technical explanation/deep_dive section")
        if sections and sections[0].get("section_type") != "intro":
            warnings.append("First section is not 'intro'")
        return failures, warnings


class DraftGate(QualityGate):
    id = "draft_gate"
    description = (
        "Draft must meet a minimum length, cover most outline sections, "
        "and contain no placeholder markers."
    )
    stage_id = "draft"

    MIN_WORDS = 300
    COVERAGE_RATIO = 0.8

    def _check(
        self,
        payload: dict[str, Any],
        previous_outputs: dict[str, dict[str, Any]],
    ) -> tuple[list[str], list[str]]:
        failures: list[str] = []
        warnings: list[str] = []
        word_count = int(payload.get("word_count") or 0)
        if word_count < self.MIN_WORDS:
            failures.append(
                f"Draft is too short ({word_count} words, minimum {self.MIN_WORDS})"
            )
        markdown = payload.get("markdown") or ""
        for pattern in PLACEHOLDER_PATTERNS:
            if pattern.search(markdown):
                failures.append(
                    f"Draft contains placeholder text matching /{pattern.pattern}/"
                )
                break
        sections_covered = {s.lower() for s in (payload.get("sections_covered") or [])}
        outline = previous_outputs.get("outline") or {}
        outline_sections = {
            (s.get("heading") or "").lower()
            for s in (outline.get("sections") or [])
            if s.get("heading")
        }
        if outline_sections:
            covered = sections_covered & outline_sections
            ratio = len(covered) / len(outline_sections)
            if ratio < self.COVERAGE_RATIO:
                missing = sorted(outline_sections - covered)
                failures.append(
                    "Draft covers only "
                    f"{int(ratio * 100)}% of outline sections; "
                    f"missing: {missing}"
                )
        return failures, warnings


class TechnicalReviewGate(QualityGate):
    id = "tech_review_gate"
    description = "No critical-severity issues unresolved."
    stage_id = "technical_review"

    def _check(
        self,
        payload: dict[str, Any],
        previous_outputs: dict[str, dict[str, Any]],
    ) -> tuple[list[str], list[str]]:
        failures: list[str] = []
        warnings: list[str] = []
        blocking = int(payload.get("blocking_issues_count") or 0)
        critical_issues = [
            issue
            for issue in (payload.get("issues") or [])
            if issue.get("severity") == "critical"
        ]
        if critical_issues or blocking > 0:
            failures.append(
                f"{max(blocking, len(critical_issues))} critical technical issue(s) reported"
            )
        major = [i for i in (payload.get("issues") or []) if i.get("severity") == "major"]
        if len(major) > 5:
            warnings.append(f"{len(major)} major issues — consider another revision pass")
        return failures, warnings


class FinalQAGate(QualityGate):
    id = "final_qa_gate"
    description = "Publishing QA must mark the package publishable."
    stage_id = "publishing_qa"

    def _check(
        self,
        payload: dict[str, Any],
        previous_outputs: dict[str, dict[str, Any]],
    ) -> tuple[list[str], list[str]]:
        failures: list[str] = []
        warnings: list[str] = []
        if not payload.get("publishable", False):
            blockers = payload.get("blocking_issues") or []
            if blockers:
                failures.append(f"Publishing QA blocked: {'; '.join(blockers)}")
            else:
                failures.append("Publishing QA marked content not publishable")
        score = payload.get("qa_score")
        if isinstance(score, int) and score < 60:
            failures.append(f"QA score {score} below threshold 60")
        return failures, warnings
