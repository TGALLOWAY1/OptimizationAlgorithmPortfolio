"""Adapt Code API — adapts source code to a different framework using LLM."""

import json
import logging

from flask import Blueprint, jsonify, request

from pipeline.llm_client import generate_with_retry, get_provider

logger = logging.getLogger(__name__)

adapt_code_bp = Blueprint("adapt_code", __name__)

ADAPT_CODE_SCHEMA = {
    "type": "object",
    "required": ["adapted_code", "notes"],
    "properties": {
        "adapted_code": {"type": "string", "minLength": 1},
        "notes": {"type": "string"},
    },
    "additionalProperties": False,
}


@adapt_code_bp.route("/api/adapt_code", methods=["POST"])
def adapt_code():
    """Adapt source code to a target framework.

    Expects JSON: {"source_code": "...", "target_framework": "...", "instructions": "..."}
    Returns JSON: {"adapted_code": "...", "notes": "..."}
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSON body is required."}), 400

    source_code = data.get("source_code", "").strip()
    target_framework = data.get("target_framework", "").strip()

    if not source_code:
        return jsonify({"error": "A non-empty 'source_code' field is required."}), 400
    if not target_framework:
        return jsonify({"error": "A non-empty 'target_framework' field is required."}), 400

    if len(source_code) > 10000:
        return jsonify({"error": "Source code must be 10000 characters or fewer."}), 400

    instructions = data.get("instructions", "").strip()

    system_prompt = (
        "You are an expert software engineer. "
        "Adapt the given algorithm implementation to the target framework. "
        "Preserve the algorithm's logic and correctness. "
        "Include all necessary imports and a brief usage example. "
        "Return valid JSON with 'adapted_code' and 'notes' fields."
    )

    user_prompt = (
        f"## Source Code\n```\n{source_code}\n```\n\n"
        f"## Target Framework\n{target_framework}\n\n"
    )
    if instructions:
        user_prompt += f"## Additional Instructions\n{instructions}\n\n"
    user_prompt += "Adapt the code."

    try:
        provider = get_provider("adapt_code")
        result = generate_with_retry(
            provider=provider,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=ADAPT_CODE_SCHEMA,
        )
        return jsonify(result)
    except Exception:
        logger.exception("Code adaptation failed")
        return jsonify({"error": "Failed to adapt code. Please try again."}), 500
