# Documentation Index

> Map of the entire `docs/` system. Last updated: 2026-05-28.

## Start Here
- [Project snapshot](PROJECT_SNAPSHOT.md) — fast, honest status + test results
- [Product brief](../01-product/PRODUCT_BRIEF.md) — what it is, who it's for
- [Current behavior](../01-product/CURRENT_BEHAVIOR.md) — what actually happens when you run it
- [Architecture](../02-architecture/ARCHITECTURE.md) — how it works internally
- [Known issues](../04-quality/KNOWN_ISSUES.md) — what's broken/partial, prioritized
- [Next agent tasks](../05-planning/NEXT_AGENT_TASKS.md) — ready-to-execute work
- [Context loading protocol](../07-ai-context/CONTEXT_LOADING_PROTOCOL.md) — for AI agents

## Overview (`00-overview/`)
- [README](README.md) — docs entry point + conventions
- [DOCUMENTATION_INDEX](DOCUMENTATION_INDEX.md) — this file
- [PROJECT_SNAPSHOT](PROJECT_SNAPSHOT.md)

## Product Docs (`01-product/`)
- [PRODUCT_BRIEF](../01-product/PRODUCT_BRIEF.md)
- [FEATURE_INVENTORY](../01-product/FEATURE_INVENTORY.md) — 21 features with status
- [CURRENT_BEHAVIOR](../01-product/CURRENT_BEHAVIOR.md)
- [USER_FLOWS](../01-product/USER_FLOWS.md) — 8 core flows
- [SCREEN_INVENTORY](../01-product/SCREEN_INVENTORY.md) — pages + components

## Architecture Docs (`02-architecture/`)
- [ARCHITECTURE](../02-architecture/ARCHITECTURE.md)
- [SYSTEM_MAP](../02-architecture/SYSTEM_MAP.md)
- [DATA_MODEL](../02-architecture/DATA_MODEL.md) — 16 JSON-schema entities
- [API_INVENTORY](../02-architecture/API_INVENTORY.md) — endpoints + CLI commands
- [STATE_MANAGEMENT](../02-architecture/STATE_MANAGEMENT.md)
- [INTEGRATIONS](../02-architecture/INTEGRATIONS.md) — Gemini, CDNs, Pages

## Implementation Docs (`03-implementation/`)
- [CODEBASE_INVENTORY](../03-implementation/CODEBASE_INVENTORY.md) — module map
- [ROUTE_INVENTORY](../03-implementation/ROUTE_INVENTORY.md)
- [CONFIG_AND_ENVIRONMENT](../03-implementation/CONFIG_AND_ENVIRONMENT.md)
- [TESTING_STRATEGY](../03-implementation/TESTING_STRATEGY.md)
- *(COMPONENT_INVENTORY: covered within SCREEN_INVENTORY + CODEBASE_INVENTORY — this is a server-rendered Jinja/JS app, not a component framework.)*

## Quality Docs (`04-quality/`)
- [KNOWN_ISSUES](../04-quality/KNOWN_ISSUES.md) — 13 issues
- [TECHNICAL_DEBT](../04-quality/TECHNICAL_DEBT.md) — 10 items
- [RISK_REGISTER](../04-quality/RISK_REGISTER.md) — 10 risks
- [REGRESSION_CHECKLIST](../04-quality/REGRESSION_CHECKLIST.md)
- [SECURITY_AND_PRIVACY_NOTES](../04-quality/SECURITY_AND_PRIVACY_NOTES.md)

## Planning Docs (`05-planning/`)
- [BACKLOG](../05-planning/BACKLOG.md) — 12 scored items
- [PRIORITIZED_TODO](../05-planning/PRIORITIZED_TODO.md)
- [ROADMAP](../05-planning/ROADMAP.md) — 5 milestones
- [NEXT_AGENT_TASKS](../05-planning/NEXT_AGENT_TASKS.md) — 5 executable prompts

## AI Agent Docs (`07-ai-context/`)
- [CONTEXT_LOADING_PROTOCOL](../07-ai-context/CONTEXT_LOADING_PROTOCOL.md)
- [CLAUDE](../07-ai-context/CLAUDE.md) — agent operating guide
- [AGENT_WORKFLOW](../07-ai-context/AGENT_WORKFLOW.md)
- [PROMPT_INVENTORY](../07-ai-context/PROMPT_INVENTORY.md)

## Historical Docs (`06-history/`)
- [DECISION_LOG](../06-history/DECISION_LOG.md) — 9 decisions
- [CHANGELOG_NOTES](../06-history/CHANGELOG_NOTES.md)
- [AUDIT_LOG](../06-history/AUDIT_LOG.md)

## Visual Docs (`08-visuals/`)
- [SCREENSHOT_MANIFEST](../08-visuals/SCREENSHOT_MANIFEST.md)
- [VISUAL_REGRESSION_PLAN](../08-visuals/VISUAL_REGRESSION_PLAN.md)
- [FLOW_DIAGRAMS](../08-visuals/FLOW_DIAGRAMS.md) — Mermaid diagrams

## Pre-existing
- [content-pipeline-orchestration.md](../content-pipeline-orchestration.md) — detailed multi-agent pipeline reference (predates this system; still accurate)

## Note on the prescribed structure
This index follows the documentation-project spec. Two files in the spec were intentionally folded rather than stubbed: `COMPONENT_INVENTORY.md` (no component framework here — content lives in `SCREEN_INVENTORY.md` + `CODEBASE_INVENTORY.md`) and a separate `07-ai-context/CLAUDE.md` exists alongside the corrected **root** `CLAUDE.md`.
