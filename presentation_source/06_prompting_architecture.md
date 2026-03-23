# Prompting Architecture

## Prompt Inventory

| # | Prompt File | Category | Provider | Output |
|---|-------------|----------|----------|--------|
| 1 | `planner_prompt.md` | Planning | Gemini | `plan.json` |
| 2 | `overview_prompt.md` | Content | Gemini | `overview.json` |
| 3 | `math_prompt.md` | Content | Gemini | `math_deep_dive.json` |
| 4 | `implementation_prompt.md` | Content | Gemini | `implementation.json` |
| 5 | `infographic_prompt.md` | Content | Gemini | `infographic_spec.json` |
| 6 | `homepage_summary_prompt.md` | Content | Gemini | `homepage_summary.json` |
| 7 | `infographic_image_prompt.md` | Image | Nano Banana | `infographic.png` |
| 8 | `preview_image_prompt.md` | Image | Nano Banana | `preview.png` |
| 9 | `recommender_prompt.md` | API | OpenAI | Recommendation response |
| 10 | `use_case_matrix_prompt.md` | Content | Gemini | `use_case_matrix.json` |

**Plus 4 inline prompts** in API endpoints (`api/math_tutor.py`, `api/compare.py`, `api/study_plan.py`, `api/adapt_code.py`) — system prompts defined as string constants within the endpoint code.

**Plus 1 judge prompt** constructed dynamically in `pipeline/judge.py` → `_build_judge_prompt()`.

**Total: 15 distinct prompting contexts.**

---

## Prompt Storage

All template prompts live in: `pipeline/prompts/*.md`

The prompt-to-artifact mapping is defined in `pipeline/generator.py`:
```python
PROMPT_MAP = {
    "plan": "planner_prompt.md",
    "overview": "overview_prompt.md",
    "math_deep_dive": "math_prompt.md",
    "implementation": "implementation_prompt.md",
    "infographic_spec": "infographic_prompt.md",
    "homepage_summary": "homepage_summary_prompt.md",
    "infographic_image": "infographic_image_prompt.md",
    "preview_image": "preview_image_prompt.md",
}
```

**Confirmed from code:** Prompts are loaded from disk at generation time, not cached. This means prompt changes take effect on the next generation run without code changes.

---

## Prompt Categories by Function

### Category 1: Planning Prompts
**Purpose:** Establish the "contract" for a technique — terminology, notation, audience, scope.

- `planner_prompt.md` — Generates `plan.json`
- One prompt per technique; output consumed by all downstream prompts

### Category 2: Content Generation Prompts
**Purpose:** Generate the actual educational content artifacts.

- `overview_prompt.md` — Comprehensive algorithm overview
- `math_prompt.md` — Mathematical deep dive with LaTeX
- `implementation_prompt.md` — Coding guide with 3 framework variations
- `infographic_prompt.md` — Visual spec for infographic design
- `homepage_summary_prompt.md` — Scannable bullet points
- `use_case_matrix_prompt.md` — Cross-algorithm comparison matrix

### Category 3: Image Generation Prompts
**Purpose:** Generate visual artifacts from structured specifications.

- `infographic_image_prompt.md` — Full infographic image from spec
- `preview_image_prompt.md` — Branded thumbnail preview

### Category 4: API/Runtime Prompts
**Purpose:** Power interactive features with structured responses.

- `recommender_prompt.md` — Algorithm recommendation
- Inline prompts in `api/math_tutor.py`, `api/compare.py`, `api/study_plan.py`, `api/adapt_code.py`

### Category 5: Evaluation Prompts
**Purpose:** Judge artifact quality and drive revision.

- Dynamic judge prompt in `pipeline/judge.py` → `_build_judge_prompt()`
- Dynamic revision prompt in `pipeline/judge.py` → `build_revision_prompt()`

---

## Variable Injection Pattern

All prompts use `{{variable_name}}` placeholder syntax. Variables are replaced via Python string `.replace()` in `pipeline/generator.py`.

**Confirmed from code:** This is simple string replacement, not a full Jinja2 template engine. The `{{...}}` syntax is a convention, not a framework feature for prompts (Jinja2 is used only for HTML templates).

### Variable Catalog

| Variable | Used In | Source |
|----------|---------|--------|
| `{{technique_name}}` | planner, preview_image, infographic_image | CLI arg / config |
| `{{plan_json}}` | overview, math, implementation, infographic, homepage_summary | `json.dumps(plan, indent=2)` |
| `{{technique_slug}}` | overview, math, implementation, infographic | `slugify(technique_name)` |
| `{{overview_summary}}` | homepage_summary | `overview["summary"]` |
| `{{title}}` | infographic_image | `infographic_spec["title"]` |
| `{{layout}}` | infographic_image | `infographic_spec["layout"]` |
| `{{color_palette}}` | infographic_image | `infographic_spec["color_palette"]` |
| `{{typography}}` | infographic_image | `infographic_spec["typography"]` |
| `{{formatted_panels}}` | infographic_image | Formatted from `infographic_spec["panels"]` |
| `{{formatted_equations}}` | infographic_image | Formatted from `infographic_spec["key_equations"]` |
| `{{formatted_metaphors}}` | infographic_image | Formatted from `infographic_spec["visual_metaphors"]` |
| `{{use_case_matrix}}` | recommender | `json.dumps(use_case_matrix)` |

---

## Prompt Chaining / Sequencing

The prompts form a **dependency chain**, not a flat set:

