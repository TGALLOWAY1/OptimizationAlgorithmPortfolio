# Project Snapshot

> A fast, honest, evidence-grounded picture of the repo as it actually is today.
> Last updated: 2026-05-28 · Branch: `claude/codebase-docs-infrastructure-D1xBK`

## What this project is

An **automated educational-content generation platform** for **Monte Carlo Tree Search (MCTS) strategies**. It uses Google Gemini LLMs to generate structured learning artifacts (overviews, math deep-dives, implementation guides, infographics) for 8 MCTS techniques, then publishes them as a static HTML site and exposes interactive helper endpoints via a Flask API.

Source of truth for the topic is `pipeline/config.json:2-17` (topic = "MCTS Strategy Portfolio").

> **Naming caveat (important):** The repository, directory, `README.md`, `CLAUDE.md`, and `SETUP.md` still call this the "Optimization Algorithm Portfolio" and reference 8 optimization algorithms + OpenAI. **That naming is stale.** The live `config.json` defines an MCTS topic routed entirely to Gemini. Trust `config.json` and code over the prose docs. See `docs/04-quality/KNOWN_ISSUES.md`.

## The 8 techniques (`pipeline/config.json:8-17`)

UCT · RAVE · Progressive History and Progressive Widening · NST (N-gram Selection Technique) · Rollout Policy Strategies · Opponent Modeling in MCTS · Root and Tree Parallelization · Adaptive Meta-Optimization

## Three subsystems

| Subsystem | What it does | Entry point | Status |
|---|---|---|---|
| **Content pipeline (single-shot)** | Generates fixed artifact types per technique, validates against JSON Schemas, writes to `generated/` | `python -m pipeline.generate` | Implemented |
| **Static site publisher** | Renders generated artifacts into HTML in `site/`; GitHub Pages deploy | `python -m pipeline.publish` / `python build_site.py` | Implemented |
| **Flask API** | 5 interactive endpoints (recommend, compare, math_tutor, study_plan, adapt_code) + static serving | `python api/app.py` | Implemented |
| **Multi-agent content pipeline** | Independent 8-stage agent orchestrator (intake→…→QA) with quality gates | `python examples/run_content_pipeline.py` | Implemented, **no production consumer** (see note) |

> The multi-agent pipeline (`pipeline/content_pipeline/` + `pipeline/agents/`) is fully built and tested but is **not** wired into the published site or the API. It is a standalone/demonstration subsystem. The single-shot `pipeline.generate` path is what feeds the site and API. Evidence: `pipeline/content_pipeline/__init__.py:7-9`; nothing in `publish.py`/`api/` reads `outputs/runs/`.

## Tech stack

- **Language:** Python 3.11+ (enforced by `pipeline/runtime.py:8-20`)
- **LLM provider:** Google Gemini only — `gemini-3.1-pro-preview`, `gemini-3.1-flash-preview`, `gemini-3.1-flash-image-preview` ("nano_banana"), all using `GEMINI_API_KEY` (`config.json:24-37`)
- **Web:** Flask 3 + flask-cors
- **Templating:** Jinja2 (`pipeline/templates/`)
- **Validation:** `jsonschema` (Draft 2020-12)
- **Images:** Pillow
- **No database.** "Entities" are JSON artifacts validated against schemas in `pipeline/schemas.py`. All outputs (`generated/`, `site/`, `outputs/`) are gitignored.

## Build / test / run commands

```bash
pip install -r requirements.txt          # see env caveat below
python -m pytest tests/ -q               # test suite
python -m pipeline.generate              # generate all techniques (needs GEMINI_API_KEY)
python -m pipeline.publish               # render static site to site/
python build_site.py                     # GitHub Pages build (full or placeholder)
python api/app.py                        # Flask app on :5000
```

> **Test environment caveat:** A fresh container needs `cffi` installed for the system `cryptography` package (pulled in transitively by `google-genai`) to import — otherwise pytest collection panics with `pyo3_runtime.PanicException: No module named '_cffi_backend'`. Fix: `pip install cffi`. This is an environment quirk, not a code bug.

## Current test status (verified 2026-05-28)

**226 tests collected · 220 passing · 6 failing.**

The 6 failures are **stale optimization-era test fixtures** not updated during the MCTS retarget:

| Test | Cause |
|---|---|
| `test_validator.py::TestImplementationValidator::test_wrong_technique_example_is_rejected` | Asserts `bfgs` flagged; validator now uses MCTS hints |
| `test_wow_features.py::TestKnowledgeGraphSchema::test_valid_graph` | Fixture category `evolutionary` not in MCTS enum |
| `test_wow_features.py::TestKnowledgeGraphSchema::test_all_valid_categories` | Uses old optimization categories |
| `test_wow_features.py::TestPlaygroundConfigSchema::test_valid_config` | `visualization_type: contour_trajectory` not in MCTS enum |
| `test_wow_features.py::TestPlaygroundConfigSchema::test_all_valid_objective_functions` | `objective_function: sphere/rosenbrock/...` not in MCTS enum |
| `test_wow_features.py::TestPlaygroundConfigSchema::test_parameter_with_description` | Same playground-enum mismatch |

> `CLAUDE.md` claims "70 tests, all passing." Reality: 226 tests, 6 broken. See `docs/04-quality/KNOWN_ISSUES.md`.

## Where to start

- New human contributor → `docs/00-overview/README.md`, then `docs/01-product/PRODUCT_BRIEF.md`
- New AI agent → `docs/07-ai-context/CONTEXT_LOADING_PROTOCOL.md`
- Understand the code → `docs/03-implementation/CODEBASE_INVENTORY.md`
- Understand the design → `docs/02-architecture/ARCHITECTURE.md`
- What's broken / risky → `docs/04-quality/KNOWN_ISSUES.md`, `docs/04-quality/RISK_REGISTER.md`
- What to do next → `docs/05-planning/NEXT_AGENT_TASKS.md`
