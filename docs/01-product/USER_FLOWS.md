# User Flows

> The core paths a user takes through the product. Failure states and API dependencies noted.
> Last updated: 2026-05-28. "(Flask only)" means the flow needs the local backend running.

---

## Flow A — Browse catalog → read a technique
- **Goal:** Learn one MCTS technique end-to-end.
- **Entry point:** `/` (homepage).
- **Steps:** View technique cards (`index.html:87-107`) → click a card → `/<slug>.html` → read Overview / Math deep-dive / Implementation → expand derivation accordions (`technique.html:138-150`) → switch code-variation tabs (`:169-181`) → view infographic.
- **Expected behavior:** Pure static reading; no backend needed.
- **Failure states:** missing thumbnail → image omitted (`index.html:91-95`); missing artifact sections hidden by `{% if %}`; CDN failure removes KaTeX math rendering / syntax highlighting only.
- **Relevant screens:** Index → Technique Detail.
- **Relevant APIs:** none.
- **Open questions:** none — this is the most robust flow.

## Flow B — Get a recommendation → open the guide *(Flask only)*
- **Goal:** Find the right technique for a described problem.
- **Entry point:** Recommender on `/` (`index.html:78`).
- **Steps:** Type a problem (≤2000 chars) → submit → `POST /api/recommend {query}` → Gemini ranks using the use-case matrix as context → confidence-badged cards → "Read Full Guide" → `/<slug>.html`.
- **Expected behavior:** 2-3 recommendations with justifications and confidence scores.
- **Failure states:** empty-query guard (`recommender_component.html:232-236`); network/non-OK error message (`:252-262`); **on Pages the fetch 404s → error shown**; returned `url_slug` not verified to exist.
- **Relevant screens:** Index (recommender) → Technique Detail.
- **Relevant APIs:** `/api/recommend`.

## Flow C — Compare two techniques *(Flask only)*
- **Goal:** Side-by-side pros/cons/best-for.
- **Entry point:** "Compare Algorithms" button on `/` (`index.html:83`) → `/compare.html`.
- **Steps:** Select technique A and B → Compare → `POST /api/compare {slug_a, slug_b}` → Gemini reads both techniques' artifacts → comparison table + summary (`compare.html:135-164`).
- **Expected behavior:** structured comparison (pros/cons/best-for/summary).
- **Failure states:** same/empty selection alerts (`:102-103`); loading + error divs (`:64-65,120-132`); 404 if a slug has no artifacts; **non-functional on Pages**.
- **Relevant screens:** Index → Compare.
- **Relevant APIs:** `/api/compare`.

## Flow D — Generate a personalized study plan *(Flask only)*
- **Goal:** Ordered learning roadmap tailored to background + goals.
- **Entry point:** "Generate Study Plan" button on `/` (`index.html:84`) → wizard modal.
- **Steps:** Enter background → Next → enter goals → Generate → SSE stream from `/api/study_plan/stream` → timeline with per-step technique links (`index.html:243-268`).
- **Expected behavior:** ordered roadmap with rationale, each step linking to a technique page.
- **Failure states:** field guards (`:172,183`); stream/parse/network error handling (`:227-266`); roadmap slugs not verified against available techniques; **non-functional on Pages**.
- **Relevant screens:** Index (modal) → Technique Detail.
- **Relevant APIs:** `/api/study_plan/stream`.

## Flow E — Explore relationships → navigate via the graph
- **Goal:** Understand how techniques relate, then jump to one.
- **Entry point:** Knowledge graph on `/` (`index.html:80`).
- **Steps:** Hover a node for a summary tooltip → click a node → `/<slug>.html`.
- **Expected behavior:** force-directed graph; nodes colored by category.
- **Failure states:** section absent if no `knowledge_graph.json`; unknown `category` → gray node (`knowledge_graph_component.html:86`); **legend taxonomy is mismatched for MCTS, so nodes likely render gray**.
- **Relevant screens:** Index (KG) → Technique Detail.
- **Relevant APIs:** none (client-side D3).

## Flow F — Math help + code adaptation on a technique page *(Flask only)*
- **Goal:** Understand an equation / port code to another framework.
- **Entry point:** Technique Detail — math section or code-variation panel.
- **Steps:** Select math text → "Explain this" tooltip (`technique.html:248-268`) → Math Tutor sidebar streams from `/api/math_tutor/stream`; **or** click "Adapt Code" → modal → `POST /api/adapt_code` → adapted code shown.
- **Expected behavior:** streamed explanation in a sidebar; adapted code in a modal.
- **Failure states:** Math Tutor loading/error (`:213,318,330`); Adapt validation + error (`:355,371,378`); **both non-functional on Pages**.
- **Relevant screens:** Technique Detail (sidebar + modal).
- **Relevant APIs:** `/api/math_tutor/stream`, `/api/adapt_code`.

## Flow G — Operator: generate + publish the whole portfolio
- **Goal:** (Re)build the full content site.
- **Entry point:** terminal.
- **Steps:** set `GEMINI_API_KEY` → `python -m pipeline.generate` (optionally `--evaluate`) → `python -m pipeline.publish` → `python api/app.py` to serve, or `python build_site.py` for the Pages artifact.
- **Expected behavior:** `generated/` populated, `site/` rendered, app serves content + working APIs locally.
- **Failure states:** missing key → `ValueError`; persistent schema failures → `RuntimeError` after retries; weak artifacts published anyway unless `--evaluate` used.
- **Relevant screens:** all.
- **Relevant APIs:** all (when served via `api/app.py`).
- **Open questions:** how is content meant to reach the *live* site? CI doesn't generate it and `generated/` is gitignored. See `docs/04-quality/KNOWN_ISSUES.md`.

## Flow H — Operator: run the multi-agent content pipeline
- **Goal:** Author a content package from arbitrary raw input via the agent workflow.
- **Entry point:** `python examples/run_content_pipeline.py --input examples/sample_input.json` (or `--dry-run` for offline stubs).
- **Steps:** intake → research → outline → draft → technical_review → editor → repurposing → publishing_qa, with quality gates and bounded revisions; state persisted under `outputs/runs/<run_id>/`.
- **Expected behavior:** a completed run with per-stage JSON + derived markdown.
- **Failure states:** gate exhaustion on a required stage raises `PipelineFailure`; optional stages skip.
- **Relevant APIs:** Gemini (per stage), unless `--dry-run`.
- **Open questions:** output is never consumed by the site/API — intended role unclear.
