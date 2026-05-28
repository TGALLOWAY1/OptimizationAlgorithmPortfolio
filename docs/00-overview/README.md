# Documentation

> Entry point for the `docs/` system. This documentation is treated as a first-class product surface: it documents **actual** behavior with status labels and file:line evidence, and distinguishes what works from what's partial, broken, or merely designed.
> Last updated: 2026-05-28.

## What this project is

**MCTS Strategy Portfolio** — an LLM (Google Gemini) content-generation platform that produces educational artifacts for 8 Monte Carlo Tree Search techniques, publishes them as a static site, and layers interactive study tools via a Flask API. (The repository is still named "OptimizationAlgorithmPortfolio" for legacy reasons; the live topic is MCTS per `pipeline/config.json`.)

## How to use these docs

1. Start with [`PROJECT_SNAPSHOT.md`](PROJECT_SNAPSHOT.md) for a fast, honest picture.
2. Use the [`DOCUMENTATION_INDEX.md`](DOCUMENTATION_INDEX.md) to find the right doc.
3. **AI agents:** load only the bundle relevant to your task — see [`../07-ai-context/CONTEXT_LOADING_PROTOCOL.md`](../07-ai-context/CONTEXT_LOADING_PROTOCOL.md). Don't read everything.

## Conventions

- **Status labels (used everywhere):** `Implemented` · `Partial` · `Stubbed` · `Broken` · `Designed only` · `Deprecated` · `Unknown`.
- **Evidence:** claims cite `file:line`. Inferences are marked.
- **Source of truth:** when prose and code disagree, trust `pipeline/config.json` + code. Several *legacy* docs (`SETUP.md`, `WOW_FACTOR_ANALYSIS.md`) predate the MCTS/Gemini migration and are stale — see [`../04-quality/KNOWN_ISSUES.md`](../04-quality/KNOWN_ISSUES.md) #5.

## Top things to know

- 226 tests, **220 pass / 6 fail** (stale fixtures). `pip install cffi` on a fresh machine before testing.
- The **live site is a placeholder**; interactive tools need the local Flask app + generated content.
- The **playground and knowledge-graph legend** are still on the old optimization domain — incorrect for MCTS.
- There are **two pipelines**: single-shot (production) and multi-agent (standalone, unused by the site/API).

## Maintaining the docs

When you change code, update the matching doc and its status labels, append to [`../06-history/AUDIT_LOG.md`](../06-history/AUDIT_LOG.md), and follow [`../07-ai-context/AGENT_WORKFLOW.md`](../07-ai-context/AGENT_WORKFLOW.md).
