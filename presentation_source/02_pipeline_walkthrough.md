# Pipeline Walkthrough: Step-by-Step Execution

## Entry Point

The pipeline is invoked via CLI:
```bash
python -m pipeline.generate [--technique "Name"] [--force] [--provider openai] [--skip-images] [--evaluate] [--skip-judge] [--clean]
```

**File:** `pipeline/generate.py` → `main()`

---

## Stage 0: Configuration Loading

**What happens:**
1. Load `pipeline/config.json` — techniques list, provider configs, artifact-to-provider mapping
2. Parse CLI arguments (technique filter, force regeneration, provider override, flags)
3. Determine which techniques to process (all 8 or a filtered subset)
4. If `--clean`, delete existing outputs for target techniques before starting

**Output:** Technique list, provider configuration, runtime flags

**Key file:** `pipeline/config.json`

---

## Stage 1: Plan Generation (Per Technique)

**Input:** Technique name (e.g., "Bayesian Optimization")

**What happens:**
1. Load prompt template: `pipeline/prompts/planner_prompt.md`
2. Inject `{{technique_name}}` into the template
3. Compute input hash (SHA-256 of prompt + schema + config)
4. Check manifest — if hash matches and not `--force`, skip (return cached plan)
5. Call LLM provider (Gemini by default) via `generate_with_retry()`
6. Validate response against `PLAN_SCHEMA` (JSON Schema)
7. Run content validation via `validate_artifact()`
8. Save `plan.json` to `content/<slug>/`
9. Update `manifest.json` with hash, timestamp, provider metadata

**Output:** `plan.json` containing:
- `technique_name`, `slug`, `aliases`
- `problem_type`, `notation_conventions`, `assumptions`
- `target_audience`, `artifacts_required`

**Why it matters:** The plan is the **foundation artifact** — all subsequent artifacts depend on it for consistency in terminology, notation, and scope.

**Retry behavior:** Up to 3 attempts with exponential backoff (2s, 4s, 8s) on API failure or schema validation failure.

---

## Stage 2: Core Artifact Generation (Per Technique, Per Artifact Type)

For each of the 4 core artifact types: `overview`, `math_deep_dive`, `implementation`, `infographic_spec`

### 2a. Overview Generation

**Input:** `plan.json` (full plan as JSON)

**Prompt:** `pipeline/prompts/overview_prompt.md`
- Variables: `{{plan_json}}`, `{{technique_slug}}`
- Instructs LLM to write 800+ word overview with use cases, strengths, limitations, comparisons

**Output:** `overview.json` → `title`, `summary`, `markdown` (800+ words), `use_cases[]`, `strengths[]`, `limitations[]`, `comparisons[]`

**Validation:**
- Schema: `OVERVIEW_SCHEMA` (all fields required, markdown minLength 800)
- Content: summary non-empty, markdown word count ≥ 800

### 2b. Math Deep Dive Generation

**Input:** `plan.json`

**Prompt:** `pipeline/prompts/math_prompt.md`
- Variables: `{{plan_json}}`, `{{technique_slug}}`
- Instructs LLM to produce formal mathematical treatment with LaTeX

**Output:** `math_deep_dive.json` → `markdown` (800+ words), `key_equations[]` (each with `equation`, `label`, `step_by_step_derivation[]`), `worked_examples[]`, `common_confusions[]`

**Validation:**
- Schema: Nested equation objects with minItems constraints
- Content: LaTeX delimiter presence (`$` or `\(`), word count ≥ 800

### 2c. Implementation Guide Generation

**Input:** `plan.json`

**Prompt:** `pipeline/prompts/implementation_prompt.md`
- Variables: `{{plan_json}}`, `{{technique_slug}}`
- Requires exactly 3 `code_variations` (NumPy, PyTorch, SciPy/scikit-learn)

**Output:** `implementation.json` → `markdown` (800+ words), `python_examples[]`, `libraries[]`, `runtime_dependencies[]`, `pseudo_code`, `code_variations[3]`

