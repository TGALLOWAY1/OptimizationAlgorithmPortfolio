# Optimization Algorithm Portfolio

An automated educational content platform that generates comprehensive learning materials for **Monte Carlo Tree Search (MCTS) strategies and enhancements** using a multi-provider LLM pipeline, plus a multi-agent orchestration layer for arbitrary technical-content production.

> The repository name reflects its origins; the active subject matter is configured in `pipeline/config.json` and is currently the MCTS Strategy Portfolio.

## Overview

This project combines three subsystems that share the same LLM client, schema validator, and prompt-template idioms:

1. **Per-technique content pipeline** (`pipeline/generate.py`) — generates structured artifacts (plan, overview, math deep dive, implementation, infographic spec, infographic image, playground config, knowledge graph) for each technique listed in `config.json`. Idempotent, manifest-aware, and routed per-artifact to the most appropriate Gemini model.
2. **Multi-agent content pipeline** (`pipeline/content_pipeline/` + `pipeline/agents/`) — takes an arbitrary raw input (idea, transcript, outline, or rough draft) and runs it through eight specialized agents, with quality gates between stages, structured run state on disk, and resume-by-run-id support.
3. **Interactive Flask API** (`api/`) — serves recommender, comparison, math tutor, study plan, and code adaptation endpoints alongside the static site.

## Current Status & Known Limitations

Honest snapshot (see [`docs/00-overview/PROJECT_SNAPSHOT.md`](docs/00-overview/PROJECT_SNAPSHOT.md) and [`docs/04-quality/KNOWN_ISSUES.md`](docs/04-quality/KNOWN_ISSUES.md) for detail):

- **Core generation, publishing, and API:** implemented and tested.
- **Tests:** 226 tests, currently **220 passing / 6 failing** — the 6 are stale optimization-era fixtures that don't match the migrated MCTS schema enums. On a fresh machine, `pip install cffi` before running tests or collection panics.
- **Live GitHub Pages site:** publishes a **placeholder** page — CI doesn't run the content pipeline and `generated/` is gitignored. Full content + the interactive `/api/*` tools (recommender, compare, study plan, math tutor, adapt code) work only when running the Flask app locally with content generated.
- **Interactive playground & knowledge-graph legend:** still hardcoded for the previous numerical-optimization domain, so they're incorrect for MCTS techniques.
- **Legacy docs:** `SETUP.md` and `WOW_FACTOR_ANALYSIS.md` predate the MCTS/Gemini migration and contain stale OpenAI/optimization references. This README and the `docs/` tree are current.

## MCTS Strategies Covered

The eight techniques currently configured in `pipeline/config.json`:

1. **UCT** — Upper Confidence Bounds for Trees
2. **RAVE** — Rapid Action Value Estimation
3. **Progressive History & Progressive Widening**
4. **NST** — N-gram Selection Technique
5. **Rollout Policy Strategies**
6. **Opponent Modeling in MCTS**
7. **Root & Tree Parallelization**
8. **Adaptive Meta-Optimization**

The list is configuration-driven. Retargeting the portfolio to a different domain is a `config.json` change — see `pipeline/generate.py` and `pipeline/config.json`.

## Quick Start

### Prerequisites

- Python 3.11+
- Google Gemini API key (`GEMINI_API_KEY`) — used for all text and image generation

### Installation

```bash
git clone https://github.com/TGALLOWAY1/OptimizationAlgorithmPortfolio.git
cd OptimizationAlgorithmPortfolio

python3.11 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cat > .env << 'EOF'
GEMINI_API_KEY=your-gemini-key-here
EOF
```

### Generate Per-Technique Content

```bash
# Generate every configured technique
python3.11 -m pipeline.generate

# Generate a single technique
python3.11 -m pipeline.generate --technique "UCT (Upper Confidence Bounds for Trees)"

# Skip image generation (faster, lower cost)
python3.11 -m pipeline.generate --skip-images

# Force regeneration of cached artifacts
python3.11 -m pipeline.generate --force
```

### Run the Multi-Agent Content Pipeline

```bash
# Smoke run with stub agents (no API key required)
python3.11 examples/run_content_pipeline.py --dry-run

# Real run (uses GEMINI_API_KEY)
python3.11 examples/run_content_pipeline.py --input examples/sample_input.json

# Resume an interrupted run by id
python3.11 examples/run_content_pipeline.py --resume <run_id>
```

