"""Unified Flask application registering all API blueprints and serving the static site."""

import os

from flask import Flask, send_from_directory, abort
from flask_cors import CORS

from api.compare import compare_bp
from api.math_tutor import math_tutor_bp
from api.study_plan import study_plan_bp
from api.adapt_code import adapt_code_bp
from pipeline.paths import SITE_DIR
from pipeline.runtime import ensure_supported_python


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

    # Serve static images from site/images/
    @app.route("/images/<path:filepath>")
    def serve_images(filepath):
        return send_from_directory(SITE_DIR / "images", filepath)

    # Serve the homepage
    @app.route("/")
    def serve_index():
        return send_from_directory(SITE_DIR, "index.html")

    # Serve any .html page from site/
    @app.route("/<path:page>")
    def serve_page(page):
        if page.endswith(".html"):
            file_path = SITE_DIR / page
            if file_path.exists():
                return send_from_directory(SITE_DIR, page)
        abort(404)

    return app


if __name__ == "__main__":
    ensure_supported_python()
    port = int(os.environ.get("PORT", 5000))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=True)
