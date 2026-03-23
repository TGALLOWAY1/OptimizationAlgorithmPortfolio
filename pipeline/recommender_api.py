"""Algorithm Recommender API — lightweight Flask endpoint for LLM-powered recommendations."""

import json
import logging
import os

from flask import Flask, jsonify, request
from flask_cors import CORS

from pipeline.llm_client import get_provider, generate_with_retry
from pipeline.paths import PROMPTS_DIR, USE_CASE_MATRIX_PATH

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

RECOMMENDER_PROMPT_PATH = PROMPTS_DIR / "recommender_prompt.md"

RECOMMENDATION_SCHEMA = {
    "type": "object",
    "properties": {
        "recommendations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "algorithm": {"type": "string"},
                    "justification": {"type": "string"},
                    "confidence_score": {"type": "integer", "minimum": 1, "maximum": 100},
                    "url_slug": {"type": "string"},
                },
                "required": ["algorithm", "justification", "confidence_score", "url_slug"],
                "additionalProperties": False,
            },
            "minItems": 2,
            "maxItems": 3,
        }
    },
    "required": ["recommendations"],
    "additionalProperties": False,
}


def _load_use_case_matrix() -> dict:
    """Load the use-case matrix JSON, returning empty dict if not found."""
    if USE_CASE_MATRIX_PATH.exists():
        return json.loads(USE_CASE_MATRIX_PATH.read_text())
    logger.warning("use_case_matrix.json not found at %s", USE_CASE_MATRIX_PATH)
    return {}


def _load_prompt_template() -> str:
    """Load the recommender prompt template."""
    return RECOMMENDER_PROMPT_PATH.read_text()


def get_recommendations(query: str) -> list[dict]:
    """Send user query + use-case matrix to the LLM and return recommendations."""
    matrix = _load_use_case_matrix()
    prompt_template = _load_prompt_template()

    system_prompt = prompt_template.replace("{{use_case_matrix}}", json.dumps(matrix, indent=2))
    user_prompt = query

    provider = get_provider("recommender")
    result = generate_with_retry(
        provider=provider,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        schema=RECOMMENDATION_SCHEMA,
    )
    return result["recommendations"]


@app.route("/api/recommend", methods=["POST"])
def recommend():
    """Handle recommendation requests.

    Expects JSON: {"query": "user's optimization problem description"}
    Returns JSON: [{"algorithm": ..., "justification": ..., "confidence_score": ..., "url_slug": ...}]
    """
    data = request.get_json(silent=True)
    if not data or not data.get("query", "").strip():
        return jsonify({"error": "A non-empty 'query' field is required."}), 400

    query = data["query"].strip()
    if len(query) > 2000:
        return jsonify({"error": "Query must be 2000 characters or fewer."}), 400

    try:
        recommendations = get_recommendations(query)
        return jsonify(recommendations)
    except Exception as e:
        logger.exception("Recommendation failed")
        return jsonify({"error": "Failed to generate recommendations. Please try again."}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
