# Extensibility and Design Tradeoffs

## Modularity Assessment

The pipeline is **highly modular** along its primary extension axes:

| Extension Type | Difficulty | Code Changes Required |
|---------------|------------|----------------------|
| Add new algorithm | Easy | 0 (config + reference file only) |
| Swap LLM provider for existing type | Easy | 1 line in config.json |
| Add new LLM provider | Moderate | 1 new class + factory registration + config |
| Add new artifact type | Moderate | 5 touchpoints (schema, prompt, validator, config, template) |
| Add new API endpoint | Moderate | 1 new file + 1 line registration |
| Modify evaluation criteria | Easy | Edit rubrics.json (no code) |
| Modify reference facts | Easy | Edit reference/*.json (no code) |
| Add new deterministic check | Moderate | Add function in evaluate.py or validator.py |
| Change the retry strategy | Easy | Modify constants in retry_loop.py |

---

## Where Abstractions Are Strong

### 1. LLM Provider Abstraction
**Pattern:** Abstract base class + factory

```python
class LLMProvider(ABC):
    @abstractmethod
    def generate(self, system_prompt, user_prompt, schema) -> dict: ...

class OpenAIProvider(LLMProvider): ...
class GeminiProvider(LLMProvider): ...

def get_provider(artifact_type, override=None) -> LLMProvider | NanoBananaProvider: ...
```

**Strength:** Adding a new provider (e.g., Claude, Mistral, Llama) requires:
1. Subclass `LLMProvider` with `generate()` method
2. Register in `get_provider()` factory
3. Add to `config.json` providers section

Business code never references providers directly — only through the factory.

### 2. Config-Driven Routing
**Pattern:** JSON configuration maps artifact types to providers

```json
"artifact_provider_map": {
    "plan": "gemini",
    "overview": "gemini",
    "judge": "openai",
    "infographic_image": "nano_banana"
}
```

**Strength:** Swapping which model handles which artifact is a single config change. No code deployment needed.

### 3. Schema-as-Contract
**Pattern:** JSON Schemas define the interface between generation and consumption

**Strength:** Adding a new field to an artifact requires updating the schema, and all validation automatically enforces the new structure. The schema acts as the contract between the generator (LLM output) and the consumer (template/endpoint).

### 4. Prompt Templates as Files
**Pattern:** Prompts stored as `.md` files, loaded at runtime

**Strength:** Prompt iteration requires only file edits. Prompts can be version-controlled, reviewed, and A/B tested independently of code.

### 5. Blueprint-Based API
**Pattern:** Flask blueprints for each endpoint, registered centrally

**Strength:** New endpoints are self-contained files. Registration is a single line in `app.py`.

---

## Where Coupling Exists

### 1. Generator ↔ Prompt Variable Names
The `generator.py` code hardcodes which variables to inject into which prompts:
```python
prompt = prompt_text.replace("{{technique_name}}", technique_name)
prompt = prompt_text.replace("{{plan_json}}", json.dumps(plan, indent=2))
```

**Impact:** Adding a new variable to a prompt requires a code change in `generator.py`, not just a prompt file change.

**Mitigation opportunity:** A generic template context dictionary would decouple this.

### 2. PROMPT_MAP Hardcoding
The mapping from artifact type to prompt file is a dict in `generator.py`:
```python
PROMPT_MAP = {"plan": "planner_prompt.md", "overview": "overview_prompt.md", ...}
```

**Impact:** Adding a new artifact type requires updating this dict in Python code.

**Mitigation opportunity:** Move to `config.json` alongside `artifact_provider_map`.

### 3. Validator ↔ Artifact Types
Content validation rules are hardcoded per artifact type with `if` statements in `validator.py`:
```python
def validate_artifact(artifact_type, data):
    if artifact_type == "overview":
        return validate_overview(data)
    elif artifact_type == "math_deep_dive":
        return validate_math_deep_dive(data)
    ...
```

**Impact:** Adding a new artifact type requires adding a new validation function and dispatch clause.

### 4. HTML Template ↔ Artifact Structure
The `technique.html` template directly references artifact field names:
```html
{{ overview.summary | markdown }}
{{ overview.markdown | md_section }}
```

**Impact:** Changing artifact field names requires template updates. This is expected for a template system but worth noting.

### 5. Image Provider Separation
`NanoBananaProvider` does not extend `LLMProvider` — it has a different interface (`generate_image()` vs `generate()`).

**Impact:** Image generation follows a separate code path from text generation. A unified provider interface would simplify the pipeline.

### 6. API Prompts Inline vs. File
The 4 API endpoint prompts are string constants in Python files, while pipeline prompts are in `prompts/`:

| Location | Prompt |
|----------|--------|
| `pipeline/prompts/*.md` | Pipeline generation prompts |
| `api/math_tutor.py` (inline) | Math tutor system prompt |
| `api/compare.py` (inline) | Comparison system prompt |
| `api/study_plan.py` (inline) | Study plan system prompt |
| `api/adapt_code.py` (inline) | Code adapter system prompt |

**Impact:** Inconsistent prompt management — pipeline prompts are easy to iterate on; API prompts require code changes.

---

## How Easy Is It to Add...

### New Pipeline Stage
**Difficulty:** Moderate
**Steps:**
1. Create prompt template in `prompts/`
2. Add schema in `schemas.py`
3. Add entry to `PROMPT_MAP` in `generator.py`
4. Add provider mapping in `config.json`
5. Add validation function in `validator.py`
6. Add generation call in `generate.py` orchestrator
7. Add template section in `technique.html`

**Bottleneck:** Steps 3 and 6 require Python code changes, not just configuration.

### New Prompt Type
**Difficulty:** Easy
**Steps:**
1. Create `.md` file in `prompts/`
2. Use `{{variable}}` placeholders
3. Register in `PROMPT_MAP` if it's a pipeline prompt

### New Artifact Type
**Difficulty:** Moderate (same as new pipeline stage above — artifact types are pipeline stages)

### New Evaluation Method
**Difficulty:** Easy to Moderate
- **New deterministic check:** Add check function in `evaluate.py`, integrate into `run_deterministic_checks()` — Easy
- **New judge criterion:** Add to `rubrics.json` criteria — Easy (no code)
- **New reference data:** Add to `reference/<slug>.json` — Easy (no code)
- **New evaluation stage:** Insert between existing stages in `evaluate_single_artifact()` — Moderate

### New Output Format
**Difficulty:** Moderate
- **New HTML template:** Create Jinja2 template, register in `publish.py` — Moderate
- **New export format (e.g., PDF, EPUB):** Would require a new publisher module — High
- **New API response format:** Adjust endpoint response structure — Easy

---

## Best Extensibility Seams

These are the points where the architecture is most amenable to extension:

### 1. `config.json` — The Control Plane
This file is the single richest extension point. Adding algorithms, changing providers, and adjusting artifact routing all happen here.

### 2. `content/rubrics.json` — Evaluation Tuning
Criteria weights, pass threshold, and per-artifact criteria selection are all configurable without code changes.

### 3. `content/reference/*.json` — Knowledge Anchoring
Reference facts and forbidden claims can be updated, expanded, or corrected without touching any code.

### 4. `pipeline/prompts/*.md` — Prompt Iteration
Prompts can be refined, expanded, or completely rewritten without code changes (as long as variable names stay the same).

### 5. `LLMProvider` ABC — Provider Addition
Clean abstract interface makes adding new providers straightforward.

---

## What Currently Blocks Extensibility

1. **No plugin system** — New artifact types require changes in multiple files (schema, validator, generator, config, template). A plugin architecture could bundle these.

2. **No prompt variable registry** — Variables injected into prompts are hardcoded per prompt type. A declarative variable mapping would make prompts fully self-describing.

3. **No evaluation plugin system** — Adding new check types requires modifying `evaluate.py` directly. A hook-based system could allow external check registration.

4. **No output format abstraction** — Publishing is HTML-only. There's no abstraction layer for alternative output formats.

5. **Image provider interface mismatch** — `NanoBananaProvider` doesn't extend `LLMProvider`, creating two parallel code paths for generation.

---

## Design Tradeoffs

### 1. Simplicity vs. Plugin Architecture
**Choice made:** Simple, explicit code over a plugin system.
**Trade-off:** Adding new types requires touching multiple files, but every extension point is obvious and traceable. No framework magic to debug.
**Assessment:** Correct choice for a project of this scale. Plugin systems add complexity that's only justified with many contributors or frequent additions.

### 2. Config-Driven vs. Code-Driven
**Choice made:** Heavy use of JSON configuration for routing and evaluation.
**Trade-off:** Easy to change behavior without code changes, but config errors are caught at runtime, not compile time.
**Assessment:** Strong choice. Configuration is the most common change vector (which model to use, which threshold to set), and JSON is readable by non-developers.

### 3. Gemini for Content, OpenAI for Judge
**Choice made:** Different providers for generation vs. evaluation.
**Trade-off:** Cross-model evaluation may catch biases that self-evaluation would miss. But it also means the judge may not understand Gemini's tendencies.
**Assessment:** Generally good practice. Using the same model to generate and evaluate creates a "grading your own homework" problem.

### 4. Sequential Pipeline vs. Parallel Generation
**Choice made:** Artifacts are generated sequentially per technique.
**Trade-off:** Simpler error handling and dependency management, but slower for large runs.
**Assessment:** Correct for a pipeline with inter-artifact dependencies (plan → content, overview → summary, spec → image). Parallelism within a technique would require careful dependency tracking.

### 5. Strict Schemas with `additionalProperties: false`
**Choice made:** No extra fields allowed in generated JSON.
**Trade-off:** Catches LLM hallucination of extra fields, but makes schema evolution harder (old artifacts won't validate against new schemas with added fields).
**Assessment:** Strong choice for a generation pipeline. LLMs often add unrequested fields; strict schemas catch this immediately.

### 6. Idempotency via Input Hashing
**Choice made:** SHA-256 hash of all inputs determines whether to regenerate.
**Trade-off:** Safe reruns and incremental updates, but any config change (even unrelated) can trigger full regeneration if included in the hash input.
**Assessment:** Good engineering practice. The hash includes the right inputs (prompt, schema, config slice, upstream data) to be useful without being too sensitive.

---

## Best Future Expansion Opportunities

### 1. Quiz Generation
**Grounded in code:** `rubrics.json` includes `"quiz"` in the `artifact_criteria_map`, and `schemas.py` comments reference quiz schemas, but quiz generation is not yet implemented in the pipeline.
**Opportunity:** Add `quiz_prompt.md`, `QUIZ_SCHEMA`, and integrate into the generation pipeline. The evaluation infrastructure already supports it.

### 2. Multi-Language Code Variations
**Grounded in code:** `code_variations` currently requires exactly 3 Python frameworks (NumPy, PyTorch, SciPy).
**Opportunity:** Extend to other languages (Julia, R, MATLAB) by making the framework list configurable and adding language-specific code execution.

### 3. Comparative Evaluation
**Grounded in code:** The judge evaluates artifacts individually, not as a set.
**Opportunity:** Add a "consistency judge" that compares all artifacts for a technique (do they use the same notation? same assumptions? same examples?).

### 4. Prompt A/B Testing
**Grounded in code:** Prompts are files loaded at runtime.
**Opportunity:** Store multiple prompt versions, generate artifacts with each, and compare judge scores to identify the best prompt for each artifact type.

### 5. Export to Additional Formats
**Grounded in code:** All content exists as structured JSON.
**Opportunity:** Add PDF export (LaTeX → PDF), EPUB, or LMS-compatible formats (SCORM/xAPI). JSON-first architecture makes this feasible.

### 6. Interactive Exercises
**Grounded in code:** The implementation artifact includes `python_examples[]` and the code runner can execute Python.
**Opportunity:** Convert static examples into interactive exercises where users modify code and see results. The code execution infrastructure already exists.

### 7. Difficulty Levels
**Grounded in code:** The plan includes `target_audience`.
**Opportunity:** Generate artifacts at multiple difficulty levels (introductory, intermediate, advanced) by varying the target_audience in the plan prompt.
