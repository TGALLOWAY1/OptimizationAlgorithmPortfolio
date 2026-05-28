# Product Brief

> What the product is, who it's for, and what it does. Evidence-grounded.
> Last updated: 2026-05-28.

## One-liner

An automated platform that uses Google Gemini to generate a complete, multi-format learning portfolio for **8 Monte Carlo Tree Search (MCTS) strategies**, publishes it as a static educational website, and layers interactive AI study tools on top via a Flask API.

## Problem it addresses

High-quality, consistent educational material for advanced algorithm families is expensive and slow to produce by hand. This project treats content as a generated, schema-validated, quality-gated artifact: each technique gets a planned set of artifacts (overview, math deep-dive, implementation guide, infographic) produced by LLMs, validated against strict JSON Schemas, and optionally scored by an LLM judge before publishing.

## Who it's for

- **Learners** studying MCTS — browse technique pages, compare strategies, get a personalized study plan, ask for equation explanations, adapt code to their framework.
- **Content operators** — run the pipeline to (re)generate and publish the whole portfolio.
- **Recruiters / reviewers** — inspect a self-documenting AI-content-engineering project.
- **Future AI agents** — extend the pipeline (new technique, artifact, provider, endpoint, or agent).

## The 8 techniques

UCT · RAVE · Progressive History and Progressive Widening · NST · Rollout Policy Strategies · Opponent Modeling in MCTS · Root and Tree Parallelization · Adaptive Meta-Optimization (`pipeline/config.json:8-17`).

## What you actually get

1. **A content engine** (`pipeline/generate.py`) — generates per-technique artifacts, idempotently, with retry + schema enforcement.
2. **A quality system** — JSON-Schema validation, content rules, an LLM-as-judge with tool use (code execution, equation checks, reference lookup), and a revision loop.
3. **A static site** (`pipeline/publish.py`) — homepage catalog, per-technique pages, comparison page, use-case matrix, knowledge graph, quality report.
4. **A Flask API** — 5 interactive endpoints: recommend, compare, math_tutor, study_plan, adapt_code (with SSE streaming variants).
5. **A multi-agent content pipeline** (`pipeline/content_pipeline/`) — an independent 8-stage authoring workflow (intake → research → outline → draft → review → edit → repurpose → QA) with quality gates. Built and tested, but not wired into the site/API.

## Honest status summary

- **Core generation + publishing + API:** Implemented and tested.
- **Live website:** Currently publishes a **placeholder** (CI doesn't run the content pipeline, and `generated/` is gitignored). Full content + interactive tools work only when running locally with content generated and the Flask app serving.
- **Interactive playground & knowledge-graph legend:** Templates still hardcoded for the old numerical-optimization domain → **Broken / semantically wrong for MCTS**.
- **Docs (`CLAUDE.md`, `SETUP.md`, `WOW_FACTOR_ANALYSIS.md`):** Significantly stale (describe optimization algorithms + OpenAI).

See `docs/01-product/FEATURE_INVENTORY.md` for per-feature detail and `docs/01-product/CURRENT_BEHAVIOR.md` for what happens when you run it.
