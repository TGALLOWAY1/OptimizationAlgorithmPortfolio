"""Pipeline and stage state types, plus on-disk persistence."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field, fields, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

RUN_FILENAME = "run.json"


class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"
    NEEDS_REVISION = "needs_revision"


class PipelineStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_FOR_REVIEW = "waiting_for_review"
    FAILED = "failed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


def utc_now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


@dataclass
class StageRun:
    """Mutable record of one stage's execution."""

    stage_id: str
    name: str
    status: StageStatus = StageStatus.PENDING
    started_at: str | None = None
    finished_at: str | None = None
    retries: int = 0
    error: str | None = None
    output_path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ContentPipelineRun:
    """Mutable top-level run record persisted to ``outputs/runs/<run_id>/run.json``."""

    run_id: str
    status: PipelineStatus
    input: dict[str, Any]
    stages: list[StageRun] = field(default_factory=list)
    gate_results: list[dict[str, Any]] = field(default_factory=list)
    artifacts: dict[str, str] = field(default_factory=dict)
    started_at: str = field(default_factory=utc_now_iso)
    finished_at: str | None = None

    def stage(self, stage_id: str) -> StageRun | None:
        for stage in self.stages:
            if stage.stage_id == stage_id:
                return stage
        return None


def _to_jsonable(obj: Any) -> Any:
    """Recursively convert dataclasses, enums, datetimes, and Paths to JSON-safe types."""
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, Path):
        return str(obj)
    if is_dataclass(obj) and not isinstance(obj, type):
        return {f.name: _to_jsonable(getattr(obj, f.name)) for f in fields(obj)}
    if isinstance(obj, dict):
        return {str(k): _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_jsonable(v) for v in obj]
    return obj


def save_run(run: ContentPipelineRun, output_dir: Path) -> Path:
    """Atomically persist a run to ``<output_dir>/run.json``."""
    output_dir.mkdir(parents=True, exist_ok=True)
    final_path = output_dir / RUN_FILENAME
    tmp_path = final_path.with_suffix(".json.tmp")
    payload = _to_jsonable(run)
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=False))
    os.replace(tmp_path, final_path)
    return final_path


def load_run(run_id: str, root: Path) -> ContentPipelineRun:
    """Load a previously persisted run from ``<root>/<run_id>/run.json``."""
    run_path = root / run_id / RUN_FILENAME
    if not run_path.exists():
        raise FileNotFoundError(f"No run.json at {run_path}")
    raw = json.loads(run_path.read_text())
    stages = [
        StageRun(
            stage_id=s["stage_id"],
            name=s["name"],
            status=StageStatus(s["status"]),
            started_at=s.get("started_at"),
            finished_at=s.get("finished_at"),
            retries=s.get("retries", 0),
            error=s.get("error"),
            output_path=s.get("output_path"),
            metadata=s.get("metadata", {}) or {},
        )
        for s in raw.get("stages", [])
    ]
    return ContentPipelineRun(
        run_id=raw["run_id"],
        status=PipelineStatus(raw["status"]),
        input=raw.get("input", {}),
        stages=stages,
        gate_results=raw.get("gate_results", []),
        artifacts=raw.get("artifacts", {}),
        started_at=raw.get("started_at", utc_now_iso()),
        finished_at=raw.get("finished_at"),
    )
