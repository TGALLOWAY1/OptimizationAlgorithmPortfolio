"""Main pipeline orchestrator — generates all artifacts for all techniques."""

import argparse
from datetime import datetime, timezone
import logging
import shutil
import sys

from pipeline.generator import (
    generate_artifact,
    generate_homepage_summary,
    generate_infographic_image,
    generate_knowledge_graph,
    generate_plan,
    generate_playground_config,
    generate_preview_image,
    slugify,
)
from pipeline.llm_client import load_config
from pipeline.runtime import ensure_supported_python

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _record_status(stats: dict[str, int], status: str) -> None:
    if status == "generated":
        stats["generated"] += 1
    elif status == "skipped":
        stats["skipped"] += 1


def _clean_technique_outputs(slug: str) -> None:
    from pipeline.generator import CONTENT_DIR, technique_dir

    out_dir = technique_dir(slug, CONTENT_DIR)
    if out_dir.exists():
        shutil.rmtree(out_dir)
        logger.info("Removed existing generated artifacts for %s", slug)


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
        choices=["gemini"],
        help="Force a specific LLM provider for all text artifacts",
    )
    parser.add_argument(
        "--skip-images",
        action="store_true",
        help="Skip Nano Banana Pro image generation",
    )
    parser.add_argument(
        "--evaluate",
        action="store_true",
        help="Run the evaluation pipeline after generation",
    )
    parser.add_argument(
        "--skip-judge",
        action="store_true",
        help="Skip LLM judge evaluation (schema + static checks only)",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Delete generated outputs for the selected techniques before regenerating",
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

    all_technique_artifacts: dict[str, dict[str, dict]] = {}
    all_plans: dict[str, dict] = {}

    for technique_name in techniques:
        slug = slugify(technique_name)
        logger.info("=== Processing: %s (%s) ===", technique_name, slug)

        if args.clean:
            _clean_technique_outputs(slug)

        # Step 1: Generate plan
        try:
            plan_result = generate_plan(
                technique_name,
                force=args.force,
                provider_override=args.provider,
            )
            plan = plan_result.payload
            _record_status(stats, plan_result.status)
        except Exception as e:
            logger.error("Failed to generate plan for %s: %s", technique_name, e)
            stats["failed"] += 1
            continue

        all_plans[slug] = plan

        # Step 2: Generate each artifact type
        infographic_spec = None
        overview = None
        technique_artifacts: dict[str, dict] = {}
        for artifact_type in artifact_types:
            try:
                artifact_result = generate_artifact(
                    slug,
                    artifact_type,
                    plan,
                    force=args.force,
                    provider_override=args.provider,
                )
                result = artifact_result.payload
                if artifact_type == "infographic_spec":
                    infographic_spec = result
                if artifact_type == "overview":
                    overview = result
                technique_artifacts[artifact_type] = result
                _record_status(stats, artifact_result.status)
            except Exception as e:
                logger.error(
                    "Failed to generate %s for %s: %s",
                    artifact_type,
                    technique_name,
                    e,
                )
                stats["failed"] += 1

        all_technique_artifacts[slug] = technique_artifacts

        # Step 2b: Generate homepage summary (requires overview)
        if overview:
            try:
                summary_result = generate_homepage_summary(
                    slug,
                    plan,
                    overview,
                    force=args.force,
                    provider_override=args.provider,
                )
                _record_status(stats, summary_result.status)
            except Exception as e:
                logger.error(
                    "Failed to generate homepage summary for %s: %s",
                    technique_name,
                    e,
                )
                stats["failed"] += 1

        # Step 3: Generate infographic image
        if not args.skip_images and infographic_spec:
            try:
                image_result = generate_infographic_image(
                    slug, technique_name, infographic_spec, force=args.force
                )
                _record_status(stats, image_result.status)
            except Exception as e:
                logger.error(
                    "Failed to generate infographic image for %s: %s",
                    technique_name,
                    e,
                )
                stats["failed"] += 1

        # Step 4: Generate homepage preview image (consistent theme for thumbnails)
        if not args.skip_images:
            try:
                preview_result = generate_preview_image(
                    slug, technique_name, force=args.force
                )
                _record_status(stats, preview_result.status)
            except Exception as e:
                logger.error(
                    "Failed to generate preview image for %s: %s",
                    technique_name,
                    e,
                )
                stats["failed"] += 1

        # Step 5: Generate playground config
        try:
            pg_result = generate_playground_config(
                slug,
                technique_name,
                plan,
                force=args.force,
                provider_override=args.provider,
            )
            _record_status(stats, pg_result.status)
        except Exception as e:
            logger.error(
                "Failed to generate playground config for %s: %s",
                technique_name,
                e,
            )
            stats["failed"] += 1

    # Step 6: Generate knowledge graph (cross-technique, runs once after all plans)
    if all_plans:
        try:
            kg_result = generate_knowledge_graph(
                all_plans, force=args.force, provider_override=args.provider
            )
            _record_status(stats, kg_result.status)
        except Exception as e:
            logger.error("Failed to generate knowledge graph: %s", e)
            stats["failed"] += 1

    logger.info("=== Pipeline Summary ===")
    logger.info(
        "Generated: %d | Skipped: %d | Failed: %d",
        stats["generated"],
        stats["skipped"],
        stats["failed"],
    )

    # Step 4: Run evaluation pipeline if requested
    if args.evaluate:
        _run_evaluation(
            techniques,
            artifact_types,
            all_technique_artifacts,
            expected_techniques=config["techniques"],
            provider_override=args.provider,
            skip_judge=args.skip_judge,
        )

    if not args.technique:
        from pipeline.generate_use_case_matrix import main as generate_use_case_matrix

        try:
            generate_use_case_matrix(force=True)
            logger.info("Refreshed use case matrix")
        except Exception as e:
            logger.error("Failed to generate use case matrix: %s", e)


def _run_evaluation(
    techniques: list[str],
    artifact_types: list[str],
    all_artifacts: dict[str, dict[str, dict]],
    expected_techniques: list[str],
    provider_override=None,
    skip_judge: bool = False,
) -> None:
    """Run the evaluation pipeline on generated artifacts."""
    from pipeline.evaluate import evaluate_technique, save_metrics

    logger.info("=== Starting Evaluation Pipeline ===")

    metrics: dict[str, dict] = {"techniques": {}}
    eval_stats = {"passed": 0, "failed": 0, "total": 0}

    for technique_name in techniques:
        slug = slugify(technique_name)
        artifacts = all_artifacts.get(slug, {})
        if not artifacts:
            logger.warning("No artifacts to evaluate for %s", technique_name)
            continue

        result = evaluate_technique(
            slug,
            artifact_types,
            artifacts,
            provider_override=provider_override,
            skip_judge=skip_judge,
        )

        metrics["techniques"][slug] = {
            "technique_name": technique_name,
            "artifacts": result["artifacts"],
        }

        for art_type, art_result in result["artifacts"].items():
            eval_stats["total"] += 1
            if art_result["status"] == "passed":
                eval_stats["passed"] += 1
            else:
                eval_stats["failed"] += 1

    is_full_scope = sorted(techniques) == sorted(expected_techniques)
    metrics["evaluated_at"] = datetime.now(timezone.utc).isoformat()
    metrics["scope"] = {
        "type": "full" if is_full_scope else "partial",
        "technique_count": len(techniques),
        "expected_technique_count": len(expected_techniques),
        "technique_slugs": [slugify(name) for name in techniques],
        "artifact_types": artifact_types,
    }
    metrics["summary"] = {
        "passed": eval_stats["passed"],
        "failed": eval_stats["failed"],
        "total": eval_stats["total"],
    }

    saved_paths = save_metrics(metrics)

    logger.info("=== Evaluation Summary ===")
    logger.info(
        "Passed: %d | Failed: %d | Total: %d",
        eval_stats["passed"],
        eval_stats["failed"],
        eval_stats["total"],
    )

    if eval_stats["failed"] > 0:
        logger.warning(
            "%d artifact(s) failed evaluation — site build may be blocked",
            eval_stats["failed"],
        )
    logger.info("Evaluation metrics saved to %s", saved_paths["latest_path"])


if __name__ == "__main__":
    ensure_supported_python()
    main()
