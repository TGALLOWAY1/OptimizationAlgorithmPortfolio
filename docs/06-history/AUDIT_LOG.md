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
