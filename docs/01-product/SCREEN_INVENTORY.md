# Screen Inventory

> Every page and embedded interactive component in the published site.
> Status labels: Implemented · Partial · Stubbed · Broken · Designed only · Deprecated · Unknown.
> Last updated: 2026-05-28. Evidence cited as file:line.

> **Context reminder:** "Partial — requires Flask" means the screen renders statically but its interactive features call `/api/*` and only work when `python api/app.py` is running with generated content. On the live GitHub Pages deploy these are non-functional. See `docs/01-product/CURRENT_BEHAVIOR.md`.

---

## Home / Index (full build)
- **Route / file:** `/` → `site/index.html`
- **Source template:** `pipeline/templates/index.html` (rendered `publish.py:334-339`)
- **Status:** Partial (static catalog Implemented; Recommender/Study-Plan/KG-fetch require Flask)
- **Primary purpose:** Landing page — technique catalog grid + entry points to interactive tools.
- **Primary user actions:** Open a technique card; use the Recommender; open Compare; launch the Study Plan wizard; explore the knowledge graph.
- **Important components:** Recommender (`index.html:78`), Knowledge Graph (`:80`), action-bar buttons (`:82-85`), Study Plan modal (`:110-145`).
- **Data dependencies:** per-technique `homepage_summary.bullets`/`overview.summary` (`publish.py:309-322`), `knowledge_graph.json` (`publish.py:326-331`), `images/<slug>/preview.png`.
- **Empty/loading/error states:** card fallback summary (`:101-103`); Study Plan loading dots + error handlers (`:204-266`); KG section self-suppresses if empty (`knowledge_graph_component.html:2`).
- **Mobile/responsive:** `viewport-fit=cover` (`:5`), fluid grid `minmax(260px,1fr)`, `@media (max-width:640px)` (`:64-68`).
- **Known UX issues:** On Pages this is the placeholder build (no widgets); KG legend categories mismatched for MCTS.
- **Screenshot status:** Not captured (site not generated in this environment). See `docs/08-visuals/`.

## Index (placeholder build)
- **Route / file:** `/` → `site/index.html`
- **Source:** inline f-string in `build_site.py:71-112` (not Jinja)
- **Status:** Implemented (intentionally minimal)
- **Primary purpose:** Fallback shown when no generated content exists; this is what the live deploy publishes.
- **Primary user actions:** None — static "Coming Soon" cards, no links.
- **Data dependencies:** `config.json` techniques + topic only.
- **Known UX issues:** Dead-end cards. Most likely the live production page.
- **Screenshot status:** Not captured.

## Technique Detail Page
- **Route / file:** `/<slug>.html` → `site/<slug>.html` (flat at root, not under `techniques/`, `publish.py:305`)
- **Source template:** `pipeline/templates/technique.html` (rendered `publish.py:292-306`)
- **Status:** Implemented (static reading) / Partial (Math Tutor + Adapt Code require Flask) / embeds a Broken playground
- **Primary purpose:** Full learning page — provenance, overview, math deep-dive, implementation, playground, infographic.
- **Primary user actions:** Read sections; expand derivation accordions (`:138-150`); switch code-variation tabs (`:169-181`); select math text → Math Tutor (`:248-268`); Adapt Code (`:338-381`).
- **Important components:** Code tabs (`:237-243`), Math Tutor tooltip+sidebar (`:245-336`), Adapt Code modal (`:338-381`), Playground (`:197`), KaTeX + highlight.js (CDN, `:7-14`).
- **Data dependencies:** `overview/math_deep_dive/implementation/infographic_spec/playground_config/plan/manifest.json` (`publish.py:292-304`); `images/<slug>/infographic.png`. APIs: `/api/math_tutor/stream`, `/api/adapt_code`.
- **Empty/loading/error states:** every section `{% if %}`-guarded (`:107,116,130,160,199`); Math Tutor loading/error (`:213,318,330`); Adapt error (`:371,378`).
- **Mobile/responsive:** `viewport-fit=cover`, `clamp()` typography, horizontal-scroll wrappers for `pre`/tables/KaTeX (`:34,43,44`), `@media (max-width:640px)` (`:95-100`).
- **Known UX issues:** interactive AI features Broken on Pages; CDN dependency; playground wrong for MCTS.
- **Screenshot status:** Not captured.

## Compare Page
- **Route / file:** `/compare.html` → `site/compare.html` (rendered `publish.py:361-368`)
- **Source template:** `pipeline/templates/compare.html`
- **Status:** Partial (requires `/api/compare`)
- **Primary purpose:** Side-by-side LLM-generated comparison of two techniques.
- **Primary user actions:** Pick two techniques from dropdowns → Compare (`:47-62,93`).
- **Important components:** two `<select>`s populated from `techniques`; JS `renderComparison` (`:135-164`).
- **Data dependencies:** `POST /api/compare {slug_a, slug_b}` (`:111-115`).
- **Empty/loading/error states:** loading (`:64,108`), error (`:65,120-132`), same/empty-selection guards (`:102-103`).
- **Mobile/responsive:** viewport meta + flex-wrap selector; no `@media`, fixed `max-width:1000px`.
- **Known UX issues:** non-functional on Pages; no narrow-screen table handling.
- **Screenshot status:** Not captured.

