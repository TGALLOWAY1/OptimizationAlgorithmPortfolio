"""Tests for the quality report rendering in publish.py."""

import json

from jinja2 import Environment, FileSystemLoader

from pipeline.publish import _publish_quality_report, TEMPLATES_DIR, md_to_html


class TestPublishQualityReport:
    def test_renders_quality_report(self, tmp_path):
        """Quality report should render from evaluation metrics."""
        from pipeline import publish

        original_site = publish.SITE_DIR
        original_full = publish.EVALUATION_LATEST_FULL_PATH
        original_partial = publish.EVALUATION_LATEST_PARTIAL_PATH
        publish.SITE_DIR = tmp_path
        publish.EVALUATION_LATEST_FULL_PATH = tmp_path / "latest-full.json"
        publish.EVALUATION_LATEST_PARTIAL_PATH = tmp_path / "latest-partial.json"

        metrics = {
            "evaluated_at": "2026-03-22T12:00:00+00:00",
            "scope": {
                "type": "full",
                "technique_count": 1,
                "expected_technique_count": 1,
            },
            "summary": {
                "passed": 2,
                "failed": 0,
                "total": 2,
            },
            "techniques": {
                "cma-es": {
                    "technique_name": "CMA-ES",
                    "artifacts": {
                        "overview": {"status": "passed", "attempts": 1},
                        "math_deep_dive": {"status": "passed", "attempts": 2},
                    }
                }
            }
        }

        publish.EVALUATION_LATEST_FULL_PATH.write_text(json.dumps(metrics))

        env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True
        )
        env.filters["markdown"] = md_to_html

        try:
            _publish_quality_report(env)
            report_path = tmp_path / "quality-report.html"
            assert report_path.exists()
            html = report_path.read_text()
            assert "Quality Report" in html
            assert "CMA-ES" in html
            assert "Passed" in html
            assert "Full evaluation" in html
        finally:
            publish.SITE_DIR = original_site
            publish.EVALUATION_LATEST_FULL_PATH = original_full
            publish.EVALUATION_LATEST_PARTIAL_PATH = original_partial

    def test_no_metrics_skips_report(self, tmp_path):
        """Should skip quality report when no metrics file exists."""
        from pipeline import publish

        original_site = publish.SITE_DIR
        original_full = publish.EVALUATION_LATEST_FULL_PATH
        original_partial = publish.EVALUATION_LATEST_PARTIAL_PATH
        publish.SITE_DIR = tmp_path
        publish.EVALUATION_LATEST_FULL_PATH = tmp_path / "latest-full.json"
        publish.EVALUATION_LATEST_PARTIAL_PATH = tmp_path / "latest-partial.json"

        env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True
        )

        # No metrics file exists, should not crash
        _publish_quality_report(env)
        report_path = tmp_path / "quality-report.html"
        assert not report_path.exists()

        publish.SITE_DIR = original_site
        publish.EVALUATION_LATEST_FULL_PATH = original_full
        publish.EVALUATION_LATEST_PARTIAL_PATH = original_partial

    def test_falls_back_to_partial_report(self, tmp_path):
        """Should render partial evaluations when no full report exists yet."""
        from pipeline import publish

        original_site = publish.SITE_DIR
        original_full = publish.EVALUATION_LATEST_FULL_PATH
        original_partial = publish.EVALUATION_LATEST_PARTIAL_PATH
        publish.SITE_DIR = tmp_path
        publish.EVALUATION_LATEST_FULL_PATH = tmp_path / "latest-full.json"
        publish.EVALUATION_LATEST_PARTIAL_PATH = tmp_path / "latest-partial.json"

        metrics = {
            "evaluated_at": "2026-03-22T12:00:00+00:00",
            "scope": {
                "type": "partial",
                "technique_count": 1,
                "expected_technique_count": 8,
            },
            "summary": {
                "passed": 1,
                "failed": 0,
                "total": 1,
            },
            "techniques": {
                "gradient-descent": {
                    "technique_name": "Gradient Descent",
                    "artifacts": {
                        "overview": {"status": "passed", "attempts": 1},
                    },
                }
            },
        }
        publish.EVALUATION_LATEST_PARTIAL_PATH.write_text(json.dumps(metrics))

        env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True
        )
        env.filters["markdown"] = md_to_html

        try:
            _publish_quality_report(env)
            html = (tmp_path / "quality-report.html").read_text()
            assert "Partial evaluation" in html
            assert "Gradient Descent" in html
        finally:
            publish.SITE_DIR = original_site
            publish.EVALUATION_LATEST_FULL_PATH = original_full
            publish.EVALUATION_LATEST_PARTIAL_PATH = original_partial
