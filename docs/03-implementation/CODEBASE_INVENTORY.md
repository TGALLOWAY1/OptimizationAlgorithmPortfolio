# Codebase Inventory

> Module-by-module map of the source tree. Status labels: Implemented · Partial · Stubbed · Broken · Designed only · Deprecated · Unknown.
> Last updated: 2026-05-28. Grounded in source reads (file:line cited).

## Repository layout

```
OptimizationAlgorithmPortfolio/
├── api/                       # Flask API blueprints + app factory
├── pipeline/                  # Content generation engine, LLM client, publisher
│   ├── agents/                # Multi-agent content pipeline agents
│   ├── content_pipeline/      # Multi-agent orchestrator, registry, gates, state
│   ├── prompts/               # Prompt templates (.md, {{var}} substitution)
│   │   └── content_pipeline/  # Agent-specific prompts
│   └── templates/             # Jinja2 HTML templates for the static site
├── tests/                     # pytest suite (20 files, 226 tests)
├── examples/                  # Multi-agent pipeline CLI driver + sample input
├── presentation_source/       # Markdown narrative/slide source (docs about the project)
├── content/                   # Tracked source inputs: reference facts, rubrics
├── generated/                 # Generated artifacts (gitignored)
├── site/                      # Published HTML (gitignored)
├── outputs/                   # Multi-agent run state (gitignored)
├── docs/                      # This documentation system
├── build_site.py              # GitHub Pages build entry point
├── requirements.txt, README.md, CLAUDE.md, SETUP.md, WOW_FACTOR_ANALYSIS.md, plan.md
```

## Pipeline core (`pipeline/`)

| Path | Responsibility | Key functions / classes | Status |
|---|---|---|---|
| `generate.py` | CLI orchestrator for single-shot per-artifact generation; optional evaluation | `main`, `_run_evaluation` (entry `:340-342`) | Implemented |
| `generator.py` | Artifact generation engine (plan, overview, math, impl, infographic, preview, homepage, knowledge graph, playground); manifest/hash idempotency | `generate_plan`, `generate_artifact`, `generate_infographic_image`, `generate_knowledge_graph`, `generate_playground_config`, `slugify`, `GenerationResult` | Implemented |
| `llm_client.py` | Provider abstraction + factory + retry + schema enforcement | `LLMProvider`, `GeminiProvider`, `NanoBananaProvider`, `get_provider`, `generate_with_retry`, `load_config`, `load_topic` | Implemented |
| `paths.py` | Centralized filesystem paths (env-overridable generated root) | `GENERATED_ROOT`, `GENERATED_TECHNIQUES_DIR`, `SITE_DIR`, `technique_dir` | Implemented |
| `runtime.py` | Python 3.11+ version guard | `ensure_supported_python` | Implemented |
| `schemas.py` | 16 JSON Schemas for all artifacts (per-technique + agent) | `SCHEMAS` dict (`:584-601`) | Implemented |
| `schema_validate.py` | Schema-validation stage wrapper | `validate_schema` | Implemented |
| `validator.py` | Content validation beyond schema (topic hints, length, LaTeX, pseudocode) | `validate_artifact`, per-type validators | Implemented |
| `evaluate.py` | Evaluation orchestrator (schema → static → code → judge) | `evaluate_technique`, `run_deterministic_checks`, `promote_artifact`, `save_metrics` | Implemented (promotion is a no-op rewrite, see Risks) |
| `retry_loop.py` | Judge-driven revision loop (max 3 attempts) | `retry_loop`, `revise_artifact` | Implemented |
| `judge.py` | LLM-as-judge (tool-using + legacy one-shot) | `evaluate_artifact`, `build_revision_prompt`, `load_rubrics` | Implemented (revision prompt has stale "optimization" wording, `:337`) |
| `judge_tools.py` | Tool registry for the tool-calling judge | `run_python_code`, `check_equation`, `verify_imports`, `dispatch_tool` | Implemented |
| `code_runner.py` | Subprocess Python execution + import allowlist (30s timeout) | `run_code`, `check_dependencies`, `validate_code_artifact` | Implemented (not sandboxed beyond allowlist — see Security) |
| `publish.py` | Static-HTML publisher (Jinja2 + markdown) | `publish`, `md_to_html`, `_publish_quality_report` (entry `:448-450`) | Implemented |
| `recommender_api.py` | Standalone Flask app for `/api/recommend` | `app` (Flask), `get_recommendations`, `recommend` | Implemented (separate Flask app — see Risks) |
| `generate_preview_images.py` | Batch homepage preview-thumbnail generation | `main` (entry `:36-42`) | Implemented |
| `generate_use_case_matrix.py` | Generate `use_case_matrix.json` for the recommender | `main` (entry `:93-100`) | Implemented |

## Multi-agent content pipeline (`pipeline/content_pipeline/` + `pipeline/agents/`)

> Independent of `pipeline.generate` (`content_pipeline/__init__.py:7-9`). Fully built and tested but **not** consumed by the published site or API.