**Validation:**
- Schema: Exactly 3 code variations, runtime_dependencies as string array
- Content: Pseudocode keywords (FUNCTION, FOR, WHILE, IF, RETURN), Python code presence, dependency format (raw import names, no descriptions)
- Technique-specific: No disallowed terms (e.g., no "BFGS" in gradient descent)

### 2d. Infographic Specification Generation

**Input:** `plan.json`

**Prompt:** `pipeline/prompts/infographic_prompt.md`
- Variables: `{{plan_json}}`, `{{technique_slug}}`

**Output:** `infographic_spec.json` → `title`, `panels[]` (4+ with visual_type), `visual_metaphors[]`, `color_palette`, `layout`, `typography`, `key_equations[]`

**Validation:**
- Schema: panels and key_equations as arrays with minItems
- Content: panels exist, layout non-empty

**Dependencies between artifacts:** Plan must exist before any core artifact. Artifacts are otherwise independent of each other.

---

## Stage 3: Homepage Summary Generation (Per Technique)

**Input:** `plan.json` + `overview.json` (specifically `overview.summary`)

**Prompt:** `pipeline/prompts/homepage_summary_prompt.md`
- Variables: `{{plan_json}}`, `{{overview_summary}}`

**Output:** `homepage_summary.json` → `bullets[]` (3-5 items, each <15 words)

**Why it matters:** These bullets appear on the homepage grid cards — they must be scannable and concise.

**Dependency:** Requires overview to exist first (uses `overview.summary` as input).

---

## Stage 4: Image Generation (Per Technique)

### 4a. Infographic Image

**Input:** `infographic_spec.json` fields (title, layout, color_palette, typography, panels, equations, metaphors)

**Prompt:** `pipeline/prompts/infographic_image_prompt.md`
- Multiple variables injected from the spec
- Formatted as structured lists (panels as numbered items, equations as bullet points)

**Provider:** Nano Banana Pro (Gemini 3.1 Flash image model)

**Output:** `infographic.png` in `content/<slug>/`

**Validation:** File must exist and be ≥ 10KB (rejects blank/corrupt images)

**Flag:** Skipped with `--skip-images`

### 4b. Preview Thumbnail

**Input:** Technique name only

