"""Tests for static site publishing and markdown rendering."""

import json

from pipeline.publish import (
    _balance_bold_italic,
    _close_unclosed_tags,
    md_to_html,
)


class TestMarkdownRendering:
    def test_preserves_latex_commands(self):
        html = md_to_html(r"The gradient is $\nabla f(x)$ and $x \neq y$.")

        assert r"\nabla f(x)" in html
        assert r"\neq y" in html

    def test_renders_bullet_lists_after_colon(self):
        html = md_to_html("Parameters:\n- First item\n- Second item")

        assert "<li>First item</li>" in html
        assert "<li>Second item</li>" in html

    def test_unbalanced_bold_does_not_bleed(self):
        """An unclosed ** must not make the next paragraph bold."""
        text = "This is **broken bold\n\nThis paragraph should be normal."
        html = md_to_html(text)
        # The second paragraph should NOT be wrapped in <strong>
        assert "<strong>This paragraph" not in html

    def test_unbalanced_italic_does_not_bleed(self):
        text = "Here is *broken italic\n\nNormal text follows."
        html = md_to_html(text)
        assert "<em>Normal text" not in html

    def test_balanced_bold_preserved(self):
        text = "This is **properly bold** text."
        html = md_to_html(text)
        assert "<strong>properly bold</strong>" in html

    def test_close_unclosed_strong_tags(self):
        html = "<p><strong>open bold</p><p>next paragraph</p>"
        fixed = _close_unclosed_tags(html)
        assert fixed.count("</strong>") == 1

    def test_balance_bold_italic_removes_trailing_stars(self):
        text = "Some **unmatched bold text"
        result = _balance_bold_italic(text)
        # The unmatched ** should be removed
        assert result.count("**") == 0


class TestPublishLifecycle:
    def test_publish_rebuilds_site_from_clean_directory(self, tmp_path):
        from pipeline import publish

        original_site = publish.SITE_DIR
        original_techniques = publish.TECHNIQUES_DIR

        site_dir = tmp_path / "site"
        techniques_dir = tmp_path / "generated" / "techniques"
        technique_dir = techniques_dir / "gradient-descent"
        technique_dir.mkdir(parents=True)

        (site_dir / "stale.html").parent.mkdir(parents=True)
        (site_dir / "stale.html").write_text("stale")

        (technique_dir / "manifest.json").write_text(
            json.dumps(
                {
                    "artifact_version": "2",
                    "updated_at": "2026-03-22T00:00:00+00:00",
                    "artifacts": {
                        "overview": {"model": "gemini-test"},
                    },
                }
            )
        )
        (technique_dir / "plan.json").write_text(
            json.dumps(
                {
                    "technique_name": "Gradient Descent",
                    "problem_type": "continuous",
                }
            )
        )
        (technique_dir / "overview.json").write_text(
            json.dumps(
                {
                    "summary": "Minimize differentiable objectives.",
                    "markdown": "Gradient descent updates parameters iteratively.",
                    "use_cases": ["Neural network training"],
                    "strengths": ["Simple"],
                    "limitations": ["Needs gradients"],
                }
            )
        )

        publish.SITE_DIR = site_dir
        publish.TECHNIQUES_DIR = techniques_dir

        try:
            publish.publish()

            assert not (site_dir / "stale.html").exists()
            assert (site_dir / "gradient-descent.html").exists()
            html = (site_dir / "gradient-descent.html").read_text()
            assert "Generated:" in html
            assert "gemini-test" in html
        finally:
            publish.SITE_DIR = original_site
            publish.TECHNIQUES_DIR = original_techniques
