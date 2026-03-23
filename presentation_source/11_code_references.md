# Code References

## Pipeline Orchestration

| Concept | File(s) | Key Functions/Classes | Why It Matters |
|---------|---------|----------------------|----------------|
| Pipeline entry point | `pipeline/generate.py` | `main()` | Top-level orchestrator; CLI argument parsing, technique iteration, stage sequencing |
| Evaluation trigger | `pipeline/generate.py` | `_run_evaluation()` | Connects generation pipeline to evaluation pipeline |
| Stats tracking | `pipeline/generate.py` | `_record_status()` | Tracks generated/skipped/failed counts per run |
| Clean mode | `pipeline/generate.py` | `_clean_technique_outputs()` | Removes existing artifacts for fresh regeneration |

## Artifact Generation

| Concept | File(s) | Key Functions/Classes | Why It Matters |
|---------|---------|----------------------|----------------|
| Plan generation | `pipeline/generator.py` | `generate_plan()` | Foundation artifact; all other artifacts depend on it |
| Artifact generation | `pipeline/generator.py` | `generate_artifact()` | Core generation function for overview, math, implementation, infographic_spec |
| Homepage summary | `pipeline/generator.py` | `generate_homepage_summary()` | Artifact chaining example (requires overview) |
| Infographic image | `pipeline/generator.py` | `generate_infographic_image()` | Cross-artifact dependency (requires infographic_spec) |
| Preview thumbnail | `pipeline/generator.py` | `generate_preview_image()` | Branded image generation |
| Slug conversion | `pipeline/generator.py` | `slugify()` | Converts technique names to filesystem-safe identifiers |
| Generation result | `pipeline/generator.py` | `GenerationResult` (dataclass) | Frozen dataclass tracking payload, status, path, input_hash |
| Input hashing | `pipeline/generator.py` | `_compute_input_hash()` | SHA-256 idempotency check — compares prompt+schema+config+upstream |
| Prompt-to-file mapping | `pipeline/generator.py` | `PROMPT_MAP` (dict) | Maps artifact types to prompt template filenames |

## LLM Provider System

| Concept | File(s) | Key Functions/Classes | Why It Matters |
|---------|---------|----------------------|----------------|
| Provider abstraction | `pipeline/llm_client.py` | `LLMProvider` (ABC) | Abstract base class enabling provider extensibility |
| OpenAI provider | `pipeline/llm_client.py` | `OpenAIProvider` | GPT-4o with `response_format="json_object"` |
| Gemini provider | `pipeline/llm_client.py` | `GeminiProvider` | Gemini 3.1 Pro with `response_mime_type='application/json'` |
| Image provider | `pipeline/llm_client.py` | `NanoBananaProvider` | Gemini 3.1 Flash for image generation (separate interface) |
| Provider factory | `pipeline/llm_client.py` | `get_provider()` | Config-driven provider selection with caching |
| Retry with backoff | `pipeline/llm_client.py` | `generate_with_retry()` | Exponential backoff (2s, 4s, 8s) with schema validation |
| Image retry | `pipeline/llm_client.py` | `generate_image_with_retry()` | Same retry pattern for image generation |
| Config loading | `pipeline/llm_client.py` | `load_config()` | Loads `config.json` from pipeline directory |
| Gemini schema adapter | `pipeline/llm_client.py` | `_schema_for_gemini()` | Removes `additionalProperties` (unsupported by Gemini API) |
| Provider cache | `pipeline/llm_client.py` | `_providers` (module-level dict) | Singleton pool prevents redundant provider instantiation |

## Schema Validation

| Concept | File(s) | Key Functions/Classes | Why It Matters |
|---------|---------|----------------------|----------------|
| Schema definitions | `pipeline/schemas.py` | `PLAN_SCHEMA`, `OVERVIEW_SCHEMA`, `MATH_DEEP_DIVE_SCHEMA`, `IMPLEMENTATION_SCHEMA`, `INFOGRAPHIC_SPEC_SCHEMA`, `HOMEPAGE_SUMMARY_SCHEMA` | All schemas use `additionalProperties: false` for strict validation |
| Schema lookup | `pipeline/schemas.py` | `SCHEMAS` (dict) | Maps artifact_type strings to schema objects |
| Schema validation function | `pipeline/schema_validate.py` | `validate_schema()` | Wraps `jsonschema.validate()` with error collection |

## Content Validation

