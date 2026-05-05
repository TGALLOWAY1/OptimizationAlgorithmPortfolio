# Multi-Agent Content Pipeline

A staged orchestration layer that turns a raw input — an idea, transcript, outline, research note, or rough draft — into a polished long-form artifact plus channel-specific derivatives. It composes eight specialized agents with quality gates between them, persists every step to disk, and supports resuming an interrupted run.

This system is independent of `pipeline.generate`, which orchestrates per-technique artifact generation for the optimization-algorithm site. Both share the same LLM client, JSON Schema validation, prompt-template idioms, and provider-routing config.

## Pipeline shape

```
ContentPipelineInput
        │
        ▼
   ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
   │ intake  │───▶│research │───▶│ outline │───▶│  draft  │
   └────┬────┘    └─────────┘    └────┬────┘    └────┬────┘
   intake_gate                  outline_gate   draft_gate
        │                            │              │
        ▼                            ▼              ▼
   ┌─────────────────┐    ┌─────────┐    ┌─────────────┐    ┌──────────────┐
   │technical_review │───▶│ editor  │───▶│ repurposing │───▶│publishing_qa │
   └─────────────────┘    └─────────┘    └─────────────┘    └──────────────┘
   tech_review_gate                       (optional)         final_qa_gate
                                                              (optional)
```

## Agent responsibilities

| Stage              | Agent                         | Input                                  | Output (schema)         | Provider key            |
| ------------------ | ----------------------------- | -------------------------------------- | ----------------------- | ----------------------- |
| `intake`           | `IntakeAgent`                 | raw input + hints                      | `content_brief`         | `agent_intake`          |
| `research`         | `ResearchAgent`               | brief                                  | `research_notes`        | `agent_research`        |
| `outline`          | `OutlineAgent`                | brief + research                       | `content_outline`       | `agent_outline`         |
| `draft`            | `DraftingAgent`               | outline + brief + research             | `draft`                 | `agent_draft`           |
| `technical_review` | `TechnicalReviewerAgent`      | draft + brief + research               | `review_report`         | `agent_technical_review`|
| `editor`           | `EditorAgent`                 | draft + review + brief                 | `edited_draft`          | `agent_editor`          |
| `repurposing`      | `RepurposingAgent` (optional) | edited draft + outline + brief         | `repurposed_assets`     | `agent_repurposing`     |
| `publishing_qa`    | `PublishingQAAgent` (optional)| edited draft + repurposed + outline    | `publishing_qa`         | `agent_publishing_qa`   |

Provider mapping lives in `pipeline/config.json` under `artifact_provider_map`. Drafting and reviewing route to the Pro model; everything else uses Flash.

## Quality gates

| Gate                | After stage        | Pass condition                                                                  |
| ------------------- | ------------------ | ------------------------------------------------------------------------------- |
| `intake_gate`       | `intake`           | brief has audience, content_type, goals, topic                                  |
| `outline_gate`      | `outline`          | title + hook present, ≥3 sections, at least one `explanation`/`deep_dive`       |
| `draft_gate`        | `draft`            | ≥300 words, no `TODO`/`TBD`/`[placeholder]` markers, ≥80% outline coverage      |
| `tech_review_gate`  | `technical_review` | no critical-severity issues unresolved                                          |
| `final_qa_gate`     | `publishing_qa`    | `publishable: true` and `qa_score >= 60`                                        |

When a gate fails, the orchestrator marks the stage `needs_revision`, appends the gate's failures to `PipelineContext.gate_feedback`, and re-runs the same agent up to `max_revisions` times (default 1). When the budget is exhausted: required stages mark the pipeline `failed`; optional stages are recorded as `skipped`.

## Data contracts

Every JSON Schema for the contracts above is registered in `pipeline.schemas.SCHEMAS`:

- `content_brief`, `research_notes`, `content_outline`, `draft`, `review_report`, `edited_draft`, `repurposed_assets`, `publishing_qa`.

