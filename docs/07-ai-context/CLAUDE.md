# Working in this repo as an AI agent

> Operating guide for AI agents. The root `CLAUDE.md` holds project facts + conventions; this file is the *how-to-work* layer. Last updated: 2026-05-28.

## Before you code
1. Read `docs/00-overview/PROJECT_SNAPSHOT.md`, then the one relevant bundle in `CONTEXT_LOADING_PROTOCOL.md`. Don't load everything.
2. Trust `pipeline/config.json` + code over prose docs when they disagree (several legacy docs predate the MCTS/Gemini migration).
3. Check `docs/04-quality/KNOWN_ISSUES.md` — your task may already be catalogued there.
4. `git status` — confirm a clean tree. If there are uncommitted changes you didn't make, **stop and report**; do not overwrite user work.

## While you code
- Make the smallest change that satisfies the task. This is a documentation-first repo; **don't refactor product code unless explicitly asked.**
- Keep schemas, templates, and tests in sync — the #1 breakage here is an enum changed in `schemas.py` without updating templates + fixtures (that's exactly what broke the suite).
- Mark behavior honestly: **Implemented** only if present and working; otherwise Partial/Stubbed/Broken/Designed only/Unknown.

## After you code
1. Run the relevant part of `docs/04-quality/REGRESSION_CHECKLIST.md`.
2. Run tests: `pip install cffi && python -m pytest tests/ -q`. Baseline is 220 pass / 6 known-fail until Issue #1 is fixed — don't add new failures.
3. Update the docs you invalidated: feature status, KNOWN_ISSUES status, and append to `docs/06-history/AUDIT_LOG.md` + `CHANGELOG_NOTES.md`. Log notable design choices in `DECISION_LOG.md`.
4. If you changed the UI and could generate/screenshot it, update `docs/08-visuals/SCREENSHOT_MANIFEST.md`.

## Committing
- Small, single-purpose commits. Don't bundle unrelated changes.
- Clear messages (`fix:`/`docs:`/`test:`/`ci:`). Never commit `.env` or secrets.
- Don't open a PR unless asked.

## Avoiding context bloat
- Use `CONTEXT_LOADING_PROTOCOL.md` bundles. Use subagents for wide searches so raw output stays out of the main context.
- Don't paste whole large files into reasoning when a targeted read suffices.

## Implemented vs planned
- "Implemented" = code present and observed/likely-working with evidence (cite file:line).
- If a feature is in docs but not in code, it's **Designed only** (e.g., the `quiz` artifact).
- If UI exists but calls a backend that isn't running/deployed, it's **Partial** (e.g., the API-backed widgets on the static deploy).

## Repo-specific landmines
- `python -m pytest` needs `cffi` on a fresh container or it panics.
- `--provider` only accepts `gemini` and overrides the cheaper flash default.
- The recommender is a separate Flask app proxied into `api/app.py` — touch with care.
- `build_site.py` ignores the generated-root env var.
- The live Pages deploy serves a placeholder; interactive tools need local Flask.
