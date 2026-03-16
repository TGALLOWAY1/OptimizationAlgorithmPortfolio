"""JSON schema validation stage for the evaluation pipeline."""

import json
import logging
from typing import Any

import jsonschema

from pipeline.schemas import SCHEMAS

logger = logging.getLogger(__name__)


def validate_schema(artifact_type: str, data: dict[str, Any]) -> dict[str, Any]:
    """Validate an artifact against its JSON schema.

    Args:
        artifact_type: The artifact type (e.g., "overview", "math_deep_dive").
        data: The artifact data to validate.

    Returns:
        A dict with keys: passed (bool), errors (list[str]).
    """
    schema = SCHEMAS.get(artifact_type)
    if schema is None:
        return {
            "passed": False,
            "errors": [f"No schema defined for artifact type: {artifact_type}"],
        }

    errors: list[str] = []
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as e:
        errors.append(e.message)
    except jsonschema.SchemaError as e:
        errors.append(f"Invalid schema: {e.message}")

    return {"passed": len(errors) == 0, "errors": errors}
