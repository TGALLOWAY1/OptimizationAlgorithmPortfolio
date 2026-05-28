# Known Issues

> Concrete, evidence-backed defects and gaps. Ordered by priority.
> Status labels: Open · Investigating · Mitigated · Fixed. Last updated: 2026-05-28.

---

## Issue #1 — 6 tests fail on stale optimization-era fixtures
- **Status:** Open
- **Severity:** High
- **User impact:** None at runtime, but the suite is red, masking regressions and contradicting docs that claim all tests pass.
- **Technical cause:** Schemas migrated to MCTS enums; fixtures in `tests/test_wow_features.py` and `tests/test_validator.py` still use optimization values (`sphere`, `rosenbrock`, `contour_trajectory`, `evolutionary`, `gradient-descent`/`bfgs`).
- **Relevant files:** `tests/test_wow_features.py`, `tests/test_validator.py:90-101`, `pipeline/schemas.py` (playground/knowledge_graph enums), `pipeline/validator.py`.
- **Suggested fix:** Update fixtures to MCTS values (`game_tree`/`tree_expansion`/`selection-policy`); change the `test_wrong_technique_example_is_rejected` assertion to an off-topic term the current validator rejects.
- **Verification:** `python -m pytest tests/test_wow_features.py tests/test_validator.py -q` → all pass; full suite green.

## Issue #2 — Interactive playground is broken for all MCTS techniques
- **Status:** Open
- **Severity:** High
- **User impact:** Every technique page's playground animates 2D gradient descent on a continuous function (Rosenbrock/Sphere/…), which is meaningless for tree-search algorithms.
- **Technical cause:** `algorithmSteps` dispatch is keyed on old optimization slugs; MCTS slugs match none, so it silently falls back to `stepGradientDescent` (`playground_component.html:343`), and objective functions are optimization-domain (`:69-78`).
- **Relevant files:** `pipeline/templates/playground_component.html:164-343,69-78`.
- **Suggested fix:** Replace the playground with MCTS-appropriate visualizations matching the `playground_config` enums (`tree_expansion`, `visit_heatmap`, `convergence_curve`, `win_rate_over_time`) and objective functions (`game_tree`, etc.), or hide it until reworked.
- **Verification:** Generate content, open a technique page, confirm the playground reflects the technique (not gradient descent).

## Issue #3 — Live GitHub Pages site shows a placeholder; all API features non-functional
- **Status:** Open
- **Severity:** High
- **User impact:** The public site has no real content and no working Recommender/Compare/Study-Plan/Math-Tutor/Adapt-Code.
- **Technical cause:** CI runs only `build_site.py` (no `GEMINI_API_KEY`, no `pipeline.generate`); `generated/` is gitignored → placeholder build. No Python backend is deployed, so `/api/*` 404s.
- **Relevant files:** `.github/workflows/pages.yml`, `build_site.py:120-123`, `api/app.py`.
- **Suggested fix:** Decide the deployment story — either generate content in CI with a key and document that interactive tools are local-only, or host the Flask app separately and point the static site at it.
- **Verification:** Inspect the deployed Pages URL; confirm whether content + tools appear.

## Issue #4 — Knowledge-graph legend/categories mismatched for MCTS
- **Status:** Open
- **Severity:** Medium
- **User impact:** Graph nodes render gray (unknown category) and the legend describes the wrong taxonomy.
- **Technical cause:** Legend/color map hardcoded to `evolutionary`/`gradient-based`/`probabilistic`/`direct-search`; schema categories are `selection-policy`/`simulation-enhancement`/`parallelization`/`meta-optimization`.
- **Relevant files:** `pipeline/templates/knowledge_graph_component.html:11-14,41-46,86`.
- **Suggested fix:** Update the legend + color map to the MCTS categories.
- **Verification:** Render the homepage with a generated `knowledge_graph.json`; nodes colored, legend correct.

