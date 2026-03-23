# Prompts: Verbatim and Reconstructed Examples

All prompts below are taken **verbatim from the codebase** unless explicitly marked as **[RECONSTRUCTED]**. Prompts live in `pipeline/prompts/*.md`. The judge and revision prompts are constructed dynamically in `pipeline/judge.py`.

---

## 1. Planner Prompt (Verbatim)

**File:** `pipeline/prompts/planner_prompt.md`
**Stage:** Plan Generation (Stage 1)
**Variables injected:** `{{technique_name}}`
**Expected output:** `plan.json`
**Why it matters:** This is the foundation prompt — its output (the plan) is injected into every downstream content prompt. Quality here cascades.

```markdown
You are an expert in optimization algorithms and mathematical techniques. Your task is to create a structured plan for generating educational content about the optimization technique: **{{technique_name}}**.

Return a JSON object with the following fields:

- **technique_name** (string): The full name of the technique.
- **slug** (string): A URL-safe lowercase slug (e.g., "bayesian-optimization").
- **aliases** (array of strings): Alternative names or abbreviations for this technique.
- **problem_type** (string): The class of problems this technique addresses (e.g., "black-box optimization", "continuous optimization").
- **notation_conventions** (array of strings): Mathematical notation conventions to use consistently across all artifacts (e.g., "f(x) for objective function", "x* for optimal solution").
- **assumptions** (array of strings): Key assumptions or prerequisites for applying this technique.
- **target_audience** (string): The intended audience level (e.g., "graduate students in CS/ML with calculus and probability background").
- **artifacts_required** (array of strings): List of artifact types to generate: ["overview", "math_deep_dive", "implementation", "infographic_spec"].

Respond with ONLY the JSON object, no additional text.
```

---

## 2. Overview Prompt (Verbatim)

**File:** `pipeline/prompts/overview_prompt.md`
**Stage:** Content Generation (Stage 2)
**Variables injected:** `{{plan_json}}`, `{{technique_slug}}`
**Expected output:** `overview.json` (title, summary, 800+ word markdown, use_cases, strengths, limitations, comparisons)
**Why it matters:** Demonstrates how the plan is injected as JSON context, and how formatting guidance ensures correct markdown rendering.

