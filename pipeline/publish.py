"""Publishing engine — renders artifact JSON + infographic images as static HTML pages."""

import json
import logging
import re
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

CONTENT_DIR = Path(__file__).resolve().parents[1] / "content"
SITE_DIR = Path(__file__).resolve().parents[1] / "site"
TEMPLATES_DIR = Path(__file__).parent / "templates"
TECHNIQUES_DIR = CONTENT_DIR / "techniques"


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
        key = json_file.stem
        artifacts[key] = json.loads(json_file.read_text())
    return artifacts


def _protect_emphasis(text: str, start_counter: int = 0) -> tuple[str, dict[str, str], int]:
    """Replace *word* and **word** with placeholders so math replacement doesn't corrupt them."""
    placeholders: dict[str, str] = {}
    counter = start_counter

    def repl(m: re.Match) -> str:
        nonlocal counter
        key = f"{{{{EMPH_{counter}}}}}"
        counter += 1
        placeholders[key] = m.group(0)
        return key

    # Only protect *word* (single asterisk) - **word** stays for markdown bold
    text = re.sub(r"\*([^*]+)\*", repl, text)
    return text, placeholders, counter


def _restore_emphasis(text: str, placeholders: dict[str, str]) -> str:
    """Restore protected *word* and **word** from placeholders."""
    for key, original in placeholders.items():
        text = text.replace(key, original)
    return text


def _escape_markdown_in_math(text: str) -> str:
    """Escape * and _ inside $...$ and $$...$$ so markdown doesn't treat them as emphasis."""
    parts = re.split(r"(\$\$[^$]*\$\$|\$[^$]*\$)", text)
    for i in range(1, len(parts), 2):
        parts[i] = parts[i].replace("*", "\\*").replace("_", "\\_")
    return "".join(parts)


def _normalize_math_in_prose(text: str) -> tuple[str, dict[str, str]]:
    """Wrap common math notation in $...$ when it appears as plain text (not already in math)."""
    # Split by $$...$$ and $...$ to avoid double-wrapping; only process non-math segments
    parts = re.split(r"(\$\$[^$]*\$\$|\$[^$]*\$)", text)
    result = []
    all_placeholders: dict[str, str] = {}
    counter = 0
    for i, part in enumerate(parts):
        if i % 2 == 1:
            result.append(part)  # Already inside math
            continue
        # Protect *word* and **word** so (\w)* replacement doesn't corrupt them
        part, emph_ph, counter = _protect_emphasis(part, counter)
        all_placeholders.update(emph_ph)
        # GP(m(x), k(x, x')): use placeholder so m(x), k(x) aren't double-wrapped
        _gp_ph = "___GP_PLACEHOLDER___"
        part = re.sub(r"GP\(m\(x\), k\(x, x'\)\)", _gp_ph, part)
        # Subscripts: D_t, X_t, Y_t, x_t, etc. (letter + _ + subscript)
        part = re.sub(r"\b([A-Za-z])_([a-zA-Z0-9]+)\b", r"$\1_{\2}$", part)
        # Optimal/star notation: x*, f*, theta* -> $x^*$, etc.
        part = re.sub(r"(\w)\*", r"$\1^*$", part)
        # Common function notation in prose: f(x), a(x), m(x), k(x,x')
        part = re.sub(r"\b(f|a|m|k)\(([^)]+)\)", r"$\1(\2)$", part)
        part = part.replace(_gp_ph, r"$GP(m(x), k(x, x'))$")
        result.append(part)
    return "".join(result), all_placeholders


def _ensure_numbered_lists(text: str) -> str:
    """Add blank lines before lines starting with 'N. ' so markdown parses them as lists."""
    return re.sub(r"\n(\s*\d+\. )", r"\n\n\1", text)


def _ensure_bullet_lists(text: str) -> str:
    """Add blank line before first bullet after a colon so markdown parses as list."""
    # "parameters:\n- First" -> "parameters:\n\n- First"
    return re.sub(r":\s*\n(\s*-\s)", r":\n\n\1", text)


def _strip_emphasis_markers(s: str) -> str:
    """Remove leading/trailing * or ** so *word* or **word** becomes word."""
    s = s.strip()
    s = re.sub(r"^[\*\s]+|[\*\s]+$", "", s)
    return s.strip()