| Path | Responsibility | Status |
|---|---|---|
| `content_pipeline/pipeline.py` | Sequential 8-stage orchestrator, resume, gate retries | Implemented (`cancel()` raises `NotImplementedError`, `:132-136`) |
| `content_pipeline/registry.py` | Ordered stage registry (rejects duplicate ids) | Implemented |
| `content_pipeline/state.py` | Run/stage state + atomic persistence | Implemented |
| `content_pipeline/history.py` | Browse prior runs on disk | Implemented |
| `content_pipeline/quality_gates.py` | 5 cross-stage gates (Intake/Outline/Draft/TechnicalReview/FinalQA) | Implemented (research + editor stages ungated) |
| `content_pipeline/prompts.py` | `{{var}}` template renderer | Implemented |
| `agents/base.py` | Agent ABC, result/metadata types, LLM helper | Implemented |
| `agents/intake_agent.py` | Raw input → ContentBrief | Implemented |
| `agents/research_agent.py` | Claims/assumptions/open-questions | Implemented |
| `agents/outline_agent.py` | Brief+research → outline | Implemented |
| `agents/drafting_agent.py` | Outline → markdown draft | Implemented |
| `agents/technical_reviewer_agent.py` | Draft → review report | Implemented |
| `agents/editor_agent.py` | Resolve review → edited draft | Implemented |
| `agents/repurposing_agent.py` | Edited draft → channel assets (optional) | Implemented |
| `agents/publishing_qa_agent.py` | Final publishability QA (optional) | Implemented |
| `agents/__init__.py` | `build_default_registry` wiring (8 stages) | Implemented |

## API (`api/`)

| Path | Responsibility | Status |
|---|---|---|
| `app.py` | App factory; registers compare/math_tutor/study_plan/adapt_code blueprints; proxies `/api/recommend`; serves static site | Implemented (recommender proxy is a fragile hack — see Risks) |
| `compare.py` | `/api/compare`, `/api/compare/slugs` | Implemented |
| `math_tutor.py` | `/api/math_tutor` (+ `/stream` SSE) | Implemented |
| `study_plan.py` | `/api/study_plan` (+ `/stream` SSE) | Implemented |
| `adapt_code.py` | `/api/adapt_code` | Implemented |

## Top-level scripts & examples

| Path | Responsibility | Status |
|---|---|---|
| `build_site.py` | GitHub Pages builder: full publisher if content exists, else placeholder landing page | Implemented (duplicates path constants instead of importing `pipeline.paths` — see Risks) |
| `examples/run_content_pipeline.py` | Multi-agent pipeline CLI driver (with `--dry-run` stub agents) | Implemented |
| `examples/sample_input.json` | Sample raw input for the multi-agent pipeline | Implemented |

## Entry points (runnable commands)

| Command | Purpose | Source |
|---|---|---|
| `python -m pipeline.generate [--technique --force --provider --skip-images --evaluate --skip-judge --clean]` | Generate artifacts for all/one technique | `pipeline/generate.py:340-342` |
| `python -m pipeline.publish` | Render generated artifacts → `site/` | `pipeline/publish.py:448-450` |
| `python -m pipeline.generate_use_case_matrix [--force]` | Generate use-case matrix | `pipeline/generate_use_case_matrix.py:93-100` |
| `python -m pipeline.generate_preview_images [--force]` | Generate preview thumbnails | `pipeline/generate_preview_images.py:36-42` |
| `python api/app.py` | Unified Flask app on `PORT` (default 5000) | `api/app.py:62-66` |
| `python -m pipeline.recommender_api` | Standalone recommender app | `pipeline/recommender_api.py:103-105` |
| `python build_site.py` | GitHub Pages build | `build_site.py:127-128` |
| `python examples/run_content_pipeline.py [--input --dry-run --resume]` | Run multi-agent pipeline | `examples/run_content_pipeline.py:320-321` |

## Known coupling / risk hotspots (see `docs/04-quality/`)

- **Recommender re-registration hack** — `pipeline/recommender_api.py` builds its own module-level Flask app; `api/app.py:28-38` proxies it via `test_request_context` + `full_dispatch_request`, dropping headers and nesting two Flask apps.
- **Four duplicate slugify implementations** — `generator.slugify` (`:55`), `publish._slugify` (`:39`), `build_site._slugify` (`:21`), plus re-slugging at `publish.py:344`.
- **`build_site.py` duplicates path constants** instead of importing `pipeline.paths` — ignores the `OPTIMIZATION_PORTFOLIO_GENERATED_ROOT` env override.
- **Evaluate "promotion" is a no-op** — `CANDIDATES_DIR`/`VALIDATED_DIR`/`CONTENT_DIR` all alias `GENERATED_TECHNIQUES_DIR` (`evaluate.py:29-31`).
- **Stale topic wording in code** — `judge.build_revision_prompt` says "expert in optimization algorithms" (`judge.py:337`).
- **Content validation is advisory at generation time** — `validate_artifact` errors only logged (`generator.py:298-306`); hard-blocking only under `--evaluate`.