Outputs land under `outputs/runs/<run_id>/` (gitignored).

### Publish Static Site

```bash
python3.11 -m pipeline.publish
```

### Run the Application

```bash
python3.11 api/app.py
# Open http://localhost:5000
```

## API Endpoints

| Endpoint              | Method | Description                                        |
| --------------------- | ------ | -------------------------------------------------- |
| `/api/recommend`      | POST   | Get algorithm recommendations for a problem        |
| `/api/compare`        | POST   | Compare two algorithms side-by-side                |
| `/api/math_tutor`     | POST   | Get explanations for math concepts (SSE streaming) |
| `/api/study_plan`     | POST   | Generate a personalized study plan (SSE streaming) |
| `/api/adapt_code`     | POST   | Adapt code between frameworks                      |

### Example: Algorithm Recommendation

```bash
curl -X POST http://localhost:5000/api/recommend \
  -H "Content-Type: application/json" \
  -d '{"query": "I need a selection policy that handles high branching factors with limited rollouts"}'
```

## Architecture

### Multi-Model LLM Routing

All requests are routed through `pipeline.llm_client.get_provider(artifact_type)`, which reads `pipeline/config.json`'s `artifact_provider_map` and returns the right provider instance. Three Gemini-family models are wired up; the assignment is deliberately asymmetric — flagship reasoning where it matters, cheap flash everywhere else, and the image model only for visual artifacts.

| Provider key   | Model                              | Role                                                                                          |
| -------------- | ---------------------------------- | --------------------------------------------------------------------------------------------- |
| `gemini`       | `gemini-3.1-pro-preview`           | High-stakes reasoning: drafting, technical review, editor, recommender, judge, math tutor, comparator, study plan, code adapter. |
| `gemini_flash` | `gemini-3.1-flash-preview`         | Bulk generation: per-technique plans, overviews, math deep dives, implementations, infographic specs, homepage summaries, knowledge graph, playground configs, intake/research/outline/repurposing/QA agents. |
| `nano_banana`  | `gemini-3.1-flash-image-preview`   | Image generation: infographic and preview images.                                              |

Adding a new provider is a three-step change: subclass `LLMProvider` in `pipeline/llm_client.py`, register it in `get_provider()`, and add an entry under `providers` and `artifact_provider_map` in `config.json`.

### Per-Technique Content Pipeline

`pipeline/generate.py` is the orchestrator for the technique-content axis:

1. **Config-driven** — `config.json` lists techniques and maps each artifact type to a provider.
2. **Manifest-aware idempotency** — `manifest.json` per technique tracks the input hash (prompt + schema + config slice + technique inputs). Artifacts regenerate only when an input changes or `--force` is set.
3. **Strict schemas** — every JSON artifact is validated against a schema in `pipeline/schemas.py` after generation, with an additional content-validation pass in `pipeline/validator.py` (word counts, LaTeX presence, technique-term coverage, off-topic detection).
4. **Exponential-backoff retry** — `generate_with_retry` retries up to three times (2s, 4s, 8s) on API failures and schema-validation failures.
5. **Generated/source split** — `content/` holds tracked source data (references, rubrics); `generated/` holds runtime outputs (gitignored); `site/` holds published HTML (gitignored).

### Multi-Agent Content Pipeline

A separate orchestration layer (`pipeline/content_pipeline/` + `pipeline/agents/`) runs an arbitrary raw input through eight specialized agents with quality gates between stages. Every step writes a typed JSON artifact to disk; failed gates trigger a bounded revision pass; interrupted runs can be resumed by run id.

```
ContentPipelineInput
       │
       ▼
   ┌─────────┐    ┌──────────┐    ┌─────────┐    ┌─────────┐
   │ intake  │───▶│ research │───▶│ outline │───▶│  draft  │
   └─────────┘    └──────────┘    └─────────┘    └─────────┘
   intake_gate                    outline_gate   draft_gate
       │                                │             │
       ▼                                ▼             ▼
   ┌──────────────────┐    ┌────────┐    ┌─────────────┐    ┌──────────────┐
   │ technical_review │───▶│ editor │───▶│ repurposing │───▶│ publishing_qa│
   └──────────────────┘    └────────┘    └─────────────┘    └──────────────┘
   tech_review_gate                        (optional)         final_qa_gate
                                                              (optional)
```

#### Agent roles

