"""Publishing engine — renders artifact JSON + infographic images as static HTML pages."""

import json
import logging
import re
import shutil
import sys
from pathlib import Path

import markdown
from jinja2 import Environment, FileSystemLoader

from pipeline.paths import (
    EVALUATION_LATEST_FULL_PATH,
    EVALUATION_LATEST_PARTIAL_PATH,
    GENERATED_TECHNIQUES_DIR,
    SITE_DIR as DEFAULT_SITE_DIR,
    TEMPLATES_DIR,
    USE_CASE_MATRIX_PATH,
)
from pipeline.runtime import ensure_supported_python

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

SITE_DIR = DEFAULT_SITE_DIR
TECHNIQUES_DIR = GENERATED_TECHNIQUES_DIR
MATH_PLACEHOLDER_PATTERN = re.compile(
    r"(\$\$.*?\$\$|\\\[.*?\\\]|\\\(.*?\\\)|(?<!\$)\$(?!\$)(?:\\.|[^$\n])+\$)",
    re.DOTALL,
)


def _slugify(name: str) -> str:
    """Convert technique name to slug (e.g. 'Bayesian Optimization' -> 'bayesian-optimization')."""
    import re
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def load_artifacts(technique_dir: Path) -> dict:
    """Load all JSON artifacts for a technique directory."""
    artifacts = {}
    for json_file in technique_dir.glob("*.json"):
        if json_file.name == "manifest.json":
            continue
        key = json_file.stem
        artifacts[key] = json.loads(json_file.read_text())
    return artifacts


def load_manifest(technique_dir: Path) -> dict:
    """Load generation metadata for a technique directory."""
    manifest_path = technique_dir / "manifest.json"
    if not manifest_path.exists():
        return {}
    try:
        return json.loads(manifest_path.read_text())
    except (json.JSONDecodeError, OSError):
        logger.warning("Could not read manifest at %s", manifest_path)
        return {}


def _extract_math_segments(text: str) -> tuple[str, dict[str, str]]:
    """Protect math spans so markdown does not alter LaTeX content."""
    placeholders: dict[str, str] = {}

    def repl(m: re.Match) -> str:
        key = f"@@MATH_{len(placeholders)}@@"
        placeholders[key] = m.group(0)
        return key

    return MATH_PLACEHOLDER_PATTERN.sub(repl, text), placeholders


def _restore_placeholders(text: str, placeholders: dict[str, str]) -> str:
    """Restore placeholder tokens back to their original content."""
    for key, original in placeholders.items():
        text = text.replace(key, original)
    return text


def _ensure_numbered_lists(text: str) -> str:
    """Add blank lines before lines starting with 'N. ' so markdown parses them as lists."""
    return re.sub(r"\n(\s*\d+\. )", r"\n\n\1", text)


def _ensure_bullet_lists(text: str) -> str:
    """Add blank line before first bullet after a colon so markdown parses as list."""
    # "parameters:\n- First" -> "parameters:\n\n- First"
    return re.sub(r":\s*\n(\s*-\s)", r":\n\n\1", text)


def _strip_redundant_leading_heading(text: str, _section_title: str = "") -> str:
    """Remove a leading # or ## line that duplicates the section context."""
    text = text.strip()
    match = re.match(r"^#{1,2}\s+.+\n?", text)
    if match:
        text = text[match.end() :].strip()
    return text


def _downgrade_headers(text: str) -> str:
    """Convert # to ## and ## to ### so content headers nest under section h2."""
    lines = text.split("\n")
    result = []
    for line in lines:
        if line.startswith("## "):
            result.append("### " + line[3:])
        elif line.startswith("# "):
            result.append("## " + line[2:])
        else:
            result.append(line)
    return "\n".join(result)


