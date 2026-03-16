# CLAUDE.md

## Project Overview

Optimization Algorithm Portfolio — an automated educational content generation platform that creates comprehensive learning materials for 8 optimization algorithms. Combines an LLM-driven content pipeline, interactive Flask API, and static site publisher.

## Quick Reference

```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests (70 tests, no API keys needed — all LLM calls are mocked)
python -m pytest tests/ -v

# Generate content for all techniques (requires API keys)
python -m pipeline.generate

# Generate single technique
python -m pipeline.generate --technique "Bayesian Optimization"

# Publish static HTML site to site/
python -m pipeline.publish

# Start Flask API server
python api/app.py
```

## Repository Structure

```
OptimizationAlgorithmPortfolio/
├── api/                        # Flask API blueprints
│   ├── app.py                  # App factory, blueprint registration
│   ├── adapt_code.py           # Code framework adaptation endpoint
│   ├── compare.py              # Algorithm comparison endpoint
│   ├── math_tutor.py           # Math equation explanation endpoint
│   └── study_plan.py           # Learning roadmap endpoint
├── pipeline/                   # Content generation pipeline
│   ├── generate.py             # CLI entry point / orchestrator
│   ├── generator.py            # Artifact generation engine
│   ├── llm_client.py           # Multi-provider LLM client (OpenAI, Gemini, Nano Banana Pro)
│   ├── publish.py              # Static HTML publisher
│   ├── schemas.py              # JSON Schema definitions for all artifacts
│   ├── validator.py            # Content validation rules
│   ├── recommender_api.py      # Algorithm recommender endpoint
│   ├── config.json             # Technique list, provider config, routing
│   ├── prompts/                # Jinja2-style prompt templates (.md)
│   └── templates/              # Jinja2 HTML templates
├── tests/                      # pytest test suite (7 files, 70 tests)
│   ├── test_generator.py       # Slugify, idempotency
│   ├── test_llm_client.py      # Provider routing, retries
│   ├── test_schemas.py         # JSON Schema validation
│   ├── test_new_schemas.py     # Extended schema coverage
│   ├── test_validator.py       # Content validation rules
│   ├── test_api_endpoints.py   # Flask endpoint tests
│   └── test_recommender_api.py # Recommender endpoint tests
├── content/                    # Generated artifacts (gitignored)
├── site/                       # Published HTML output (gitignored)
├── requirements.txt            # Python dependencies
├── SETUP.md                    # Setup instructions and cost estimates
└── plan.md                     # Implementation plan
```

## Architecture

### Content Pipeline (`pipeline/`)
- **Config-driven**: `config.json` maps techniques → artifact types → LLM providers
- **Multi-provider**: Routes artifacts to OpenAI (gpt-4o), Gemini (gemini-3.1-pro-preview), or Nano Banana Pro based on config
- **Idempotent**: Skips regeneration if artifact files already exist (use `--force` to override)
- **Schema-validated**: All generated JSON artifacts are validated against strict JSON Schemas in `schemas.py`
- **Retry logic**: Exponential backoff (2s, 4s, 8s) for API calls and schema validation failures

### Flask API (`api/`)
- 5 endpoints: `/api/recommend`, `/api/compare`, `/api/math_tutor`, `/api/study_plan`, `/api/adapt_code`
- All accept JSON POST requests, return JSON responses
- Blueprint-based architecture registered in `app.py`

### 8 Optimization Techniques
Bayesian Optimization, Genetic Algorithm, Simulated Annealing, Particle Swarm Optimization, Gradient Descent, Nelder-Mead Simplex, CMA-ES, Differential Evolution

### Artifact Types per Technique
`plan.json`, `overview.json`, `math_deep_dive.json`, `implementation.json`, `infographic_spec.json`, `quiz.json`, `infographic.png`

## Environment Variables

```bash
OPENAI_API_KEY=sk-...     # Required for content generation and API
GEMINI_API_KEY=...        # Required for content generation (Gemini + Nano Banana Pro)
```

Not needed for running tests (all LLM calls are mocked).

## Testing

```bash
python -m pytest tests/ -v              # All tests, verbose
python -m pytest tests/ -q              # All tests, quiet
python -m pytest tests/test_schemas.py  # Single file
python -m pytest tests/ -k "test_valid" # Filter by name
```

- All 70 tests use `unittest.mock` — no real API keys or network calls required
- Tests cover: schema validation, content validation, API endpoints, generator logic, LLM client routing

## Code Conventions

- **Python 3.11+** required
- Type hints on function signatures
- Docstrings on all public functions
- `logging` module for all log output
- Abstract base class (`LLMProvider`) for provider extensibility
- Factory pattern (`get_provider()`) for provider selection
- Prompt templates use `{{variable}}` placeholder syntax
- Configuration-driven routing — no hardcoded provider logic in business code

## Key Patterns

- **Adding a new LLM provider**: Subclass `LLMProvider` in `llm_client.py`, register in `get_provider()`, add to `config.json`
- **Adding a new artifact type**: Add schema in `schemas.py`, prompt template in `prompts/`, validation in `validator.py`, routing in `config.json`
- **Adding a new API endpoint**: Create blueprint in `api/`, register in `api/app.py`

## Important Notes

- `content/` and `site/` directories are gitignored — generated at runtime
- No CI/CD pipeline exists; run tests locally before pushing
- Full pipeline run costs ~$4-10 in API credits
- Use `--skip-images` flag to avoid expensive image generation during development