| Concept | File(s) | Key Functions/Classes | Why It Matters |
|---------|---------|----------------------|----------------|
| Validation dispatcher | `pipeline/validator.py` | `validate_artifact()` | Routes to type-specific validator + common checks |
| Overview validation | `pipeline/validator.py` | `validate_overview()` | Summary non-empty, markdown ≥800 words |
| Math validation | `pipeline/validator.py` | `validate_math_deep_dive()` | Markdown ≥800 words, LaTeX delimiters present |
| Implementation validation | `pipeline/validator.py` | `validate_implementation()` | Pseudocode keywords, Python examples, dependency format |
| Infographic validation | `pipeline/validator.py` | `validate_infographic_spec()` | Panels exist, layout non-empty |
| Image validation | `pipeline/validator.py` | `validate_infographic_image()` | File exists, ≥10KB |
| Off-topic detection | `pipeline/validator.py` | `OFF_TOPIC_HINTS` (set) | Detects startup/VC/business terms in algorithm content |
| Technique-specific terms | `pipeline/validator.py` | `TECHNIQUE_HINTS` (dict) | Ensures correct algorithm terms appear in content |
| Disallowed terms | `pipeline/validator.py` | `IMPLEMENTATION_DISALLOWED_TERMS` (dict) | Prevents wrong algorithm terms (e.g., BFGS in gradient descent) |
| String field traversal | `pipeline/validator.py` | `iter_string_fields()` | Recursively yields all strings from nested structures |

## Evaluation Pipeline

