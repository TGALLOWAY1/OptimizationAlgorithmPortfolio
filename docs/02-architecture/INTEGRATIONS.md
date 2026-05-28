# Integrations

> External services and third-party dependencies, and how the project couples to them.
> Last updated: 2026-05-28.

## Google Gemini (the only runtime external service)

- **SDK:** `google-genai>=1.0.0`, imported as `from google import genai` (`llm_client.py:22`).
- **Models (config-driven, `config.json:24-37`):**
  - `gemini` → `gemini-3.1-pro-preview` (recommend, compare, math_tutor, study_plan, adapt_code, judge, agent_draft/technical_review/editor)
  - `gemini_flash` → `gemini-3.1-flash-preview` (most content + agent stages)
  - `nano_banana` → `gemini-3.1-flash-image-preview` (infographic/preview images)
- **Auth:** single `GEMINI_API_KEY` for all three. Missing key → `ValueError` at provider construction (`llm_client.py:85-86`).
- **How it's called:**
  - JSON generation: `GeminiProvider.generate` concatenates system+user into one `contents` string and enforces output via `response_mime_type="application/json"` + `response_json_schema` (`:90-101`).
  - Streaming: `generate_content_stream` yields raw text (no schema, no JSON mime) (`:103-112`).
  - Tool use (judge): `generate_with_tools` uses a real `system_instruction`, declares functions, and loops dispatching `function_call`s (`:114-208`).
  - Images: `NanoBananaProvider.generate_image` with `response_modalities=["IMAGE"]` (`:221-241`).
- **Resilience:** `generate_with_retry` ≤3 attempts, backoff 2s/4s (`:289-317`). Cost multiplies through retry_loop (≤3 revise rounds) and the judge tool loop (≤5 turns).
- **Coupling risk:** provider/artifact *keys* are hardcoded string literals at call sites (`get_provider("judge")`, etc.), though model names are config-driven. Single-vendor, single-key.

## Browser CDNs (client-side only)

Loaded by templates; required for full UX but not for serving:
- **KaTeX** — math rendering on technique pages (`technique.html:7-14`).
- **highlight.js** — code syntax highlighting.
- **D3 v7** — knowledge-graph force layout (`knowledge_graph_component.html:37`).

Offline or CDN-blocked → equations render as raw LaTeX, code unhighlighted, graph absent. No local/bundled fallback.

## GitHub Pages + Actions (deployment)

- **Workflow:** `.github/workflows/pages.yml`. Trigger: push to `main`/`master` or manual dispatch.
- **Build:** Python 3.11 → `pip install -r requirements.txt` → `python build_site.py` → upload `site/`.
- **Deploy:** `actions/deploy-pages@v4` to the `github-pages` environment.
- **Reality:** CI does **not** run `pipeline.generate` (no API keys) and `generated/` is gitignored, so the deploy publishes the **placeholder** landing page. No Python backend is deployed, so **all `/api/*` features are non-functional in production**. To ship real content to Pages you must either run the pipeline in CI (with a key) or commit generated content.

## Flask + flask-cors

- `api/app.py` and `recommender_api.py` both call `CORS(app)` with no restrictions → all origins allowed.
- Both run with `debug=True` and `host=0.0.0.0` in their `__main__` blocks — fine for local dev, unsafe if exposed.

## Notable non-integrations

- **No OpenAI.** Despite `SETUP.md`/`CLAUDE.md`/`WOW_FACTOR_ANALYSIS.md` references, there is no OpenAI dependency or provider.
- **No database, cache, queue, or object store.** All persistence is local files.
- **No auth provider, analytics, or monitoring.**
