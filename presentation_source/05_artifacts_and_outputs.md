# Artifacts and Outputs

## Per-Technique Artifacts

### 1. `plan.json`
- **Purpose:** Foundation document establishing terminology, notation, audience, and scope for all subsequent artifacts
- **When generated:** Stage 1, first artifact for each technique
- **Upstream dependencies:** Technique name from `config.json`
- **Format:** JSON with fields: `technique_name`, `slug`, `aliases[]`, `problem_type`, `notation_conventions[]`, `assumptions[]`, `target_audience`, `artifacts_required[]`
- **Storage:** `content/<slug>/plan.json`
- **Used later by:** Every other artifact prompt (injected as `{{plan_json}}`)
- **User-visible:** Indirectly — plan data appears in HTML page structure and provenance
- **Intermediate or final:** Intermediate (consumed by downstream generation, not directly displayed)

### 2. `overview.json`
- **Purpose:** Comprehensive introduction to the algorithm — what it is, when to use it, strengths, limitations, comparisons
- **When generated:** Stage 2, after plan exists
- **Upstream dependencies:** `plan.json`
- **Format:** JSON with `title`, `summary` (2-3 sentences), `markdown` (800+ words), `use_cases[]`, `strengths[]`, `limitations[]`, `comparisons[]`
- **Storage:** `content/<slug>/overview.json`
- **Used later by:** Homepage summary (uses `overview.summary`), technique HTML page, comparison endpoint
- **User-visible:** Yes — rendered as the overview section on technique pages
- **Intermediate or final:** Final (directly rendered to HTML)

### 3. `math_deep_dive.json`
- **Purpose:** Formal mathematical treatment with equations, derivations, worked examples, and common confusions
- **When generated:** Stage 2, after plan exists
- **Upstream dependencies:** `plan.json`
- **Format:** JSON with `markdown` (800+ words with LaTeX), `key_equations[]` (each with `equation`, `label`, `step_by_step_derivation[]`), `worked_examples[]`, `common_confusions[]`
- **Storage:** `content/<slug>/math_deep_dive.json`
- **Used later by:** Technique HTML page, math tutor endpoint (provides context)
- **User-visible:** Yes — rendered with KaTeX on technique pages, collapsible derivations
- **Intermediate or final:** Final

### 4. `implementation.json`
- **Purpose:** Practical coding guide with pseudocode, Python examples, library references, and framework-specific code variations
- **When generated:** Stage 2, after plan exists
- **Upstream dependencies:** `plan.json`
- **Format:** JSON with `markdown` (800+ words), `python_examples[]`, `libraries[]`, `runtime_dependencies[]`, `pseudo_code`, `code_variations[3]` (NumPy, PyTorch, SciPy/scikit-learn with `framework`, `label`, `code`)
- **Storage:** `content/<slug>/implementation.json`
- **Used later by:** Technique HTML page (tabbed code viewer), code adapter endpoint, code execution validation
- **User-visible:** Yes — rendered with Highlight.js syntax highlighting and tabbed framework selector
- **Intermediate or final:** Final

### 5. `infographic_spec.json`
- **Purpose:** Structured specification for visual infographic generation — panels, layout, colors, typography, metaphors
- **When generated:** Stage 2, after plan exists
- **Upstream dependencies:** `plan.json`
- **Format:** JSON with `title`, `panels[]` (4+ items with `title`, `content`, `visual_type`), `visual_metaphors[]`, `color_palette`, `layout`, `typography`, `key_equations[]`
- **Storage:** `content/<slug>/infographic_spec.json`
- **Used later by:** Infographic image generation (formatted fields injected into image prompt)
- **User-visible:** Indirectly — drives image generation
- **Intermediate or final:** Intermediate (consumed by image generation prompt)

### 6. `homepage_summary.json`
- **Purpose:** 3-5 scannable bullet points for homepage technique cards
- **When generated:** Stage 3, after overview exists
- **Upstream dependencies:** `plan.json`, `overview.json` (specifically `overview.summary`)
- **Format:** JSON with `bullets[]` (3-5 items, each <15 words)
- **Storage:** `content/<slug>/homepage_summary.json`
- **Used later by:** Homepage grid cards on `index.html`
- **User-visible:** Yes — appears on homepage
- **Intermediate or final:** Final

### 7. `infographic.png`
- **Purpose:** Visual infographic image illustrating the algorithm's key concepts
- **When generated:** Stage 4, after infographic_spec exists
- **Upstream dependencies:** `infographic_spec.json` (title, layout, panels, equations, metaphors, colors, typography)
- **Format:** PNG image
- **Storage:** `content/<slug>/infographic.png` → copied to `site/images/<slug>/infographic.png`
- **Used later by:** Technique HTML page (embedded image)
- **User-visible:** Yes
- **Intermediate or final:** Final

