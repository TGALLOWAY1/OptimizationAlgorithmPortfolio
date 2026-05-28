# API Inventory

> Every Flask endpoint and CLI command. All endpoints are unauthenticated and call Gemini per request.
> Last updated: 2026-05-28. Evidence cited as file:line.

## HTTP endpoints

### POST /api/recommend
- **Purpose:** Recommend 2-3 techniques for a described problem, using the use-case matrix as context.
- **Inputs:** `{query: string}` (≤2000 chars).
- **Outputs:** array of `{algorithm, justification, confidence_score (1-100), url_slug}` (2-3 items).
- **Auth:** none. **Provider:** `recommender` → gemini.
- **Validation:** query required/non-empty/≤2000 (`recommender_api.py:88-93`). Returned `url_slug` not verified to exist.
- **Errors:** 400 bad query; 500 on failure (broad catch, generic message).
- **Source:** `pipeline/recommender_api.py:80-100`; proxied at `api/app.py:31-38`. **Status:** Implemented (proxy fragile).

### POST /api/compare
- **Purpose:** Structured comparison of two techniques from their stored artifacts.
- **Inputs:** `{slug_a, slug_b}` (distinct, non-empty).
- **Outputs:** `{algorithm_a/b, pros_a/b, cons_a/b, best_for_a/b, summary}`.
- **Auth:** none. **Provider:** `compare` → gemini.
- **Validation:** both slugs present/non-empty/distinct; each technique dir must exist with ≥1 `*.json` (`compare.py:35-43,76-82`). **Slug not sanitized for path traversal** (`compare.py:37`) — mitigated only by dir/glob existence. Artifacts truncated to 4000 chars each.
- **Errors:** 400 missing/identical; 404 unknown slug; 500 LLM failure.
- **Source:** `api/compare.py:56-109`. **Status:** Implemented.

### GET /api/compare/slugs
- **Purpose:** List available technique slugs (for dropdowns). Returns sorted array.
- **Auth:** none. **Validation:** none needed. **Source:** `api/compare.py:112-115`. Not referenced by any template. **Status:** Implemented.

### POST /api/math_tutor  ·  POST /api/math_tutor/stream
- **Purpose:** Explain selected math/text, optionally with surrounding context.
- **Inputs:** `{selected_text (≤2000), context? (≤5000)}`.
- **Outputs:** non-stream `{explanation}` (schema-validated); stream `text/event-stream` of `{token}` then `{done|error}`.
- **Auth:** none. **Provider:** `math_tutor` → gemini.
- **Validation:** `selected_text` required/non-empty/≤2000; `context` ≤5000 (`math_tutor.py:38-41`). **Stream output is NOT schema-validated** (`:111`). Validation/prompt logic duplicated and already drifted between the two handlers.
- **Errors:** 400 invalid input; 500/SSE-error on failure.
- **Source:** `api/math_tutor.py:24-118`. **Status:** Implemented.

### POST /api/study_plan  ·  POST /api/study_plan/stream
- **Purpose:** Ordered learning roadmap from background + goals.
- **Inputs:** `{background (≤2000), goals (≤2000)}`.
- **Outputs:** `{roadmap:[{slug,title,reason,order}], rationale}` (non-stream schema-validated); SSE tokens (stream).
- **Auth:** none. **Provider:** `study_plan` → gemini.
- **Validation:** both fields required/non-empty/≤2000 (`study_plan.py:78-82`); 404 if no techniques exist. **Returned slugs not verified** against available set. Stream output not validated. Heavy duplication between the two handlers.
- **Errors:** 400; 404; 500/SSE-error.
- **Source:** `api/study_plan.py:64-164`. **Status:** Implemented.

### POST /api/adapt_code
- **Purpose:** Adapt source code to a target framework.
- **Inputs:** `{source_code (≤10000), target_framework, instructions?}`.
- **Outputs:** `{adapted_code, notes}`.
- **Auth:** none. **Provider:** `adapt_code` → gemini.
- **Validation:** `source_code`/`target_framework` required; `source_code` ≤10000. `target_framework`/`instructions` **length unbounded**. Returns text only — **does not execute code**.
- **Errors:** 400; 500.
- **Source:** `api/adapt_code.py:25-76`. **Status:** Implemented. Direct prompt-injection surface.

### Static-serving routes
| Route | Purpose | Source |
|---|---|---|
| `GET /images/<path>` | Serve `site/images/` (Flask safe-join) | `app.py:41-43` |
| `GET /` | Serve `site/index.html` | `app.py:46-48` |
| `GET /<path:page>` | Serve any existing `.html` in `site/`, else 404 | `app.py:51-57` |

## CLI commands

| Command | Purpose | Key flags | Source |
|---|---|---|---|
| `python -m pipeline.generate` | Generate artifacts for all/one technique; optional eval | `--technique`, `--force`, `--provider {gemini}`, `--skip-images`, `--evaluate`, `--skip-judge`, `--clean` | `generate.py:340-342` |
| `python -m pipeline.publish` | Render artifacts → `site/` | — | `publish.py:448-450` |
| `python -m pipeline.generate_use_case_matrix` | Generate `use_case_matrix.json` | `--force` | `generate_use_case_matrix.py:93-100` |
| `python -m pipeline.generate_preview_images` | Generate preview thumbnails | `--force` | `generate_preview_images.py:36-42` |
| `python api/app.py` | Unified Flask app (static + API) | env `PORT` | `api/app.py:62-66` |
| `python -m pipeline.recommender_api` | Standalone recommender app | env `PORT` | `recommender_api.py:103-105` |
| `python build_site.py` | GitHub Pages build (full or placeholder) | — | `build_site.py:127-128` |
| `python examples/run_content_pipeline.py` | Multi-agent pipeline driver | `--input`, `--dry-run`, `--resume`, `--output-root` | `examples/run_content_pipeline.py:320-321` |

`pipeline/evaluate.py` has **no** `__main__` block — it is a library used by `pipeline.generate`, not a CLI command.

## Cross-cutting

- **No auth, no rate limiting, open CORS** on every route. Each call costs Gemini credits.
- **`debug=True`** in both Flask entry points (`app.py:66`, `recommender_api.py:105`) — exposes the Werkzeug debugger if reachable (security risk). See `docs/04-quality/SECURITY_AND_PRIVACY_NOTES.md`.
- **Error hygiene:** endpoints catch broad `Exception`, log via `logger.exception`, return generic messages — no stack traces leak through the JSON paths (but `debug=True` could expose them on unhandled errors).
- **`--provider` only accepts `gemini`** (`generate.py:60-64`), which overrides the cheaper `gemini_flash` default for text artifacts — there is no way to force `gemini_flash`.
