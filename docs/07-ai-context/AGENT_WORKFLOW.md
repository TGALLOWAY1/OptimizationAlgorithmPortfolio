# Agent Workflow

> The standard loop for executing a task in this repo, and how to keep the docs system current.
> Last updated: 2026-05-28.

## Standard loop

```
1. ORIENT     read PROJECT_SNAPSHOT + one CONTEXT_LOADING_PROTOCOL bundle
2. CONFIRM    git status clean; task understood; check KNOWN_ISSUES
3. PLAN       smallest change; identify files; note non-goals
4. CHANGE     edit code/docs; keep schemas↔templates↔tests in sync
5. VERIFY     run tests + relevant REGRESSION_CHECKLIST section
6. DOCUMENT   update affected docs + status labels; append AUDIT_LOG
7. COMMIT     small, single-purpose, clear message
```

## Using subagents (recommended for breadth)
This documentation system was built with parallel audit subagents. Reuse the pattern:
- Spawn focused, read-only audit agents for wide searches (e.g., "find every place X is rendered"), so large outputs stay out of your main context.
- Give each a narrow task and ask for structured markdown with file:line evidence.
- Don't duplicate a subagent's work in the main thread.

## Keeping docs in sync (which doc changes when)

| You changed… | Update… |
|---|---|
| A feature's behavior/status | `01-product/FEATURE_INVENTORY.md`, `CURRENT_BEHAVIOR.md` |
| A page/template | `01-product/SCREEN_INVENTORY.md`, screenshots in `08-visuals/` |
| A route/endpoint | `02-architecture/API_INVENTORY.md`, `03-implementation/ROUTE_INVENTORY.md` |
| A schema | `02-architecture/DATA_MODEL.md` + fixtures |
| A module's role | `03-implementation/CODEBASE_INVENTORY.md`, `02-architecture/SYSTEM_MAP.md` |
| A prompt | `07-ai-context/PROMPT_INVENTORY.md` |
| Fixed/found a defect | `04-quality/KNOWN_ISSUES.md` (flip status / add) |
| Any task | append `06-history/AUDIT_LOG.md`; add to `CHANGELOG_NOTES.md` |
| A notable design choice | `06-history/DECISION_LOG.md` |

## Status-label discipline
Use exactly: Implemented · Partial · Stubbed · Broken · Designed only · Deprecated · Unknown. Cite file:line evidence. Never upgrade a label without evidence.

## Safety rules
- Never overwrite uncommitted user changes — stop and report.
- Never commit secrets/`.env`.
- Don't run destructive git operations without explicit instruction.
- Don't open PRs unless asked.