| Concept | File(s) | Key Functions/Classes | Why It Matters |
|---------|---------|----------------------|----------------|
| Evaluation orchestrator | `pipeline/evaluate.py` | `evaluate_single_artifact()` | 4-stage pipeline: schema → static → code → judge |
| Deterministic checks | `pipeline/evaluate.py` | `run_deterministic_checks()` | Placeholder detection, LaTeX balance, duplicate paragraphs |
| Technique evaluation | `pipeline/evaluate.py` | `evaluate_technique()` | Evaluates all artifacts for one technique, promotes passing ones |
| Artifact promotion | `pipeline/evaluate.py` | `promote_artifact()` | Writes validated artifact to content directory |
| Metrics saving | `pipeline/evaluate.py` | `save_metrics()` | Saves run-scoped + latest metrics JSON |
| Evaluation logging | `pipeline/evaluate.py` | `save_evaluation_log()` | Per-artifact evaluation trace |
| Placeholder patterns | `pipeline/evaluate.py` | `PLACEHOLDER_PATTERNS` (list) | Regex patterns: TODO, TBD, FIXME, XXX, [INSERT, PLACEHOLDER |

## LLM Judge

| Concept | File(s) | Key Functions/Classes | Why It Matters |
|---------|---------|----------------------|----------------|
| Rubric loading | `pipeline/judge.py` | `load_rubrics()` | Loads `content/rubrics.json` with fallback to defaults |
| Default rubrics | `pipeline/judge.py` | `_default_rubrics()` | 4 criteria with weights: accuracy 0.3, math 0.3, clarity 0.25, code 0.15 |
| Reference loading | `pipeline/judge.py` | `load_reference()` | Loads `content/reference/<slug>.json` with key_facts and forbidden_claims |
| Judge prompt builder | `pipeline/judge.py` | `_build_judge_prompt()` | Dynamic prompt assembly — criteria + reference + artifact content |
| Judge execution | `pipeline/judge.py` | `evaluate_artifact()` | Calls GPT-4o via `generate_with_retry()` with JUDGE_OUTPUT_SCHEMA |
| Revision prompt builder | `pipeline/judge.py` | `build_revision_prompt()` | Assembles score + critiques + instructions into revision prompt |
| Judge output schema | `pipeline/judge.py` | `JUDGE_OUTPUT_SCHEMA` (dict) | Defines expected judge response structure |
| Pass threshold | `pipeline/judge.py` | `DEFAULT_PASS_THRESHOLD = 7` | Minimum overall_score for passing |

## Retry Loop

| Concept | File(s) | Key Functions/Classes | Why It Matters |
|---------|---------|----------------------|----------------|
| Retry orchestrator | `pipeline/retry_loop.py` | `retry_loop()` | Up to 3 attempts: schema → judge → revise → repeat |
| Artifact revision | `pipeline/retry_loop.py` | `revise_artifact()` | Calls LLM with revision prompt, validates against schema |
| Max attempts | `pipeline/retry_loop.py` | `MAX_ATTEMPTS = 3` | Configurable retry limit |

## Code Execution

| Concept | File(s) | Key Functions/Classes | Why It Matters |
|---------|---------|----------------------|----------------|
| Code validation | `pipeline/code_runner.py` | `validate_code_artifact()` | Full validation: deps → imports → execution |
| Dependency check | `pipeline/code_runner.py` | `check_dependencies()` | Checks against ALLOWED_LIBRARIES allowlist |
| Import extraction | `pipeline/code_runner.py` | `extract_imports()` | AST-based import parsing |
| Code execution | `pipeline/code_runner.py` | `run_code()` | Subprocess execution with 30s timeout |
| Allowed libraries | `pipeline/code_runner.py` | `ALLOWED_LIBRARIES` (set) | 22 approved packages |

## Publishing

| Concept | File(s) | Key Functions/Classes | Why It Matters |
|---------|---------|----------------------|----------------|
| Site publisher | `pipeline/publish.py` | `publish()` | Renders all artifacts as static HTML site |
| Quality report | `pipeline/publish.py` | `_publish_quality_report()` | Renders evaluation metrics as HTML report |
| Markdown rendering | `pipeline/publish.py` | `_render_markdown()` | LaTeX-preserving markdown → HTML conversion |
| LaTeX protection | `pipeline/publish.py` | `_extract_math_segments()`, `_restore_placeholders()` | Protects $...$ and $$...$$ from markdown parser |
| List formatting | `pipeline/publish.py` | `_ensure_numbered_lists()`, `_ensure_bullet_lists()` | Fixes markdown list spacing |
| Provenance builder | `pipeline/publish.py` | `_build_provenance()` | Extracts model/timestamp/version from manifest |

## API Endpoints

| Concept | File(s) | Key Functions/Classes | Why It Matters |
|---------|---------|----------------------|----------------|
| App factory | `api/app.py` | `create_app()` | Blueprint registration, CORS, static serving |
| Algorithm recommender | `pipeline/recommender_api.py` | `get_recommendations()`, `recommend()` | Uses use-case matrix as context for recommendations |
| Algorithm comparison | `api/compare.py` | `compare()`, `_load_technique_artifacts()` | Loads artifacts, truncates to 4000 chars, calls LLM |
| Math tutor | `api/math_tutor.py` | `math_tutor()` | Bounded explanation from selected text + context |
| Study plan | `api/study_plan.py` | `study_plan()`, `_get_available_techniques()` | Personalized roadmap from available technique summaries |
| Code adapter | `api/adapt_code.py` | `adapt_code()` | Framework conversion with source code max 10000 chars |

## Configuration

| Concept | File(s) | Key Functions/Classes | Why It Matters |
|---------|---------|----------------------|----------------|
| Pipeline config | `pipeline/config.json` | — | Techniques, providers, artifact-to-provider mapping |
| Scoring rubrics | `content/rubrics.json` | — | Criteria weights, pass threshold, per-artifact criteria map |
| Reference facts | `content/reference/*.json` | — | 8 files with key_facts and forbidden_claims per technique |

## Tests

| Concept | File(s) | Tests | Why It Matters |
|---------|---------|-------|----------------|
| Schema tests | `tests/test_schemas.py`, `tests/test_new_schemas.py`, `tests/test_schema_validate.py` | 20 | Schema correctness and boundary enforcement |
| Validator tests | `tests/test_validator.py` | 16 | Content quality rules |
| API endpoint tests | `tests/test_api_endpoints.py` | 18 | All 400/404/500 error paths + success paths |
| Generator tests | `tests/test_generator.py` | 3 | Slugify + idempotency |
| LLM client tests | `tests/test_llm_client.py` | 6 | Provider routing + retry logic |
| Recommender tests | `tests/test_recommender_api.py` | 11 | Recommendation endpoint |
| Evaluation tests | `tests/test_evaluate.py` | 14 | Deterministic checks, LaTeX balance, artifact promotion |
| Judge tests | `tests/test_judge.py` | 6 | Rubric loading, reference loading, artifact evaluation |
| Retry tests | `tests/test_retry_loop.py` | 6 | Retry loop behavior |
| Code runner tests | `tests/test_code_runner.py` | 12 | Dependency checks, import extraction, code execution |
| Publishing tests | `tests/test_publish_rendering.py` | 4 | Quality report rendering, publish lifecycle |
| Runtime tests | `tests/test_runtime.py` | 2 | Python version guard |