def _bold_definition_list_items(text: str) -> str:
    """Bold the leading term in list items like '- Term: description' or '1. Term: description'."""
    def bullet_repl(m: re.Match) -> str:
        term = _strip_emphasis_markers(m.group(1))
        return f"- **{term}**:"
    def numbered_repl(m: re.Match) -> str:
        term = _strip_emphasis_markers(m.group(2))
        return f"{m.group(1)}. **{term}**:"
    text = re.sub(r"^- ([^:]+):", bullet_repl, text, flags=re.MULTILINE)
    # Only match when term has no period (avoids "1. First step. 2. Next:")
    text = re.sub(r"^(\d+)\. ([^:.]*):", numbered_repl, text, flags=re.MULTILINE)
    return text


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


def md_to_html(text: str, strip_leading_heading: bool = False) -> str:
    """Convert markdown to HTML. Normalizes math, lists, and formatting."""
    # Convert literal \n (from LLM/JSON) to actual newlines
    text = text.replace("\\n", "\n")
    # Normalize math in prose (subscripts, f(x), etc.)
    text, emph_placeholders = _normalize_math_in_prose(text)
    # Restore emphasis so _bold_definition_list_items can strip * from terms
    text = _restore_emphasis(text, emph_placeholders)
    # Ensure numbered and bullet lists parse correctly
    text = _ensure_numbered_lists(text)
    text = _ensure_bullet_lists(text)
    # Bold leading terms in definition-style list items
    text = _bold_definition_list_items(text)
    if strip_leading_heading:
        text = _strip_redundant_leading_heading(text, "")
    text = _escape_markdown_in_math(text)
    return markdown.markdown(
        text,
        extensions=["fenced_code", "tables"],
    )


def md_section(text: str) -> str:
    """Like md_to_html but strips redundant leading heading and downgrades header levels."""
    text = text.replace("\\n", "\n")
    text, emph_placeholders = _normalize_math_in_prose(text)
    text = _restore_emphasis(text, emph_placeholders)
    text = _ensure_numbered_lists(text)
    text = _ensure_bullet_lists(text)
    text = _bold_definition_list_items(text)
    text = _strip_redundant_leading_heading(text, "")
    text = _downgrade_headers(text)
    text = _escape_markdown_in_math(text)
    return markdown.markdown(text, extensions=["fenced_code", "tables"])


def md_downgrade(text: str) -> str:
    """Like md_to_html but downgrades # to ##, ## to ### (no strip)."""
    text = text.replace("\\n", "\n")
    text, emph_placeholders = _normalize_math_in_prose(text)
    text = _restore_emphasis(text, emph_placeholders)
    text = _ensure_numbered_lists(text)
    text = _ensure_bullet_lists(text)
    text = _bold_definition_list_items(text)
    text = _downgrade_headers(text)
    text = _escape_markdown_in_math(text)
    return markdown.markdown(text, extensions=["fenced_code", "tables"])


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

    SITE_DIR.mkdir(parents=True, exist_ok=True)
    images_dir = SITE_DIR / "images"
    images_dir.mkdir(exist_ok=True)

    techniques = []

    for technique_dir in sorted(TECHNIQUES_DIR.iterdir()):
        if not technique_dir.is_dir():
            continue

        slug = technique_dir.name
        artifacts = load_artifacts(technique_dir)

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
            quiz=artifacts.get("quiz"),
            has_infographic=has_infographic,
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
    use_case_matrix_path = CONTENT_DIR / "use_case_matrix.json"
    if use_case_matrix_path.exists():
        data = json.loads(use_case_matrix_path.read_text())
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
    metrics_path = CONTENT_DIR / "evaluation_metrics.json"
    if not metrics_path.exists():
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
    total_artifacts = 0
    total_passed = 0
    total_retries = 0

    for slug, tech_metrics in metrics.get("techniques", {}).items():
        tech_name = slug.replace("-", " ").title()
        artifacts_list = []
        tech_passed = True

        for art_type, art_info in tech_metrics.get("artifacts", {}).items():
            status = art_info.get("status", "unknown")
            attempts = art_info.get("attempts", 0)
            total_artifacts += 1
            total_retries += max(0, attempts - 1)

            if status == "passed":
                total_passed += 1
            else:
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

    import datetime

    report_html = report_template.render(
        timestamp=datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%d %H:%M UTC"
        ),
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
    publish()
