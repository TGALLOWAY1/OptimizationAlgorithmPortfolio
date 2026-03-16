"""Math Tutor API — explains highlighted math equations using LLM."""

import json
import logging

from flask import Blueprint, jsonify, request

from pipeline.llm_client import generate_with_retry, get_provider

logger = logging.getLogger(__name__)

math_tutor_bp = Blueprint("math_tutor", __name__)

MATH_TUTOR_SCHEMA = {
    "type": "object",
    "required": ["explanation"],
    "properties": {
        "explanation": {"type": "string", "minLength": 1},
    },
    "additionalProperties": False,
}


@math_tutor_bp.route("/api/math_tutor", methods=["POST"])
def math_tutor():
    """Explain a highlighted math equation bounded by its surrounding context.

    Expects JSON: {"selected_text": "...", "context": "..."}
    Returns JSON: {"explanation": "LaTeX-formatted Markdown explanation"}
    """
    data = request.get_json(silent=True)
    if not data or not data.get("selected_text", "").strip():
        return jsonify({"error": "A non-empty 'selected_text' field is required."}), 400

    selected_text = data["selected_text"].strip()
    context = data.get("context", "").strip()

    if len(selected_text) > 2000:
        return jsonify({"error": "Selected text must be 2000 characters or fewer."}), 400
    if len(context) > 5000:
        return jsonify({"error": "Context must be 5000 characters or fewer."}), 400

    system_prompt = (
        "You are a patient math tutor specializing in optimization algorithms. "
        "The user has highlighted a piece of text from an educational article. "
        "Explain the highlighted text clearly and thoroughly. "
        "Use LaTeX notation (inline: $...$, display: $$...$$) for all math. "
        "IMPORTANT: Your explanation must be strictly bounded by the provided context paragraph. "
        "Do not introduce concepts or equations not present in the context. "
        "Return valid JSON with a single 'explanation' field containing Markdown."
    )

    user_prompt = (
        f"## Highlighted Text\n{selected_text}\n\n"
        f"## Surrounding Context\n{context}\n\n"
        "Explain the highlighted text step by step."
    )

    try:
        provider = get_provider("math_tutor")
        result = generate_with_retry(
            provider=provider,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=MATH_TUTOR_SCHEMA,
        )
        return jsonify(result)
    except Exception:
        logger.exception("Math tutor request failed")
        return jsonify({"error": "Failed to generate explanation. Please try again."}), 500