Payloads stay as plain dicts validated by `jsonschema` — the same convention as every other artifact in the repo. Orchestration internals (`StageRun`, `ContentPipelineRun`, `AgentResult`, `AgentMetadata`, `QualityGateResult`, `PipelineContext`) are `@dataclass` types in `pipeline/content_pipeline/state.py` and `pipeline/agents/base.py`.

## Pipeline & stage statuses

`PipelineStatus`: `queued`, `running`, `waiting_for_review`, `failed`, `completed`, `cancelled`.
`StageStatus`: `pending`, `running`, `succeeded`, `failed`, `skipped`, `needs_revision`.

The `cancelled` status is reserved for a future external-cancellation mechanism; `ContentPipeline.cancel()` raises `NotImplementedError`. The `waiting_for_review` status is set when `auto_approve=False` and the technical reviewer flags `requires_human: true` — the run pauses and can be resumed later.

## Failure handling and resume

Every stage transition writes `outputs/runs/<run_id>/run.json` atomically (tmp file + `os.replace`). On a partial failure or interruption you can resume:

```bash
python examples/run_content_pipeline.py --resume <run_id>
```

The orchestrator scans the loaded run for stages already marked `succeeded` with their JSON output present on disk and skips them, replaying only the remaining stages.

## How to run the example

```bash
# Smoke test with stub agents (no API key required)
python examples/run_content_pipeline.py --dry-run --input examples/sample_input.json

# Real run (needs GEMINI_API_KEY; ~$0.50–2 in tokens)
python examples/run_content_pipeline.py --input examples/sample_input.json
```

A successful run writes the following under `outputs/runs/<run_id>/`:

```
run.json
intake.json
research.json
outline.json
draft.json          draft.md
technical_review.json
editor.json         edited-draft.md
repurposing.json    linkedin-post.md
                    x-thread.md
                    youtube-description.md
                    short-form-script.md
                    newsletter-blurb.md
                    readme-excerpt.md
publishing_qa.json
```

## How to add a new agent

1. **Schema.** Add a new JSON Schema in `pipeline/schemas.py` and register it in `SCHEMAS`.
2. **Prompt.** Add `pipeline/prompts/content_pipeline/<your_agent>.md` with `{{var}}` placeholders.
3. **Provider routing.** Add a key under `artifact_provider_map` in `pipeline/config.json`.
4. **Agent class.** Create `pipeline/agents/<your_agent>.py` subclassing `ContentAgent`. Declare `STAGE_ID`, `ARTIFACT_TYPE`, `SCHEMA_KEY`, `PROMPT_FILE`. Implement `run(stage_input, context)` — typically pull required context from `context.previous_outputs`, render the prompt, call `self._call_llm`, and return `AgentResult`.
5. **Quality gate (optional).** Add a `QualityGate` subclass in `pipeline/content_pipeline/quality_gates.py`.
6. **Register.** Add a `StageDefinition` to the list returned by `build_default_registry()` in `pipeline/agents/__init__.py`.
7. **Tests.** Per-agent unit tests in `tests/test_content_agents.py` (mock `pipeline.agents.base.get_provider` + `pipeline.agents.base.generate_with_retry`); gate tests in `tests/test_quality_gates.py`.

## How to run the tests

```bash
# Multi-agent pipeline tests only
python -m pytest tests/test_content_agents.py tests/test_quality_gates.py tests/test_content_pipeline.py -v

# Full suite
python -m pytest tests/ -q
```

All 37 multi-agent tests use `unittest.mock` — no API keys are needed.

## Future extensions

- **Live web research.** The `ResearchAgent` currently marks every claim `needs_verification: true` because the pipeline has no browse tool. The existing `LLMProvider.generate_with_tools` capability in `pipeline/llm_client.py` is the natural extension point.
- **Cancellation.** `ContentPipeline.cancel()` is reserved for an external signal (e.g., a future API endpoint).
- **Human-in-the-loop.** `auto_approve=False` already pauses the run after `technical_review` if the reviewer flags `requires_human`. A small Flask blueprint can expose an approval endpoint.
- **Streaming progress.** The repo already has SSE precedents (`api/math_tutor.py` stream endpoint). The pipeline is currently synchronous; per-stage events could be streamed to a UI without changing agent contracts.
