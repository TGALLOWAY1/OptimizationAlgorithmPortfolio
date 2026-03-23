# Presentation Storyline

## Suggested Deck Title

**"From Prompt to Publication: Building a Self-Correcting Educational Content Pipeline with LLMs"**

---

## Narrative Arc

The presentation tells the story of a system that turns 8 algorithm names into a complete, quality-assured educational website — automatically. The arc moves from **"what and why"** → **"how it works"** → **"how it maintains quality"** → **"where it can go next."**

---

## Opening Framing (Slides 1-2)

### Slide 1: The Hook
**"What if you could type 8 algorithm names into a config file and get a complete educational website — with overviews, math derivations, code examples, infographics, and interactive tools?"**

Show a split: left side shows `config.json` with 8 technique names. Right side shows the published website with polished technique pages.

### Slide 2: The Problem
**"Creating quality educational content about optimization algorithms is expensive."**

Bullet points:
- Subject matter expertise for math, code, and prose
- 6-8 artifact types per algorithm × 8 algorithms = 48-64 pieces of content
- Consistency across artifacts (same notation, same assumptions)
- Quality assurance for factual accuracy, math correctness, code correctness
- Manual updates when content needs revision

**"This pipeline automates the entire workflow."**

---

## What It Produces (Slides 3-4)

### Slide 3: The Output
**"65+ artifacts from a single pipeline run"**

Show the artifact inventory visually:
- 8 plans, 8 overviews, 8 math deep dives, 8 implementation guides
- 8 infographic specs, 8 homepage summaries
- 8 infographic images, 8 preview thumbnails
- 1 use-case matrix, 1 quality report
- Complete static website with 5 interactive API features

### Slide 4: The Website in Action
Show screenshots or a brief demo of:
- Homepage with technique grid
- A technique detail page (overview → math → implementation → infographic)
- The use-case matrix (color-coded table)
- The algorithm recommender widget

---

## How It Works: Pipeline Architecture (Slides 5-8)

### Slide 5: High-Level Architecture
**Show Diagram A** (high-level system diagram from `03_data_flow_and_system_diagrams.md`)

Key callouts:
- Three LLM providers (Gemini, Nano Banana, OpenAI) serve different roles
- Config-driven routing — no hardcoded provider logic
- Evaluation pipeline with feedback loops

### Slide 6: Pipeline Stages Overview
**Show Diagram B** (pipeline data flow) — simplified version

Walk through the 7 stages:
1. Config Loading
2. Plan Generation (foundation)
3. Content Generation (4 artifact types)
4. Homepage Summary
5. Image Generation
6. Use-Case Matrix
7. Evaluation Pipeline

### Slide 7: The Plan-as-Contract Pattern
**Show a real `plan.json` example** (or excerpt)

Explain:
- Plan establishes terminology, notation, audience, scope
- Plan JSON is injected verbatim into all downstream prompts
- This ensures consistency without manual coordination
- "The plan is the contract that all artifacts sign"

### Slide 8: Multi-Provider Routing
**Show the `artifact_provider_map`** from config.json

Explain:
- Gemini 3.1 Pro handles text content (cost-effective, good at structured output)
- Nano Banana Pro handles image generation (Gemini Flash image model)
- OpenAI GPT-4o handles API endpoints and judge evaluation
- Swapping providers is a config change, not a code change

---

## How Prompting Works (Slides 9-10)

### Slide 9: Prompt Architecture
**Show the prompt chain diagram** (from `06_prompting_architecture.md`)

Key points:
- 10 template files + 5 inline/dynamic prompts
- `{{variable}}` injection pattern
- Plan JSON cascades through all content prompts
- Artifact chaining: overview → summary, spec → image

### Slide 10: A Prompt Close-Up
**Show the implementation prompt** (or a compelling excerpt)

Highlight:
- Exactly 3 code_variations required (NumPy, PyTorch, SciPy)
- Pseudocode must use specific keywords (FUNCTION, FOR, WHILE, IF, RETURN)
- Runtime dependencies must be raw import names
- Schema validation enforces these constraints automatically

---

## How Quality Is Maintained (Slides 11-14)

### Slide 11: The Quality Problem
**"LLMs are non-deterministic. How do you get reliable output?"**

