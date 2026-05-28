# CLAUDE.md

> **Documentation system:** A full, evidence-grounded documentation set lives in `docs/`. Start at `docs/00-overview/PROJECT_SNAPSHOT.md` and use `docs/07-ai-context/CONTEXT_LOADING_PROTOCOL.md` to load only the bundle relevant to your task. Trust `pipeline/config.json` + code over any prose when they disagree.

## Project Overview

**MCTS Strategy Portfolio** — an automated educational content generation platform that creates learning materials for **8 Monte Carlo Tree Search (MCTS) strategies**. Combines an LLM-driven content pipeline (Google Gemini), an interactive Flask API, and a static site publisher.

> Note: the repository/directory is still named "OptimizationAlgorithmPortfolio" for legacy reasons. The live topic is MCTS (`pipeline/config.json`).

## Quick Reference

```bash
# Install dependencies (on a fresh container also: pip install cffi)
pip install -r requirements.txt

# Run all tests — 226 tests, no API keys needed (all LLM calls are mocked)
# Current baseline: 220 pass, 6 fail (stale fixtures, see docs/04-quality/KNOWN_ISSUES.md #1)
python -m pytest tests/ -q

# Generate content for all techniques (requires GEMINI_API_KEY)
python -m pipeline.generate

# Generate a single technique
python -m pipeline.generate --technique "UCT (Upper Confidence Bounds for Trees)"

# Publish static HTML site to site/
python -m pipeline.publish

# Start Flask API server (static site + /api/*)
python api/app.py
```

## Repository Structure

```
OptimizationAlgorithmPortfolio/
├── api/                        # Flask API blueprints + app factory
│   ├── app.py                  # App factory; registers blueprints; proxies /api/recommend; serves site/
│   ├── adapt_code.py · compare.py · math_tutor.py · study_plan.py
├── pipeline/                   # Content generation engine
│   ├── generate.py             # CLI orchestrator (single-shot per-artifact pipeline)
│   ├── generator.py            # Artifact generation engine (manifest/hash idempotency)
│   ├── llm_client.py           # Gemini provider client (Gemini pro/flash + Nano Banana image)
│   ├── publish.py · build via build_site.py
│   ├── schemas.py · validator.py · schema_validate.py   # 16 JSON schemas + content rules
│   ├── evaluate.py · judge.py · judge_tools.py · retry_loop.py · code_runner.py  # eval/judge
│   ├── recommender_api.py · generate_use_case_matrix.py · generate_preview_images.py
│   ├── config.json             # Topic, techniques, providers, artifact_provider_map (source of truth)
│   ├── prompts/                # Prompt templates (.md, {{var}} substitution)
│   ├── templates/              # Jinja2 HTML templates
│   ├── agents/                 # Multi-agent content pipeline agents
│   └── content_pipeline/       # Multi-agent orchestrator, registry, gates, state
├── tests/                      # pytest suite — 20 files, 226 tests
├── examples/                   # Multi-agent pipeline CLI driver + sample input
├── docs/                       # Documentation system (see docs/00-overview/DOCUMENTATION_INDEX.md)
├── build_site.py               # GitHub Pages build (full publisher or placeholder)
├── requirements.txt · README.md · SETUP.md
```

## Architecture

### Content Pipeline (`pipeline/`)
- **Config-driven**: `config.json` maps techniques → artifact types → providers.
- **Gemini-only multi-model**: routes artifacts to `gemini` (gemini-3.1-pro-preview), `gemini_flash` (gemini-3.1-flash-preview), or `nano_banana` (gemini-3.1-flash-image-preview). All use `GEMINI_API_KEY`. **There is no OpenAI provider.**
- **Idempotent**: skips regeneration when an artifact's input hash is unchanged (`--force` overrides, `--clean` wipes).
- **Schema-validated**: generated JSON is validated against strict schemas in `schemas.py`; content rules in `validator.py` are advisory at generation time (blocking only under `--evaluate`).
- **Retry logic**: exponential backoff for API + schema-validation failures.

