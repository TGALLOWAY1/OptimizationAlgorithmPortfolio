# Current Behavior

> What actually happens when you run the project today. Describes observed/evidence-based behavior, not intentions.
> Last updated: 2026-05-28.

## The two execution contexts (this distinction matters)

| | **Local full run** (Flask + generated content) | **Live GitHub Pages** |
|---|---|---|
| Content | Real generated technique pages | Placeholder cards only |
| Recommender / Compare / Study Plan / Math Tutor / Adapt Code | Work (call local `/api/*`) | **Broken** (no Python backend; `fetch` 404s) |
| Knowledge graph / Playground | Render client-side | Render only if data committed (it isn't) |
| Why | You ran `pipeline.generate` + `pipeline.publish` + `api/app.py` | CI runs only `build_site.py`; `generated/` is gitignored |

Everything below assumes a correctly configured local environment unless noted.

## `python -m pipeline.generate` (with `GEMINI_API_KEY`)

1. Enforces Python 3.11+ (`runtime.py`), loads `config.json`.
2. For each of the 8 techniques: generates `plan.json`, then `overview/math_deep_dive/implementation/infographic_spec.json`, `homepage_summary.json`, `infographic.png` + `preview.png` (unless `--skip-images`), `playground_config.json`.
3. Generates one cross-technique `knowledge_graph.json`.
4. Idempotent: skips artifacts whose input hash is unchanged (use `--force` to override; `--clean` to wipe first).
5. Each artifact is JSON-schema-validated with retry (2s/4s backoff). Content-rule violations are **logged as warnings but do not stop writing** the artifact.
6. With `--evaluate`: runs schema → static checks → code execution (for implementation) → LLM judge → up to 3 revise attempts; writes metrics under `generated/evaluations/`.
7. Outputs land in `generated/` (gitignored).

**Failure modes:** missing `GEMINI_API_KEY` → `ValueError` at provider construction; persistent schema-validation failure → `RuntimeError` after 3 retries; per-technique errors are caught and logged so one failure doesn't abort the whole run (`generate.py` has broad try/except per stage).

## `python -m pipeline.publish`

Renders `generated/` artifacts into `site/`: `index.html`, one `<slug>.html` per technique (flat at site root), `compare.html`, `use-case-matrix.html` (only if matrix JSON exists), `quality-report.html` (only if evaluation metrics exist), and copies images to `site/images/<slug>/`. Compare/quality rendering is wrapped in try/except so a render error skips that page rather than crashing.

## `python build_site.py`

If `generated/techniques/` has content → runs the full publisher. Otherwise → writes a **placeholder** `index.html` with one "Coming Soon" card per technique and no interactive widgets. This is what CI publishes.

## `python api/app.py`

Starts Flask on port 5000 (`debug=True`), registers blueprints for compare/math_tutor/study_plan/adapt_code, proxies `/api/recommend` to the standalone recommender app, and serves the static `site/` directory. CORS is wide open; there is no authentication or rate limiting. Every endpoint makes a live Gemini call per request.

**Observed endpoint behavior:**
- `POST /api/recommend {query}` → 2-3 recommendations or 400/500.
- `POST /api/compare {slug_a, slug_b}` → comparison object; 400 on missing/identical slugs, 404 if a slug has no artifacts.
- `POST /api/math_tutor` and `/stream` → explanation (JSON or SSE).
- `POST /api/study_plan` and `/stream` → roadmap (JSON or SSE).
- `POST /api/adapt_code {source_code, target_framework}` → adapted code (text).
- `GET /`, `/<page>.html`, `/images/<path>` → static files (404 if absent).

## `python examples/run_content_pipeline.py`

Runs the independent multi-agent pipeline. `--dry-run` uses canned stub agent outputs (no API calls) for an offline smoke test; otherwise each stage calls Gemini. Writes run state and per-stage JSON to `outputs/runs/<run_id>/`, plus derived markdown (`draft.md`, `edited-draft.md`, per-channel repurposed files) on completion. This output is **not** consumed by the site or API.

## `python -m pytest tests/`

226 tests collected, **220 pass, 6 fail**. The 6 failures are stale optimization-era fixtures (`sphere`, `evolutionary`, `bfgs`, `contour_trajectory`) that don't match the MCTS schema enums. All tests are mocked (no API keys/network). On a fresh container, install `cffi` first or collection panics.

## Known behavioral gaps (summary)

- **Playground** animates gradient descent on a 2D function for every MCTS technique (wrong algorithm + wrong domain).
- **Knowledge-graph** nodes render gray because the legend categories are from the optimization taxonomy.
- **Live site** shows placeholder content and non-functional interactive tools.
- **Content validation** doesn't block publishing of weak artifacts unless `--evaluate` is used.

See `docs/04-quality/KNOWN_ISSUES.md` for the prioritized issue list.
