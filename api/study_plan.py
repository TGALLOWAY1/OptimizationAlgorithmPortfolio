"""Study Plan API — generates a personalized learning roadmap."""

import json
import logging
from pathlib import Path

from flask import Blueprint, jsonify, request

from pipeline.llm_client import generate_with_retry, get_provider

logger = logging.getLogger(__name__)

study_plan_bp = Blueprint("study_plan", __name__)

CONTENT_DIR = Path("content/techniques")

STUDY_PLAN_SCHEMA = {
    "type": "object",
    "required": ["roadmap", "rationale"],
    "properties": {
        "roadmap": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["slug", "title", "reason", "order"],
                "properties": {
                    "slug": {"type": "string", "minLength": 1},
                    "title": {"type": "string", "minLength": 1},
                    "reason": {"type": "string", "minLength": 1},
                    "order": {"type": "integer", "minimum": 1},
                },
                "additionalProperties": False,
            },
            "minItems": 1,
        },
        "rationale": {"type": "string", "minLength": 1},
    },
    "additionalProperties": False,
}


def _get_available_techniques() -> list[dict]:
    """Return summary info for all available techniques."""
    if not CONTENT_DIR.exists():
        return []
    techniques = []
    for d in sorted(CONTENT_DIR.iterdir()):
        if not d.is_dir():
            continue
        plan_path = d / "plan.json"
        overview_path = d / "overview.json"
        info = {"slug": d.name}
        if plan_path.exists():
            plan = json.loads(plan_path.read_text())
            info["name"] = plan.get("technique_name", d.name)
            info["problem_type"] = plan.get("problem_type", "")
        if overview_path.exists():
            overview = json.loads(overview_path.read_text())
            info["summary"] = overview.get("summary", "")
        techniques.append(info)
    return techniques


@study_plan_bp.route("/api/study_plan", methods=["POST"])
def study_plan():
    """Generate a personalized study plan.

    Expects JSON: {"background": "...", "goals": "..."}
    Returns JSON: {"roadmap": [...], "rationale": "..."}
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSON body is required."}), 400

    background = data.get("background", "").strip()
    goals = data.get("goals", "").strip()

    if not background or not goals:
        return jsonify({"error": "Both 'background' and 'goals' fields are required."}), 400

    if len(background) > 2000 or len(goals) > 2000:
        return jsonify({"error": "Fields must be 2000 characters or fewer."}), 400

    available = _get_available_techniques()
    if not available:
        return jsonify({"error": "No technique content is available yet."}), 404

    system_prompt = (
        "You are an expert optimization curriculum designer. "
        "Given a student's background and learning goals, create an ordered learning roadmap "
        "from the available techniques. The roadmap should progress from foundational to advanced. "
        "Only include techniques from the available list. "
        "Return valid JSON matching the schema."
    )

    user_prompt = (
        f"## Student Background\n{background}\n\n"
        f"## Learning Goals\n{goals}\n\n"
        f"## Available Techniques\n```json\n{json.dumps(available, indent=2)}\n```\n\n"
        "Create an ordered study roadmap."
    )

    try:
        provider = get_provider("study_plan")
        result = generate_with_retry(
            provider=provider,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=STUDY_PLAN_SCHEMA,
        )
        return jsonify(result)
    except Exception:
        logger.exception("Study plan generation failed")
        return jsonify({"error": "Failed to generate study plan. Please try again."}), 500
