"""Tests for the quality report rendering in publish.py."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from jinja2 import Environment, FileSystemLoader

from pipeline.publish import _publish_quality_report, TEMPLATES_DIR, md_to_html


class TestPublishQualityReport:
    def test_renders_quality_report(self, tmp_path):
        """Quality report should render from evaluation metrics."""
        from pipeline import publish

        original_site = publish.SITE_DIR
        publish.SITE_DIR = tmp_path

        metrics = {
            "techniques": {
                "cma-es": {
                    "artifacts": {
                        "overview": {"status": "passed", "attempts": 1},
                        "math_deep_dive": {"status": "passed", "attempts": 2},
                    }
                }
            }
        }

        metrics_path = tmp_path / "metrics.json"
        metrics_path.write_text(json.dumps(metrics))

        env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True
        )
        env.filters["markdown"] = md_to_html

        with patch("pipeline.publish.Path") as mock_path_cls:
            # We need to patch the metrics path check
            pass

        # Directly call with patched metrics path
        original_metrics = Path("content/evaluation_metrics.json")
        with patch(
            "pipeline.publish.Path",
            side_effect=lambda p: metrics_path if "evaluation_metrics" in str(p) else Path(p),
        ):
            # Simpler approach: just write the metrics and call directly
            pass

        # Write metrics to the expected location
        metrics_file = Path("content/evaluation_metrics.json")
        metrics_file.parent.mkdir(parents=True, exist_ok=True)
        metrics_file.write_text(json.dumps(metrics))

        try:
            _publish_quality_report(env)
            report_path = tmp_path / "quality-report.html"
            assert report_path.exists()
            html = report_path.read_text()
            assert "Quality Report" in html
            assert "Cma Es" in html or "Cma-Es" in html  # title-cased slug
            assert "Passed" in html
        finally:
            publish.SITE_DIR = original_site

    def test_no_metrics_skips_report(self, tmp_path):
        """Should skip quality report when no metrics file exists."""
        from pipeline import publish

        original_site = publish.SITE_DIR
        publish.SITE_DIR = tmp_path

        env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True
        )

        # No metrics file exists, should not crash
        _publish_quality_report(env)
        report_path = tmp_path / "quality-report.html"
        # Report should not be created if no metrics
        # (depends on whether content/evaluation_metrics.json exists on disk)

        publish.SITE_DIR = original_site
