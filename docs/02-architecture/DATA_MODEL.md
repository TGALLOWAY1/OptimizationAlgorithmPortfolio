# Data Model

> There is no database. "Entities" are JSON artifacts validated against JSON Schemas in `pipeline/schemas.py` (the `SCHEMAS` dict, `:584-601`). 16 schemas in two families.
> Last updated: 2026-05-28. Field-level evidence cited as file:line.

## Schema registry

`SCHEMAS` is a module-level dict mapping artifact-type key → schema (`schemas.py:584-601`). Lookups: `schema_validate.py:24` (`.get`), `generator.py` (direct subscript), `agents/base.py:13,87` (`SCHEMAS[self.SCHEMA_KEY]`), `retry_loop.py:42`. All 16 schemas set `additionalProperties: False`. Gemini strips `additionalProperties` before sending (`llm_client.py:50-64`), so that constraint is enforced only by the post-generation `jsonschema.validate`.

## Family 1 — per-technique artifacts (single-shot pipeline)

### plan
- **Purpose:** Per-technique generation contract; upstream of every other artifact. `schemas.py:3-38`.
- **Key fields (all required):** `technique_name`, `slug`, `aliases[]`, `problem_type`, `notation_conventions[]`, `assumptions[]`, `target_audience`, `artifacts_required[]`.
- **Produced by:** `generate_plan()` / `planner_prompt.md` / `gemini_flash`.
- **Consumed by:** every other generator + `technique.html`.
- **Validated by:** schema only (no `validator.py` rule).
- **Open questions:** `artifacts_required` is free text, never cross-checked against `config.json artifact_types`.

### overview
- **Purpose:** Long-form prose overview. `schemas.py:40-81`.
- **Key fields:** `technique_slug`, `artifact_type` (const), `title`, `summary`, `markdown` (minLength **800 chars**), `use_cases[]`, `strengths[]`, `limitations[]`, `comparisons[]`.
- **Validated by:** schema + `validate_overview` (requires **800 words**, no leading heading, on-topic) — note the chars-vs-words mismatch; the word rule is non-blocking at generation.

### math_deep_dive
- **Purpose:** Equation-focused deep dive. `schemas.py:83-127`.
- **Key fields:** `markdown` (≥800 chars), `key_equations[]` (each: `equation`, `label`, `step_by_step_derivation[]` minItems 2), `worked_examples[]`, `common_confusions[]`.
- **Validated by:** schema + `validate_math_deep_dive` (≥800 words; must contain `$` or `\(`).

### implementation
- **Purpose:** Implementation guide. `schemas.py:129-177`.
- **Key fields:** `markdown` (≥800 chars), `python_examples[]`, `libraries[]`, `runtime_dependencies[]` (items minLength 1, **no minItems** → empty list passes), `pseudo_code`, `code_variations[]` (**exactly 3**: `framework`, `label`, `code`).
- **Validated by:** schema + `validate_implementation` (≥800 words, pseudocode keyword, Python present, deps are bare import names). Code is executed during `--evaluate` (`code_runner`).

### infographic_spec
- **Purpose:** Design spec for image generation. `schemas.py:179-216`.
- **Key fields:** `title`, `panels[]` (**untyped objects** — shape unconstrained), `visual_metaphors[]`, `color_palette`, `layout`, `typography`, `key_equations[]`.
- **Open questions:** image generator assumes `panels[].title`/`content` but schema doesn't enforce them → schema-valid spec can render empty panels.

### homepage_summary
- **Purpose:** 3-5 bullet card. `schemas.py:218-230`. Field: `bullets[]` (minItems 3 / maxItems 5). Schema-only validation.

### knowledge_graph
- **Purpose:** Cross-technique graph. `schemas.py:232-276`.
- **Key fields:** `nodes[]` (`slug`, `label`, `category` enum=`selection-policy`/`simulation-enhancement`/`parallelization`/`meta-optimization`, `summary`), `edges[]` (`source`, `target`, `relationship`, `strength` 0-1).
- **Open questions:** edge endpoints not checked against node slugs (no referential integrity). Category enum is MCTS-specific. **Templates' legend uses a different (optimization) taxonomy** → mismatch.

