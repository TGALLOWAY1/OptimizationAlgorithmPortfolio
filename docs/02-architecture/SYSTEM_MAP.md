# System Map

> Module-level dependency and data-flow map. Companion to `ARCHITECTURE.md`.
> Last updated: 2026-05-28.

## Component diagram (text)

```
                         ┌──────────────────────────────────────────┐
                         │            pipeline/config.json            │
                         │  topic · techniques · providers · routing  │
                         └───────────────┬────────────────────────────┘
                                         │ load_config / load_topic
                ┌────────────────────────┼─────────────────────────────┐
                │                         │                             │
        ┌───────▼────────┐      ┌─────────▼─────────┐         ┌─────────▼──────────┐
        │  generate.py    │      │   llm_client.py    │         │    schemas.py       │
        │ (orchestrator)  │─────►│ get_provider /      │◄────────│  SCHEMAS registry   │
        └───────┬────────┘      │ generate_with_retry │         └─────────┬──────────┘
                │               │ Gemini / NanoBanana │                   │
        ┌───────▼────────┐      └─────────┬──────────┘          ┌─────────▼──────────┐
        │  generator.py   │                │                    │ validator.py /      │
        │ artifact engine │                │                    │ schema_validate.py  │
        │ + manifest hash │                ▼                    └─────────────────────┘
        └───────┬────────┘        Google Gemini API
                │ writes
        ┌───────▼─────────────────────────────────────┐
        │ generated/techniques/<slug>/*.json + *.png   │
        │ generated/{knowledge_graph,use_case_matrix}  │
        └───────┬───────────────────────────┬──────────┘
                │ read                       │ read
        ┌───────▼────────┐          ┌────────▼─────────┐
        │  evaluate.py    │          │   publish.py      │──► site/*.html + site/images/
        │ judge/retry/    │          │  + templates/     │        │
        │ code_runner     │          └───────────────────┘        │
        └────────────────┘                                        ▼
                                              ┌───────────────────────────────┐
                                              │  GitHub Pages (static)  OR     │
                                              │  api/app.py (static + /api/*)  │
                                              └───────────────┬───────────────┘
                                                              │ per-request
                                                              ▼  live Gemini
                                              recommend / compare / math_tutor /
                                              study_plan / adapt_code

   ── independent subsystem (no production consumer) ────────────────────────────
        examples/run_content_pipeline.py
              │
        content_pipeline/pipeline.py ──► agents/* (8 stages) ──► outputs/runs/<run_id>/
              │  uses quality_gates.py, registry.py, state.py, history.py
              └─ shares: llm_client.py, schemas.py, config.json, prompt idiom
```

## Dependency notes

- `api/app.py` imports the **four blueprints** plus the **recommender Flask app object** (not a blueprint) and proxies it (`app.py:8-12,28-38`).
- `build_site.py` does **not** import `pipeline.paths`; it redefines `PROJECT_ROOT`/`SITE_DIR`/`GENERATED_TECHNIQUES_DIR`/`_slugify` locally (`build_site.py:15-25`).
- `generate_use_case_matrix.py` rides `get_provider("overview")` to reach `gemini_flash` (`:83`) — semantic mismatch, behaviorally correct.
- `agents/__init__.py:build_default_registry` lazily imports agents to avoid an import cycle (`:37-96`).

## Module call-ins (who calls the LLM client)

| Caller | Provider key(s) | Path |
|---|---|---|
| `generator.py` | plan, overview, math_deep_dive, implementation, infographic_spec, homepage_summary, infographic_image, knowledge_graph, playground_config | content generation |
| `judge.py` | judge | evaluation |
| `recommender_api.py` | recommender | `/api/recommend` |
| `compare/math_tutor/study_plan/adapt_code.py` | compare, math_tutor, study_plan, adapt_code | API endpoints |
| `generate_use_case_matrix.py` | overview (reused) | matrix generation |
| `agents/*.py` | agent_intake … agent_publishing_qa | multi-agent pipeline |

## Where to look first by task

- Change generation behavior → `generate.py`, `generator.py`
- Change/inspect an artifact shape → `schemas.py`, `validator.py`
- Change provider/model routing → `config.json`, `llm_client.py:get_provider`
- Change a page's HTML → `templates/*.html`, `publish.py`
- Change an API endpoint → `api/<endpoint>.py`, register in `api/app.py`
- Change the agent workflow → `content_pipeline/`, `agents/`
