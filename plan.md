# Implementation Plan: Optimization Technique Content Generation Pipeline (V1)

## Overview

Build an automated content generation pipeline that produces 32 structured educational artifacts (8 techniques × 4 artifacts each) using **both OpenAI and Gemini 3.1 Pro** APIs, validates them against schemas, generates infographic images via **Nano Banana Pro** (Google's Gemini 3 image model), and publishes everything as static web pages.

---

## Step 1: Project Scaffolding & Configuration

**Files to create:**
- `pipeline/config.json` — technique list, artifact types, and LLM provider settings
- `pipeline/generate.py` — main entry point (empty scaffold)
- `requirements.txt` — dependencies (openai, google-genai, jsonschema, jinja2, markdown, Pillow)
- `.gitignore` — ignore `.env`, `__pycache__`, `site/`, etc.

**Details:**
- `config.json` contains the 8 techniques, 4 artifact type names, and a `providers` block:
  ```json
  {
    "providers": {
      "openai": {
        "model": "gpt-4o",
        "api_key_env": "OPENAI_API_KEY"
      },
      "gemini": {
        "model": "gemini-3.1-pro-preview",
        "api_key_env": "GEMINI_API_KEY"
      },
      "nano_banana": {
        "model": "nano-banana-pro",
        "api_key_env": "GEMINI_API_KEY"
      }
    },
    "artifact_provider_map": {
      "plan": "gemini",
      "overview": "openai",
      "math_deep_dive": "openai",
      "implementation": "gemini",
      "infographic_spec": "gemini",
      "infographic_image": "nano_banana"
    }
  }
  ```
- Provider mapping is configurable — any artifact can be routed to either LLM
- Create empty `content/techniques/` directory structure (one subfolder per technique slug)
- Create empty `pipeline/prompts/` directory

---

## Step 2: Define JSON Schemas for Validation

**File to create:**
- `pipeline/schemas.py` — Python module exporting JSON Schema dicts for each artifact type

**Schemas needed (5 total for text artifacts):**
1. `plan` — technique_name, slug, aliases, problem_type, notation_conventions, assumptions, target_audience, artifacts_required
2. `overview` — technique_slug, artifact_type, title, summary, markdown, use_cases, strengths, limitations, comparisons
3. `math_deep_dive` — technique_slug, artifact_type, markdown, key_equations, worked_examples, common_confusions
4. `implementation` — technique_slug, artifact_type, markdown, python_examples, libraries, pseudo_code
5. `infographic_spec` — technique_slug, artifact_type, title, panels, visual_metaphors, color_palette, layout, typography, key_equations

All fields required. Arrays must have `minItems: 1` where content is expected. `markdown` fields get `minLength` constraints matching PRD word-count requirements.

---

## Step 3: Write Prompt Templates

**Files to create:**
- `pipeline/prompts/planner_prompt.md`
- `pipeline/prompts/overview_prompt.md`
- `pipeline/prompts/math_prompt.md`
- `pipeline/prompts/implementation_prompt.md`
- `pipeline/prompts/infographic_prompt.md`
- `pipeline/prompts/infographic_image_prompt.md` — Nano Banana Pro image generation prompt

**Details:**
- Each prompt instructs the LLM to return valid JSON matching the corresponding schema
- The planner prompt takes a technique name as input
- Artifact prompts take `plan.json` content + technique name as context
- Prompts specify expected length, required sections, notation rules, and output format constraints
- Math prompt emphasizes LaTeX formatting and symbol-before-use rule
- Implementation prompt emphasizes pseudocode + Python code requirements
- The infographic image prompt is purpose-built for Nano Banana Pro (see Step 8)

---

## Step 4: Build the LLM Client Module

**File to create:**
- `pipeline/llm_client.py`

**Architecture — Multi-Provider Client:**

The client implements a unified interface with two provider backends:

### 4a. Provider Interface

```python
class LLMProvider(ABC):
    def generate(self, system_prompt: str, user_prompt: str, schema: dict) -> dict: ...

class OpenAIProvider(LLMProvider): ...
class GeminiProvider(LLMProvider): ...
```

### 4b. OpenAI Provider
- Uses the `openai` Python SDK (Responses API)
- Sends request with `response_format={"type": "json_object"}`
- Parses JSON response and validates against schema using `jsonschema`
- Read API key from `OPENAI_API_KEY` environment variable

### 4c. Gemini 3.1 Pro Provider
- Uses the `google-genai` Python SDK
- Sends request with `response_mime_type="application/json"` and `response_json_schema` set to the artifact's JSON schema
- Gemini 3.1 Pro natively enforces schema adherence via structured output mode
- Read API key from `GEMINI_API_KEY` environment variable
- Model ID: `gemini-3.1-pro-preview`

### 4d. Provider Router
- `get_provider(artifact_type: str) -> LLMProvider` reads `artifact_provider_map` from `config.json` and returns the correct provider
- Can be overridden at the CLI level with `--provider openai|gemini`

### 4e. Shared Reliability Logic
- On API failure: retry up to 3 times with exponential backoff (2s, 4s, 8s)
- On schema validation failure: retry generation (up to 3 attempts)
- Raises after all retries exhausted

---

## Step 5: Build the Artifact Generation Engine

**File to create:**
- `pipeline/generator.py`

**Functions:**
- `generate_plan(technique_name: str) -> dict` — calls LLM (via provider router) with planner prompt, saves `plan.json`
- `generate_artifact(technique_slug: str, artifact_type: str, plan: dict) -> dict` — loads artifact-specific prompt, injects plan context, calls LLM via the correct provider, saves artifact JSON
- `slugify(name: str) -> str` — converts technique name to filesystem slug

**Idempotency logic:**
- Before generating, check if the target JSON file already exists
- Skip generation if file exists (unless `--force` flag is set)
- Log skip/generate decisions

---

## Step 6: Build Validation Module

**File to create:**
- `pipeline/validator.py`

**Validation rules (beyond schema validation):**
- **Overview**: `summary` is non-empty; `markdown` word count > 800
- **Math Deep Dive**: `markdown` contains LaTeX delimiters (`$` or `\(`); symbols defined before use (best-effort check)
- **Implementation**: `markdown` or `pseudo_code` contains pseudocode keywords; `python_examples` is non-empty or `markdown` contains Python code blocks
- **Infographic Spec**: `panels` array is non-empty; `layout` is non-empty
- **Infographic Image**: file exists and is a valid PNG; file size > 10KB (not a blank/error image)

Returns list of validation errors per artifact. Generation retries on validation failure.

---

## Step 7: Build the Main Pipeline Orchestrator

**File to update:**
- `pipeline/generate.py`

**CLI interface (using `argparse`):**
```
python pipeline/generate.py                                          # generate all
python pipeline/generate.py --technique "Bayesian Optimization"      # single technique
python pipeline/generate.py --force                                  # regenerate existing
python pipeline/generate.py --provider openai                        # force a specific provider
python pipeline/generate.py --skip-images                            # skip Nano Banana image gen
```

**Execution flow:**
```
1. Load config.json
2. For each technique:
   a. generate_plan() → save content/techniques/{slug}/plan.json
   b. For each artifact type:
      i.   generate_artifact() → get JSON (routed to correct provider)
      ii.  validate() → check content rules
      iii. save → content/techniques/{slug}/{artifact_type}.json
   c. generate_infographic_image() → call Nano Banana Pro (Step 8)
      i.   validate image output
      ii.  save → content/techniques/{slug}/infographic.png
3. Print summary (generated / skipped / failed counts per provider)
```

**Logging:**
- Use Python `logging` module
- Log: generation start, success, failure, retry attempts, skip (already exists)
- Log which provider was used for each artifact

---

## Step 8: Nano Banana Pro — Infographic Image Generation

**Files involved:**
- `pipeline/llm_client.py` — add `NanoBananaProvider` class
- `pipeline/prompts/infographic_image_prompt.md` — image generation prompt template
- `pipeline/generator.py` — add `generate_infographic_image()` function

### 8a. Overview

Nano Banana Pro is Google's Gemini 3 Pro Image model, accessed via the same Gemini API (`google-genai` SDK). It generates high-quality infographic images with accurate text rendering, making it ideal for producing visual summaries of each optimization technique.

### 8b. NanoBananaProvider Implementation

```python
class NanoBananaProvider:
    """Generates infographic images via Nano Banana Pro (Gemini 3 Image)."""

    def generate_image(self, prompt: str, output_path: str) -> str:
        """
        Calls the Gemini API with model='nano-banana-pro'.
        Returns the path to the saved PNG file.
        """
```

- Uses the `google-genai` SDK with `model="nano-banana-pro"`
- Calls `client.models.generate_content()` with the image generation prompt
- Extracts the image bytes from the response (`response.candidates[0].content.parts[0].inline_data`)
- Saves as PNG to `content/techniques/{slug}/infographic.png`
- Same retry logic as text providers (3 attempts, exponential backoff)

### 8c. Image Prompt Construction

The infographic image prompt is built dynamically from the `infographic_spec.json` artifact:

```
prompt = f"""
Create a professional educational infographic about {technique_name}.

Title: {spec['title']}

Layout: {spec['layout']}
Color Palette: {spec['color_palette']}
Typography: {spec['typography']}

Panels:
{formatted_panels}

Key Equations (render as LaTeX in the image):
{formatted_equations}

Visual Metaphors:
{formatted_metaphors}

Style requirements:
- Clean, modern design suitable for technical education
- All text must be legible and correctly rendered
- Use the specified color palette consistently
- Equations should be rendered clearly with proper mathematical notation
- Each panel should be visually distinct but cohesive
- Resolution: high quality, suitable for web and print
"""
```

### 8d. Nano Banana Pro Features to Leverage

- **Text rendering** — NB Pro is best-in-class at rendering legible text in images, critical for equation-heavy infographics
- **Thinking mode** — Enable for complex multi-panel layouts so the model reasons through composition before generating
- **High resolution** — Request high-res output for print-quality infographics
- **Search grounding** (optional) — Can be enabled to pull real-time data for accuracy verification

### 8e. Output

Each technique gets one infographic image:
```
content/techniques/{slug}/infographic.png
```

The publishing engine (Step 9) embeds this image on the technique page.

---

## Step 9: Build the Publishing Engine

**Files to create:**
- `pipeline/publish.py` — reads artifact JSON + infographic images, renders HTML pages
- `pipeline/templates/technique.html` — Jinja2 template for technique pages
- `pipeline/templates/index.html` — Jinja2 template for index page

**Details:**
- Read all artifact JSON from `content/techniques/{slug}/`
- Convert `markdown` fields to HTML using the `markdown` library (with LaTeX pass-through)
- Embed `infographic.png` on each technique page via `<img>` tag
- Render per-technique pages with sections: Overview, Mathematics, Implementation, Infographic
- Render index page listing all techniques with thumbnail infographics
- Copy infographic PNGs to `site/images/{slug}/`
- Output to `site/` directory as static HTML files
- CLI: `python pipeline/publish.py`

---

## Step 10: Add Tests

**Files to create:**
- `tests/test_schemas.py` — validate that sample data passes/fails schema checks correctly
- `tests/test_validator.py` — test content validation rules
- `tests/test_generator.py` — test slugify, idempotency skip logic (mock LLM calls)
- `tests/test_llm_client.py` — test provider routing, retry logic (mock both APIs)

**Details:**
- Use `pytest`
- Mock both OpenAI and Gemini API calls — no real API calls in tests
- Test that invalid JSON is rejected by schemas
- Test that validation rules catch missing content
- Test provider routing logic (correct provider selected per artifact type)
- Test that `--provider` CLI override works

---

## Execution Order Summary

| Step | Deliverable | Dependencies |
|------|------------|--------------|
| 1 | Scaffolding & config | None |
| 2 | JSON schemas | None |
| 3 | Prompt templates | Step 2 (schema awareness) |
| 4 | LLM client (OpenAI + Gemini + NB Pro) | Step 2 |
| 5 | Generator | Steps 2, 3, 4 |
| 6 | Validator | Step 2 |
| 7 | Pipeline orchestrator | Steps 4, 5, 6 |
| 8 | Nano Banana Pro image generation | Steps 4, 5 |
| 9 | Publishing engine | Step 1 (directory structure) |
| 10 | Tests | Steps 2, 4, 5, 6 |

---

## Key Design Decisions

1. **Dual LLM providers (OpenAI + Gemini 3.1 Pro)** — configurable per-artifact routing allows using the best model for each task, and provides fallback flexibility
2. **Gemini structured output via `response_json_schema`** — Gemini 3.1 Pro natively enforces JSON schema adherence, complementing OpenAI's `response_format=json_object`
3. **Nano Banana Pro for infographic images** — Google's Gemini 3 image model provides best-in-class text rendering in generated images, critical for equation-heavy educational infographics
4. **Infographic spec → image pipeline** — the `infographic_spec.json` artifact drives the Nano Banana Pro prompt, ensuring visual output is grounded in structured content
5. **`jsonschema` for validation** — standard, well-tested library for JSON Schema validation
6. **File-existence check for idempotency** — simple, reliable; no database needed
7. **Jinja2 for templating** — lightweight, standard for static site generation
8. **No async in V1** — synchronous loop is simpler and meets PRD requirements; async is listed as future enhancement
9. **Prompts as markdown files** — easy to iterate on without code changes
10. **Separate validator module** — keeps content-quality rules decoupled from schema validation
