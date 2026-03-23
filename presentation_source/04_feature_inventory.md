# Feature Inventory

## Content Generation Features

### 1. Config-Driven Technique Pipeline
- **What it does:** Generates complete educational content packages for each optimization algorithm listed in configuration
- **Why it exists:** Automates the creation of consistent, structured learning materials without manual authoring
- **Where it lives:** `pipeline/generate.py` (orchestrator), `pipeline/generator.py` (engine), `pipeline/config.json` (technique list)
- **Inputs:** Technique names from config, prompt templates, JSON schemas
- **Outputs:** 6-8 JSON/PNG artifacts per technique in `content/<slug>/`
- **Status:** Core
- **Caveats:** Full pipeline run costs $4-10 in API credits

### 2. Plan-First Generation Strategy
- **What it does:** Generates a structured plan (terminology, notation, audience, scope) before any content artifacts
- **Why it exists:** Ensures consistency across all artifacts for a technique — same notation, same assumptions, same audience level
- **Where it lives:** `pipeline/generator.py` → `generate_plan()`, `pipeline/prompts/planner_prompt.md`
- **Inputs:** Technique name
- **Outputs:** `plan.json` with slug, aliases, problem_type, notation_conventions, assumptions, target_audience
- **Status:** Core — all other artifacts depend on the plan
- **Caveats:** Plan quality directly impacts all downstream artifact quality

### 3. Multi-Provider LLM Routing
- **What it does:** Routes different artifact types to different LLM providers based on configuration
- **Why it exists:** Different tasks benefit from different models (text vs. images, cost vs. quality)
- **Where it lives:** `pipeline/llm_client.py` → `get_provider()`, `pipeline/config.json` → `artifact_provider_map`
- **Inputs:** Artifact type string
- **Outputs:** Configured LLM provider instance
- **Status:** Core
- **Caveats:** Provider cache is module-level global; providers are instantiated once per type

### 4. Idempotent Generation with Manifest Tracking
- **What it does:** Computes SHA-256 hash of all inputs (prompt, schema, config, upstream artifacts); skips generation if hash matches stored manifest
- **Why it exists:** Prevents redundant API calls, enables safe partial reruns, supports incremental updates
- **Where it lives:** `pipeline/generator.py` → `_compute_input_hash()`, `manifest.json` per technique
- **Inputs:** Prompt text, schema, config slice, upstream artifact data
- **Outputs:** Hash comparison result; skip or generate decision
- **Status:** Core
- **Caveats:** `--force` flag overrides idempotency; hash changes if any input changes (including config)

### 5. Image Generation via Nano Banana Pro
- **What it does:** Generates infographic PNGs and preview thumbnails using Gemini 3.1 Flash image model
- **Why it exists:** Provides visual learning aids and homepage previews without manual design
- **Where it lives:** `pipeline/llm_client.py` → `NanoBananaProvider`, `pipeline/generator.py` → `generate_infographic_image()`, `generate_preview_image()`
- **Inputs:** Infographic spec JSON (for infographics), technique name (for previews)
- **Outputs:** `infographic.png`, `preview.png` in `content/<slug>/`
- **Status:** Core (skippable with `--skip-images`)
- **Caveats:** Images validated only by file size (≥10KB); no content quality check for images

### 6. Use-Case Matrix Generation
- **What it does:** Generates a cross-reference matrix rating each algorithm against problem space dimensions (search space type, objective characteristics, dimensionality, etc.)
- **Why it exists:** Helps users compare algorithms across structured criteria
- **Where it lives:** `pipeline/prompts/use_case_matrix_prompt.md`, published via `pipeline/publish.py`
- **Inputs:** None (prompt is self-contained with algorithm list)
- **Outputs:** `use_case_matrix.json` with ratings: "ideal", "suitable", "unsuitable"
- **Status:** Core (only on full 8-technique runs)
- **Caveats:** Matrix quality depends entirely on LLM knowledge; no reference-based validation

---

## Quality Assurance Features

### 7. JSON Schema Validation
- **What it does:** Validates every generated artifact against strict JSON Schemas with required fields, type constraints, array limits, and `additionalProperties: false`
- **Why it exists:** Catches structural issues before content is accepted
- **Where it lives:** `pipeline/schemas.py` (schema definitions), `pipeline/schema_validate.py` (validation function)
- **Inputs:** Artifact data, artifact type
- **Outputs:** `{passed: bool, errors: [str]}`
- **Status:** Core — integrated into generation retry loop and evaluation pipeline
- **Caveats:** Schema validation is necessary but not sufficient; content can be structurally valid but semantically wrong

