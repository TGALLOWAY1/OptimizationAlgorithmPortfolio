# Feature Inventory

> Canonical list of features with honest status. Labels: Implemented · Partial · Stubbed · Broken · Designed only · Deprecated · Unknown.
> Last updated: 2026-05-28. Each entry cites source evidence.

## Status at a glance

| # | Feature | Status |
|---|---|---|
| 1 | Per-technique content generation (single-shot) | Implemented |
| 2 | Gemini multi-provider LLM client + routing | Implemented |
| 3 | Schema + content validation | Implemented (advisory at gen time) |
| 4 | LLM-as-judge evaluation + revision loop | Implemented |
| 5 | Code execution for implementation artifacts | Implemented (weak sandbox) |
| 6 | Infographic + preview image generation | Implemented |
| 7 | Static site publisher | Implemented |
| 8 | Homepage technique catalog | Partial (placeholder on live site) |
| 9 | Technique detail pages | Implemented (static) / Partial (interactive) |
| 10 | Recommender | Partial (requires Flask) |
| 11 | Compare two techniques | Partial (requires Flask) |
| 12 | Math Tutor (text-selection, streaming) | Partial (requires Flask) |
| 13 | Study Plan wizard (streaming) | Partial (requires Flask) |
| 14 | Adapt Code | Partial (requires Flask) |
| 15 | Knowledge graph visualization | Partial (legend mismatched for MCTS) |
| 16 | Interactive playground | Broken (for MCTS topic) |
| 17 | Use-case matrix page | Implemented (conditional on data) |
| 18 | Quality / evaluation report page | Implemented (orphaned navigation) |
| 19 | Multi-agent content pipeline | Implemented (no production consumer) |
| 20 | GitHub Pages deployment | Implemented (publishes placeholder) |
| 21 | Quiz artifact | Designed only (absent) |

---

## 1. Per-technique content generation (single-shot)
**Status:** Implemented
**User value:** Produces a full, consistent artifact set per technique without manual authoring.
**Primary flow:** `python -m pipeline.generate [--technique …] [--force] [--skip-images] [--evaluate]` → loops techniques → generates plan → overview/math/implementation/infographic_spec → homepage summary → images → playground config → knowledge graph.
**Relevant routes/CLI:** `pipeline/generate.py:45-262`, entry `:340-342`.
**Relevant components:** `pipeline/generator.py` (engine), `pipeline/llm_client.py` (provider+retry), `pipeline/schemas.py` (validation).
**Data dependencies:** `GEMINI_API_KEY`; writes `generated/techniques/<slug>/*.json` + PNGs + `manifest.json`.
**Known issues:** Idempotency via input-hash manifest (`generator.py:141-160`); content-validation errors are logged but **non-blocking** (`generator.py:298-306`). `--provider` only allows `gemini`, silently overriding the cheaper `gemini_flash` default.
**Evidence:** `pipeline/generate.py`, `pipeline/generator.py`.

