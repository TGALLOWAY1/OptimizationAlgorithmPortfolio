# Audit Log

> Chronological record of documentation/audit passes. Newest entries appended at the bottom.

---

# Audit Entry — Phase 1: Repo Discovery & Baseline Safety
- **Date:** 2026-05-28
- **Scope:** Whole repo — structure, stack, entry points, config, environment, test status; baseline for the documentation system.
- **Agent:** Claude Code (claude-opus-4-7) + 6 parallel general-purpose audit subagents (architecture, API, data model, AI/prompts, testing/debt, UI/templates).
- **Summary:** Established the repo is an MCTS-strategy educational-content platform (not the "optimization algorithm" platform its prose docs claim). Confirmed Gemini-only LLM routing, two parallel generation pipelines (single-shot is the production path; multi-agent is a standalone subsystem), and a static-site + Flask-API publishing model. Measured the real test status.
- **Files inspected:** `pipeline/config.json`, `pipeline/paths.py`, `api/app.py`, `build_site.py`, `SETUP.md`, `.github/workflows/pages.yml`, `requirements.txt`, `.gitignore`; subagents read all of `pipeline/`, `api/`, `pipeline/agents/`, `pipeline/content_pipeline/`, `pipeline/prompts/`, `pipeline/templates/`, `tests/`, `examples/`.
- **Docs changed:** Created `docs/` tree; wrote `00-overview/PROJECT_SNAPSHOT.md`, `03-implementation/CODEBASE_INVENTORY.md`, `03-implementation/CONFIG_AND_ENVIRONMENT.md`, `06-history/AUDIT_LOG.md`.
- **Findings:**
  - **226 tests, 220 pass, 6 fail** (not "70 tests passing"). All 6 failures are stale optimization-era fixtures vs. migrated MCTS schema enums.
  - `CLAUDE.md`, `SETUP.md`, `WOW_FACTOR_ANALYSIS.md` are significantly stale (wrong domain, wrong provider, wrong test counts). `README.md` is largely current.
  - Live GitHub Pages deploy almost certainly serves the placeholder page (no content committed, no pipeline run in CI).
  - Playground + knowledge-graph templates hardcoded for numerical optimization → Broken/wrong for MCTS slugs.
  - Fresh-container pytest needs `pip install cffi`.
- **Open questions:** Is the multi-agent pipeline intended to replace the single-shot path? Is the live site meant to show real content (requires committing `generated/` or running the pipeline in CI)?
- **Next recommended action:** Phase 2 — product & feature inventory.
- **Commit:** `docs: add baseline codebase inventory` (see git log).

---

# Audit Entry — Phases 2-8: Documentation System Build
- **Date:** 2026-05-28
- **Scope:** Product/feature inventory, screens/routes/flows, architecture + data model + API + state + integrations, testing/quality/risk/security, backlog/roadmap/next-tasks, AI-context protocol, decision/change history.
- **Agent:** Claude Code (claude-opus-4-7), synthesizing the 6 Phase-1 audit subagents' findings.
- **Summary:** Authored the full `docs/` tree with honest status labels and file:line evidence. Reconstructed the decision history from git (`git log`), confirming the optimization→MCTS retarget, OpenAI→Gemini switch, tool-calling judge, dual-pipeline design, and quiz removal. Corrected the stale root `CLAUDE.md`.
- **Files inspected:** All Phase-1 sources plus `git log` history; `SETUP.md`, `.github/workflows/pages.yml`, `pipeline/paths.py` re-read for config/deploy docs.
- **Docs changed:** Created all docs under `01-product/`, `02-architecture/`, `03-implementation/` (testing), `04-quality/`, `05-planning/`, `06-history/` (decision log + changelog), `07-ai-context/`; updated root `CLAUDE.md`.
- **Findings:** Confirmed and documented 13 known issues, 10 debt items, 10 risks. Notable: quiz was explicitly removed end-to-end (`2e75bd6`) yet still in `CLAUDE.md`; the multi-agent pipeline has no production consumer; the live deploy is a placeholder.
- **Open questions:** deployment story for real content; multi-agent pipeline's intended role; whether to restore multi-provider support.
- **Next recommended action:** Phases 9-10 — visual regression plan + documentation index/onboarding.
- **Commit:** see `docs:` commits for Phases 2-8 in git log.
