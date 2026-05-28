# Regression Checklist

> Manual + automated checks to run before merging changes. Tailored to this repo's failure modes.
> Last updated: 2026-05-28.

## Always (every change)

- [ ] `pip install cffi` (fresh container) then `python -m pytest tests/ -q` — note the current baseline is **220 pass / 6 known fail** (Issue #1). New failures beyond those 6 are regressions.
- [ ] `git status` clean of unintended files; no secrets staged (`.env`).
- [ ] No new stale-domain wording introduced (grep `optimization algorithm`, `OpenAI`, `gpt-4o`).

## Schema / data model changes (`pipeline/schemas.py`, `validator.py`)

- [ ] Update the matching fixtures in `tests/test_schemas.py`, `test_new_schemas.py`, `test_validator.py`, `test_wow_features.py` (enum changes are the #1 breakage source).
- [ ] If you change an enum (`objective_function`, `visualization_type`, knowledge_graph `category`), update **both** the schema and the templates that render it (`playground_component.html`, `knowledge_graph_component.html`).
- [ ] Confirm `additionalProperties: False` is intentional on any new schema.

## Generation pipeline changes (`generate.py`, `generator.py`, `llm_client.py`)

- [ ] `python -m pipeline.generate --technique "UCT (Upper Confidence Bounds for Trees)" --skip-images` (with a key) completes and writes `generated/techniques/uct-.../*.json`.
- [ ] Idempotency: rerun without `--force` skips unchanged artifacts; with `--force` regenerates.
- [ ] Provider routing unchanged unless intended (`config.json artifact_provider_map`).

## Publisher / template changes (`publish.py`, `templates/`)

- [ ] `python -m pipeline.publish` renders `site/index.html` + per-technique pages without exceptions.
- [ ] Technique page: derivation accordions expand, code-variation tabs switch, sections gracefully omitted when an artifact is missing.
- [ ] Knowledge-graph legend matches MCTS categories; nodes are colored (not all gray) — see Issue #4.
- [ ] Playground reflects the technique (tracking Issue #2).
- [ ] `compare.html`, `use-case-matrix.html`, `quality-report.html` render when their data exists; no dangling links.

## API changes (`api/*.py`, `recommender_api.py`)

- [ ] `python api/app.py`; each endpoint returns expected shape with valid input and 400/404 with invalid input.
- [ ] Stream vs non-stream variants stay consistent (math_tutor, study_plan) — watch for prompt/validation drift (Debt #2/#3).
- [ ] `/api/recommend` still works through the proxy (Issue #10).
- [ ] No new auth/CORS regressions; `debug` flag intentional.

## Multi-agent pipeline changes (`content_pipeline/`, `agents/`)

- [ ] `python examples/run_content_pipeline.py --dry-run` completes all 8 stages with stub agents.
- [ ] Adding/renaming a stage updates all 5 touch points (schema, prompt, provider key, agent class, registry) — see `CLAUDE.md` key patterns.
- [ ] Gate thresholds unchanged unless intended.

## Visual (when content is available)

- [ ] Capture/compare screenshots per `docs/08-visuals/VISUAL_REGRESSION_PLAN.md` for homepage + one technique page at desktop + mobile widths.
