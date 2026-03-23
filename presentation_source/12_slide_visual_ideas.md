# Slide Visual Ideas

## Slide 1: The Hook
**Title:** "8 Names In, Complete Website Out"

**Visual:** Split-screen mockup
- Left: `config.json` code snippet showing the 8 technique names (dark code editor theme)
- Right: Screenshot of the published homepage with technique cards
- Arrow connecting left → right with label "$4-10"

**Simplification for non-technical:** Focus on the before/after visual. The config file shows "just a list of names." The website shows polished output.

---

## Slide 2: The Problem
**Title:** "The Content Creation Challenge"

**Visual:** Grid showing 8 algorithms × 6-8 artifact types = matrix of 48-64 cells. Most cells empty with a "?" icon. A few filled in to show the scale of the task.

**Alternative:** Stacked cost icons — person-hours, subject matter expertise, consistency checks, code review, math review

---

## Slide 3: What It Produces
**Title:** "65+ Artifacts, One Pipeline Run"

**Visual:** Artifact tree diagram:
```
Pipeline Run
├── Bayesian Optimization
│   ├── plan.json
│   ├── overview.json → HTML
│   ├── math_deep_dive.json → HTML (KaTeX)
│   ├── implementation.json → HTML (Highlight.js)
│   ├── infographic_spec.json → infographic.png
│   ├── homepage_summary.json → card
│   └── preview.png → thumbnail
├── Genetic Algorithm
│   └── (same structure)
├── ... (×8)
├── use_case_matrix.json → comparison table
└── quality_report.json → evaluation dashboard
```

**Progressive reveal:** Show one technique, then expand to show all 8 share the same structure.

---

## Slide 4: The Website
**Title:** "The Published Output"

**Visual:** 3-4 annotated screenshots:
1. Homepage with technique grid (annotate: "LLM-generated summaries, branded thumbnails")
2. Technique page overview section (annotate: "800+ word overview with LaTeX math")
3. Implementation section with tabbed code viewer (annotate: "3 framework variations: NumPy, PyTorch, SciPy")
4. Use-case matrix (annotate: "Color-coded: ideal / suitable / unsuitable")

---

## Slide 5: System Architecture
**Title:** "High-Level Architecture"

**Visual:** Mermaid Diagram A from `03_data_flow_and_system_diagrams.md`, rendered as a clean diagram

**Key annotations:**
- Circle Gemini/Nano Banana/OpenAI with different colors
- Highlight the feedback loop between Evaluator → Judge → Retry
- Label the two output paths: "Batch" (static site) and "Runtime" (Flask API)

---

## Slide 6: Pipeline Stages
**Title:** "7 Stages, Start to Finish"

**Visual:** Horizontal pipeline diagram with numbered stages:
```
[1 Config] → [2 Plan] → [3 Content ×4] → [4 Summary] → [5 Images] → [6 Matrix] → [7 Evaluate]
                                                                                        ↓
                                                                                   [Publish]
```

**Progressive reveal:** Reveal stages one at a time, left to right.

**Code snippet to show:** The CLI command that triggers it all:
```bash
python -m pipeline.generate --evaluate
```

---

## Slide 7: Plan as Contract
**Title:** "The Plan Is the Contract"

**Visual:** Show a real (or representative) `plan.json` excerpt:
```json
{
  "technique_name": "Bayesian Optimization",
  "slug": "bayesian-optimization",
  "notation_conventions": ["f(x) for objective function", "x* for optimal solution"],
  "target_audience": "graduate students in CS/ML",
  "assumptions": ["black-box objective function", "expensive evaluation cost"]
}
```

Then show arrows from this plan to 4 downstream prompts, each inheriting the notation and audience.

**Key message:** "One plan, consistent content across all artifacts."

---

## Slide 8: Multi-Provider Routing
**Title:** "Right Model for the Right Job"

**Visual:** Routing table from `config.json`:
```
plan, overview, math, impl, infographic_spec, summary → Gemini 3.1 Pro
infographic_image, preview_image → Nano Banana Pro (Gemini Flash)
recommender, compare, math_tutor, study_plan, judge → OpenAI GPT-4o
```

Color-code each provider. Show that swapping is one line in a config file.

---

## Slide 9: Prompt Architecture
**Title:** "10 Templates, 15 Prompting Contexts"

**Visual:** Prompt chain diagram showing dependency arrows:
```
planner_prompt.md
    ↓ plan.json
    ├→ overview_prompt.md → overview.json
    │                         ↓
    │                    homepage_summary_prompt.md
    ├→ math_prompt.md
    ├→ implementation_prompt.md
    └→ infographic_prompt.md → infographic_spec.json
                                    ↓
                              infographic_image_prompt.md
```

**Key message:** "Prompts form a dependency graph, not a flat list."

---

## Slide 10: Prompt Close-Up
**Title:** "Inside the Implementation Prompt"

**Visual:** Annotated prompt excerpt with callouts:
- Callout 1: `{{plan_json}}` → "Full plan injected as context"
- Callout 2: `code_variations (array of 3 objects)` → "Exactly 3 framework variations required"
- Callout 3: `runtime_dependencies` → "Raw import names only, no descriptions"
- Callout 4: `Respond with ONLY the JSON object` → "Schema-enforced output"

**Code snippet:** Show 3-4 key lines of the prompt, not the full thing.

---

## Slide 11: The Quality Problem
**Title:** "LLMs Are Non-Deterministic. How Do You Get Reliable Output?"

**Visual:** Simple graphic showing LLM as a "black box" with variable outputs — some good, some with issues (wrong math, placeholder text, broken code).

**Transition:** "Answer: A 4-stage quality pipeline."