```
planner_prompt.md
  │
  ├─► plan.json ──► overview_prompt.md ──► overview.json
  │                                         │
  │                                         └─► homepage_summary_prompt.md
  │
  ├─► plan.json ──► math_prompt.md ──► math_deep_dive.json
  │
  ├─► plan.json ──► implementation_prompt.md ──► implementation.json
  │
  └─► plan.json ──► infographic_prompt.md ──► infographic_spec.json
                                                │
                                                └─► infographic_image_prompt.md ──► infographic.png
```

**Key insight:** The plan JSON is injected verbatim into every downstream prompt. This means the plan's terminology, notation, and scope propagate to all artifacts, ensuring consistency without manual coordination.

**Secondary chain:** The overview summary feeds into the homepage summary prompt, and the infographic spec feeds into the image generation prompt. These are **data-dependent** chains where one artifact's output becomes another's input.

---

## Prompt Design Patterns

### Pattern 1: JSON-Only Response Constraint
Every content prompt ends with a strict instruction:
> "Respond with ONLY the JSON object, no additional text."

This ensures LLM output can be parsed directly as JSON without extraction.

### Pattern 2: Schema Inline Specification
Content prompts describe the expected JSON structure inline in the prompt text, then schema validation catches deviations. The prompt describes *what* the fields should contain; the schema enforces *structure*.

### Pattern 3: Plan Injection as Context
All content prompts receive the full plan as `{{plan_json}}`, giving the LLM consistent context about:
- What the algorithm is called and its aliases
- What notation to use
- What assumptions to make
- Who the target audience is
- What artifacts are expected

### Pattern 4: Formatting Guidance
Prompts include detailed formatting rules:
- LaTeX: `$...$` for inline, `$$...$$` for display
- Headers: `##` for sections, `###` for subsections
- Lists: blank line before numbered/bullet lists
- Bold: `**Term**: description` pattern

This ensures generated markdown renders correctly in the publishing pipeline.

### Pattern 5: Negative Constraints
Several prompts include explicit prohibitions:
- "No metadata, design specs, or behind-the-scenes information should appear in the final image" (infographic_image)
- Disallowed algorithm terms (implementation — e.g., no "BFGS" in gradient descent)
- "Explanation must be strictly bounded by context — no new concepts introduced" (math_tutor)

### Pattern 6: Structured Formatting for Images
The infographic image prompt formats spec data into human-readable lists:
```
Panels:
1. [Title]: [Content] (visual_type)
2. ...

Key Equations:
- equation_1
- equation_2
```

This transforms JSON into a more natural prompt format for the image model.

---

## Prompt Reusability

**High reusability:**
- All content prompts share the same injection pattern (`{{plan_json}}`, `{{technique_slug}}`)
- Adding a new technique requires zero prompt changes — the plan drives customization

**Low reusability (by design):**
- Each prompt is specialized for one artifact type
- Image prompts are fundamentally different from text prompts
- API prompts are tailored to their specific interaction pattern

**Likely inferred from code structure:** The prompt templates could theoretically be used with different LLM providers by changing the `artifact_provider_map` in config. The prompts themselves are provider-agnostic.

---

## Risks and Strengths of the Prompt Design

### Strengths
1. **Plan-as-contract** — Single source of truth for terminology and scope
2. **Template-based** — Prompts are editable files, not hardcoded strings (for pipeline prompts)
3. **Schema-backed** — Every prompt has a corresponding schema, so structural issues are caught automatically
4. **Formatting guidance** — Reduces markdown rendering issues by specifying expected format
5. **Negative constraints** — Explicitly lists what to avoid, reducing off-topic generation

### Risks
1. **No prompt versioning** — Prompts are files on disk; no history of prompt changes unless tracked by git
2. **Simple string replacement** — `{{variable}}` replacement can't handle conditional logic or loops
3. **Long context injection** — `{{plan_json}}` dumps the entire plan into every prompt; plan growth increases token cost
4. **Truncation in judge** — Artifacts are truncated to 8000 chars for judging, which may miss issues in longer content
5. **API prompts are inline** — The 4 API endpoint prompts live as string constants in Python code, not in the `prompts/` directory, making them harder to find and edit
6. **No prompt testing** — Prompts are tested indirectly through mocked LLM calls, not through prompt-specific quality checks

---

## Prompts Worth Showing in a Presentation

### 1. The Planner Prompt (Conceptual Keystone)
**Why:** It's the foundation of the entire pipeline. Show how a single technique name becomes a structured plan that drives all downstream generation. This illustrates the "plan as contract" pattern.

### 2. The Implementation Prompt (Most Complex)
**Why:** Requires exactly 3 framework variations (NumPy, PyTorch, SciPy), pseudocode, Python examples, and runtime dependencies. Show the constraint complexity and how the schema enforces it.

### 3. The Infographic Image Prompt (Cross-Artifact Dependency)
**Why:** Show how structured JSON spec data (panels, equations, metaphors) gets reformatted into a natural-language image generation prompt. It's a great example of artifact chaining.

### 4. The Judge Prompt (Quality Gate)
**Why:** Show how rubric criteria, reference facts, and forbidden claims are assembled into a scoring prompt. This explains the entire quality assurance mechanism in one prompt.

### 5. The Revision Prompt (Feedback Loop)
**Why:** Show how critiques and instructions from a failed judge evaluation become input for the next generation attempt. This is the "self-improving" aspect of the pipeline.
