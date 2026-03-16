"""Publishing engine — renders artifact JSON + infographic images as static HTML pages."""

import json
import logging
import shutil
import sys
from pathlib import Path

import markdown
from jinja2 import Environment, FileSystemLoader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

CONTENT_DIR = Path("content/techniques")
SITE_DIR = Path("site")
TEMPLATES_DIR = Path(__file__).parent / "templates"


def load_artifacts(technique_dir: Path) -> dict:
    """Load all JSON artifacts for a technique directory."""
    artifacts = {}
    for json_file in technique_dir.glob("*.json"):
        key = json_file.stem
        artifacts[key] = json.loads(json_file.read_text())
    return artifacts


def md_to_html(text: str) -> str:
    """Convert markdown to HTML, passing through LaTeX delimiters."""
    return markdown.markdown(
        text,
        extensions=["fenced_code", "tables", "codehilite"],
    )


def publish():
    """Render all technique artifacts as static HTML pages."""
    if not CONTENT_DIR.exists():
        logger.error("Content directory not found: %s", CONTENT_DIR)
        sys.exit(1)

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)
    env.filters["markdown"] = md_to_html

    technique_template = env.get_template("technique.html")
    index_template = env.get_template("index.html")

    SITE_DIR.mkdir(parents=True, exist_ok=True)
    images_dir = SITE_DIR / "images"
    images_dir.mkdir(exist_ok=True)

    techniques = []

    for technique_dir in sorted(CONTENT_DIR.iterdir()):
        if not technique_dir.is_dir():
            continue

        slug = technique_dir.name
        artifacts = load_artifacts(technique_dir)

        if not artifacts:
            logger.warning("No artifacts found for %s, skipping", slug)
            continue

        plan = artifacts.get("plan", {})
        technique_name = plan.get("technique_name", slug.replace("-", " ").title())

        # Copy infographic image if it exists
        infographic_src = technique_dir / "infographic.png"
        has_infographic = infographic_src.exists()
        if has_infographic:
            img_dest_dir = images_dir / slug
            img_dest_dir.mkdir(exist_ok=True)
            shutil.copy2(infographic_src, img_dest_dir / "infographic.png")

        # Render technique page
        html = technique_template.render(
            technique_name=technique_name,
            slug=slug,
            plan=plan,
            overview=artifacts.get("overview"),
            math_deep_dive=artifacts.get("math_deep_dive"),
            implementation=artifacts.get("implementation"),
            infographic_spec=artifacts.get("infographic_spec"),
            quiz=artifacts.get("quiz"),
            has_infographic=has_infographic,
        )
        page_path = SITE_DIR / f"{slug}.html"
        page_path.write_text(html)
        logger.info("Published %s", page_path)

        techniques.append(
            {
                "name": technique_name,
                "slug": slug,
                "summary": artifacts.get("overview", {}).get("summary", ""),
                "has_infographic": has_infographic,
            }
        )

    # Render index page
    index_html = index_template.render(techniques=techniques)
    index_path = SITE_DIR / "index.html"
    index_path.write_text(index_html)
    logger.info("Published index page with %d techniques", len(techniques))

    # Render compare page
    compare_template = env.get_template("compare.html")
    compare_html = compare_template.render(techniques=techniques)
    compare_path = SITE_DIR / "compare.html"
    compare_path.write_text(compare_html)
    logger.info("Published compare page")


if __name__ == "__main__":
    publish()