## Use Case Matrix Page
- **Route / file:** `/use-case-matrix.html` → `site/use-case-matrix.html` (rendered `publish.py:342-358`, only if matrix JSON exists)
- **Source template:** `pipeline/templates/use_case_matrix.html`
- **Status:** Implemented (conditional on data; works on Pages)
- **Primary purpose:** Grid of problem-spaces × techniques with ideal/suitable/unsuitable ratings.
- **Primary user actions:** Read; click an algorithm header to jump to its page (`:60`).
- **Data dependencies:** `generated/use_case_matrix.json`.
- **Empty/loading/error states:** page skipped entirely if JSON missing → homepage link (`index.html:75`) then 404s.
- **Mobile/responsive:** horizontal-scroll `.matrix-wrap` + swipe hint; `@media (max-width:640px)`.
- **Known UX issues:** potential dangling link from homepage when not generated.
- **Screenshot status:** Not captured.

## Quality / Eval Report Page
- **Route / file:** `/quality-report.html` → `site/quality-report.html` (rendered `publish.py:374-445`)
- **Source template:** `pipeline/templates/eval_report.html`
- **Status:** Implemented (conditional; orphaned navigation)
- **Primary purpose:** Per-technique/artifact evaluation metrics.
- **Primary user actions:** Read-only.
- **Data dependencies:** `evaluation_latest_full.json` else `_partial.json`.
- **Empty/loading/error states:** skipped if no metrics; full/partial scope banner (`eval_report.html:159-165`).
- **Known UX issues:** no inbound link from any nav — direct-URL only.
- **Screenshot status:** Not captured.

## Recommender (embedded in Index)
- **Component:** `#recommender` — `pipeline/templates/recommender_component.html`
- **Status:** Partial (requires `/api/recommend`)
- **Primary user actions:** type query (maxlength 2000) → "Find Best Algorithm".
- **Important widgets:** textarea, spinner button, confidence-badged result cards (`:271-289`), "Read Full Guide" CTA.
- **Data dependencies:** `POST /api/recommend {query}`.
- **Empty/loading/error states:** empty-query guard (`:232-236`), loading (`:238-243`), error (`:252-262`).
- **Known UX issues:** Broken on Pages.
- **Screenshot status:** Not captured.

## Knowledge Graph (embedded in Index)
- **Component:** `#knowledge-graph` — `pipeline/templates/knowledge_graph_component.html`
- **Status:** Partial (works client-side; legend mismatched for MCTS)
- **Primary user actions:** drag nodes, hover tooltip, click node → `<slug>.html`.
- **Important widgets:** D3 v7 force simulation (CDN, `:37`), legend (`:10-15`).
- **Data dependencies:** `knowledge_graph` injected via `{{ knowledge_graph | tojson }}` (`:40`).
- **Empty/loading/error states:** section omitted if no nodes (`:2`); unknown category → gray node (`:86`).
- **Mobile/responsive:** fixed 480px container; resize re-centers (`:151-157`); no small-screen adaptation.
- **Known UX issues:** MCTS nodes likely all gray (legend taxonomy mismatch).
- **Screenshot status:** Not captured.

## Playground (embedded in each Technique page)
- **Component:** `#playground` — `pipeline/templates/playground_component.html`
- **Status:** Broken (for MCTS topic)
- **Primary user actions:** drag parameter sliders; Play/Pause/Step/Reset.
- **Important widgets:** sliders from `playground_config.parameters`; `<canvas>` contour renderer; 8 step functions + dispatch (`:164-343`).
- **Data dependencies:** `playground_config.json` (client-side only; no API).
- **Empty/loading/error states:** section omitted if no config; silent fallbacks `stepFn ... || stepGradientDescent` (`:343`), `objFn ... || sphere` (`:75`).
- **Known UX issues:** MCTS slugs match no `algorithmSteps` key → always gradient descent on a 2D function; meaningless for tree search.
- **Screenshot status:** Not captured.

## Study Plan Wizard (embedded modal in Index)
- **Component:** modal in `pipeline/templates/index.html:110-275`
- **Status:** Partial (requires `/api/study_plan/stream`)
- **Primary user actions:** 2-step form (background → goals) → Generate → streamed timeline.
- **Important widgets:** step modal, SSE reader (`:193-241`), timeline renderer with per-step links (`:243-268`).
- **Data dependencies:** `POST /api/study_plan/stream {background, goals}`.
- **Empty/loading/error states:** required-field guards (`:172,183`), loading dots (`:204-207`), error/parse-failure handling (`:227-266`).
- **Known UX issues:** Broken on Pages.
- **Screenshot status:** Not captured.
