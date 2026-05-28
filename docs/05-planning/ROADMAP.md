# Roadmap

> Themed milestones. Not date-bound — sequenced by dependency and value. Last updated: 2026-05-28.

## Milestone 1 — Trustworthy baseline
**Goal:** Green tests, CI, honest docs.
- B1 — Fix the 6 stale-fixture failures.
- B5 — Add CI running `pytest`.
- B4 — Refresh `SETUP.md`, `WOW_FACTOR_ANALYSIS.md`, `CLAUDE.md`.
**Exit criteria:** CI gates PRs on a green suite; no stale runtime claims in docs.

## Milestone 2 — Finish the MCTS migration
**Goal:** The UI matches the MCTS domain end-to-end.
- B2 — Rework playground + knowledge-graph legend for MCTS.
- B11 — Decide the multi-agent pipeline's role and document it.
- Issue #11 — Use `load_topic()` in the judge revision prompt.
**Exit criteria:** No optimization-domain artifacts remain in code/templates; playground and graph are meaningful for MCTS.

## Milestone 3 — Real, representative deployment
**Goal:** The public site reflects the product.
- B3 — Implement the deployment story (content in CI or hosted backend).
- B12 — Fix orphan/dangling navigation.
**Exit criteria:** Visiting the deployed URL shows real content and the interactive-tool behavior matches documentation.

## Milestone 4 — Production-readiness (only if hosting the API publicly)
**Goal:** Safe to expose.
- B7 — Auth, rate limiting, CORS allowlist, `debug=False`, slug validation, request-size limit.
- B9 — Blocking content validation.
**Exit criteria:** Security checklist in `SECURITY_AND_PRIVACY_NOTES.md` satisfied.

## Milestone 5 — Maintainability hardening
**Goal:** Reduce drift and untested surface.
- B10 — Smoke tests for `generate.py`/`publish.py`.
- B6 — Recommender → Blueprint.
- B8 — Consolidate slugify + shared prompt/validation helpers.
- Split large modules (`generator.py`, `publish.py`).
**Exit criteria:** Core orchestration covered by tests; no duplicate slugify; recommender is a blueprint.

## Out of scope / open questions
- Should the multi-agent pipeline replace or feed the single-shot pipeline?
- Multi-provider support (the `LLMProvider` ABC allows it) — reintroduce a non-Gemini fallback?
- A `quiz` artifact (documented but never built) — build or drop?
