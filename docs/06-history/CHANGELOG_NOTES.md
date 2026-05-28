# Changelog Notes

> Narrative history of how the codebase evolved, grouped by theme. Reconstructed from git history (`git log`).
> Not a formal release changelog — there are no version tags. Last updated: 2026-05-28.

## Theme: Topic migration (optimization → MCTS)
- `0f860cb` Make content pipeline topic-agnostic via config-driven domain — *enabled the later switch.*
- `1637986` Retarget pipeline from optimization algorithms to MCTS strategies.
- `f6af636` Fix Read Full Guide link broken by absolute path after MCTS retarget.
- **Left incomplete:** templates (playground/KG), judge revision prompt, docs, and test fixtures still reference optimization (KNOWN_ISSUES #1/#2/#4/#5).

## Theme: Provider consolidation (OpenAI → Gemini)
- `34c7930` Replace all OpenAI services with Gemini — single key, three Gemini models.

## Theme: Quality / evaluation system
- `598e08a` Add artifact manifests and clean regeneration flow.
- `abcbdf3` Harden evaluation persistence and quality report scope.
- `2909e86` Align implementation schema with runtime dependency validation.
- `459723f` Expand content validation for nested fields and technique identity.
- `94e5f8e` Add tool-calling judge and asymmetric model routing.

## Theme: "Wow factor" interactive features
- `479227c` Add wow factor analysis (5 feature proposals) — see `WOW_FACTOR_ANALYSIS.md` (now stale).
- `6355a11` Implement wow factor features 1-3: SSE streaming, knowledge graph, playground.
- `2258779` Add manual verification checklist to README.
- `77016b6` Improve infographic quality / fix markdown formatting bleed.

## Theme: Multi-agent orchestration
- `6b28d3c` Add multi-agent content orchestration pipeline (independent of `pipeline.generate`).

## Theme: Runtime & deployment hardening
- `809b819` Add GitHub Pages deployment workflow and build script.
- `a456020` / `f62244c` Enforce Python 3.11; validate test environment; untrack legacy derived artifacts.
- `8835df7` Serialize manifest provider metadata safely.
- `2e75bd6` Remove the quiz feature end-to-end.

## Theme: Documentation
- `fdd7aa5` Add presentation source materials (NotebookLM) — `presentation_source/`.
- `ce1ab5f` Document generated artifact model and regeneration workflow.
- `63f6236` Update README to reflect current codebase state — *README is the one largely-current legacy doc.*
- 2026-05-28 — **Documentation infrastructure project** (this `docs/` system): baseline inventory, product/feature inventory, screens/flows, architecture + data model, quality/risk audit, backlog/roadmap, AI-context protocol, decision/audit history, visual-regression plan, and a documentation index. Corrected the stale root `CLAUDE.md`.

## Known still-stale at time of writing
- `SETUP.md`, `WOW_FACTOR_ANALYSIS.md`: still describe OpenAI + optimization (BACKLOG B4).
- Test suite: 6 failing on stale fixtures (KNOWN_ISSUES #1).