| Stage              | Agent                       | Responsibility                                                                                                                                                          | Provider key            |
| ------------------ | --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------- |
| `intake`           | **Intake Agent**            | Parses the user's raw input (idea, transcript, outline, draft) and extracts a normalized `ContentBrief`: topic, audience, content type, technical depth, goals, requested artifacts. | `agent_intake` (Flash)  |
| `research`         | **Research Agent**          | Surfaces the claims a piece needs to support, marks each claim's `needs_verification` flag, and lists assumptions and open questions. (No live web access — claims that depend on external sources are flagged for human verification.) | `agent_research` (Flash)|
| `outline`          | **Outline Agent**           | Converts brief + research into a structured outline with title, hook, ordered sections, per-section purpose and key points, target word count, and target format.       | `agent_outline` (Flash) |
| `draft`            | **Drafting Agent**          | Produces the first full Markdown draft, using the outline as the source of truth, matching audience and depth from the brief. Refuses placeholder text.                  | `agent_draft` (Pro)     |
| `technical_review` | **Technical Reviewer Agent**| Reads the draft as a careful senior engineer would: flags inaccuracies, vague claims, missing steps, unsupported assumptions. Returns issues with explicit severity (`critical/major/minor/nit`). Does not rewrite prose. | `agent_technical_review` (Pro) |
| `editor`           | **Editor Agent**            | Improves clarity, structure, transitions, concision, and tone while preserving every load-bearing technical claim. Resolves reviewer issues and reports the edits made.  | `agent_editor` (Pro)    |
| `repurposing`      | **Repurposing Agent**       | Converts the edited long-form into channel-specific assets: LinkedIn post, X thread, YouTube description, short-form video script, newsletter blurb, README excerpt. Each asset matches its channel's voice and length conventions. *(Optional stage — failures are recorded as `skipped`, not `failed`.)* | `agent_repurposing` (Flash) |
| `publishing_qa`    | **Publishing QA Agent**     | Final gate before shipping. Reads the edited long-form and the repurposed assets together; flags missing sections, broken formatting, overclaiming, weak hooks, missing CTAs, terminology drift, completeness issues. Produces a 0–100 QA score and a `publishable` boolean. *(Optional stage.)* | `agent_publishing_qa` (Flash) |

#### Quality gates

Five gates run between stages. A gate failure marks the stage `needs_revision`, feeds the gate's failures back to the agent as additional context, and re-runs the agent up to `max_revisions` times (default 1). When the budget is exhausted, the pipeline fails for required stages or skips the stage for optional ones.

| Gate                | After stage        | Pass condition                                                                  |
| ------------------- | ------------------ | ------------------------------------------------------------------------------- |
| `intake_gate`       | `intake`           | Brief has audience, content_type, goals, topic                                  |
| `outline_gate`      | `outline`          | Title + hook present, ≥3 sections, at least one `explanation`/`deep_dive`       |
| `draft_gate`        | `draft`            | ≥300 words, no `TODO`/`TBD`/`[placeholder]` markers, ≥80% outline coverage      |
| `tech_review_gate`  | `technical_review` | No critical-severity issues unresolved                                          |
| `final_qa_gate`     | `publishing_qa`    | `publishable: true` and `qa_score >= 60`                                        |

#### State and persistence

Every transition writes `outputs/runs/<run_id>/run.json` atomically (tmp file + `os.replace`). Pipeline statuses: `queued`, `running`, `waiting_for_review`, `failed`, `completed`, `cancelled`. Stage statuses: `pending`, `running`, `succeeded`, `failed`, `skipped`, `needs_revision`. Resume reads back already-succeeded stages and replays only the rest.

See [`docs/content-pipeline-orchestration.md`](docs/content-pipeline-orchestration.md) for the full architecture, data contracts, and instructions for adding a new agent.

## Documentation

This repo has a full, evidence-grounded documentation system under [`docs/`](docs/). Start at the index: [`docs/00-overview/DOCUMENTATION_INDEX.md`](docs/00-overview/DOCUMENTATION_INDEX.md).

