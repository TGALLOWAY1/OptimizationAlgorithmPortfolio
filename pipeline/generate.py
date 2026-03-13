"""Main pipeline orchestrator — generates all artifacts for all techniques."""

import argparse
import json
import logging
import sys
from pathlib import Path

from pipeline.generator import (
    generate_artifact,
    generate_infographic_image,
    generate_plan,
    slugify,
)
from pipeline.llm_client import load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Generate optimization technique content artifacts"
    )
    parser.add_argument(
        "--technique",
        type=str,
        help="Generate for a single technique (by name)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate existing artifacts",
    )
    parser.add_argument(
        "--provider",
        type=str,
        choices=["openai", "gemini"],
        help="Force a specific LLM provider for all text artifacts",
    )
    parser.add_argument(
        "--skip-images",
        action="store_true",
        help="Skip Nano Banana Pro image generation",
    )
    args = parser.parse_args()

    config = load_config()
    techniques = config["techniques"]
    artifact_types = config["artifact_types"]

    if args.technique:
        matching = [t for t in techniques if t.lower() == args.technique.lower()]
        if not matching:
            logger.error("Technique '%s' not found in config", args.technique)
            sys.exit(1)
        techniques = matching

    stats = {"generated": 0, "skipped": 0, "failed": 0}

    for technique_name in techniques:
        slug = slugify(technique_name)
        logger.info("=== Processing: %s (%s) ===", technique_name, slug)

        # Step 1: Generate plan
        try:
            plan = generate_plan(
                technique_name,
                force=args.force,
                provider_override=args.provider,
            )
            stats["generated"] += 1
        except Exception as e:
            logger.error("Failed to generate plan for %s: %s", technique_name, e)
            stats["failed"] += 1
            continue

        # Step 2: Generate each artifact type
        infographic_spec = None
        for artifact_type in artifact_types:
            try:
                result = generate_artifact(
                    slug,
                    artifact_type,
                    plan,
                    force=args.force,
                    provider_override=args.provider,
                )
                if artifact_type == "infographic_spec":
                    infographic_spec = result
                stats["generated"] += 1
            except Exception as e:
                logger.error(
                    "Failed to generate %s for %s: %s",
                    artifact_type,
                    technique_name,
                    e,
                )
                stats["failed"] += 1

        # Step 3: Generate infographic image
        if not args.skip_images and infographic_spec:
            try:
                generate_infographic_image(
                    slug, technique_name, infographic_spec, force=args.force
                )
                stats["generated"] += 1
            except Exception as e:
                logger.error(
                    "Failed to generate infographic image for %s: %s",
                    technique_name,
                    e,
                )
                stats["failed"] += 1

    logger.info("=== Pipeline Summary ===")
    logger.info(
        "Generated: %d | Skipped: %d | Failed: %d",
        stats["generated"],
        stats["skipped"],
        stats["failed"],
    )


if __name__ == "__main__":
    main()
