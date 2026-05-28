# Testing Strategy

> What's tested, what isn't, and how to run it. Verified 2026-05-28.

## How to run

```bash
pip install -r requirements.txt
pip install cffi          # fresh-container fix (see note)
python -m pytest tests/ -q
```

> **Fresh-container note:** without `cffi`, collection panics with `pyo3_runtime.PanicException: No module named '_cffi_backend'` (system `cryptography`, pulled in by `google-genai`, can't load). This is environment-only.

## Current status (verified)

**226 tests collected · 220 passing · 6 failing.** All failures are stale optimization-era fixtures clashing with the migrated MCTS schema enums (see `docs/04-quality/KNOWN_ISSUES.md`, issue #1). All tests use `unittest.mock` — no API keys or network calls.

## Test inventory (20 files)

| File | Covers | ~tests |
|---|---|---|
| `test_api_endpoints.py` | Flask endpoints (adapt_code, compare, math_tutor, study_plan) | 16 |
| `test_code_runner.py` | Sandboxed code execution | 15 |
| `test_content_agents.py` | All 8 agents + base | 14 |
| `test_content_pipeline.py` | Orchestrator, gates, registry, state | 7 |
| `test_evaluate.py` | Evaluation scoring / placeholder detection | 19 |
| `test_generator.py` | slugify + idempotency | 6 |
| `test_judge.py` | LLM-judge prompts/flow | 8 |
| `test_judge_tools.py` | Judge tools + tool loop | 29 |
| `test_llm_client.py` | Provider routing / retries | 9 |
| `test_new_schemas.py` | Extended schemas | 9 |
| `test_publish_rendering.py` | Markdown/LaTeX rendering helpers | 8 |
| `test_quality_gates.py` | Quality gates | 16 |
| `test_quality_report.py` | Quality-report rendering | 3 |
| `test_recommender_api.py` | Recommender endpoint | 9 |
| `test_retry_loop.py` | Retry/backoff | 5 |
| `test_runtime.py` | Python version guard | 2 |
| `test_schema_validate.py` | Schema-validation wrapper | 6 |
| `test_schemas.py` | Core schemas | 7 |
| `test_validator.py` | Content validation rules | 16 |
| `test_wow_features.py` | KnowledgeGraph/Playground schemas, streaming, generator features | 22 |

## Coverage gaps (highest first)

| Module | Coverage | Risk | Why it matters |
|---|---|---|---|
| `pipeline/generate.py` (342 lines) | **None** (no test imports it) | High | The top-level orchestrator; 8 broad `except` blocks and all CLI flags untested |
| `pipeline/publish.py` (450 lines) | Partial (only rendering helpers) | High | Page assembly + data loading + error paths untested; largest file |
| `pipeline/generate_use_case_matrix.py` | None | Medium | Failure silently degrades the recommender |
| `pipeline/generate_preview_images.py` | None | Low/Med | Side-effect heavy image gen |
| `content_pipeline/state.py`, `history.py` | Indirect only | Medium | Resume-by-run-id lightly covered |
| `api/app.py` factory | Indirect | Low | Exercised via endpoint tests |

## Conventions

- Pure `unittest`/`pytest` with `unittest.mock`; providers and the Gemini SDK are always mocked.
- No fixtures hit the network or filesystem-of-record beyond temp dirs.
- No CI exists (`CLAUDE.md:129`) — the red suite went undetected. Adding a minimal GitHub Actions `pytest` job is the top testing-infra recommendation (`docs/05-planning/BACKLOG.md`).

## What good test hygiene looks like here

1. Keep schema fixtures in sync with `pipeline/schemas.py` enums when the topic changes (the current breakage is exactly this failure mode).
2. Add at least smoke coverage for `generate.py` and `publish.py` page assembly (mock the provider, assert files written / HTML rendered).
3. Run the suite before every push (no CI gate yet).
