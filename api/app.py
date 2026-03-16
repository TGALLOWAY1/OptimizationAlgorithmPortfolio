"""Unified Flask application registering all API blueprints."""

import os

from flask import Flask
from flask_cors import CORS

from api.compare import compare_bp
from api.math_tutor import math_tutor_bp
from api.study_plan import study_plan_bp
from api.adapt_code import adapt_code_bp


def create_app() -> Flask:
    """Application factory — creates and configures the Flask app."""
    app = Flask(__name__)
    CORS(app)

    # Register all API blueprints
    app.register_blueprint(compare_bp)
    app.register_blueprint(math_tutor_bp)
    app.register_blueprint(study_plan_bp)
    app.register_blueprint(adapt_code_bp)

    # Also register the legacy recommender blueprint
    from pipeline.recommender_api import app as recommender_app

    # Re-register the recommend route from the existing module
    @app.route("/api/recommend", methods=["POST"])
    def recommend_proxy():
        with recommender_app.test_request_context(
            "/api/recommend",
            method="POST",
            json=__import__("flask").request.get_json(silent=True),
        ):
            return recommender_app.full_dispatch_request()

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=True)