**Prompt:** `pipeline/prompts/preview_image_prompt.md`
- Strict branding: deep indigo background (#1A237E), coral accent (#FF7043), white text
- 16:9 aspect ratio, 280×160px crop-safe

**Provider:** Nano Banana Pro

**Output:** `preview.png` in `content/<slug>/`

**Flag:** Skipped with `--skip-images`

---

## Stage 5: Use-Case Matrix Generation (Full Run Only)

**Trigger:** Only when processing ALL 8 techniques (not single-technique runs)

**Prompt:** `pipeline/prompts/use_case_matrix_prompt.md`

**Output:** `use_case_matrix.json` → `title`, `description`, `problem_spaces[]` (search space type, objective characteristics, evaluation cost, dimensionality, constraints, problem structure), `matrix` (algorithm × problem_space → "ideal"/"suitable"/"unsuitable")

**Why it matters:** Provides a structured comparison framework rendered as a color-coded HTML table.

---

## Stage 6: Evaluation Pipeline (Optional, `--evaluate` flag)

**File:** `pipeline/evaluate.py` → `_run_evaluation()`

This is a **multi-stage quality assurance pipeline** that runs after generation.

### 6a. Schema Validation
- Validates each artifact against its JSON Schema
- **Controlling:** Blocks further evaluation on failure

### 6b. Deterministic Static Checks
- Placeholder detection (TODO, TBD, FIXME, XXX, [INSERT, PLACEHOLDER)
- LaTeX delimiter balance ($...$ pairs, $$...$$ pairs, \(...\) pairs)
- Duplicated paragraph detection (>50 char paragraphs appearing twice)
- Content validation rules (word count, pseudocode keywords, LaTeX presence)
- **Controlling:** Blocks further evaluation on failure

### 6c. Code Execution (Implementation artifacts only)
- Dependency allowlist check (22 approved libraries)
- Import extraction via AST parsing
- Undeclared import detection
- Blocked import detection
- Sandboxed subprocess execution with 30s timeout
- **Controlling:** Blocks further evaluation on failure

### 6d. LLM Judge + Retry Loop
- Load rubrics (`content/rubrics.json`) with 4 criteria and weights
- Load reference facts (`content/reference/<slug>.json`) with key_facts and forbidden_claims
- Score artifact 1-10 on: factual_accuracy (30%), math_correctness (30%), clarity (25%), code_quality (15%)
- **Pass threshold:** overall_score ≥ 7
- On failure: extract critiques and revision_instructions → construct revision prompt → re-generate → re-evaluate
- **Max attempts:** 3
- **Advisory/Controlling:** Controls retry loop; persistent failure is logged but doesn't crash pipeline

### 6e. Artifact Promotion
- Passing artifacts are written to `content/<slug>/<artifact_type>.json`
- Evaluation metrics saved to `content/evaluations/` (run-scoped + latest alias)
- Per-artifact evaluation logs saved to `content/logs/evaluation/<slug>/`

---

## Stage 7: Static Site Publishing

**Entry point:** `python -m pipeline.publish` → `pipeline/publish.py` → `publish()`

**What happens:**
1. Scan `content/` directory for technique folders with JSON artifacts
2. For each technique:
   - Load all JSON artifacts (plan, overview, math_deep_dive, implementation, infographic_spec, homepage_summary)
   - Load manifest for provenance metadata (model, timestamp, version)
   - Render `technique.html` template with Jinja2 filters
3. Render `index.html` with homepage grid (technique cards with previews and bullets)
4. Render `compare.html` (algorithm comparison page)
5. If `use_case_matrix.json` exists: render `use_case_matrix.html`
6. If evaluation metrics exist: render `quality-report.html`
7. Copy images from `content/<slug>/` to `site/images/<slug>/`

**Markdown rendering pipeline:**
1. Extract LaTeX math spans → replace with `@@MATH_N@@` placeholders
2. Fix list formatting (ensure blank lines before numbered/bullet lists)
3. Render markdown to HTML
4. Restore LaTeX placeholders
5. Apply header downgrading where needed (# → ##, ## → ###)

**Output:** Complete static website in `site/` directory

---

## Stage 8: Flask API Server (Runtime)

**Entry point:** `python api/app.py` → `create_app()`

Serves the static site AND provides 5 live LLM-powered endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/recommend` | POST | Algorithm recommendation from problem description |
| `/api/compare` | POST | Head-to-head algorithm comparison |
| `/api/math_tutor` | POST | Equation explanation from highlighted text |
| `/api/study_plan` | POST | Personalized learning roadmap |
| `/api/adapt_code` | POST | Code framework conversion |

All endpoints use OpenAI GPT-4o, accept JSON POST, return structured JSON with schema validation.

---

## Pipeline Dependency Graph

```
config.json
    │
    ▼
Plan Generation ──────────────────────┐
    │                                 │
    ├──► Overview ────► Homepage      │
    │                   Summary       │
    ├──► Math Deep Dive               │
    │                                 │
    ├──► Implementation               │
    │                                 │
    ├──► Infographic Spec ──► Infographic Image
    │                                 │
    │                    Preview Image│
    │                                 │
    ▼                                 ▼
Evaluation Pipeline           Use-Case Matrix
    │                         (full runs only)
    ▼
Static Site Publishing
    │
    ▼
Flask API Server (runtime)
```

---

## Failure Modes and Recovery

| Failure | Handling | Recovery |
|---------|----------|----------|
| API call fails | Exponential backoff retry (2s, 4s, 8s), 3 attempts | Automatic |
| Schema validation fails | Retry with fresh LLM call | Automatic |
| Content validation warns | Logged as warning, generation proceeds | Manual review |
| Judge scores < 7 | Revision prompt constructed, artifact re-generated | Automatic (up to 3 attempts) |
| Image too small (<10KB) | Retry with fresh image call | Automatic |
| Single technique fails | Exception caught, pipeline continues to next technique | Partial output |
| Code execution fails | Logged, flagged in evaluation | Manual fix or re-generate |
| Code execution timeout | 30s subprocess timeout | Automatic failure |
