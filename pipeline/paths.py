"""Shared filesystem paths for tracked inputs and generated outputs."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PIPELINE_DIR = PROJECT_ROOT / "pipeline"
PROMPTS_DIR = PIPELINE_DIR / "prompts"
TEMPLATES_DIR = PIPELINE_DIR / "templates"
SOURCE_CONTENT_DIR = PROJECT_ROOT / "content"
REFERENCE_DIR = SOURCE_CONTENT_DIR / "reference"
RUBRICS_PATH = SOURCE_CONTENT_DIR / "rubrics.json"
SITE_DIR = PROJECT_ROOT / "site"

GENERATED_ROOT_ENV = "OPTIMIZATION_PORTFOLIO_GENERATED_ROOT"


def _resolve_generated_root() -> Path:
    raw = os.environ.get(GENERATED_ROOT_ENV)
    if not raw:
        return PROJECT_ROOT / "generated"

    root = Path(raw).expanduser()
    if not root.is_absolute():
        root = PROJECT_ROOT / root
    return root.resolve()


GENERATED_ROOT = _resolve_generated_root()
GENERATED_TECHNIQUES_DIR = GENERATED_ROOT / "techniques"
GENERATED_EVALUATIONS_DIR = GENERATED_ROOT / "evaluations"
GENERATED_LOGS_DIR = GENERATED_ROOT / "logs"
USE_CASE_MATRIX_PATH = GENERATED_ROOT / "use_case_matrix.json"
EVALUATION_LATEST_FULL_PATH = GENERATED_ROOT / "evaluation_latest_full.json"
EVALUATION_LATEST_PARTIAL_PATH = GENERATED_ROOT / "evaluation_latest_partial.json"


def technique_dir(slug: str, base_dir: Path | None = None) -> Path:
    """Return the directory that stores generated artifacts for a technique."""
    return (base_dir or GENERATED_TECHNIQUES_DIR) / slug
