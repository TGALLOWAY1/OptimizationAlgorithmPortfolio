# Architecture

> How the system works internally. Evidence-grounded; cites file:line.
> Last updated: 2026-05-28.

## System overview

The platform is a **batch content generator + static publisher + thin API layer**, all backed by Google Gemini. There is no database and no persistent server state — "state" is JSON/PNG files on disk. Three cooperating subsystems plus one independent subsystem:

1. **Single-shot content pipeline** (`pipeline/generate.py` + `generator.py`) — the production content path.
2. **Static site publisher** (`pipeline/publish.py` + `templates/`) — turns artifacts into HTML.
3. **Flask API** (`api/` + `recommender_api.py`) — interactive, per-request LLM tools.
4. **Multi-agent content pipeline** (`pipeline/content_pipeline/` + `agents/`) — an independent, gated authoring workflow with **no production consumer**.

Shared foundation across all four: the LLM client (`llm_client.py`), the schema registry (`schemas.py`), config (`config.json`), and the `{{var}}` prompt idiom.

## Major modules

| Layer | Modules | Role |
|---|---|---|
| Config & paths | `config.json`, `paths.py`, `runtime.py` | Topic/provider routing, filesystem layout, version guard |
| LLM access | `llm_client.py` | Provider abstraction, factory, retry, schema enforcement, streaming, tool-use |
| Generation | `generate.py`, `generator.py` | Orchestration + per-artifact engine with manifest idempotency |
| Validation | `schemas.py`, `validator.py`, `schema_validate.py` | Structure + content rules |
| Evaluation | `evaluate.py`, `judge.py`, `judge_tools.py`, `retry_loop.py`, `code_runner.py` | LLM-as-judge with tool use + revision loop + code execution |
| Publishing | `publish.py`, `build_site.py`, `templates/` | Static HTML rendering + Pages build |
| API | `api/app.py`, `compare.py`, `math_tutor.py`, `study_plan.py`, `adapt_code.py`, `recommender_api.py` | Interactive endpoints |
| Multi-agent | `content_pipeline/*`, `agents/*` | Independent gated authoring workflow |

## Runtime flow — content generation

`python -m pipeline.generate` (`generate.py:340-342`):
1. `ensure_supported_python()` → load `config.json` (`generate.py:341,87-89`).
2. Per technique: `slugify(name)` → `generate_plan()` (`generate.py:104,112`). Plan generation loads `planner_prompt.md`, computes a SHA-256 input hash (version + prompt + schema + config slice + materials), and reuses the cached artifact if the hash matches (`generator.py:112-160`).
3. On a cache miss: substitute `{{vars}}` → `get_provider("plan")` → `generate_with_retry()` which calls `provider.generate()` then `jsonschema.validate`, retrying ≤3× with backoff (`llm_client.py:289-317`).
4. For each artifact type (`overview`, `math_deep_dive`, `implementation`, `infographic_spec`): `generate_artifact()` repeats the pattern and additionally runs `validate_artifact()` whose errors are **logged but non-fatal** (`generator.py:298-306`).
5. Derived artifacts: homepage summary (needs overview), infographic + preview images (unless `--skip-images`), playground config.
6. Cross-technique: `knowledge_graph.json` once after all plans (`generator.py:544-588`).
7. Optional `--evaluate`: schema → static checks → code execution → judge + revise (`evaluate.py:144-218`).
8. Outputs to `generated/` (gitignored).

## Runtime flow — multi-agent pipeline

