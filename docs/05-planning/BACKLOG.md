# Backlog

> Actionable items derived from the audit. Scoring: **Priority = user impact + technical risk reduction + recruiter/demo value − implementation complexity** (each 1-5; higher = do sooner).
> Last updated: 2026-05-28. See `PRIORITIZED_TODO.md` for the ranked shortlist.

---

## B1 — Fix the 6 failing tests (MCTS fixture migration)
- **Priority:** High (impact 2 + risk 4 + demo 3 − complexity 1 = 8)
- **Category:** Test debt
- **User impact:** None directly; restores a green suite and trust.
- **Technical impact:** Removes the red baseline that hides regressions.
- **Why now:** Lowest effort, highest signal; unblocks CI.
- **Relevant files:** `tests/test_wow_features.py`, `tests/test_validator.py:90-101`.
- **Dependencies:** none.
- **Acceptance criteria:** `python -m pytest tests/ -q` → all pass.
- **Implementation plan:** Replace optimization enum values with MCTS ones (`game_tree`/`tree_expansion`/`selection-policy`); fix the `test_wrong_technique_example_is_rejected` assertion to use a term the current validator rejects.
- **Verification:** Full suite green.

## B2 — Finish the MCTS migration in templates (playground + knowledge graph)
- **Priority:** High (impact 5 + risk 2 + demo 5 − complexity 3 = 9)
- **Category:** Correctness / UX
- **User impact:** Playground currently animates gradient descent for every technique; KG nodes render gray.
- **Technical impact:** Aligns the UI with the MCTS schemas.
- **Why now:** Most visible wrongness; high demo value.
- **Relevant files:** `pipeline/templates/playground_component.html:69-78,164-343`, `knowledge_graph_component.html:11-14,41-46`.
- **Dependencies:** understanding of intended MCTS visualizations.
- **Acceptance criteria:** Playground renders MCTS-appropriate visualizations keyed to `playground_config` enums; KG legend/colors match MCTS categories.
- **Verification:** Generate content; open homepage + a technique page; confirm visuals.

## B3 — Decide and implement the deployment story
- **Priority:** High (impact 5 + risk 2 + demo 5 − complexity 3 = 9)
- **Category:** Product/deploy
- **User impact:** Live site is a placeholder with non-functional tools.
- **Technical impact:** Defines how content + API reach users.
- **Why now:** The public artifact doesn't represent the product.
- **Relevant files:** `.github/workflows/pages.yml`, `build_site.py`, `api/app.py`.
- **Acceptance criteria:** Either CI generates+publishes real content (with a key) and docs state tools are local-only, or the Flask app is hosted and the static site points at it.
- **Verification:** Visit the deployed URL; content + (documented) tools behave as stated.

## B4 — Refresh stale documentation (SETUP.md, WOW_FACTOR_ANALYSIS.md, CLAUDE.md)
- **Priority:** Medium-High (impact 3 + risk 2 + demo 4 − complexity 2 = 7)
- **Category:** Docs
- **User impact:** Stops misleading contributors (OpenAI keys, optimization domain, wrong test counts).
- **Relevant files:** `SETUP.md`, `WOW_FACTOR_ANALYSIS.md`, `CLAUDE.md`, `README.md`.
- **Acceptance criteria:** No stale OpenAI/optimization/test-count claims; setup describes Gemini-only + `cffi` note.
- **Verification:** grep finds no stale runtime claims.

## B5 — Add a CI workflow that runs the tests
- **Priority:** Medium-High (impact 2 + risk 4 + demo 3 − complexity 2 = 7)
- **Category:** Process/tooling
- **Technical impact:** Catches red suites and regressions automatically.
- **Relevant files:** new `.github/workflows/tests.yml`.
- **Dependencies:** B1 (so CI starts green).
- **Acceptance criteria:** PRs run `pytest tests/ -q` (with the `cffi` install) and gate on green.
- **Verification:** A failing test blocks a PR.

## B6 — Refactor the recommender into a Blueprint
- **Priority:** Medium (impact 1 + risk 3 + demo 1 − complexity 2 = 3)
- **Category:** Architecture
- **Technical impact:** Removes the two-Flask-app proxy hack; consistent error handling/headers.
- **Relevant files:** `pipeline/recommender_api.py`, `api/app.py:28-38`.
- **Acceptance criteria:** `/api/recommend` served by a registered blueprint; proxy + second Flask app removed; tests pass.

## B7 — Security hardening for any public API hosting
- **Priority:** Medium (impact 3 + risk 5 + demo 1 − complexity 3 = 6); High if hosting publicly
- **Category:** Security
- **Relevant files:** `api/app.py`, `recommender_api.py`, `api/compare.py`.
- **Acceptance criteria:** `debug=False` option, CORS allowlist, auth + rate limit, slug validation, request-size limit. See `docs/04-quality/SECURITY_AND_PRIVACY_NOTES.md` checklist.

## B8 — Consolidate duplicated helpers (slugify, prompt/validation builders)
- **Priority:** Medium (impact 1 + risk 3 + demo 1 − complexity 2 = 3)
- **Category:** Debt
- **Relevant files:** `generator.py:55`, `publish.py:39`, `build_site.py:21`; `api/math_tutor.py`, `api/study_plan.py`.
- **Acceptance criteria:** One `slugify`; shared math-tutor/study-plan prompt+validation helper used by both JSON and SSE routes.

## B9 — Make content validation blocking (or add `--strict`)
- **Priority:** Medium (impact 3 + risk 2 + demo 2 − complexity 2 = 5)
- **Category:** Quality
- **Relevant files:** `pipeline/generator.py:298-307`.
- **Acceptance criteria:** Content-rule failures stop the artifact from being written/published (default or via flag).

## B10 — Add smoke tests for `generate.py` and `publish.py`
- **Priority:** Medium (impact 2 + risk 4 + demo 1 − complexity 3 = 4)
- **Category:** Test coverage
- **Relevant files:** `pipeline/generate.py`, `pipeline/publish.py`, new tests.
- **Acceptance criteria:** Mocked-provider tests assert artifacts written and HTML rendered; covers the major branches.

## B11 — Clarify the multi-agent pipeline's role
- **Priority:** Low-Medium (impact 2 + risk 1 + demo 3 − complexity 2 = 4)
- **Category:** Product/architecture
- **Description:** It's fully built but unused by the site/API. Decide: wire it into publishing, keep as a demo, or document explicitly as standalone.
- **Relevant files:** `pipeline/content_pipeline/`, `docs/01-product/FEATURE_INVENTORY.md`.

## B12 — Fix orphan/dangling navigation
- **Priority:** Low (impact 1 + risk 1 + demo 2 − complexity 1 = 3)
- **Relevant files:** `index.html:75`, `publish.py:342-358,374-445`.
- **Acceptance criteria:** quality-report linked from nav; use-case-matrix link only rendered when the page exists.
