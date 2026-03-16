"""Generate preview images for all techniques (homepage thumbnails). Skips infographic and content generation."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline.generator import generate_preview_image, slugify
from pipeline.llm_client import load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main(force: bool = False) -> None:
    """Generate preview images for all techniques."""
    config = load_config()
    techniques = config["techniques"]

    for technique_name in techniques:
        slug = slugify(technique_name)
        try:
            generate_preview_image(slug, technique_name, force=force)
        except Exception as e:
            logger.error("Failed to generate preview for %s: %s", technique_name, e)

    logger.info("Preview image generation complete")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Regenerate even if exists")
    args = parser.parse_args()
    main(force=args.force)