### 8. `preview.png`
- **Purpose:** 16:9 thumbnail preview for homepage cards with consistent branding
- **When generated:** Stage 4, independent of other artifacts
- **Upstream dependencies:** Technique name only
- **Format:** PNG image, 280×160px crop-safe, branded colors (indigo #1A237E, coral #FF7043, white text)
- **Storage:** `content/<slug>/preview.png` → copied to `site/images/<slug>/preview.png`
- **Used later by:** Homepage grid cards on `index.html`
- **User-visible:** Yes
- **Intermediate or final:** Final

### 9. `manifest.json`
- **Purpose:** Tracks generation metadata — input hashes, provider info, timestamps, filenames
- **When generated:** Updated after each artifact generation
- **Upstream dependencies:** All generation inputs
- **Format:** JSON with per-artifact entries: `{filename, input_hash, provider, model, timestamp, artifact_version}`
- **Storage:** `content/<slug>/manifest.json`
- **Used later by:** Idempotency checks (hash comparison), provenance display on HTML pages
- **User-visible:** Indirectly — provenance info appears in page header
- **Intermediate or final:** Infrastructure (supports pipeline operations)

---

## Global Artifacts

### 10. `use_case_matrix.json`
- **Purpose:** Cross-reference matrix rating all 8 algorithms against problem space dimensions
- **When generated:** Stage 5, only on full 8-technique runs
- **Upstream dependencies:** None (prompt is self-contained)
- **Format:** JSON with `title`, `description`, `problem_spaces[]` (with `id`, `label`, `description`), `matrix` (algorithm → problem_space → "ideal"/"suitable"/"unsuitable")
- **Storage:** `content/use_case_matrix.json`
- **Used later by:** Algorithm recommender (injected as context), published as `use_case_matrix.html`
- **User-visible:** Yes — color-coded HTML table
- **Intermediate or final:** Final

### 11. Evaluation Metrics
- **Purpose:** Comprehensive quality assessment results for all evaluated artifacts
- **When generated:** Stage 6, after evaluation pipeline runs
- **Upstream dependencies:** All generated artifacts, rubrics, references
- **Format:** JSON with `timestamp`, `scope`, `summary` (counts), per-technique results (per-artifact status, attempts, scores)
- **Storage:** `content/evaluations/<timestamp>-<scope>.json` + `content/evaluations/latest-full.json` (alias)
- **Used later by:** Quality report HTML page
- **User-visible:** Yes — rendered as `quality-report.html`
- **Intermediate or final:** Final

### 12. Evaluation Logs
- **Purpose:** Detailed per-artifact evaluation trace for debugging
- **When generated:** During evaluation pipeline
- **Upstream dependencies:** Evaluation results
- **Format:** JSON with stage history, judge scores, critiques, attempt counts
- **Storage:** `content/logs/evaluation/<slug>/<artifact_type>.json`
- **Used later by:** Debugging/auditing only
- **User-visible:** No
- **Intermediate or final:** Infrastructure

---

## Published Site Artifacts

### 13. `site/index.html`
- **Purpose:** Homepage with grid of technique cards, recommender widget, comparison/study plan buttons
- **Format:** HTML + embedded JS (recommender, study plan wizard)
- **Template:** `pipeline/templates/index.html`

### 14. `site/<slug>.html` (×8)
- **Purpose:** Technique detail pages with all artifact content rendered
- **Format:** HTML + CSS + JS (KaTeX, Highlight.js, math tutor sidebar, code adapter modal, tabbed code viewer)
- **Template:** `pipeline/templates/technique.html`

### 15. `site/compare.html`
- **Purpose:** Algorithm comparison page with two dropdowns and dynamic comparison table
- **Format:** HTML + JS (fetches `/api/compare`)
- **Template:** `pipeline/templates/compare.html`

### 16. `site/use-case-matrix.html`
- **Purpose:** Color-coded comparison matrix table
- **Format:** HTML + CSS (responsive table)
- **Template:** `pipeline/templates/use_case_matrix.html`

### 17. `site/quality-report.html`
- **Purpose:** Evaluation quality report with pass/fail badges and methodology
- **Format:** HTML
- **Template:** `pipeline/templates/eval_report.html`

---

## API Response Artifacts (Runtime)

### 18. Recommendation Response
- **Format:** `[{algorithm, justification, confidence_score, url_slug}]` (2-3 items)
- **Source:** `/api/recommend`

### 19. Comparison Response
- **Format:** `{algorithm_a/b, pros_a/b[], cons_a/b[], best_for_a/b, summary}`
- **Source:** `/api/compare`

### 20. Math Explanation Response
- **Format:** `{explanation}` (LaTeX-formatted markdown)
- **Source:** `/api/math_tutor`

### 21. Study Plan Response
- **Format:** `{roadmap: [{slug, title, reason, order}], rationale}`
- **Source:** `/api/study_plan`

### 22. Adapted Code Response
- **Format:** `{adapted_code, notes}`
- **Source:** `/api/adapt_code`

---

## Artifacts Worth Showcasing in the Presentation

### Tier 1: Visually Compelling
1. **Use-case matrix** — Color-coded table showing ideal/suitable/unsuitable ratings across problem dimensions. Great slide content because it's information-dense and visually striking.
2. **Infographic images** — Generated PNGs showing algorithm concepts visually. Show a before (spec JSON) → after (rendered PNG) comparison.
3. **Homepage with technique cards** — Shows the full output of the pipeline as a polished product.

### Tier 2: Conceptually Interesting
4. **plan.json** — Show a real example to explain "the plan is the contract." All downstream artifacts inherit its terminology and scope.
5. **Math deep dive with KaTeX rendering** — Show raw JSON with LaTeX → rendered HTML with beautiful math. Demonstrates the LaTeX preservation pipeline.
6. **Implementation with tabbed code viewer** — Show the same algorithm in NumPy vs. PyTorch vs. SciPy side by side.

### Tier 3: Architecture Showcase
7. **Evaluation metrics** — Show pass/fail rates, retry counts, and scores to demonstrate quality assurance.
8. **manifest.json** — Show input hashing and provenance tracking as a production-grade pattern.
9. **Judge output** — Show a real `{critiques, revision_instructions, scores}` to demonstrate the feedback loop.

### Tier 4: Interactive Demo Potential
10. **Algorithm recommender** — Live demo: type a problem, get recommendations with confidence scores.
11. **Math tutor** — Live demo: highlight an equation, get an explanation.
12. **Code adapter** — Live demo: paste NumPy code, get PyTorch version.