## 2. Gemini multi-provider LLM client + routing
**Status:** Implemented
**User value:** Config-driven model selection (pro vs flash vs image) per artifact, with retries and JSON-schema enforcement.
**Primary flow:** `get_provider(artifact_type)` resolves a provider from `config.json artifact_provider_map`; `generate_with_retry` validates output and retries with backoff.
**Relevant components:** `LLMProvider`, `GeminiProvider`, `NanoBananaProvider`, `get_provider`, `generate_with_retry` (`pipeline/llm_client.py:67-341`).
**Known issues:** Only Gemini exists (no OpenAI, despite docs). Backoff is effectively 2s/4s (final attempt doesn't sleep) vs documented "2/4/8". Non-streaming path concatenates system+user into one prompt (no system/user trust boundary). Provider cache is process-global, not thread-safe.
**Evidence:** `pipeline/llm_client.py:248-341`.

## 3. Schema + content validation
**Status:** Implemented (advisory at generation time)
**User value:** Guarantees generated artifacts have required structure before publishing.
**Primary flow:** `jsonschema.validate` against `SCHEMAS[...]` inside `generate_with_retry`; then `validate_artifact` applies content rules (length, LaTeX presence, topic-hint relevance).
**Relevant components:** `pipeline/schemas.py` (16 schemas), `pipeline/validator.py`, `pipeline/schema_validate.py`.
**Known issues:** "800" threshold means characters in schema but words in `validator.py` — two different bars. Content validation is non-blocking at generation; only enforced under `--evaluate`. `knowledge_graph` has no edge↔node referential check; `playground_config` doesn't enforce min≤default≤max.
**Evidence:** `pipeline/schemas.py:584-601`, `pipeline/validator.py:212-228`. See `docs/02-architecture/DATA_MODEL.md`.

## 4. LLM-as-judge evaluation + revision loop
**Status:** Implemented
**User value:** Automated quality scoring (factual accuracy, math correctness, clarity, code quality) with a revise-until-pass loop.
**Primary flow:** `--evaluate` → `evaluate_single_artifact` runs schema → static checks → code execution (implementation) → judge; `retry_loop` revises up to 3 times.
**Relevant components:** `pipeline/judge.py`, `pipeline/judge_tools.py` (tool-calling: run code, check equation, lookup reference, verify imports), `pipeline/retry_loop.py`, `pipeline/evaluate.py`.
**Known issues:** Rubric weights are passed to the LLM as text, never used for deterministic aggregation. `build_revision_prompt` says "expert in optimization algorithms" (stale, `judge.py:337`). Judge fail-closed on parse/validation errors.
**Evidence:** `pipeline/judge.py:231-318`, `pipeline/evaluate.py:144-218`.

## 5. Code execution for implementation artifacts
**Status:** Implemented (weak sandbox)
**User value:** Verifies generated Python actually runs and uses only allowed libraries.
**Primary flow:** Judge tool `run_python_code` → `code_runner.run_code` writes a temp file and runs it via `subprocess.run([sys.executable, ...], timeout=30)`.
**Relevant components:** `pipeline/code_runner.py`, `pipeline/judge_tools.py:26-39`.
**Known issues:** Not reachable from any HTTP endpoint (offline eval only). No real sandbox — code runs as the same OS user with filesystem/network access; the import allowlist is enforced for *declared* deps but not for the executed code string. See `docs/04-quality/SECURITY_AND_PRIVACY_NOTES.md`.
**Evidence:** `pipeline/code_runner.py:91-141`.

## 6. Infographic + preview image generation
**Status:** Implemented
**User value:** Generates a per-technique infographic PNG and a homepage thumbnail.
**Primary flow:** `generate_infographic_image` / `generate_preview_image` build a prompt from the infographic spec and call the `nano_banana` image model. Skippable via `--skip-images`.
**Relevant components:** `pipeline/generator.py:398-541`, `pipeline/generate_preview_images.py`, `NanoBananaProvider`.
**Known issues:** Images are not schema-validated (only file-size ≥10 KB check, `validator.py:199-209`). Preview cache key reuses the infographic config slice.
**Evidence:** `pipeline/generator.py`, `pipeline/prompts/infographic_image_prompt.md`, `preview_image_prompt.md`.

## 7. Static site publisher
**Status:** Implemented
**User value:** Renders all generated artifacts into a browsable static HTML site.
**Primary flow:** `python -m pipeline.publish` → renders index, per-technique pages, compare, use-case matrix, knowledge graph, quality report into `site/`.
**Relevant components:** `pipeline/publish.py`, `pipeline/templates/*.html`.
**Known issues:** Technique pages published flat at `site/<slug>.html` (not under `techniques/`, contradicting CLAUDE.md). Quality report is orphaned; use-case-matrix link can dangle.
**Evidence:** `pipeline/publish.py:237-450`.

## 8. Homepage technique catalog
**Status:** Partial
**User value:** Entry point — grid of technique cards + access to interactive tools.
**Relevant components:** `pipeline/templates/index.html`, rendered `publish.py:334-339`.
**Data dependencies:** `homepage_summary.bullets` (or overview summary), `knowledge_graph.json`, preview images.
**Known issues:** On the live GitHub Pages deploy this is the **placeholder** page (cards with "Coming Soon", no widgets) because no content is committed. Full catalog renders only after a local pipeline run.
**Evidence:** `pipeline/publish.py:309-339`, `build_site.py:42-116`.

## 9. Technique detail pages
**Status:** Implemented (static reading) / Partial (interactive features)
**User value:** Full learning page — overview, math deep-dive (with derivation accordions + KaTeX), implementation (code-variation tabs), infographic, playground, math-tutor selection, adapt-code.
**Relevant components:** `pipeline/templates/technique.html`, rendered `publish.py:292-306`.
**Known issues:** Reading content works statically; Math Tutor and Adapt Code require Flask (`/api/...`), so they're Broken on Pages. Depends on CDN (KaTeX/highlight.js). Embedded playground is Broken for MCTS (see #16).
**Evidence:** `pipeline/templates/technique.html`.

## 10. Recommender
**Status:** Partial (requires Flask)
**User value:** Free-text problem description → 2-3 ranked technique recommendations with confidence scores.
**Primary flow:** Homepage widget → `POST /api/recommend {query}` → Gemini using the use-case matrix as system context → cards with "Read Full Guide" links.
**Relevant components:** `pipeline/recommender_api.py`, `recommender_component.html`, `prompts/recommender_prompt.md`.
**Known issues:** No auth/rate limit. Standalone Flask app proxied awkwardly into `api/app.py` (see #20 / DECISION_LOG). Non-functional on static Pages. Returned `url_slug` not verified to exist.
**Evidence:** `pipeline/recommender_api.py:80-100`, `api/app.py:31-38`.

## 11. Compare two techniques
**Status:** Partial (requires Flask)
**User value:** Side-by-side pros/cons/best-for/summary of two techniques.
**Primary flow:** `/compare.html` dropdowns → `POST /api/compare {slug_a, slug_b}` → Gemini reads both techniques' artifacts → comparison table.
**Relevant components:** `api/compare.py`, `compare.html`.
**Known issues:** Slug not sanitized for path traversal (`compare.py:37`); mitigated by dir/glob existence checks. Non-functional on static Pages. No responsive table for narrow screens.
**Evidence:** `api/compare.py:56-115`.

## 12. Math Tutor (text-selection, streaming)
**Status:** Partial (requires Flask)
**User value:** Select an equation/text on a technique page → streamed plain-language explanation.
**Primary flow:** Selection tooltip → `POST /api/math_tutor/stream {selected_text, context}` → SSE token stream into a sidebar.
**Relevant components:** `api/math_tutor.py`, `technique.html:245-336`.
**Known issues:** Streaming output is **not schema-validated** (raw tokens). Prompt-building/validation duplicated between stream and non-stream handlers (already drifted). Non-functional on static Pages.
**Evidence:** `api/math_tutor.py:97-118`.

## 13. Study Plan wizard (streaming)
**Status:** Partial (requires Flask)
**User value:** Background + goals → ordered, justified learning roadmap across techniques.
**Primary flow:** Homepage modal (2-step form) → `POST /api/study_plan/stream {background, goals}` → SSE → timeline with per-technique links.
**Relevant components:** `api/study_plan.py`, `index.html:110-275`.
**Known issues:** Returned roadmap slugs not verified against available techniques. Streaming output unvalidated. Non-functional on static Pages.
**Evidence:** `api/study_plan.py:118-164`.

## 14. Adapt Code
**Status:** Partial (requires Flask)
**User value:** Paste source code + target framework → adapted code + notes.
**Primary flow:** Technique-page modal → `POST /api/adapt_code {source_code, target_framework, instructions?}` → Gemini → adapted code (text only; never executed).
**Relevant components:** `api/adapt_code.py`, `technique.html:338-381`.
**Known issues:** `target_framework`/`instructions` lengths unbounded; direct prompt-injection surface. Non-functional on static Pages.
**Evidence:** `api/adapt_code.py:25-76`.

## 15. Knowledge graph visualization
**Status:** Partial
**User value:** D3 force-directed map of technique relationships; click a node to open its page.
**Relevant components:** `knowledge_graph_component.html`, data `generated/knowledge_graph.json`.
**Known issues:** Legend/category color map hardcoded to numerical-optimization taxonomy (`evolutionary`/`gradient-based`/...) — MCTS categories aren't matched, so nodes render gray. Works client-side on Pages (subject to this caveat) only if `knowledge_graph.json` is present.
**Evidence:** `knowledge_graph_component.html:11-14,41-46,86`.

## 16. Interactive playground
**Status:** Broken (for the MCTS topic)
**User value:** Intended: animate the algorithm optimizing a 2D function with adjustable parameters.
**Relevant components:** `playground_component.html`, data `playground_config.json`.
**Known issues:** `algorithmSteps` dispatch is keyed on old optimization slugs (`gradient-descent`, etc.); MCTS slugs match none, so every technique falls back to `stepGradientDescent` over continuous 2D objective functions — meaningless for tree search. Objective functions (Rosenbrock/Rastrigin/Sphere/Ackley) are optimization-domain.
**Evidence:** `playground_component.html:332-343,69-78`.

## 17. Use-case matrix page
**Status:** Implemented (conditional on data)
**User value:** Grid of problem-spaces × techniques with ideal/suitable/unsuitable ratings; feeds the recommender.
**Relevant components:** `use_case_matrix.html`, `pipeline/generate_use_case_matrix.py`, data `generated/use_case_matrix.json`.
**Known issues:** Page only built if the JSON exists; homepage always links to it → potential dangling link. No interactivity required (works on Pages).
**Evidence:** `pipeline/publish.py:342-358`.

## 18. Quality / evaluation report page
**Status:** Implemented (orphaned navigation)
**User value:** Per-technique/per-artifact evaluation metrics in a table.
**Relevant components:** `eval_report.html`, data `evaluation_latest_full.json`/`_partial.json`.
**Known issues:** No inbound link from any nav — discoverable only by direct URL. Conditional on an evaluation run.
**Evidence:** `pipeline/publish.py:374-445`.

## 19. Multi-agent content pipeline
**Status:** Implemented (no production consumer)
**User value:** A general authoring workflow that turns arbitrary raw input into a reviewed, edited, repurposed content package via 8 gated agent stages.
**Primary flow:** `python examples/run_content_pipeline.py [--input … | --dry-run | --resume …]` → intake → research → outline → draft → technical_review → editor → repurposing → publishing_qa; state in `outputs/runs/<run_id>/`.
**Relevant components:** `pipeline/content_pipeline/`, `pipeline/agents/`, prompts in `pipeline/prompts/content_pipeline/`.
**Known issues:** Not read by the publisher or API — standalone. `cancel()` raises `NotImplementedError`. `requires_human` honored only when `auto_approve=False` (defaults True).
**Evidence:** `pipeline/content_pipeline/__init__.py:7-9`, `pipeline/content_pipeline/pipeline.py`.

## 20. GitHub Pages deployment
**Status:** Implemented (publishes placeholder)
**User value:** Auto-deploys the site on push to main/master.
**Relevant components:** `.github/workflows/pages.yml`, `build_site.py`.
**Known issues:** CI never runs the content pipeline and `generated/` is gitignored, so the deploy publishes the placeholder landing page; no Flask is deployed, so all `/api/*` features are non-functional in production.
**Evidence:** `.github/workflows/pages.yml`, `build_site.py:120-123`.

## 21. Quiz artifact
**Status:** Designed only (absent)
**User value:** (Intended) self-test quiz per technique.
**Known issues:** `CLAUDE.md` lists `quiz.json` as an artifact type, but it is **not** in `config.json artifact_types`, has no schema, no prompt, and no generator. Pure documentation aspiration.
**Evidence:** `CLAUDE.md` vs `pipeline/config.json:18-23`, `pipeline/schemas.py`.