def _render_markdown(
    text: str,
    *,
    strip_leading_heading: bool = False,
    downgrade_headers: bool = False,
) -> str:
    """Render markdown while preserving math spans exactly."""
    if not text:
        return ""

    text = _ensure_numbered_lists(text)
    text = _ensure_bullet_lists(text)

    if strip_leading_heading:
        text = _strip_redundant_leading_heading(text, "")
    if downgrade_headers:
        text = _downgrade_headers(text)

    text, math_placeholders = _extract_math_segments(text)
    html = markdown.markdown(text, extensions=["fenced_code", "tables", "sane_lists"])
    return _restore_placeholders(html, math_placeholders)


def md_to_html(text: str, strip_leading_heading: bool = False) -> str:
    """Convert markdown to HTML."""
    return _render_markdown(text, strip_leading_heading=strip_leading_heading)


def md_section(text: str) -> str:
    """Like md_to_html but strips redundant leading heading and downgrades header levels."""
    return _render_markdown(
        text,
        strip_leading_heading=True,
        downgrade_headers=True,
    )


def md_downgrade(text: str) -> str:
    """Like md_to_html but downgrades # to ##, ## to ### (no strip)."""
    return _render_markdown(text, downgrade_headers=True)


def _build_provenance(manifest: dict) -> dict[str, str]:
    """Build a compact provenance summary for a technique page."""
    artifacts = manifest.get("artifacts", {})
    text_entry = (
        artifacts.get("overview")
        or artifacts.get("plan")
        or artifacts.get("implementation")
        or {}
    )
    image_entry = artifacts.get("infographic_image") or artifacts.get("preview_image") or {}
    return {
        "generated_at": manifest.get("updated_at") or text_entry.get("generated_at") or "Unknown",
        "artifact_version": str(manifest.get("artifact_version", "Unknown")),
        "text_model": text_entry.get("model") or "Unknown",
        "image_model": image_entry.get("model") or "Not generated",
    }


def publish():
    """Render all technique artifacts as static HTML pages."""
    if not TECHNIQUES_DIR.exists():
        logger.error("Content directory not found: %s", TECHNIQUES_DIR)
        sys.exit(1)

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)
    env.filters["markdown"] = md_to_html
    env.filters["md_section"] = md_section
    env.filters["md_downgrade"] = md_downgrade

    technique_template = env.get_template("technique.html")
    index_template = env.get_template("index.html")
    use_case_matrix_template = env.get_template("use_case_matrix.html")

    if SITE_DIR.exists():
        shutil.rmtree(SITE_DIR)
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    images_dir = SITE_DIR / "images"
    images_dir.mkdir(exist_ok=True)

    techniques = []

    for technique_dir in sorted(TECHNIQUES_DIR.iterdir()):
        if not technique_dir.is_dir():
            continue

        slug = technique_dir.name
        artifacts = load_artifacts(technique_dir)
        manifest = load_manifest(technique_dir)

        if not artifacts:
            logger.warning("No artifacts found for %s, skipping", slug)
            continue

        plan = artifacts.get("plan", {})
        technique_name = plan.get("technique_name", slug.replace("-", " ").title())

        # Copy images if they exist
        img_dest_dir = images_dir / slug
        infographic_src = technique_dir / "infographic.png"
        preview_src = technique_dir / "preview.png"
        has_infographic = infographic_src.exists()
        has_preview = preview_src.exists()
        if has_infographic or has_preview:
            img_dest_dir.mkdir(exist_ok=True)
        if has_infographic:
            shutil.copy2(infographic_src, img_dest_dir / "infographic.png")
        if has_preview:
            shutil.copy2(preview_src, img_dest_dir / "preview.png")

        # Render technique page
        html = technique_template.render(
            technique_name=technique_name,
            slug=slug,
            plan=plan,
            overview=artifacts.get("overview"),
            math_deep_dive=artifacts.get("math_deep_dive"),
            implementation=artifacts.get("implementation"),
            infographic_spec=artifacts.get("infographic_spec"),
            has_infographic=has_infographic,
            provenance=_build_provenance(manifest),
        )
        page_path = SITE_DIR / f"{slug}.html"
        page_path.write_text(html)
        logger.info("Published %s", page_path)

        homepage_summary = artifacts.get("homepage_summary", {})
        bullets = homepage_summary.get("bullets")
        summary = artifacts.get("overview", {}).get("summary", "")

        techniques.append(
            {
                "name": technique_name,
                "slug": slug,
                "bullets": bullets if bullets else None,
                "summary": summary,
                "has_infographic": has_infographic,
                "has_preview": has_preview,
            }
        )

    # Render index page
    index_html = index_template.render(techniques=techniques)
    index_path = SITE_DIR / "index.html"
    index_path.write_text(index_html)
    logger.info("Published index page with %d techniques", len(techniques))

    # Render use case matrix page (if exists)
    if USE_CASE_MATRIX_PATH.exists():
        data = json.loads(USE_CASE_MATRIX_PATH.read_text())
        algorithms = list(data["matrix"].keys())
        algorithm_slugs = {alg: _slugify(alg) for alg in algorithms}
        matrix_html = use_case_matrix_template.render(
            title=data["title"],
            description=data["description"],
            problem_spaces=data["problem_spaces"],
            algorithms=algorithms,
            matrix=data["matrix"],
            algorithm_slugs=algorithm_slugs,
        )
        (SITE_DIR / "use-case-matrix.html").write_text(matrix_html)
        logger.info("Published use case matrix page")
    else:
        logger.info("No use_case_matrix.json found, skipping use case matrix page")

    # Render compare page
    try:
        compare_template = env.get_template("compare.html")
        compare_html = compare_template.render(techniques=techniques)
        compare_path = SITE_DIR / "compare.html"
        compare_path.write_text(compare_html)
        logger.info("Published compare page")
    except Exception as e:
        logger.warning("Could not publish compare page: %s", e)

    # Render quality report if metrics exist
    _publish_quality_report(env)