There are **two independent pipelines**: the single-shot `pipeline.generate` (the production path feeding the site/API) and the standalone multi-agent `pipeline/content_pipeline/` (built and tested, but not consumed by the site/API). See `docs/02-architecture/ARCHITECTURE.md`.

### Flask API (`api/`)
- 5 logical endpoints: `/api/recommend`, `/api/compare`, `/api/math_tutor` (+`/stream`), `/api/study_plan` (+`/stream`), `/api/adapt_code`. JSON POST in/out.
- Blueprint-based, registered in `app.py`. The recommender is a separate Flask app proxied in (see `docs/06-history/DECISION_LOG.md`).
- **No auth, no rate limiting, open CORS, `debug=True`** — local-dev posture. See `docs/04-quality/SECURITY_AND_PRIVACY_NOTES.md`.

### 8 MCTS Techniques
UCT · RAVE · Progressive History and Progressive Widening · NST · Rollout Policy Strategies · Opponent Modeling in MCTS · Root and Tree Parallelization · Adaptive Meta-Optimization.

### Artifact Types per Technique
`config.json artifact_types`: `overview`, `math_deep_dive`, `implementation`, `infographic_spec` (plus derived `plan`, `homepage_summary`, `playground_config`, `infographic.png`, `preview.png`, and a cross-technique `knowledge_graph`). There is **no `quiz` artifact** (documented historically but never built).

## Environment Variables

```bash
GEMINI_API_KEY=...   # The only key used — content generation + all API endpoints (Gemini + Nano Banana)
# Optional: OPTIMIZATION_PORTFOLIO_GENERATED_ROOT (relocates generated/), PORT (Flask port)
```

Not needed for running tests (all LLM calls are mocked).

## Testing

```bash
python -m pytest tests/ -q              # all tests
python -m pytest tests/test_schemas.py  # single file
python -m pytest tests/ -k "test_valid" # filter by name
```

- 226 tests across 20 files, all mocked. Current baseline: **220 pass, 6 fail** (stale optimization-era fixtures vs MCTS schema enums — `docs/04-quality/KNOWN_ISSUES.md` #1).
- Fresh container: `pip install cffi` first, or collection panics (`No module named '_cffi_backend'`).

## Code Conventions

- **Python 3.11+** (enforced by `runtime.py`). Type hints + docstrings on public functions. `logging` for output.
- Abstract base class (`LLMProvider`) + factory (`get_provider()`) for providers.
- Prompt templates use `{{variable}}` substitution.
- Configuration-driven routing — no hardcoded provider logic in business code.

## Key Patterns

- **Adding a new LLM provider**: subclass `LLMProvider` in `llm_client.py`, register in `get_provider()`, add to `config.json`.
- **Adding a new artifact type**: add schema in `schemas.py`, prompt in `prompts/`, validation in `validator.py`, routing in `config.json`. If it has a rendered enum, update the matching template + test fixtures (the #1 breakage source).
- **Adding a new API endpoint**: create a blueprint in `api/`, register in `api/app.py`.
- **Adding a new content agent**: create `pipeline/agents/<name>_agent.py` subclassing `ContentAgent`, add prompt to `pipeline/prompts/content_pipeline/`, add schema to `schemas.py`, add provider key to `config.json artifact_provider_map`, register in `build_default_registry()` in `pipeline/agents/__init__.py`. See `docs/content-pipeline-orchestration.md`.

## Important Notes

- `generated/`, `site/`, and `outputs/` are gitignored — produced at runtime. Tracked inputs: `content/reference/`, `content/rubrics.json`.
- No CI/CD currently runs tests; run them locally before pushing.
- Full pipeline run costs ~$4-10 in Gemini credits. Use `--skip-images` to reduce dev cost.
- The live GitHub Pages deploy serves a **placeholder** (CI doesn't run the pipeline); interactive `/api/*` tools require the local Flask app. See `docs/04-quality/KNOWN_ISSUES.md` #3.