Answer: A 4-stage quality pipeline that combines deterministic and probabilistic checks.

### Slide 12: The 4-Stage Quality Funnel
**Show Diagram D** (judge/evaluation flow)

Walk through each stage:
1. **Schema Validation** — Structural correctness (instant, free)
2. **Static Checks** — Placeholders, LaTeX balance, off-topic detection (instant, free)
3. **Code Execution** — Python examples run in subprocess (30s, CPU only)
4. **LLM Judge** — Rubric-based scoring against reference facts (API call)

"Each stage filters out more issues. Cheap checks first, expensive checks last."

### Slide 13: The LLM Judge
**Show rubric criteria** and a **reference fact file**

Explain:
- 4 criteria: factual_accuracy (30%), math_correctness (30%), clarity (25%), code_quality (15%)
- Pass threshold: 7/10
- Reference files anchor the judge with ground truth (key facts + forbidden claims)
- Different criteria apply to different artifact types

### Slide 14: The Self-Correction Loop
**Show the retry loop flow**

Explain:
- Judge scores < 7 → extracts critiques and revision instructions
- Constructs revision prompt: "Your score was 5/10. Here's what's wrong. Fix it."
- Re-generates artifact, re-evaluates
- Up to 3 total attempts
- "The pipeline debugs its own output"

Show a **reconstructed revision prompt** example (from `09_prompts_used_or_reconstructed.md`)

---

## What Makes This Interesting (Slides 15-16)

### Slide 15: Design Decisions That Matter
Pick 3-4 of the most interesting:

1. **Idempotency via input hashing** — SHA-256 of all inputs prevents redundant API calls; safe reruns
2. **Cross-model evaluation** — Gemini generates, GPT-4o judges (avoids "grading your own homework")
3. **Config-driven everything** — Adding an algorithm requires zero code changes
4. **LaTeX preservation in rendering** — Math spans extracted → placeholders → markdown → restore

### Slide 16: Extensibility
**Show Diagram E** (extensibility diagram)

Key callouts:
- Adding a new algorithm: 2 steps (config + reference file)
- Adding a new provider: 3 steps (class + factory + config)
- Modifying evaluation: edit JSON files, no code
- "The architecture anticipates the most common changes"

---

## Interactive Features (Slide 17)

### Slide 17: Beyond Static Content
**Show the 5 API endpoints**

Brief explanation of each:
- **Recommender**: Describe your problem → get algorithm suggestions with confidence scores
- **Comparison**: Head-to-head analysis with pros/cons
- **Math Tutor**: Highlight equation → get explanation
- **Study Plan**: Background + goals → personalized learning roadmap
- **Code Adapter**: Convert code between frameworks

"These turn static content into an interactive learning platform."

---

## Closing (Slides 18-19)

### Slide 18: Key Numbers

| Metric | Value |
|--------|-------|
| Algorithms covered | 8 |
| Artifacts generated | 65+ |
| Prompt templates | 10 |
| Quality stages | 4 |
| Test cases (no API keys needed) | 70+ |
| Pipeline cost | $4-10 |
| Code changes to add an algorithm | 0 |

### Slide 19: Final Takeaway
**"This pipeline demonstrates that LLM-powered content generation can be reliable, repeatable, and high-quality — if you treat it as an engineering problem, not a prompting problem."**

Key insight: The value isn't in any single prompt. It's in the **system around the prompts**: schemas, validation, evaluation, revision, configuration, and reproducibility.

---

## Presentation Tips

1. **Demo opportunity:** If presenting live, demo the recommender or math tutor. These are the most visually compelling interactive features.

2. **For technical audiences:** Spend more time on the judge method, retry loop, and code execution. These are the most architecturally novel elements.

3. **For semi-technical audiences:** Focus on the pipeline stages diagram, the "65+ artifacts" number, and the "$4-10 for a complete educational website" framing. Skip code-level details.

4. **For stakeholder audiences:** Lead with the output (website screenshots), explain the quality pipeline briefly, and emphasize the extensibility/cost-effectiveness story.

5. **Progressive reveal:** For the quality funnel, reveal stages one at a time (schema → static → code → judge) to build the narrative of increasing sophistication.
