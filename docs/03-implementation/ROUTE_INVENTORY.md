# Route Inventory

> Every URL the project serves, what file/handler backs it, and whether it needs the Flask backend.
> Last updated: 2026-05-28.

## How routing works

There are two serving modes:
- **Static (GitHub Pages):** serves files from `site/` only. No Python; `/api/*` does not exist.
- **Flask (`python api/app.py`):** serves `site/` static files **and** the `/api/*` endpoints. `create_app()` registers blueprints and a catch-all static server (`api/app.py:16-59`).

## Page routes (HTML)

| URL | File | Served by | Needs Flask API? |
|---|---|---|---|
| `/` | `site/index.html` | Pages or Flask `serve_index` (`app.py:46-48`) | Page no; embedded Recommender/Study-Plan/KG-fetch **yes** |
| `/<slug>.html` | `site/<slug>.html` | Pages or Flask `serve_page` (`app.py:51-57`) | Page no; Math Tutor + Adapt Code **yes**; Playground no (client-side) |
| `/compare.html` | `site/compare.html` | Pages or Flask `serve_page` | **Yes** (`/api/compare`) |
| `/use-case-matrix.html` | `site/use-case-matrix.html` | Pages or Flask `serve_page` | No |
| `/quality-report.html` | `site/quality-report.html` | Pages or Flask `serve_page` | No (orphan link) |
| `/images/<path>` | `site/images/...` | Pages or Flask `serve_images` (`app.py:41-43`) | No |

Static `serve_page` only serves paths ending in `.html` that exist, else `abort(404)` (`app.py:53-57`).

## API routes (Flask only)

| Method · Path | Handler | Purpose | Auth | Notes |
|---|---|---|---|---|
| POST `/api/recommend` | proxy in `app.py:31-38` → `recommender_api.py:80` | 2-3 technique recommendations | none | Proxy hack: re-dispatches into a separate Flask app via `test_request_context` |
| POST `/api/compare` | `api/compare.py:56` | Compare two techniques | none | 400 missing/identical slugs; 404 unknown slug; slug not path-sanitized |
| GET `/api/compare/slugs` | `api/compare.py:112` | List available slugs | none | Not referenced by any template |
| POST `/api/math_tutor` | `api/math_tutor.py:24` | Explain selected math (JSON) | none | Schema-validated output |
| POST `/api/math_tutor/stream` | `api/math_tutor.py:97` | Explain selected math (SSE) | none | **No** output schema validation |
| POST `/api/study_plan` | `api/study_plan.py:64` | Learning roadmap (JSON) | none | Roadmap slugs not verified |
| POST `/api/study_plan/stream` | `api/study_plan.py:118` | Learning roadmap (SSE) | none | **No** output schema validation |
| POST `/api/adapt_code` | `api/adapt_code.py:25` | Adapt code to a framework | none | Returns text only; never executes code |

Full input/output/validation detail is in `docs/02-architecture/API_INVENTORY.md`.

## Cross-cutting routing facts

- **No authentication or rate limiting** on any route. **CORS is open** (`CORS(app)`, `app.py:19`).
- Templates call the **streaming** variants of math_tutor and study_plan; the non-stream variants exist but aren't used by the UI.
- **Static-deploy non-functional set:** Recommender, Compare, Study Plan, Math Tutor, Adapt Code (all `fetch('/api/...')`). Knowledge Graph + Playground are client-side and work on Pages (with the MCTS-mismatch caveats).
- The recommender exists in two places: the standalone app `pipeline/recommender_api.py` (`python -m pipeline.recommender_api`) and the proxied route in `api/app.py`. See `docs/06-history/DECISION_LOG.md`.
