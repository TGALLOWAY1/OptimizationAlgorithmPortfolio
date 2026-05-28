# Prompt Inventory

> Every prompt template and where it's used. Substitution is `{{var}}` text replacement.
> Root prompts load via `generator.py:_load_prompt` (`PROMPT_MAP`, `:31-42`). Agent prompts load via `content_pipeline/prompts.py:render_prompt` (`:24-41`), which also blanks any unfilled `{{...}}`.
> Last updated: 2026-05-28.

## Single-shot pipeline prompts (`pipeline/prompts/`)

| Prompt file | Used by | Variables | Output / schema |
|---|---|---|---|
| `planner_prompt.md` | `generate_plan` (gemini_flash) | `technique_name`, `domain` | `plan.json` / `PLAN_SCHEMA` |
| `overview_prompt.md` | `generate_artifact` (gemini_flash); reused by `generate_use_case_matrix` | `plan_json`, `technique_slug`, `domain` | `overview.json` / `OVERVIEW_SCHEMA` |
| `math_prompt.md` | `generate_artifact` (gemini_flash) | `plan_json`, `technique_slug`, `domain` | `math_deep_dive.json` |
| `implementation_prompt.md` | `generate_artifact` (gemini_flash) | `domain`, `plan_json`, `technique_slug` | `implementation.json` |
| `infographic_prompt.md` | `generate_artifact` (gemini_flash) | `plan_json`, `technique_slug` | `infographic_spec.json` |
| `homepage_summary_prompt.md` | `generate_homepage_summary` (gemini_flash) | `plan_json`, `overview_summary`, `domain` | `homepage_summary.json` |
| `infographic_image_prompt.md` | `generate_infographic_image` (nano_banana) | `technique_name`, `title`, `layout`, `formatted_panels`, `formatted_equations`, `formatted_metaphors`, `color_palette`, `typography` | `infographic.png` (no schema) |
| `preview_image_prompt.md` | `generate_preview_image` (nano_banana) | `technique_name` | `preview.png` (no schema) |
| `knowledge_graph_prompt.md` | `generate_knowledge_graph` (gemini_flash) | `all_plans_json`, `domain` | `knowledge_graph.json` |
| `playground_config_prompt.md` | `generate_playground_config` (gemini_flash) | `plan_json`, `technique_name`, `domain` | `playground_config.json` |
| `recommender_prompt.md` | `recommender_api.get_recommendations` (gemini); used as **system** prompt | `use_case_matrix` | inline `RECOMMENDATION_SCHEMA` |
| `use_case_matrix_prompt.md` | `generate_use_case_matrix` | `topic_name`, `domain`, `technique_list` | `use_case_matrix.json` (inline schema) |

## Multi-agent pipeline prompts (`pipeline/prompts/content_pipeline/`)

| Prompt file | Agent (provider) | Variables | Output schema |
|---|---|---|---|
| `intake.md` | IntakeAgent (gemini_flash) | `raw_input`, `audience_hint`, `content_type_hint`, `gate_feedback` | `content_brief` |
| `research.md` | ResearchAgent (gemini_flash) | `brief_json`, `gate_feedback` | `research_notes` |
| `outline.md` | OutlineAgent (gemini_flash) | `brief_json`, `research_json`, `gate_feedback` | `content_outline` |
| `draft.md` | DraftingAgent (gemini) | `brief_json`, `outline_json`, `research_json`, `gate_feedback` | `draft` |
| `technical_review.md` | TechnicalReviewerAgent (gemini) | `draft_markdown`, `brief_json`, `research_json` | `review_report` |
| `editor.md` | EditorAgent (gemini) | `draft_markdown`, `review_json`, `brief_json` | `edited_draft` |
| `repurposing.md` | RepurposingAgent (gemini_flash) | `edited_markdown`, `brief_json`, `outline_json` | `repurposed_assets` |
| `publishing_qa.md` | PublishingQAAgent (gemini_flash) | `edited_markdown`, `repurposed_json`, `brief_json`, `outline_json` | `publishing_qa` |

## Inline (code-built) prompts — not `.md` files
- **Judge:** `judge.py:_build_judge_prompt` (`:95-138`), `_build_tool_using_judge_prompt` (`:141-189`), `build_revision_prompt` (`:321-357`). ⚠️ `build_revision_prompt` hardcodes "expert in optimization algorithms" (stale — KNOWN_ISSUES #11).
- **API endpoints:** `compare`, `math_tutor`, `study_plan`, `adapt_code` build prompts inline in Python (no `.md`). Math-tutor/study-plan prompt logic is duplicated between stream/non-stream handlers and has drifted (TECHNICAL_DEBT #2).

## Notes
- No `quiz.md` exists despite `CLAUDE.md` listing a quiz artifact (Designed only).
- The non-tool Gemini path concatenates system+user into one `contents` string — there is **no system/user trust boundary** there (prompt-injection relevance, RISK_REGISTER R5).
