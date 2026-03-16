"""Compare API — structured comparison of two optimization algorithms."""

import json
import logging
from pathlib import Path

from flask import Blueprint, jsonify, request

from pipeline.llm_client import generate_with_retry, get_provider

logger = logging.getLogger(__name__)

compare_bp = Blueprint("compare", __name__)

CONTENT_DIR = Path("content/techniques")

COMPARE_SCHEMA = {
    "type": "object",
    "required": ["algorithm_a", "algorithm_b", "pros_a", "pros_b", "cons_a", "cons_b", "best_for_a", "best_for_b", "summary"],
    "properties": {
        "algorithm_a": {"type": "string", "minLength": 1},
        "algorithm_b": {"type": "string", "minLength": 1},
        "pros_a": {"type": "array", "items": {"type": "string"}, "minItems": 1},
        "pros_b": {"type": "array", "items": {"type": "string"}, "minItems": 1},
        "cons_a": {"type": "array", "items": {"type": "string"}, "minItems": 1},
        "cons_b": {"type": "array", "items": {"type": "string"}, "minItems": 1},
        "best_for_a": {"type": "string", "minLength": 1},
        "best_for_b": {"type": "string", "minLength": 1},
        "summary": {"type": "string", "minLength": 1},
    },
    "additionalProperties": False,
}


def _load_technique_artifacts(slug: str) -> dict | None:
    """Load all JSON artifacts for a technique slug."""
    technique_dir = CONTENT_DIR / slug
    if not technique_dir.is_dir():
        return None
    artifacts = {}
    for json_file in technique_dir.glob("*.json"):
        artifacts[json_file.stem] = json.loads(json_file.read_text())
    return artifacts if artifacts else None


def _get_available_slugs() -> list[str]:
    """Return all technique slugs that have content."""
    if not CONTENT_DIR.exists():
        return []
    return sorted(
        d.name for d in CONTENT_DIR.iterdir()
        if d.is_dir() and any(d.glob("*.json"))
    )


@compare_bp.route("/api/compare", methods=["POST"])
def compare():
    """Compare two algorithms.

    Expects JSON: {"slug_a": "...", "slug_b": "..."}
    Returns JSON: structured comparison object.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSON body is required."}), 400

    slug_a = data.get("slug_a", "").strip()
    slug_b = data.get("slug_b", "").strip()

    if not slug_a or not slug_b:
        return jsonify({"error": "Both 'slug_a' and 'slug_b' are required."}), 400

    if slug_a == slug_b:
        return jsonify({"error": "Please select two different algorithms."}), 400

    artifacts_a = _load_technique_artifacts(slug_a)
    artifacts_b = _load_technique_artifacts(slug_b)

    if not artifacts_a:
        return jsonify({"error": f"Algorithm '{slug_a}' not found."}), 404
    if not artifacts_b:
        return jsonify({"error": f"Algorithm '{slug_b}' not found."}), 404

    system_prompt = (
        "You are an expert in optimization algorithms. "
        "Compare the two algorithms based on the provided artifacts. "
        "Return valid JSON with pros, cons, and best-use-case for each algorithm, "
        "plus a brief summary of when to prefer one over the other."
    )

    user_prompt = (
        f"## Algorithm A: {slug_a}\n```json\n{json.dumps(artifacts_a, indent=2, default=str)[:4000]}\n```\n\n"
        f"## Algorithm B: {slug_b}\n```json\n{json.dumps(artifacts_b, indent=2, default=str)[:4000]}\n```\n\n"
        "Provide a structured comparison."
    )

    try:
        provider = get_provider("compare")
        result = generate_with_retry(
            provider=provider,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=COMPARE_SCHEMA,
        )
        return jsonify(result)
    except Exception:
        logger.exception("Compare request failed")
        return jsonify({"error": "Failed to generate comparison. Please try again."}), 500


@compare_bp.route("/api/compare/slugs", methods=["GET"])
def list_slugs():
    """Return all available technique slugs for the comparison dropdowns."""
    return jsonify(_get_available_slugs())