### playground_config
- **Purpose:** Interactive playground config. `schemas.py:278-315`.
- **Key fields:** `parameters[]` (`name`,`label`,`min`,`max`,`default`,`step`), `objective_function` enum=`game_tree`/`random_tree`/`adversarial_tree`/`blokus_position`, `visualization_type` enum=`tree_expansion`/`visit_heatmap`/`convergence_curve`/`win_rate_over_time`.
- **Open questions:** no `min≤default≤max` or `step>0` constraint. **Template JS expects optimization objective functions/visualizations** → playground Broken for MCTS.

## Family 2 — multi-agent content-pipeline artifacts

Each is produced by one agent (`SCHEMA_KEY`) and consumed by downstream agents/gates.

| Schema | Produced by (agent / ARTIFACT_TYPE) | Key required fields | Gate |
|---|---|---|---|
| `content_brief` (`:317-361`) | IntakeAgent / agent_intake | `topic`, `audience`, `content_type` (enum), `technical_depth` (enum), `goals[]`, `requested_artifacts[]`, `raw_input_summary` | IntakeGate |
| `research_notes` (`:364-400`) | ResearchAgent / agent_research | `notes[]` (`claim`,`supporting_points[]`,`needs_verification`), `assumptions[]`, `open_questions[]` | none |
| `content_outline` (`:403-449`) | OutlineAgent / agent_outline | `title`, `hook`, `sections[]` (minItems 3; `heading`,`purpose`,`key_points[]`,`section_type` enum), `estimated_word_count`, `target_format` | OutlineGate |
| `draft` (`:452-465`) | DraftingAgent / agent_draft | `markdown` (≥200), `word_count`, `sections_covered[]` | DraftGate |
| `review_report` (`:468-494`) | TechnicalReviewerAgent / agent_technical_review | `issues[]` (`severity` enum, `location`, `description`), `blocking_issues_count`, `overall_assessment`, `requires_human?` | TechnicalReviewGate |
| `edited_draft` (`:497-513`) | EditorAgent / agent_editor | `markdown`, `word_count`, `changes_made[]`, `resolved_issues[]` | none |
| `repurposed_assets` (`:516-539`) | RepurposingAgent / agent_repurposing | `linkedin_post`, `x_thread[]` (minItems 2), `youtube_description`, `short_form_script`, `newsletter_blurb`, `readme_excerpt` | none (optional stage) |
| `publishing_qa` (`:542-581`) | PublishingQAAgent / agent_publishing_qa | `findings[]` (`category` enum, `severity` enum, `description`), `qa_score` (0-100), `publishable`, `blocking_issues[]` | FinalQAGate |

### Two-namespace caveat
Agents declare `ARTIFACT_TYPE` (the `config.json` provider-routing key, e.g. `agent_intake`) separately from `SCHEMA_KEY` (the `SCHEMAS` key, e.g. `content_brief`) — `agents/base.py:58-62`. This is the most error-prone area for newcomers; per-technique artifacts use a single name for both.

## Non-schema artifacts

- **Images** (`infographic.png`, `preview.png`): no schema — validated by file existence + ≥10 KB size (`validator.py:199-209`). Provider keys `infographic_image`/`preview_image` exist in config but not in `SCHEMAS`.
- **Provider-only keys** (`recommender`, `math_tutor`, `compare`, `study_plan`, `adapt_code`, `judge`): exist only in `artifact_provider_map` for routing; no artifact schema. (The recommender, study-plan, etc. do use *inline* schemas defined in their own modules — e.g. `recommender_api.py:24-46`.)

## Validation pipeline (summary)

- **Generation-time (A):** `generate_with_retry` runs `jsonschema.validate` with ≤3 retries (`llm_client.py:289-317`); then `validate_artifact` content rules — **logged, non-blocking** (`generator.py:298-307`).
- **Evaluation-time (B):** `retry_loop` runs schema-first then LLM judge, revising up to 3× (`retry_loop.py:48-169`).
- **Gates (C, content-pipeline only):** behavioral checks after each schema-valid stage; `IntakeGate`/`OutlineGate`/`DraftGate`/`TechnicalReviewGate`/`FinalQAGate` (`quality_gates.py:71-225`); research + editor stages ungated.

## On-disk layout

See `docs/03-implementation/CONFIG_AND_ENVIRONMENT.md` and `docs/02-architecture/STATE_MANAGEMENT.md` for the directory/file map and the `manifest.json` idempotency record.
