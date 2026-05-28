# Prioritized TODO

> The ranked shortlist. Pull from the top. Full detail in `BACKLOG.md`; executable prompts in `NEXT_AGENT_TASKS.md`.
> Last updated: 2026-05-28.

| Rank | Task | Score | Effort | Why |
|---|---|---|---|---|
| 1 | **B1** — Fix 6 failing tests (MCTS fixtures) | 8 | XS | Restores green suite; unblocks CI; tiny effort |
| 2 | **B2** — Finish MCTS migration in templates (playground + KG) | 9 | M | Most visible defect; high demo value |
| 3 | **B3** — Decide/implement deployment story | 9 | M | Live site is a non-representative placeholder |
| 4 | **B4** — Refresh stale docs (SETUP/WOW/CLAUDE) | 7 | S | Stops actively misleading contributors |
| 5 | **B5** — Add CI test workflow | 7 | S | Prevents future red suites (do after B1) |
| 6 | **B7** — Security hardening (if hosting publicly) | 6 | M | Blocks public exposure of paid endpoints |
| 7 | **B9** — Blocking content validation / `--strict` | 5 | S | Stops publishing weak artifacts |
| 8 | **B10** — Smoke tests for generate.py / publish.py | 4 | M | Covers the untested core |
| 9 | **B11** — Clarify multi-agent pipeline role | 4 | S | Resolve "built but unused" |
| 10 | **B6** — Recommender → Blueprint | 3 | S | Removes the proxy hack |
| 11 | **B8** — Consolidate slugify + prompt/validation helpers | 3 | S | Reduce drift risk |
| 12 | **B12** — Fix orphan/dangling nav | 3 | XS | Small UX polish |

## Suggested first sprint
B1 → B5 (green suite + CI), then B2 + B4 (visible correctness + honest docs), then B3 (deploy decision). These maximize demo value and contributor trust for the least risk.