def _publish_quality_report(env: Environment) -> None:
    """Render the quality report page from evaluation metrics."""
    metrics_path = None
    report_scope = "full"
    if EVALUATION_LATEST_FULL_PATH.exists():
        metrics_path = EVALUATION_LATEST_FULL_PATH
    elif EVALUATION_LATEST_PARTIAL_PATH.exists():
        metrics_path = EVALUATION_LATEST_PARTIAL_PATH
        report_scope = "partial"

    if metrics_path is None:
        logger.info("No evaluation metrics found, skipping quality report")
        return

    try:
        metrics = json.loads(metrics_path.read_text())
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Could not read evaluation metrics: %s", e)
        return

    try:
        report_template = env.get_template("eval_report.html")
    except Exception as e:
        logger.warning("Could not load eval_report.html template: %s", e)
        return

    # Build template data from metrics
    technique_data = []
    summary = metrics.get("summary", {})
    total_artifacts = summary.get("total", 0)
    total_passed = summary.get("passed", 0)
    total_retries = 0

    for slug, tech_metrics in metrics.get("techniques", {}).items():
        tech_name = tech_metrics.get("technique_name", slug.replace("-", " ").title())
        artifacts_list = []
        tech_passed = True

        for art_type, art_info in tech_metrics.get("artifacts", {}).items():
            status = art_info.get("status", "unknown")
            attempts = art_info.get("attempts", 0)
            total_retries += max(0, attempts - 1)
            if status != "passed":
                tech_passed = False

            artifacts_list.append({
                "type": art_type.replace("_", " ").title(),
                "status": status,
                "attempts": attempts,
            })

        technique_data.append({
            "name": tech_name,
            "overall_passed": tech_passed,
            "artifacts": artifacts_list,
        })

    report_html = report_template.render(
        timestamp=metrics.get("evaluated_at", ""),
        report_scope=report_scope,
        scope=metrics.get("scope", {}),
        total_techniques=len(technique_data),
        total_artifacts=total_artifacts,
        total_passed=total_passed,
        total_retries=total_retries,
        techniques=technique_data,
    )

    report_path = SITE_DIR / "quality-report.html"
    report_path.write_text(report_html)
    logger.info("Published quality report page")


if __name__ == "__main__":
    ensure_supported_python()
    publish()