`ContentPipeline.run()` (`content_pipeline/pipeline.py:53-128`):
1. `build_default_registry()` wires 8 ordered stages with gates (`agents/__init__.py:37-96`): intake(IntakeGate) → research → outline(OutlineGate) → draft(DraftGate) → technical_review(TechnicalReviewGate) → editor → repurposing(optional) → publishing_qa(optional, FinalQAGate).
2. Creates a run id + `run.json` under `outputs/runs/<run_id>/`.
3. Each stage: agent pulls dependencies from `previous_outputs`, renders its prompt, calls `_call_llm()` → `get_provider(ARTIFACT_TYPE)` + `generate_with_retry` against `SCHEMAS[SCHEMA_KEY]` (`agents/base.py:80-97`).
4. Stage output written; if a gate exists it runs; on failure (with attempts left) → `NEEDS_REVISION`, gate feedback fed back, stage re-run up to `max_revisions+1` times (`pipeline.py:181-252`).
5. Resume supported via `resume_run_id` (skips already-succeeded stages).
6. Finalize writes derived markdown; status → `COMPLETED`.

## Data flow & storage model

```
config.json ──► generator ──► generated/techniques/<slug>/*.json + *.png + manifest.json
                    │                         │
                    └──► generated/knowledge_graph.json, use_case_matrix.json
                                              │
                              publish.py ─────┴──► site/*.html + site/images/<slug>/
                                                          │
                          GitHub Pages (static)  ◄────────┘   (or)  Flask app.py ──► /api/* (live Gemini)

examples/run_content_pipeline.py ──► content_pipeline ──► outputs/runs/<run_id>/  (NOT consumed by site/API)
```

All output roots (`generated/`, `site/`, `outputs/`) are gitignored. Tracked inputs: `content/reference/<slug>.json`, `content/rubrics.json`. Detail in `docs/02-architecture/DATA_MODEL.md` and `docs/02-architecture/STATE_MANAGEMENT.md`.

## Auth flow

**None.** No authentication, authorization, sessions, or rate limiting exist anywhere. Every API endpoint is an open, unauthenticated proxy to a paid Gemini API. CORS is fully open (`CORS(app)`). See `docs/04-quality/SECURITY_AND_PRIVACY_NOTES.md`.

## External services

- **Google Gemini** (`google-genai`) — the only external dependency at runtime: `gemini-3.1-pro-preview`, `gemini-3.1-flash-preview`, `gemini-3.1-flash-image-preview`. Single key `GEMINI_API_KEY`.
- **CDNs (browser only):** KaTeX, highlight.js, D3 v7 — loaded by templates; offline → no math rendering / highlighting / graph.
- **GitHub Pages / Actions** — deployment. See `docs/02-architecture/INTEGRATIONS.md`.

## Important boundaries

- **Generation vs. serving:** content is generated offline (batch) and served statically or via Flask. The API does *not* generate technique artifacts; it generates ephemeral per-request responses (recommend/compare/etc.).
- **Schema key vs. provider key:** agents declare a `SCHEMA_KEY` (entry in `SCHEMAS`) separate from `ARTIFACT_TYPE` (key in `config.json artifact_provider_map`). Per-technique artifacts collapse these into one name.
- **Two pipelines:** `generate.py` (production) and `content_pipeline/` (standalone) share only the LLM client, schemas, config, and prompt idiom.

## Areas of architectural risk

1. **Recommender re-registration hack** — `recommender_api.py` builds its own Flask app; `api/app.py:28-38` nests it via `test_request_context` + `full_dispatch_request`, dropping headers and running two Flask apps in one process.
2. **Four duplicate slugify implementations** (`generator.py:55`, `publish.py:39`, `build_site.py:21`, `publish.py:344`) — drift would break slug↔file matching silently.
3. **`build_site.py` hardcodes path constants** instead of importing `pipeline.paths` — ignores the generated-root env override.
4. **Evaluate "promotion" is a no-op** — candidate/validated/content dirs all alias the same directory (`evaluate.py:29-31`).
5. **Content validation advisory at generation** — weak artifacts publish unless `--evaluate` is run.
6. **Topic drift in code & templates** — judge revision prompt and playground/knowledge-graph templates still assume the old optimization domain.
7. **Process-global, non-thread-safe provider cache** (`llm_client.py:245`) under Flask threaded serving.

Full risk treatment in `docs/04-quality/RISK_REGISTER.md`.