## Issue #5 — Stale project documentation (wrong domain, wrong provider, wrong test counts)
- **Status:** Open
- **Severity:** Medium
- **User impact:** Misleads contributors/recruiters/agents (e.g., tells users to get an OpenAI key that isn't used).
- **Technical cause:** Docs predate the optimization→MCTS retarget and the OpenAI→Gemini switch.
- **Relevant files:** `CLAUDE.md` (8 optimization algorithms, OpenAI, "70 tests/7 files", `quiz.json`, `--technique "Bayesian Optimization"`), `SETUP.md` (OpenAI key + tests), `WOW_FACTOR_ANALYSIS.md` (OpenAI + optimization). `README.md` is largely current.
- **Suggested fix:** Update or archive these. Root `CLAUDE.md` and `README.md` are refreshed by this documentation project (Phases 7/10); `SETUP.md` and `WOW_FACTOR_ANALYSIS.md` still need correction.
- **Verification:** Grep for `OpenAI`, `optimization algorithm`, `70 tests` → no stale runtime claims remain.

## Issue #6 — Streaming endpoints return unvalidated LLM output
- **Status:** Open
- **Severity:** Medium
- **User impact:** `/api/math_tutor/stream` and `/api/study_plan/stream` stream raw model tokens with no schema enforcement, unlike their non-stream siblings.
- **Technical cause:** `provider.generate_stream` sets no `response_mime_type`/schema (`llm_client.py:103-112`); handlers stream tokens directly (`math_tutor.py:111`, `study_plan.py:157`).
- **Relevant files:** `api/math_tutor.py:97-118`, `api/study_plan.py:118-164`, `pipeline/llm_client.py:103-112`.
- **Suggested fix:** Buffer-and-validate, or document streamed output as best-effort free text.
- **Verification:** Inspect stream output shape; decide acceptable contract.

## Issue #7 — `/api/compare` slug not sanitized for path traversal
- **Status:** Open
- **Severity:** Medium (security)
- **User impact:** A crafted `slug_a/slug_b` is used directly as a path segment (`CONTENT_DIR / slug`), so it can point outside the techniques dir; mitigated only by the `is_dir()` + `*.json` existence check.
- **Technical cause:** No slug-format validation before filesystem join (`compare.py:37`).
- **Relevant files:** `api/compare.py:35-43`.
- **Suggested fix:** Validate slug against `^[a-z0-9-]+$` and/or check membership in the known slug set before any path use.
- **Verification:** Send `slug_a=../../etc` → 400, not a filesystem read.

## Issue #8 — No auth / rate limiting + open CORS + `debug=True`
- **Status:** Open
- **Severity:** High (cost/security)
- **User impact:** Any origin can drive unlimited paid Gemini calls; if exposed, the Werkzeug debugger enables RCE.
- **Technical cause:** `CORS(app)` open; no auth/limits; `app.run(debug=True, host=0.0.0.0)` in both entry points.
- **Relevant files:** `api/app.py:19,66`, `pipeline/recommender_api.py:20,105`.
- **Suggested fix:** Restrict CORS, add an API key/rate limit, set `debug=False` for any non-local serving.
- **Verification:** Confirm cross-origin calls rejected; debugger off.

## Issue #9 — Content-validation failures don't block publishing
- **Status:** Open
- **Severity:** Medium
- **User impact:** Weak/off-topic artifacts (failing word-count, LaTeX, or topic-hint rules) are written and published unless `--evaluate` is run.
- **Technical cause:** `validate_artifact` errors are logged, not raised, in `generate_artifact` (`generator.py:298-306`).
- **Relevant files:** `pipeline/generator.py:298-307`.
- **Suggested fix:** Make content validation blocking (or a `--strict` flag), or always run the evaluate gate before publish.
- **Verification:** Generate a deliberately weak artifact; confirm it is rejected.

## Issue #10 — Recommender served via a fragile proxy hack
- **Status:** Open
- **Severity:** Medium
- **User impact:** `/api/recommend` works but drops headers/query/content-type and nests two Flask apps; brittle and inconsistent error handling.
- **Technical cause:** `recommender_api.py` is a standalone Flask app, not a blueprint; `app.py:31-38` re-dispatches it via `test_request_context`.
- **Relevant files:** `api/app.py:28-38`, `pipeline/recommender_api.py`.
- **Suggested fix:** Refactor the recommender into a Blueprint and register it like the others.
- **Verification:** `/api/recommend` works without the proxy; one Flask app.

## Issue #11 — Judge revision prompt has stale "optimization" wording
- **Status:** Open
- **Severity:** Low/Medium
- **User impact:** Revisions are framed for the wrong domain ("expert in optimization algorithms").
- **Technical cause:** Hardcoded role string instead of `load_topic()` (`judge.py:337`).
- **Relevant files:** `pipeline/judge.py:337`.
- **Suggested fix:** Use `load_topic()` like other generators.

## Issue #12 — `quiz` artifact is documented but does not exist
- **Status:** Open
- **Severity:** Low
- **User impact:** Docs imply a quiz feature that isn't built.
- **Technical cause:** `CLAUDE.md` lists `quiz.json`; no schema/prompt/generator/config entry exists.
- **Relevant files:** `CLAUDE.md`, `pipeline/config.json:18-23`.
- **Suggested fix:** Remove the claim or build the feature.

## Issue #13 — Orphan quality-report page / dangling use-case-matrix link
- **Status:** Open
- **Severity:** Low
- **User impact:** `quality-report.html` is unreachable via nav; homepage always links `use-case-matrix.html` which may 404 if the matrix wasn't generated.
- **Relevant files:** `pipeline/templates/index.html:75`, `pipeline/publish.py:342-358,374-445`.
- **Suggested fix:** Add a nav link to the quality report; conditionally render the matrix link.