### 8. Deterministic Static Checks
- **What it does:** Runs fast, deterministic quality checks: placeholder detection (TODO/TBD/FIXME), LaTeX balance, duplicated paragraphs, off-topic detection, technique-specific terms
- **Why it exists:** Catches common LLM failure modes without expensive API calls
- **Where it lives:** `pipeline/evaluate.py` → `run_deterministic_checks()`, `pipeline/validator.py`
- **Inputs:** Artifact type, artifact data
- **Outputs:** `{passed: bool, errors: [str]}`
- **Status:** Core — runs in evaluation pipeline
- **Caveats:** Heuristic-based; may produce false positives/negatives for edge cases

### 9. Code Execution Validation
- **What it does:** Extracts Python examples from implementation artifacts, checks dependencies against an allowlist, and runs code in sandboxed subprocess with 30-second timeout
- **Why it exists:** Verifies that generated code actually runs — not just syntactically valid but executable
- **Where it lives:** `pipeline/code_runner.py` → `validate_code_artifact()`
- **Inputs:** Implementation artifact with `python_examples[]` and `runtime_dependencies[]`
- **Outputs:** Per-example results with exit_code, stdout, stderr; undeclared/blocked import lists
- **Status:** Core — only for implementation artifacts
- **Caveats:** 22-library allowlist may be too restrictive for some algorithms; subprocess execution is local (no true sandboxing)

### 10. LLM Judge Evaluation
- **What it does:** Uses GPT-4o to score artifacts 1-10 on rubric criteria (factual_accuracy, math_correctness, clarity, code_quality), comparing against reference facts and forbidden claims
- **Why it exists:** Catches semantic and factual issues that deterministic checks cannot detect
- **Where it lives:** `pipeline/judge.py` → `evaluate_artifact()`, `content/rubrics.json`, `content/reference/*.json`
- **Inputs:** Artifact data, rubrics with criteria/weights, reference facts + forbidden claims
- **Outputs:** `{passed: bool, overall_score: int, criteria_scores: {}, critiques: [], revision_instructions: []}`
- **Status:** Core — controllable via `--skip-judge`
- **Caveats:** LLM judge is probabilistic; same artifact may receive different scores on different runs; judge truncates artifacts to 8000 chars

### 11. Retry Loop with Revision
- **What it does:** When judge fails an artifact, constructs a revision prompt with score, critiques, and instructions; re-generates and re-evaluates up to 3 total attempts
- **Why it exists:** Automates the "fix and resubmit" cycle that would otherwise be manual
- **Where it lives:** `pipeline/retry_loop.py` → `retry_loop()`, `revise_artifact()`
- **Inputs:** Failed artifact, judge result with critiques/instructions
- **Outputs:** Revised artifact or persistent_failure status with judge_history
- **Status:** Core
- **Caveats:** Max 3 attempts; persistent failures are logged but not resolved automatically

---

## Publishing Features

### 12. Static Site Publisher
- **What it does:** Renders all technique artifacts as a complete static HTML website using Jinja2 templates
- **Why it exists:** Makes generated content browsable without a running server
- **Where it lives:** `pipeline/publish.py` → `publish()`, `pipeline/templates/*.html`
- **Inputs:** JSON artifacts from `content/`, Jinja2 templates
- **Outputs:** `site/` directory with index, technique pages, comparison page, matrix page, quality report
- **Status:** Core
- **Caveats:** Requires content generation to have run first; deletes stale HTML for removed techniques

### 13. LaTeX-Preserving Markdown Rendering
- **What it does:** Converts markdown to HTML while protecting LaTeX math expressions from being mangled by the markdown parser
- **Why it exists:** Math content uses `$...$` and `$$...$$` which conflict with markdown syntax
- **Where it lives:** `pipeline/publish.py` → `_render_markdown()`, `_extract_math_segments()`, `_restore_placeholders()`
- **Inputs:** Markdown text with embedded LaTeX
- **Outputs:** HTML with intact LaTeX for KaTeX client-side rendering
- **Status:** Core
- **Caveats:** Regex-based extraction; edge cases with nested or malformed delimiters possible

### 14. Quality Report Publishing
- **What it does:** Renders evaluation metrics as an HTML quality report page with pass/fail badges, attempt counts, and methodology explanation
- **Why it exists:** Provides transparency about content quality and evaluation process
- **Where it lives:** `pipeline/publish.py` → `_publish_quality_report()`, `pipeline/templates/eval_report.html`
- **Inputs:** Evaluation metrics JSON from `content/evaluations/`
- **Outputs:** `site/quality-report.html`
- **Status:** Core (only if evaluation was run)
- **Caveats:** Report is informational; does not block publishing of failing artifacts

---

## Interactive API Features

