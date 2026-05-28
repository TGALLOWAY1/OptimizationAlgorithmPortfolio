# Next Agent Tasks

> Self-contained prompts another AI agent (or developer) can execute directly. Each lists context, files, goal, non-goals, acceptance criteria, checks, and a commit instruction.
> Pull tasks in order. Last updated: 2026-05-28.

---

## TASK 1 — Fix the 6 failing tests (finish the MCTS fixture migration)

**Context to read first:**
- `docs/04-quality/KNOWN_ISSUES.md` (Issue #1)
- `pipeline/schemas.py` — the `playground_config` and `knowledge_graph` enums
- `pipeline/validator.py` — `_common_technique_errors` / topic-hint logic

**Files likely to edit:** `tests/test_wow_features.py`, `tests/test_validator.py`.

**Goal:** Make `python -m pytest tests/ -q` fully green by updating stale optimization-era fixtures to MCTS values.

**Non-goals:** Don't change `pipeline/schemas.py` or `validator.py` behavior; don't touch production code. This is a test-only fix.

**Specifics:**
- In `test_wow_features.py`: replace `objective_function` values (`sphere`/`rosenbrock`/…) with the schema enum (`game_tree`/`random_tree`/`adversarial_tree`/`blokus_position`); replace `visualization_type` (`contour_trajectory`) with (`tree_expansion`/`visit_heatmap`/`convergence_curve`/`win_rate_over_time`); replace knowledge-graph `category` values (`evolutionary`/…) with (`selection-policy`/`simulation-enhancement`/`parallelization`/`meta-optimization`).
- In `test_validator.py:90-101`: the test feeds a `gradient-descent`/BFGS example and asserts `bfgs` is flagged. Rework it to use an MCTS technique slug and an off-topic term the current validator actually rejects (inspect `technique_hints` in `pipeline/config.json` and `validator.py`).

**Acceptance criteria:** 226 tests, 0 failures.

**Checks:** `pip install cffi && python -m pytest tests/ -q`.

**Commit:** `test: migrate stale optimization fixtures to MCTS schema enums`.

---

## TASK 2 — Make the playground and knowledge graph correct for MCTS

**Context to read first:**
- `docs/04-quality/KNOWN_ISSUES.md` (Issues #2, #4)
- `docs/01-product/SCREEN_INVENTORY.md` (Playground, Knowledge Graph)
- `pipeline/schemas.py` — `playground_config` + `knowledge_graph` enums

**Files likely to edit:** `pipeline/templates/playground_component.html`, `pipeline/templates/knowledge_graph_component.html`.

**Goal:** The playground should visualize MCTS behavior (per the `playground_config` `visualization_type`/`objective_function` enums) instead of falling back to 2D gradient descent; the knowledge-graph legend/colors should use the MCTS `category` enum.

**Non-goals:** Don't change the schemas or the generator; work within the existing `playground_config`/`knowledge_graph` data contracts.

**Specifics:**
- Playground: the `algorithmSteps` dispatch (`playground_component.html:332-343`) is keyed on optimization slugs; MCTS slugs match none, so it falls back to `stepGradientDescent`. Implement visualizations matching `tree_expansion`/`visit_heatmap`/`convergence_curve`/`win_rate_over_time`. If a full rework is out of scope, hide the playground for techniques whose `visualization_type` isn't supported, rather than silently misrendering.
- Knowledge graph: update the legend + color map (`knowledge_graph_component.html:11-14,41-46`) to `selection-policy`/`simulation-enhancement`/`parallelization`/`meta-optimization`.

**Acceptance criteria:** With generated content, the homepage graph is colored + legend correct; technique pages show a meaningful (or hidden) playground, never gradient descent for MCTS.

**Checks:** `python -m pipeline.publish` renders without error; manual browser check (document if browser unavailable). Run `python -m pytest tests/ -q`.

**Commit:** `fix: align playground and knowledge-graph UI with MCTS domain`.

---

## TASK 3 — Refresh stale documentation

**Context to read first:** `docs/04-quality/KNOWN_ISSUES.md` (Issue #5), `docs/00-overview/PROJECT_SNAPSHOT.md`, `pipeline/config.json`.

**Files likely to edit:** `SETUP.md`, `WOW_FACTOR_ANALYSIS.md`, `CLAUDE.md` (root).

**Goal:** Remove all stale claims: OpenAI/gpt-4o usage, "8 optimization algorithms", "70 tests / 7 files", `--provider openai`, `quiz.json`, `--technique "Bayesian Optimization"`. Reflect: MCTS domain, Gemini-only, 226 tests (note the cffi fix), correct artifact types, correct technique names.

**Non-goals:** Don't change code. Don't delete `WOW_FACTOR_ANALYSIS.md` — correct it, or archive it under `docs/06-history/` with a note if obsolete.

**Acceptance criteria:** `grep -ri "openai\|optimization algorithm\|70 tests\|gpt-4o" SETUP.md WOW_FACTOR_ANALYSIS.md CLAUDE.md` returns no stale runtime claims.

**Checks:** Re-read each doc against `pipeline/config.json` + `requirements.txt`.

**Commit:** `docs: correct stale optimization/OpenAI references to MCTS+Gemini`.

---

## TASK 4 — Add a CI workflow running the tests

**Context to read first:** `docs/03-implementation/TESTING_STRATEGY.md`, `.github/workflows/pages.yml`.

**Files likely to edit:** new `.github/workflows/tests.yml`.

**Goal:** Run `pytest tests/ -q` on push/PR (Python 3.11), installing `cffi` before tests to avoid the collection panic.

**Non-goals:** Don't add coverage thresholds yet; don't run the content pipeline (no keys in CI).

**Dependencies:** Do TASK 1 first so CI starts green.

**Acceptance criteria:** Workflow runs on PRs and fails on a failing test.

**Checks:** Push a trivial branch; confirm the workflow runs green.

**Commit:** `ci: run pytest on push and pull requests`.

---

## TASK 5 — Decide and implement the deployment story

**Context to read first:** `docs/04-quality/KNOWN_ISSUES.md` (Issue #3), `docs/02-architecture/INTEGRATIONS.md`, `.github/workflows/pages.yml`, `build_site.py`.

**Goal:** Make the live site representative. Options: (a) generate content in CI using a `GEMINI_API_KEY` secret then publish, documenting that interactive `/api/*` tools are local-only; or (b) host the Flask app and point the static site's `fetch` calls at it.

**Non-goals:** Don't expose unauthenticated paid endpoints publicly without doing TASK in B7 (security hardening) first.

**Acceptance criteria:** The deployed URL shows real content; tool behavior matches what the docs claim.

**Checks:** Deploy preview; verify.

**Commit:** `deploy: publish real MCTS content (or wire static site to hosted API)`.

> After completing any task: update `docs/06-history/AUDIT_LOG.md` and `docs/06-history/CHANGELOG_NOTES.md`, flip the relevant status in `docs/04-quality/KNOWN_ISSUES.md`, and re-run the relevant section of `docs/04-quality/REGRESSION_CHECKLIST.md`.
