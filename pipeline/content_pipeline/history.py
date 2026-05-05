"""Helpers for browsing prior pipeline runs on disk."""

from __future__ import annotations

from pathlib import Path

from pipeline.content_pipeline.state import (
    ContentPipelineRun,
    RUN_FILENAME,
    load_run,
)


def list_runs(root: Path) -> list[str]:
    """Return the run ids under ``root`` that have a ``run.json``, newest first."""
    if not root.exists():
        return []
    candidates = []
    for child in root.iterdir():
        if child.is_dir() and (child / RUN_FILENAME).exists():
            candidates.append(child.name)
    return sorted(candidates, reverse=True)


def load_latest(root: Path) -> ContentPipelineRun | None:
    """Return the most recent run under ``root``, or ``None`` if none exist."""
    ids = list_runs(root)
    if not ids:
        return None
    return load_run(ids[0], root)
