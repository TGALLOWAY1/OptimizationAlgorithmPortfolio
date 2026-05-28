# Context Loading Protocol

> Load the smallest relevant bundle for the task. Do **not** read all docs for every task — it causes context bloat and "lost in the middle" failures.
> Last updated: 2026-05-28.

## Always read first (tiny, orienting)
- `docs/00-overview/PROJECT_SNAPSHOT.md`

Then load **one** bundle below based on the task.

## Product / feature work
Read:
- `docs/01-product/PRODUCT_BRIEF.md`
- `docs/01-product/FEATURE_INVENTORY.md`
- `docs/01-product/CURRENT_BEHAVIOR.md`

Do not read: full decision log, changelogs, prompt inventory, archived docs.

## Frontend / UI / template work
Read:
- `docs/01-product/SCREEN_INVENTORY.md`
- `docs/01-product/USER_FLOWS.md`
- `docs/04-quality/REGRESSION_CHECKLIST.md` (UI section)
- the specific template under `pipeline/templates/` you're changing

Do not read: API internals, data model, agent docs.

## Backend / API work
Read:
- `docs/02-architecture/API_INVENTORY.md`
- `docs/02-architecture/DATA_MODEL.md`
- `docs/02-architecture/ARCHITECTURE.md`
- `docs/04-quality/RISK_REGISTER.md` (security items)

## Content-generation pipeline work
Read:
- `docs/02-architecture/ARCHITECTURE.md` (runtime flow — generation)
- `docs/02-architecture/DATA_MODEL.md`
- `docs/03-implementation/CODEBASE_INVENTORY.md` (pipeline section)
- `docs/03-implementation/CONFIG_AND_ENVIRONMENT.md`

## AI / prompt / model work
Read:
- `docs/07-ai-context/PROMPT_INVENTORY.md`
- `docs/02-architecture/INTEGRATIONS.md`
- `docs/04-quality/KNOWN_ISSUES.md` (AI-related issues)

## Multi-agent pipeline work
Read:
- `docs/02-architecture/ARCHITECTURE.md` (runtime flow — multi-agent)
- `docs/02-architecture/DATA_MODEL.md` (Family 2 schemas)
- `docs/03-implementation/CODEBASE_INVENTORY.md` (multi-agent section)
- `CLAUDE.md` (root) — "Adding a new content agent" 5-touchpoint pattern

## Bug-fix work
Read:
- `docs/04-quality/KNOWN_ISSUES.md`
- `docs/04-quality/REGRESSION_CHECKLIST.md`
- only the relevant feature/screen/API doc

## Testing work
Read:
- `docs/03-implementation/TESTING_STRATEGY.md`
- `docs/04-quality/REGRESSION_CHECKLIST.md`

## Planning / triage work
Read:
- `docs/05-planning/PRIORITIZED_TODO.md`
- `docs/05-planning/BACKLOG.md`
- `docs/05-planning/NEXT_AGENT_TASKS.md`

## Documentation work
Read:
- `docs/00-overview/DOCUMENTATION_INDEX.md`
- `docs/06-history/AUDIT_LOG.md`
- `docs/07-ai-context/AGENT_WORKFLOW.md`

## Anti-patterns
- Don't load the whole `/docs` tree "to be safe."
- Don't read `WOW_FACTOR_ANALYSIS.md` or stale `SETUP.md` for facts — they predate the MCTS/Gemini migration (see KNOWN_ISSUES #5).
- Prefer the audited docs over re-deriving facts from a full code sweep.
