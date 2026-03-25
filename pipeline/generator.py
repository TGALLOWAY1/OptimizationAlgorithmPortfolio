"""Artifact generation engine — creates plan and content artifacts for each technique."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.llm_client import (
    NanoBananaProvider,
    generate_image_with_retry,
    generate_with_retry,
    get_provider,
    load_config,
    load_topic,
)
from pipeline.paths import GENERATED_ROOT, GENERATED_TECHNIQUES_DIR, PROMPTS_DIR, technique_dir
from pipeline.schemas import SCHEMAS
from pipeline.validator import validate_artifact, validate_infographic_image

logger = logging.getLogger(__name__)

CONTENT_DIR = GENERATED_TECHNIQUES_DIR
ARTIFACT_VERSION = "2"
MANIFEST_FILENAME = "manifest.json"
PROMPT_MAP = {
    "plan": "planner_prompt.md",
    "overview": "overview_prompt.md",
    "math_deep_dive": "math_prompt.md",
    "implementation": "implementation_prompt.md",
    "infographic_spec": "infographic_prompt.md",
    "homepage_summary": "homepage_summary_prompt.md",
    "infographic_image": "infographic_image_prompt.md",
    "preview_image": "preview_image_prompt.md",
    "knowledge_graph": "knowledge_graph_prompt.md",
    "playground_config": "playground_config_prompt.md",
}


@dataclass(frozen=True)
class GenerationResult:
    """Result of generating or reusing an artifact."""

    payload: Any
    status: str
    path: Path
    input_hash: str


def slugify(name: str) -> str:
    """Convert a technique name to a filesystem-safe slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def _load_prompt(filename: str) -> str:
    return (PROMPTS_DIR / filename).read_text()


