"""Build the static site for GitHub Pages deployment.

If generated content exists, runs the full publisher.
Otherwise, creates a standalone landing page with algorithm cards.
"""

import json
import logging
import shutil
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent
SITE_DIR = PROJECT_ROOT / "site"
GENERATED_TECHNIQUES_DIR = PROJECT_ROOT / "generated" / "techniques"
CONFIG_PATH = PROJECT_ROOT / "pipeline" / "config.json"


def _slugify(name: str) -> str:
    import re
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def _has_generated_content() -> bool:
    """Check if any generated technique content exists."""
    if not GENERATED_TECHNIQUES_DIR.exists():
        return False
    return any(GENERATED_TECHNIQUES_DIR.iterdir())


def _build_full_site() -> None:
    """Build the site using the full publisher pipeline."""
    logger.info("Generated content found — running full publisher")
    from pipeline.publish import publish
    publish()


def _build_placeholder_site() -> None:
    """Build a standalone landing page when no generated content is available."""
    logger.info("No generated content — building placeholder landing page")

    config = json.loads(CONFIG_PATH.read_text())
    techniques = config.get("techniques", [])

    if SITE_DIR.exists():
        shutil.rmtree(SITE_DIR)
    SITE_DIR.mkdir(parents=True, exist_ok=True)

    cards_html = ""
    for name in techniques:
        slug = _slugify(name)
        cards_html += f"""
            <div class="card">
                <div class="card-inner">
                    <h2>{name}</h2>
                    <p>Educational content for {name} — including mathematical foundations, implementation guides, and interactive examples.</p>
                    <span class="badge">Coming Soon</span>
                </div>
            </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Optimization Algorithm Portfolio</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', system-ui, sans-serif; line-height: 1.7; color: #1a1a2e; background: #fafbfc; }}
        header {{ background: #1a237e; color: white; padding: 2.5rem 1rem; text-align: center; }}
        header h1 {{ font-size: clamp(1.8rem, 5vw, 2.6rem); }}
        header p {{ opacity: 0.9; margin-top: 0.5rem; max-width: 48rem; margin-inline: auto; }}
        .container {{ width: min(95%, 1200px); margin: 0 auto; padding: 2rem; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; margin-top: 2rem; }}
        .card {{ background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); transition: transform 0.2s, box-shadow 0.2s; }}
        .card:hover {{ transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,0.12); }}
        .card-inner {{ padding: 1.5rem; }}
        .card h2 {{ font-size: 1.15rem; color: #1a237e; margin-bottom: 0.5rem; }}
        .card p {{ font-size: 0.9rem; color: #555; }}
        .badge {{ display: inline-block; margin-top: 0.75rem; padding: 0.25rem 0.75rem; background: #e8eaf6; color: #1a237e; border-radius: 12px; font-size: 0.8rem; font-weight: 600; }}
        .info {{ text-align: center; margin: 2rem 0; padding: 1.5rem; background: #e8eaf6; border-radius: 8px; }}
        .info p {{ max-width: 600px; margin-inline: auto; color: #333; }}
        footer {{ text-align: center; padding: 2rem; color: #666; font-size: 0.85rem; }}
        .techniques-list {{ font-size: 0.85rem; color: #666; margin-top: 0.5rem; }}
    </style>
</head>
<body>
    <header>
        <h1>Optimization Algorithm Portfolio</h1>
        <p>Comprehensive educational content on optimization techniques — mathematical foundations, implementation guides, interactive comparisons, and more.</p>
    </header>
    <div class="container">
        <div class="info">
            <p><strong>This site is auto-deployed from GitHub Pages.</strong> Full content (deep dives, code examples, quizzes, infographics) will appear once the content pipeline has been run.</p>
        </div>
        <h2 style="text-align:center; color:#1a237e;">Covered Algorithms</h2>
        <div class="grid">{cards_html}
        </div>
    </div>
    <footer>Optimization Algorithm Portfolio</footer>
</body>
</html>"""

    index_path = SITE_DIR / "index.html"
    index_path.write_text(html)
    logger.info("Published placeholder index.html with %d algorithm cards", len(techniques))


def main() -> None:
    if _has_generated_content():
        _build_full_site()
    else:
        _build_placeholder_site()
    logger.info("Site built at %s", SITE_DIR)


if __name__ == "__main__":
    main()