| Area | Start here |
| --- | --- |
| Fast orientation | [`docs/00-overview/PROJECT_SNAPSHOT.md`](docs/00-overview/PROJECT_SNAPSHOT.md) |
| Product & features | [`docs/01-product/`](docs/01-product/) — brief, feature inventory, current behavior, screens, flows |
| Architecture | [`docs/02-architecture/`](docs/02-architecture/) — architecture, system map, data model, API inventory, integrations |
| Implementation | [`docs/03-implementation/`](docs/03-implementation/) — codebase/route inventory, config/env, testing strategy |
| Quality & risk | [`docs/04-quality/`](docs/04-quality/) — known issues, technical debt, risk register, regression checklist, security |
| Planning | [`docs/05-planning/`](docs/05-planning/) — backlog, prioritized TODO, roadmap, next-agent tasks |
| History | [`docs/06-history/`](docs/06-history/) — decision log, changelog notes, audit log |
| AI agents | [`docs/07-ai-context/`](docs/07-ai-context/) — context-loading protocol, agent workflow, prompt inventory |

**Where to start:**
- **New contributor** → this README, then `docs/01-product/PRODUCT_BRIEF.md`.
- **AI agent** → `docs/07-ai-context/CONTEXT_LOADING_PROTOCOL.md` (load only the task-relevant bundle).
- **Picking up work** → `docs/05-planning/NEXT_AGENT_TASKS.md`.

## Project Structure

```
OptimizationAlgorithmPortfolio/
├── api/                                # Flask API blueprints
│   ├── app.py                          # App factory + static-site serving
│   ├── adapt_code.py
│   ├── compare.py
│   ├── math_tutor.py
│   └── study_plan.py
├── pipeline/                           # Content generation pipeline
│   ├── generate.py                     # Per-technique CLI orchestrator
│   ├── generator.py                    # Per-technique artifact engine
│   ├── llm_client.py                   # LLMProvider ABC, Gemini + Nano Banana providers, retry
│   ├── publish.py                      # Static HTML publisher
│   ├── schemas.py                      # JSON Schema definitions
│   ├── validator.py                    # Content validation rules
│   ├── recommender_api.py              # Recommender Flask app
│   ├── config.json                     # Topic, techniques, providers, artifact routing
│   ├── prompts/                        # Prompt templates ({{var}} substitution)
│   │   └── content_pipeline/           # Multi-agent prompt templates
│   ├── templates/                      # Jinja2 HTML templates
│   ├── agents/                         # 8 ContentAgent subclasses + base ABC + default registry
│   └── content_pipeline/               # Orchestrator, registry, gates, state, history
├── examples/
│   ├── run_content_pipeline.py         # Multi-agent pipeline CLI (incl. --dry-run)
│   └── sample_input.json
├── docs/                               # Documentation system (00-overview … 08-visuals)
│   ├── 00-overview/ … 08-visuals/      # See docs/00-overview/DOCUMENTATION_INDEX.md
│   └── content-pipeline-orchestration.md
├── tests/                              # 226 tests, all LLM calls mocked
├── content/                            # Tracked source data (references, rubrics)
├── generated/                          # Per-technique outputs (gitignored)
├── outputs/                            # Multi-agent pipeline runs (gitignored)
├── site/                               # Published HTML (gitignored)
├── requirements.txt
├── SETUP.md
└── CLAUDE.md
```

## Testing

```bash
# Full suite
python3.11 -m pytest tests/ -q

# Multi-agent pipeline tests only
python3.11 -m pytest tests/test_content_agents.py tests/test_quality_gates.py tests/test_content_pipeline.py -v

# Filter by name
python3.11 -m pytest tests/ -k "schema" -v
```

All tests use `unittest.mock` — no API keys or network calls are required. The 37 multi-agent tests cover happy path, hard failure, optional-stage skip, gate-driven revision, gate budget exhaustion, and resume-from-run-id.

## Cost Estimates

Full per-technique content refresh:

| Provider          | Artifacts                                                                  | Est. Cost |
| ----------------- | -------------------------------------------------------------------------- | --------- |
| Gemini 3.1 Flash  | Plans, overviews, math deep dives, implementations, infographic specs, summaries, knowledge graph, playground configs | ~$3–8     |
| Gemini 3.1 Pro    | Recommender, judge, math tutor, comparator, study plan, code adapter        | ~$0.50–2  |
| Nano Banana Pro   | Infographic + preview images                                                | ~$1–3     |
| **Total**         | **Full content refresh**                                                    | **~$4–13**|

Use `--skip-images` during development to reduce costs. The multi-agent pipeline costs roughly $0.50–2 per run depending on input length.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests to ensure nothing breaks (`python3 -m pytest tests/`)
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## License

This project is available under the MIT License. See [LICENSE](LICENSE) for details.