### 15. Algorithm Recommender
- **What it does:** Accepts a natural-language problem description and returns 2-3 algorithm recommendations with confidence scores and justifications
- **Why it exists:** Helps users find the right algorithm for their problem without reading all 8 guides
- **Where it lives:** `pipeline/recommender_api.py` → `get_recommendations()`, `pipeline/prompts/recommender_prompt.md`
- **Inputs:** User query (max 2000 chars), use-case matrix as context
- **Outputs:** `[{algorithm, justification, confidence_score (1-100), url_slug}]`
- **Status:** Core
- **Caveats:** Uses OpenAI GPT-4o; quality depends on use-case matrix and LLM reasoning

### 16. Algorithm Comparison
- **What it does:** Generates a structured head-to-head comparison of two algorithms with pros, cons, best-for scenarios, and summary
- **Why it exists:** Helps users decide between two specific algorithms
- **Where it lives:** `api/compare.py`, `pipeline/templates/compare.html`
- **Inputs:** Two technique slugs; loads artifacts from `content/` (truncated to 4000 chars each)
- **Outputs:** `{algorithm_a/b, pros_a/b[], cons_a/b[], best_for_a/b, summary}`
- **Status:** Core
- **Caveats:** Requires generated content to exist for both algorithms

### 17. Math Tutor
- **What it does:** Explains a highlighted math equation in context, using LaTeX notation
- **Why it exists:** Enables interactive learning — users highlight confusing equations and get explanations
- **Where it lives:** `api/math_tutor.py`, triggered from `technique.html` template via text selection
- **Inputs:** `selected_text` (max 2000 chars), optional `context` (max 5000 chars)
- **Outputs:** `{explanation: "LaTeX-formatted markdown"}`
- **Status:** Core
- **Caveats:** Explanation must stay bounded by provided context (no new concepts introduced)

### 18. Study Plan Generator
- **What it does:** Creates a personalized learning roadmap ordering algorithms from foundational to advanced based on user background and goals
- **Why it exists:** Helps learners navigate the 8 algorithms in the most effective order
- **Where it lives:** `api/study_plan.py`
- **Inputs:** `background` + `goals` (max 2000 chars each); loads available technique summaries
- **Outputs:** `{roadmap: [{slug, title, reason, order}], rationale}`
- **Status:** Core
- **Caveats:** Only recommends algorithms that have generated content available

### 19. Code Adapter
- **What it does:** Converts optimization algorithm code between frameworks (NumPy, PyTorch, SciPy)
- **Why it exists:** Helps users adapt examples to their preferred framework
- **Where it lives:** `api/adapt_code.py`
- **Inputs:** `source_code` (max 10000 chars), `target_framework`, optional `instructions`
- **Outputs:** `{adapted_code, notes}`
- **Status:** Core
- **Caveats:** LLM-based conversion; no automated correctness verification of adapted code

---

## Infrastructure Features

### 20. Exponential Backoff Retry
- **What it does:** Retries API calls on failure with exponential backoff (2s, 4s, 8s), up to 3 attempts
- **Why it exists:** Handles transient API failures and rate limiting gracefully
- **Where it lives:** `pipeline/llm_client.py` → `generate_with_retry()`, `generate_image_with_retry()`
- **Inputs:** Provider, prompts, schema
- **Outputs:** Validated LLM response or raised RuntimeError
- **Status:** Core
- **Caveats:** Backoff is fixed exponential; no jitter

### 21. Provenance Tracking
- **What it does:** Records model name, timestamp, artifact version, and input hash for every generated artifact in `manifest.json`
- **Why it exists:** Enables reproducibility, debugging, and transparency about what generated what
- **Where it lives:** `pipeline/generator.py` → manifest update logic, `pipeline/publish.py` → `_build_provenance()`
- **Inputs:** Generation metadata
- **Outputs:** `manifest.json` per technique; provenance box on technique HTML pages
- **Status:** Core
- **Caveats:** Manifest is per-technique, not centralized

### 22. Python Version Guard
- **What it does:** Checks that runtime is Python 3.11+ at startup
- **Why it exists:** Uses features (typing, match statements) not available in older Python
- **Where it lives:** `api/app.py` → `ensure_supported_python()`
- **Inputs:** `sys.version_info`
- **Outputs:** SystemExit if < 3.11
- **Status:** Core
- **Caveats:** Only checked at API server startup, not during pipeline execution

### 23. Comprehensive Test Suite
- **What it does:** 70+ tests covering schemas, validation, API endpoints, generator logic, LLM client, evaluator, judge, code runner, retry loop, publishing
- **Why it exists:** Ensures pipeline correctness without requiring API keys or network access
- **Where it lives:** `tests/` directory (16 test files)
- **Inputs:** Mock data, MagicMock providers
- **Outputs:** pytest results
- **Status:** Core
- **Caveats:** All LLM calls are mocked; tests verify logic, not LLM output quality
