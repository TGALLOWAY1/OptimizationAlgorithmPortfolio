"""Artifact generation engine — creates plan and content artifacts for each technique."""

import json
import logging
import re
from pathlib import Path

from pipeline.llm_client import (
    NanoBananaProvider,
    generate_image_with_retry,
    generate_with_retry,
    get_provider,
)
from pipeline.schemas import SCHEMAS
from pipeline.validator import validate_artifact, validate_infographic_image

logger = logging.getLogger(__name__)

CONTENT_DIR = Path("content/techniques")
PROMPTS_DIR = Path(__file__).parent / "prompts"


def slugify(name: str) -> str:
    """Convert a technique name to a filesystem-safe slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def _load_prompt(filename: str) -> str:
    return (PROMPTS_DIR / filename).read_text()


def generate_plan(
    technique_name: str,
    force: bool = False,
    provider_override: str | None = None,
) -> dict:
    """Generate (or load) the plan for a technique."""
    slug = slugify(technique_name)
    out_dir = CONTENT_DIR / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    plan_path = out_dir / "plan.json"

    if plan_path.exists() and not force:
        logger.info("Plan already exists for %s, skipping", technique_name)
        return json.loads(plan_path.read_text())

    logger.info("Generating plan for %s", technique_name)
    prompt_template = _load_prompt("planner_prompt.md")
    user_prompt = prompt_template.replace("{{technique_name}}", technique_name)
    system_prompt = "You are an optimization algorithm expert. Respond with valid JSON only."

    provider = get_provider("plan", override=provider_override)
    schema = SCHEMAS["plan"]
    result = generate_with_retry(provider, system_prompt, user_prompt, schema)

    plan_path.write_text(json.dumps(result, indent=2))
    logger.info("Saved plan to %s", plan_path)
    return result


def generate_artifact(
    technique_slug: str,
    artifact_type: str,
    plan: dict,
    force: bool = False,
    provider_override: str | None = None,
) -> dict:
    """Generate a single artifact for a technique."""
    out_dir = CONTENT_DIR / technique_slug
    out_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = out_dir / f"{artifact_type}.json"

    if artifact_path.exists() and not force:
        logger.info(
            "Artifact %s already exists for %s, skipping",
            artifact_type,
            technique_slug,
        )
        return json.loads(artifact_path.read_text())

    prompt_map = {
        "overview": "overview_prompt.md",
        "math_deep_dive": "math_prompt.md",
        "implementation": "implementation_prompt.md",
        "infographic_spec": "infographic_prompt.md",
        "quiz": "quiz_prompt.md",
    }
    prompt_file = prompt_map.get(artifact_type)
    if not prompt_file:
        raise ValueError(f"Unknown artifact type: {artifact_type}")

    logger.info("Generating %s for %s", artifact_type, technique_slug)
    prompt_template = _load_prompt(prompt_file)
    plan_json = json.dumps(plan, indent=2)
    user_prompt = prompt_template.replace("{{plan_json}}", plan_json).replace(
        "{{technique_slug}}", technique_slug
    )
    system_prompt = (
        "You are an expert in optimization algorithms. Respond with valid JSON only."
    )

    provider = get_provider(artifact_type, override=provider_override)
    schema = SCHEMAS[artifact_type]
    result = generate_with_retry(provider, system_prompt, user_prompt, schema)

    # Content validation
    validation_errors = validate_artifact(artifact_type, result)
    if validation_errors:
        logger.warning(
            "Validation errors for %s/%s: %s",
            technique_slug,
            artifact_type,
            validation_errors,
        )

    artifact_path.write_text(json.dumps(result, indent=2))
    logger.info("Saved %s to %s", artifact_type, artifact_path)
    return result


def generate_infographic_image(
    technique_slug: str,
    technique_name: str,
    infographic_spec: dict,
    force: bool = False,
) -> str | None:
    """Generate the infographic image using Nano Banana Pro."""
    out_dir = CONTENT_DIR / technique_slug
    image_path = out_dir / "infographic.png"

    if image_path.exists() and not force:
        logger.info("Infographic image already exists for %s, skipping", technique_slug)
        return str(image_path)

    logger.info("Generating infographic image for %s", technique_slug)

    # Build the image prompt from the spec
    prompt_template = _load_prompt("infographic_image_prompt.md")

    formatted_panels = "\n".join(
        f"- Panel {i+1}: {p.get('title', 'Untitled')} — {p.get('content', '')}"
        for i, p in enumerate(infographic_spec.get("panels", []))
    )
    formatted_equations = "\n".join(
        f"- {eq}" for eq in infographic_spec.get("key_equations", [])
    )
    formatted_metaphors = "\n".join(
        f"- {m}" for m in infographic_spec.get("visual_metaphors", [])
    )

    prompt = (
        prompt_template.replace("{{technique_name}}", technique_name)
        .replace("{{title}}", infographic_spec.get("title", technique_name))
        .replace("{{layout}}", infographic_spec.get("layout", ""))
        .replace("{{color_palette}}", infographic_spec.get("color_palette", ""))
        .replace("{{typography}}", infographic_spec.get("typography", ""))
        .replace("{{formatted_panels}}", formatted_panels)
        .replace("{{formatted_equations}}", formatted_equations)
        .replace("{{formatted_metaphors}}", formatted_metaphors)
    )

    provider = get_provider("infographic_image")
    result_path = generate_image_with_retry(provider, prompt, str(image_path))

    # Validate the image
    errors = validate_infographic_image(result_path)
    if errors:
        logger.warning("Image validation warnings for %s: %s", technique_slug, errors)

    return result_path