```markdown
You are an expert technical writer specializing in optimization algorithms. Create a comprehensive overview of the optimization technique described in the plan below.

## Plan Context
\```json
{{plan_json}}
\```

## Requirements

Return a JSON object with these fields:

- **technique_slug** (string): "{{technique_slug}}"
- **artifact_type** (string): "overview"
- **title** (string): A descriptive title for this overview article.
- **summary** (string): A 2-3 sentence executive summary of the technique.
- **markdown** (string): A comprehensive markdown article (minimum 800 words) covering:
  - Use LaTeX for all math: inline with `$...$` (e.g. `$D_t$`, `$f(x)$`, `$GP(m(x), k(x, x'))$`), display with `$$...$$`.
  - Use proper markdown: `##` for section headers, `###` for subsections. Numbered lists need a blank line before the first item; each item on its own line.
  - Bold key terms in definition-style lists: `- **Term**: description` or `1. **Term**: description`.
  - What the technique is and its historical context
  - How it works at a high level (intuition before formalism)
  - When to use it vs. alternatives
  - Key parameters and their effects
  - Practical considerations and tips
- **use_cases** (array of strings): At least 3 real-world applications.
- **strengths** (array of strings): At least 3 advantages of this technique.
- **limitations** (array of strings): At least 3 limitations or drawbacks.
- **comparisons** (array of strings): At least 2 comparisons with related techniques.

Use the notation conventions from the plan. Write for the target audience specified in the plan.

Respond with ONLY the JSON object, no additional text.
```

---

## 3. Math Deep Dive Prompt (Verbatim)

**File:** `pipeline/prompts/math_prompt.md`
**Stage:** Content Generation (Stage 2)
**Variables injected:** `{{plan_json}}`, `{{technique_slug}}`
**Expected output:** `math_deep_dive.json`
**Why it matters:** The "every symbol must be defined before first use" rule is a notable constraint that shapes output quality.

```markdown
You are a mathematics professor specializing in optimization theory. Create a detailed mathematical deep dive for the optimization technique described in the plan below.

## Plan Context
\```json
{{plan_json}}
\```

## Requirements

Return a JSON object with these fields:

- **technique_slug** (string): "{{technique_slug}}"
- **artifact_type** (string): "math_deep_dive"
- **markdown** (string): A rigorous mathematical treatment (minimum 800 words) covering:
  - Formal problem statement and notation
  - Core algorithm derivation with step-by-step reasoning
  - Convergence analysis or theoretical guarantees (where applicable)
  - Complexity analysis (time and space)
  - Mathematical connections to related methods
  Use LaTeX notation: inline math with `$...$` and display math with `$$...$$`.
  **Critical rule**: Every symbol must be defined before its first use.
- **key_equations** (array of objects): The most important equations. Each object has:
  - "equation" (string): The equation in LaTeX with `$$...$$` delimiters.
  - "label" (string): A short descriptive label (e.g., "Update Rule", "Objective Function").
  - "step_by_step_derivation" (array of strings): An ordered array of derivation steps showing how this equation is derived. Each step should contain LaTeX math and a brief English explanation. Include at least 3 steps for complex equations. For simple definitions, provide at least 2 steps explaining the intuition.
- **worked_examples** (array of strings): At least 2 step-by-step worked examples showing the technique applied to concrete problems. Each example must start with `### Example N:` as a header. Use LaTeX for all math.
- **common_confusions** (array of strings): At least 2 common misconceptions or points of confusion, with clarifications.

Use the notation conventions from the plan. Ensure mathematical rigor appropriate for the target audience.

Respond with ONLY the JSON object, no additional text.
```

---

## 4. Implementation Prompt (Verbatim)

**File:** `pipeline/prompts/implementation_prompt.md`
**Stage:** Content Generation (Stage 2)
**Variables injected:** `{{plan_json}}`, `{{technique_slug}}`
**Expected output:** `implementation.json` with exactly 3 code_variations
**Why it matters:** Most constrained prompt — requires exactly 3 framework variations, pseudocode with specific keywords, and raw import names for dependencies.

```markdown
You are a senior software engineer and optimization specialist. Create a comprehensive implementation guide for the optimization technique described in the plan below.

## Plan Context
\```json
{{plan_json}}
\```

## Requirements

Return a JSON object with these fields:

- **technique_slug** (string): "{{technique_slug}}"
- **artifact_type** (string): "implementation"
- **markdown** (string): A detailed implementation guide (minimum 800 words) covering:
  - Do NOT start with a redundant title (e.g. "# Comprehensive Implementation Guide..."); the section header is provided by the page.
  - Use `##` for main sections, `###` for subsections. ...
  - Algorithm pseudocode with clear step numbering
  - Data structures and their rationale
  - Key implementation decisions and trade-offs
  - Performance optimization tips
  - Common pitfalls and how to avoid them
  - Testing and debugging strategies
- **python_examples** (array of strings): At least 2 complete, runnable Python code examples
- **libraries** (array of strings): Reader-facing library guidance with brief descriptions
- **runtime_dependencies** (array of strings): Raw Python import names needed to run the examples. Use importable module names only, with no descriptions.
- **pseudo_code** (string): Language-agnostic pseudocode using FUNCTION, FOR, WHILE, IF, RETURN.
- **code_variations** (array of 3 objects): Three complete implementation variations using different frameworks. Each object has:
  - "framework" (string): One of "numpy", "pytorch", or "scipy"
  - "label" (string): A human-readable label
  - "code" (string): A complete, runnable Python code example

Respond with ONLY the JSON object, no additional text.
```

---

## 5. Infographic Image Prompt (Verbatim)

**File:** `pipeline/prompts/infographic_image_prompt.md`
**Stage:** Image Generation (Stage 4)
**Variables injected:** `{{technique_name}}`, `{{title}}`, `{{layout}}`, `{{color_palette}}`, `{{typography}}`, `{{formatted_panels}}`, `{{formatted_equations}}`, `{{formatted_metaphors}}`
**Expected output:** `infographic.png`
**Why it matters:** Shows how structured JSON spec is reformatted into natural language for image generation. Note the "apply invisibly — do NOT display as text" rule.

```markdown
Create a professional educational infographic about {{technique_name}}.

Title: {{title}}

Layout: {{layout}}

**Content to include (render these):**
Panels:
{{formatted_panels}}

Key Equations (render as LaTeX in the image):
{{formatted_equations}}

Visual Metaphors:
{{formatted_metaphors}}

**Design guidance (apply invisibly — do NOT display as text):**
- Color palette: {{color_palette}} — Use these colors throughout the design. Never show color swatches, hex codes, or a "color palette" section in the image.
- Typography: {{typography}} — Use these font styles and sizes. Never display font names, point sizes, or typography specifications as visible text.

**Style requirements:**
- Clean, modern design suitable for technical education
- All text must be legible and correctly rendered
- Equations should be rendered clearly with proper mathematical notation
- Each panel should be visually distinct but cohesive
- Resolution: high quality, suitable for web and print
- No metadata, design specs, or behind-the-scenes information should appear in the final image
```

---

## 6. Homepage Summary Prompt (Verbatim)

**File:** `pipeline/prompts/homepage_summary_prompt.md`
**Stage:** Homepage Summary (Stage 3)
**Variables injected:** `{{plan_json}}`, `{{overview_summary}}`
**Expected output:** `homepage_summary.json` with 3-5 bullets
**Why it matters:** Shows artifact chaining — overview summary becomes input to this prompt.

```markdown
You are an expert technical writer. Create a very short, scannable summary for a homepage card.

## Plan
\```json
{{plan_json}}
\```

## Overview Summary (for context)
{{overview_summary}}

## Requirements

Return a JSON object with one field:

- **bullets** (array of strings): Exactly 3–5 short bullet points that capture the essence of this optimization technique. Each bullet should be one concise phrase or short sentence (under 15 words). No long paragraphs. Focus on: what it is, when to use it, and one key strength or characteristic.

Example format:
\```json
{
  "bullets": [
    "Model-based approach for expensive black-box functions",
    "Uses Gaussian Process surrogate and acquisition function",
    "Sample-efficient: few evaluations to find optimum",
    "Ideal for hyperparameter tuning and costly experiments"
  ]
}
\```

Respond with ONLY the JSON object, no additional text.
```

---

## 7. Preview Image Prompt (Verbatim)

**File:** `pipeline/prompts/preview_image_prompt.md`
**Stage:** Image Generation (Stage 4)
**Variables injected:** `{{technique_name}}`
**Expected output:** `preview.png`
**Why it matters:** Shows strict branding requirements — exact hex colors, aspect ratio, composition rules. Designed for visual consistency across 8 thumbnails.

```markdown
Create a single, cohesive preview image for the optimization algorithm "{{technique_name}}" for use as a homepage thumbnail card.

**Purpose:** This image will be displayed as a 280×160px thumbnail on a grid of optimization techniques. It must look consistent with other algorithm previews and work well when cropped to a wide landscape format.

**Strict design requirements (apply to ALL optimization algorithm previews):**
- Aspect ratio: 16:9 landscape. The composition must be centered and balanced so any crop works.
- Color palette (use exactly these — do NOT display as text or swatches):
  - Background: deep indigo #1A237E
  - Accent/highlights: coral #FF7043
  - Secondary: light blue #E3F2FD
  - Text/contrast: white #FFFFFF
- Style: Clean, modern technical illustration. Flat or subtle gradient. No photorealistic imagery.
- Composition: Single focal element in the center. ...
- Text: Only the algorithm name "{{technique_name}}" in white, 24–32pt sans-serif, centered at the bottom. No other text, equations, or labels.
- No color swatches, hex codes, typography specs, or design metadata in the image.

...

**Output:** A high-quality PNG, 16:9 aspect ratio, suitable for web. The image must feel cohesive with a portfolio of 8 different optimization algorithms — same color scheme, same composition rules, same level of visual density.
```

---

## 8. Recommender Prompt (Verbatim)

**File:** `pipeline/prompts/recommender_prompt.md`
**Stage:** API Runtime
**Variables injected:** `{{use_case_matrix}}`
**Expected output:** JSON with 2-3 recommendations
**Why it matters:** Shows context injection at runtime — the entire use-case matrix is embedded as context for recommendation.

```markdown
You are an expert optimization algorithm advisor. Your job is to recommend the best optimization algorithms for a user's specific problem.

You have access to the following use-case matrix that maps algorithms to their characteristics, strengths, and ideal problem types:

\```json
{{use_case_matrix}}
\```

Based on the user's problem description, recommend exactly 2-3 algorithms that best fit their needs. For each recommendation, provide:

1. **algorithm**: The exact name of the algorithm (must match one from the matrix).
2. **justification**: A clear 2-3 sentence explanation of why this algorithm is a good fit for their specific problem.
3. **confidence_score**: An integer from 1-100 indicating how confident you are that this algorithm is appropriate. Be calibrated — use 90+ only for near-perfect matches.
4. **url_slug**: The URL-friendly slug for the algorithm.

Order recommendations from highest to lowest confidence score.

Return ONLY valid JSON matching this schema — no markdown, no commentary:
```

---

## 9. Judge Prompt [RECONSTRUCTED]

**File:** Dynamically constructed in `pipeline/judge.py` → `_build_judge_prompt()`
**Stage:** Evaluation Pipeline (Stage 6d)
**Variables:** artifact_type, rubric criteria, pass_threshold, reference facts, forbidden claims, artifact content (truncated to 8000 chars)
**Expected output:** Judge score JSON
**Why it matters:** This is the core quality gate. The prompt is NOT a template file — it's assembled in Python code. Reconstructed below with realistic values for a Bayesian Optimization overview evaluation.

### System Prompt (Verbatim from code):
```
You are a strict educational content evaluator. Evaluate the provided artifact against the rubric criteria and reference facts. Score each criterion from 1-10. Set passed=true only if overall_score >= 7. Provide specific critiques and actionable revision instructions. Respond with valid JSON only.
```

### User Prompt (Reconstructed with Bayesian Optimization overview):
```markdown
## Artifact Type: overview

## Evaluation Criteria
- factual_accuracy: Are all factual claims accurate and verifiable? Does the content correctly describe the algorithm's behavior, properties, and applications?
- math_correctness: Are mathematical expressions, derivations, and notation correct? Are equations properly formatted and steps logically sound?
- clarity: Is the content clear, well-organized, and pedagogically effective? Does it build understanding progressively?
- code_quality: Is the code correct, readable, well-documented, and pedagogically aligned with the explanatory text?

## Pass Threshold: 7/10

## Canonical Reference Facts
- Bayesian Optimization is a sequential model-based optimization strategy for black-box functions
- It uses a surrogate model (typically a Gaussian Process) to approximate the objective function
- An acquisition function (e.g., Expected Improvement, UCB) guides the selection of the next evaluation point
- It is particularly effective for expensive-to-evaluate objective functions
- It balances exploration (sampling uncertain regions) and exploitation (sampling promising regions)
- Bayesian Optimization was introduced by Jonas Mockus and has roots in Bayesian decision theory
- Common surrogate models include Gaussian Processes, Random Forests, and Tree-structured Parzen Estimators

## Forbidden Claims (must NOT appear)
- Bayesian Optimization requires gradients of the objective function
- Bayesian Optimization guarantees finding the global optimum
- Bayesian Optimization scales well to very high dimensions without modification
- Bayesian Optimization is a type of evolutionary algorithm

## Artifact Content
\```json
{...truncated to 8000 chars...}
\```

Evaluate this artifact. Respond with JSON matching the judge output schema.
```

---

## 10. Revision Prompt [RECONSTRUCTED]

**File:** Dynamically constructed in `pipeline/judge.py` → `build_revision_prompt()`
**Stage:** Retry Loop (Stage 6d, attempts 2-3)
**Variables:** artifact_type, current score, critiques, revision_instructions, current artifact content (truncated to 8000 chars)
**Expected output:** Revised artifact JSON
**Why it matters:** Shows how judge feedback drives targeted revision — the LLM sees its score, specific critiques, and actionable instructions.

### System Prompt (Verbatim from code):
```
You are an expert in optimization algorithms. Revise the provided artifact based on the improvement instructions. Maintain the same JSON structure. Respond with valid JSON only.
```

### User Prompt (Reconstructed with example failure scenario):
```markdown
## Artifact Type: overview

## Current Score: 5/10

## Critiques
- Missing explanation of acquisition function trade-offs between Expected Improvement and Upper Confidence Bound
- Historical context section incorrectly attributes the method to the wrong decade
- Use cases list is too generic — "machine learning" is not specific enough

## Revision Instructions
- Add a subsection comparing EI and UCB acquisition functions with their respective strengths
- Correct the historical attribution: Mockus's seminal work was in 1975, not 1990s
- Replace generic use cases with specific examples: hyperparameter tuning for neural networks, experimental design in drug discovery, A/B test optimization

## Current Artifact
\```json
{...truncated to 8000 chars...}
\```

Revise this artifact to address all critiques and instructions. Return the complete revised artifact as JSON.
```

---

## 11. Use-Case Matrix Prompt (Verbatim)

**File:** `pipeline/prompts/use_case_matrix_prompt.md`
**Stage:** Use-Case Matrix Generation (Stage 5)
**Variables injected:** None (self-contained)
**Expected output:** `use_case_matrix.json`
**Why it matters:** The most self-contained prompt — no variable injection. Its output is consumed by the recommender endpoint as context.

*(Full prompt is 75 lines — key excerpts:)*

```markdown
You are an expert in optimization algorithms. Create a comprehensive comparison table showing which optimization techniques are well-suited (or poorly suited) for different problem spaces and use cases.

## Techniques to Compare
The following 8 optimization algorithms must appear in the matrix:
- Bayesian Optimization
- Genetic Algorithm
- Simulated Annealing
- ...

## Problem Spaces / Use Cases
Define 12–18 distinct problem spaces or use-case categories...

## Rating Rules
For each (algorithm, problem_space) pair, use exactly one of:
- **"ideal"** — The algorithm is among the best choices for this use case.
- **"suitable"** — The algorithm works well but may not be the top choice.
- **"unsuitable"** — The algorithm is a poor fit.

Be rigorous: an algorithm should be "ideal" or "suitable" only when it genuinely fits.

...

Respond with ONLY the JSON object, no additional text or markdown fences.
```

---

## Prompt Pattern Summary

| Pattern | Prompts Using It | Presentation Value |
|---------|-----------------|-------------------|
| Plan-as-context injection | Overview, Math, Implementation, Infographic, Summary | High — shows cascade |
| JSON-only response constraint | All 10 templates | Medium — ensures parseability |
| Artifact chaining (output → input) | Summary ← Overview, Image ← Spec | High — shows data flow |
| Negative constraints | Image (no metadata), Implementation (no wrong algos), Math tutor (bounded) | High — shows quality control |
| Exact structural requirements | Implementation (3 variations), Summary (3-5 bullets) | Medium — shows precision |
| Formatting guidance | Overview, Math, Implementation | Medium — prevents rendering bugs |
| Dynamic assembly | Judge, Revision | High — shows runtime prompting |
| Context injection | Recommender (matrix), Compare (artifacts) | High — shows RAG-like pattern |
