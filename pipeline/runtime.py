"""Runtime environment guards for supported execution contexts."""

from __future__ import annotations

import sys
from typing import Sequence

MINIMUM_PYTHON = (3, 11)


def ensure_supported_python(
    version_info: Sequence[int] | None = None,
) -> None:
    """Raise a readable error when running under an unsupported interpreter."""
    current = tuple(version_info or sys.version_info[:3])
    if current < MINIMUM_PYTHON:
        raise RuntimeError(
            "Optimization Algorithm Portfolio requires Python 3.11+ "
            f"(detected {current[0]}.{current[1]}.{current[2]})."
        )