---

## Slide 12: Quality Funnel
**Title:** "4 Stages: Structure → Content → Code → Semantics"

**Visual:** Funnel diagram (wide at top, narrow at bottom):

```
╔══════════════════════════════════════╗
║  Stage 1: Schema Validation          ║  FREE, INSTANT
║  (Does it match the JSON structure?) ║
╠═════════════════════════════════════╣
║  Stage 2: Static Checks              ║  FREE, INSTANT
║  (Placeholders? LaTeX balanced?      ║
║   Off-topic? Duplicated paragraphs?) ║
╠══════════════════════════════════════╣
║  Stage 3: Code Execution             ║  CPU, 30s MAX
║  (Do Python examples actually run?)  ║
╠══════════════════════════════════════╣
║  Stage 4: LLM Judge                  ║  API CALL
║  (Factually accurate? Math correct?  ║
║   Clear? Well-coded? Score ≥ 7/10?)  ║
╚══════════════════════════════════════╝
```

**Progressive reveal:** Reveal each stage one at a time, building the funnel.

---

## Slide 13: The LLM Judge
**Title:** "Rubric-Based Scoring Against Reference Facts"

**Visual:** Two-column layout:

Left column — **Rubric:**
```
factual_accuracy:  30%  "Are claims accurate?"
math_correctness:  30%  "Are equations correct?"
clarity:           25%  "Is it pedagogically effective?"
code_quality:      15%  "Is code correct and readable?"

Pass threshold: 7/10
```

Right column — **Reference (Bayesian Optimization):**
```
Key facts:
✅ Uses surrogate model (Gaussian Process)
✅ Acquisition function guides sampling
✅ Designed for expensive functions

Forbidden claims:
❌ Requires gradients
❌ Guarantees global optimum
❌ Scales to high dimensions
```

---

## Slide 14: Self-Correction Loop
**Title:** "The Pipeline Debugs Its Own Output"

**Visual:** Circular flow diagram:
```
Generate → Judge → Score < 7?
                     ↓ Yes
              Extract Critiques →
              Build Revision Prompt →
              Re-Generate → Re-Judge
              (up to 3 attempts)
```

**Code snippet:** Show the reconstructed revision prompt excerpt:
```
Current Score: 5/10

Critiques:
- Missing explanation of acquisition function trade-offs
- Historical context incorrectly attributed

Revision Instructions:
- Add comparison between EI and UCB
- Correct attribution to Mockus (1975)
```

---

## Slide 15: Key Design Decisions
**Title:** "What Makes This Pipeline Production-Grade"

**Visual:** 4 cards, each with an icon and short explanation:

1. **Idempotency** — SHA-256 input hashing; safe reruns, no wasted API calls
2. **Cross-Model Evaluation** — Gemini generates, GPT-4o judges; no "grading your own homework"
3. **Config Over Code** — New algorithm = config entry + reference file; zero code changes
4. **LaTeX Preservation** — Math extracted before markdown rendering, restored after

---

## Slide 16: Extensibility
**Title:** "Built to Grow"

**Visual:** Table showing extension difficulty:

| Add... | Steps | Code Changes? |
|--------|-------|---------------|
| New algorithm | 2 | No |
| New provider | 3 | Minimal |
| New artifact type | 5 | Yes |
| New evaluation criteria | 1 | No |
| New reference facts | 1 | No |

---

## Slide 17: Interactive Features
**Title:** "5 Live API Endpoints"

**Visual:** Screenshot carousel or mockup of each feature:
1. **Recommender** — Input: problem description → Output: 2-3 algorithm cards with confidence scores
2. **Comparison** — Two dropdown selectors → structured pros/cons table
3. **Math Tutor** — Highlighted equation → sidebar explanation
4. **Study Plan** — Background + goals → ordered roadmap
5. **Code Adapter** — Source code + target framework → adapted code

**Demo opportunity:** If presenting live, show the recommender in action.

---

## Slide 18: By the Numbers
**Title:** "Key Metrics"

**Visual:** Large-number dashboard layout:

```
8        algorithms
65+      artifacts generated
10       prompt templates
4        quality stages
70+      tests (no API keys needed)
$4-10    total pipeline cost
0        code changes to add an algorithm
7/10     judge pass threshold
3        max retry attempts
```

---

## Slide 19: Final Takeaway
**Title:** "Treat LLM Content as an Engineering Problem"

**Visual:** Simple text slide with the key insight:

> "The value isn't in any single prompt. It's in the **system around the prompts**: schemas, validation, evaluation, revision, configuration, and reproducibility."

**Subtext:** "From prompt to publication — reliably."

---

## Animation / Progressive Reveal Suggestions

1. **Pipeline stages (Slide 6):** Reveal left to right, one stage at a time
2. **Quality funnel (Slide 12):** Reveal top to bottom, one stage at a time, with cost labels appearing
3. **Plan as contract (Slide 7):** Show plan first, then arrows radiating out to downstream artifacts
4. **Self-correction loop (Slide 14):** Animate the circular flow, then show the revision prompt content
5. **Extensibility table (Slide 16):** Highlight the "No code changes" rows in green

## What to Simplify for Non-Technical Viewers

- Replace "SHA-256 input hashing" with "fingerprinting inputs so nothing gets regenerated unnecessarily"
- Replace "JSON Schema validation" with "checking the structure of the output"
- Replace "exponential backoff" with "waiting longer between retries"
- Replace "AST parsing" with "analyzing code imports"
- Replace "subprocess execution" with "running the code in a safe sandbox"
- Skip the Gemini schema adaptation detail (`_schema_for_gemini`)
- Skip the LaTeX preservation regex details; show before/after instead