def _stable_json(value: Any) -> str:
    """Serialize a value deterministically for hashing and manifest storage."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _manifest_path(out_dir: Path) -> Path:
    return out_dir / MANIFEST_FILENAME


def _load_manifest(out_dir: Path) -> dict[str, Any]:
    manifest_path = _manifest_path(out_dir)
    if not manifest_path.exists():
        return {"artifact_version": ARTIFACT_VERSION, "artifacts": {}}

    try:
        manifest = json.loads(manifest_path.read_text())
    except json.JSONDecodeError:
        logger.warning("Ignoring invalid manifest at %s", manifest_path)
        return {"artifact_version": ARTIFACT_VERSION, "artifacts": {}}

    manifest.setdefault("artifact_version", ARTIFACT_VERSION)
    manifest.setdefault("artifacts", {})
    return manifest


def _save_manifest(out_dir: Path, manifest: dict[str, Any]) -> None:
    manifest["artifact_version"] = ARTIFACT_VERSION
    manifest["updated_at"] = _timestamp()
    _manifest_path(out_dir).write_text(json.dumps(manifest, indent=2))


def _config_slice(artifact_type: str) -> dict[str, Any]:
    config = load_config()
    provider_name = config["artifact_provider_map"].get(artifact_type)
    provider_config = config.get("providers", {}).get(provider_name, {})
    return {
        "artifact_type": artifact_type,
        "provider_name": provider_name,
        "provider_config": provider_config,
    }


def _compute_input_hash(
    artifact_type: str,
    *,
    prompt_text: str = "",
    schema: dict[str, Any] | None = None,
    config_slice: dict[str, Any] | None = None,
    material_inputs: dict[str, Any] | None = None,
) -> str:
    payload = {
        "artifact_version": ARTIFACT_VERSION,
        "artifact_type": artifact_type,
        "prompt_text": prompt_text,
        "schema": schema or {},
        "config_slice": config_slice or {},
        "material_inputs": material_inputs or {},
    }
    return hashlib.sha256(_stable_json(payload).encode("utf-8")).hexdigest()


def _provider_metadata(provider: Any) -> dict[str, Any]:
    model = getattr(provider, "model", None)
    if model is not None and not isinstance(model, (str, int, float, bool)):
        model = str(model)
    return {
        "provider_class": type(provider).__name__,
        "model": model,
    }


def _can_reuse_artifact(
    *,
    out_dir: Path,
    artifact_key: str,
    artifact_path: Path,
    input_hash: str,
    force: bool,
) -> tuple[bool, dict[str, Any]]:
    manifest = _load_manifest(out_dir)
    if force or not artifact_path.exists():
        return False, manifest

    artifact_meta = manifest.get("artifacts", {}).get(artifact_key)
    if not artifact_meta:
        return False, manifest

    if manifest.get("artifact_version") != ARTIFACT_VERSION:
        return False, manifest

    return artifact_meta.get("input_hash") == input_hash, manifest


def _update_manifest(
    *,
    out_dir: Path,
    manifest: dict[str, Any],
    artifact_key: str,
    artifact_path: Path,
    input_hash: str,
    provider: Any,
) -> None:
    manifest.setdefault("artifacts", {})
    manifest["artifacts"][artifact_key] = {
        "file": artifact_path.name,
        "generated_at": _timestamp(),
        "input_hash": input_hash,
        **_provider_metadata(provider),
    }
    _save_manifest(out_dir, manifest)


def generate_plan(
    technique_name: str,
    force: bool = False,
    provider_override=None,
) -> GenerationResult:
    """Generate (or load) the plan for a technique."""
    slug = slugify(technique_name)
    out_dir = technique_dir(slug, CONTENT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    plan_path = out_dir / "plan.json"
    prompt_template = _load_prompt(PROMPT_MAP["plan"])
    schema = SCHEMAS["plan"]
    input_hash = _compute_input_hash(
        "plan",
        prompt_text=prompt_template,
        schema=schema,
        config_slice=_config_slice("plan"),
        material_inputs={"technique_name": technique_name, "slug": slug},
    )
    reusable, manifest = _can_reuse_artifact(
        out_dir=out_dir,
        artifact_key="plan",
        artifact_path=plan_path,
        input_hash=input_hash,
        force=force,
    )
    if reusable:
        logger.info("Plan up to date for %s, skipping", technique_name)
        return GenerationResult(
            payload=json.loads(plan_path.read_text()),
            status="skipped",
            path=plan_path,
            input_hash=input_hash,
        )

    logger.info("Generating plan for %s", technique_name)
    topic = load_topic()
    user_prompt = prompt_template.replace("{{technique_name}}", technique_name).replace(
        "{{domain}}", topic["domain"]
    )
    system_prompt = f"You are an expert in {topic['domain']}. Respond with valid JSON only."

    provider = get_provider("plan", override=provider_override)
    result = generate_with_retry(provider, system_prompt, user_prompt, schema)

    plan_path.write_text(json.dumps(result, indent=2))
    _update_manifest(
        out_dir=out_dir,
        manifest=manifest,
        artifact_key="plan",
        artifact_path=plan_path,
        input_hash=input_hash,
        provider=provider,
    )
    logger.info("Saved plan to %s", plan_path)
    return GenerationResult(
        payload=result,
        status="generated",
        path=plan_path,
        input_hash=input_hash,
    )


def generate_artifact(
    technique_slug: str,
    artifact_type: str,
    plan: dict,
    force: bool = False,
    provider_override=None,
) -> GenerationResult:
    """Generate a single artifact for a technique."""
    out_dir = technique_dir(technique_slug, CONTENT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = out_dir / f"{artifact_type}.json"
    prompt_file = PROMPT_MAP.get(artifact_type)
    if not prompt_file:
        raise ValueError(f"Unknown artifact type: {artifact_type}")
    prompt_template = _load_prompt(prompt_file)
    schema = SCHEMAS[artifact_type]
    input_hash = _compute_input_hash(
        artifact_type,
        prompt_text=prompt_template,
        schema=schema,
        config_slice=_config_slice(artifact_type),
        material_inputs={"plan": plan, "technique_slug": technique_slug},
    )
    reusable, manifest = _can_reuse_artifact(
        out_dir=out_dir,
        artifact_key=artifact_type,
        artifact_path=artifact_path,
        input_hash=input_hash,
        force=force,
    )
    if reusable:
        logger.info("Artifact %s up to date for %s, skipping", artifact_type, technique_slug)
        return GenerationResult(
            payload=json.loads(artifact_path.read_text()),
            status="skipped",
            path=artifact_path,
            input_hash=input_hash,
        )

    logger.info("Generating %s for %s", artifact_type, technique_slug)
    plan_json = json.dumps(plan, indent=2)
    topic = load_topic()
    user_prompt = prompt_template.replace("{{plan_json}}", plan_json).replace(
        "{{technique_slug}}", technique_slug
    ).replace("{{domain}}", topic["domain"])
    system_prompt = (
        f"You are an expert in {topic['domain']}. Respond with valid JSON only."
    )

    provider = get_provider(artifact_type, override=provider_override)
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
    _update_manifest(
        out_dir=out_dir,
        manifest=manifest,
        artifact_key=artifact_type,
        artifact_path=artifact_path,
        input_hash=input_hash,
        provider=provider,
    )
    logger.info("Saved %s to %s", artifact_type, artifact_path)
    return GenerationResult(
        payload=result,
        status="generated",
        path=artifact_path,
        input_hash=input_hash,
    )


def generate_homepage_summary(
    technique_slug: str,
    plan: dict,
    overview: dict,
    force: bool = False,
    provider_override=None,
) -> GenerationResult:
    """Generate short bullet-point summary for homepage cards."""
    out_dir = technique_dir(technique_slug, CONTENT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = out_dir / "homepage_summary.json"
    prompt_template = _load_prompt(PROMPT_MAP["homepage_summary"])
    schema = SCHEMAS["homepage_summary"]
    input_hash = _compute_input_hash(
        "homepage_summary",
        prompt_text=prompt_template,
        schema=schema,
        config_slice=_config_slice("homepage_summary"),
        material_inputs={
            "plan": plan,
            "overview_summary": overview.get("summary", ""),
            "technique_slug": technique_slug,
        },
    )
    reusable, manifest = _can_reuse_artifact(
        out_dir=out_dir,
        artifact_key="homepage_summary",
        artifact_path=artifact_path,
        input_hash=input_hash,
        force=force,
    )
    if reusable:
        logger.info("Homepage summary up to date for %s, skipping", technique_slug)
        return GenerationResult(
            payload=json.loads(artifact_path.read_text()),
            status="skipped",
            path=artifact_path,
            input_hash=input_hash,
        )

    logger.info("Generating homepage summary for %s", technique_slug)
    overview_summary = overview.get("summary", "")
    topic = load_topic()
    user_prompt = (
        prompt_template.replace("{{plan_json}}", json.dumps(plan, indent=2))
        .replace("{{overview_summary}}", overview_summary)
        .replace("{{domain}}", topic["domain"])
    )
    system_prompt = (
        f"You are an expert in {topic['domain']}. Respond with valid JSON only."
    )

    provider = get_provider("homepage_summary", override=provider_override)
    result = generate_with_retry(provider, system_prompt, user_prompt, schema)

    artifact_path.write_text(json.dumps(result, indent=2))
    _update_manifest(
        out_dir=out_dir,
        manifest=manifest,
        artifact_key="homepage_summary",
        artifact_path=artifact_path,
        input_hash=input_hash,
        provider=provider,
    )
    logger.info("Saved homepage_summary to %s", artifact_path)
    return GenerationResult(
        payload=result,
        status="generated",
        path=artifact_path,
        input_hash=input_hash,
    )


def generate_infographic_image(
    technique_slug: str,
    technique_name: str,
    infographic_spec: dict,
    force: bool = False,
) -> GenerationResult:
    """Generate the infographic image using Nano Banana Pro."""
    out_dir = technique_dir(technique_slug, CONTENT_DIR)
    image_path = out_dir / "infographic.png"
    prompt_template = _load_prompt(PROMPT_MAP["infographic_image"])
    input_hash = _compute_input_hash(
        "infographic_image",
        prompt_text=prompt_template,
        config_slice=_config_slice("infographic_image"),
        material_inputs={
            "technique_name": technique_name,
            "technique_slug": technique_slug,
            "infographic_spec": infographic_spec,
        },
    )
    reusable, manifest = _can_reuse_artifact(
        out_dir=out_dir,
        artifact_key="infographic_image",
        artifact_path=image_path,
        input_hash=input_hash,
        force=force,
    )
    if reusable:
        logger.info("Infographic image up to date for %s, skipping", technique_slug)
        return GenerationResult(
            payload=str(image_path),
            status="skipped",
            path=image_path,
            input_hash=input_hash,
        )

    logger.info("Generating infographic image for %s", technique_slug)

    # Build the image prompt from the spec
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
    _update_manifest(
        out_dir=out_dir,
        manifest=manifest,
        artifact_key="infographic_image",
        artifact_path=image_path,
        input_hash=input_hash,
        provider=provider,
    )

    # Validate the image
    errors = validate_infographic_image(result_path)
    if errors:
        logger.warning("Image validation warnings for %s: %s", technique_slug, errors)

    return GenerationResult(
        payload=result_path,
        status="generated",
        path=image_path,
        input_hash=input_hash,
    )


def generate_preview_image(
    technique_slug: str,
    technique_name: str,
    force: bool = False,
) -> GenerationResult:
    """Generate a homepage preview thumbnail using Nano Banana. Consistent theme across all techniques."""
    out_dir = technique_dir(technique_slug, CONTENT_DIR)
    image_path = out_dir / "preview.png"
    prompt_template = _load_prompt(PROMPT_MAP["preview_image"])
    input_hash = _compute_input_hash(
        "preview_image",
        prompt_text=prompt_template,
        config_slice=_config_slice("infographic_image"),
        material_inputs={
            "technique_name": technique_name,
            "technique_slug": technique_slug,
        },
    )
    reusable, manifest = _can_reuse_artifact(
        out_dir=out_dir,
        artifact_key="preview_image",
        artifact_path=image_path,
        input_hash=input_hash,
        force=force,
    )
    if reusable:
        logger.info("Preview image up to date for %s, skipping", technique_slug)
        return GenerationResult(
            payload=str(image_path),
            status="skipped",
            path=image_path,
            input_hash=input_hash,
        )

    logger.info("Generating preview image for %s", technique_slug)

    prompt = prompt_template.replace("{{technique_name}}", technique_name)

    provider = get_provider("infographic_image")
    result_path = generate_image_with_retry(provider, prompt, str(image_path))
    _update_manifest(
        out_dir=out_dir,
        manifest=manifest,
        artifact_key="preview_image",
        artifact_path=image_path,
        input_hash=input_hash,
        provider=provider,
    )

    errors = validate_infographic_image(result_path)
    if errors:
        logger.warning("Preview image validation warnings for %s: %s", technique_slug, errors)

    return GenerationResult(
        payload=result_path,
        status="generated",
        path=image_path,
        input_hash=input_hash,
    )


def generate_knowledge_graph(
    all_plans: dict[str, dict],
    force: bool = False,
    provider_override=None,
) -> GenerationResult:
    """Generate the knowledge graph JSON mapping relationships between all techniques."""
    out_path = GENERATED_ROOT / "knowledge_graph.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    prompt_template = _load_prompt(PROMPT_MAP["knowledge_graph"])
    schema = SCHEMAS["knowledge_graph"]
    input_hash = _compute_input_hash(
        "knowledge_graph",
        prompt_text=prompt_template,
        schema=schema,
        config_slice=_config_slice("knowledge_graph"),
        material_inputs={"all_plans": all_plans},
    )

    if not force and out_path.exists():
        try:
            existing = json.loads(out_path.read_text())
            logger.info("Knowledge graph up to date, skipping")
            return GenerationResult(
                payload=existing, status="skipped", path=out_path, input_hash=input_hash
            )
        except (json.JSONDecodeError, OSError):
            pass

    logger.info("Generating knowledge graph")
    topic = load_topic()
    all_plans_json = json.dumps(all_plans, indent=2)
    user_prompt = prompt_template.replace(
        "{{all_plans_json}}", all_plans_json
    ).replace("{{domain}}", topic["domain"])
    system_prompt = f"You are an expert in {topic['domain']}. Respond with valid JSON only."

    provider = get_provider("knowledge_graph", override=provider_override)
    result = generate_with_retry(provider, system_prompt, user_prompt, schema)

    out_path.write_text(json.dumps(result, indent=2))
    logger.info("Saved knowledge graph to %s", out_path)
    return GenerationResult(
        payload=result, status="generated", path=out_path, input_hash=input_hash
    )


def generate_playground_config(
    technique_slug: str,
    technique_name: str,
    plan: dict,
    force: bool = False,
    provider_override=None,
) -> GenerationResult:
    """Generate playground parameter configuration for a technique."""
    out_dir = technique_dir(technique_slug, CONTENT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    config_path = out_dir / "playground_config.json"

    prompt_template = _load_prompt(PROMPT_MAP["playground_config"])
    schema = SCHEMAS["playground_config"]
    input_hash = _compute_input_hash(
        "playground_config",
        prompt_text=prompt_template,
        schema=schema,
        config_slice=_config_slice("playground_config"),
        material_inputs={"plan": plan, "technique_slug": technique_slug},
    )

    reusable, manifest = _can_reuse_artifact(
        out_dir=out_dir,
        artifact_key="playground_config",
        artifact_path=config_path,
        input_hash=input_hash,
        force=force,
    )
    if reusable:
        logger.info("Playground config up to date for %s, skipping", technique_slug)
        return GenerationResult(
            payload=json.loads(config_path.read_text()),
            status="skipped",
            path=config_path,
            input_hash=input_hash,
        )

    logger.info("Generating playground config for %s", technique_slug)
    topic = load_topic()
    user_prompt = (
        prompt_template.replace("{{plan_json}}", json.dumps(plan, indent=2))
        .replace("{{technique_name}}", technique_name)
        .replace("{{domain}}", topic["domain"])
    )
    system_prompt = f"You are an expert in {topic['domain']}. Respond with valid JSON only."

    provider = get_provider("playground_config", override=provider_override)
    result = generate_with_retry(provider, system_prompt, user_prompt, schema)

    config_path.write_text(json.dumps(result, indent=2))
    _update_manifest(
        out_dir=out_dir,
        manifest=manifest,
        artifact_key="playground_config",
        artifact_path=config_path,
        input_hash=input_hash,
        provider=provider,
    )
    logger.info("Saved playground config to %s", config_path)
    return GenerationResult(
        payload=result, status="generated", path=config_path, input_hash=input_hash
    )
