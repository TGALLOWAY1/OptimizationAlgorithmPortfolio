# Data Flow and System Diagrams

## A. High-Level System Diagram

### Mermaid Diagram

```mermaid
graph TB
    subgraph Configuration
        CONFIG[config.json<br/>Techniques, Providers, Routing]
        PROMPTS[Prompt Templates<br/>10 Jinja2 .md files]
        SCHEMAS[JSON Schemas<br/>6 schema definitions]
        RUBRICS[rubrics.json<br/>Scoring criteria & weights]
        REFS[Reference Facts<br/>8 technique .json files]
    end

    subgraph LLM Providers
        GEMINI[Gemini 3.1 Pro<br/>Text Content]
        NANO[Nano Banana Pro<br/>Image Generation]
        OPENAI[OpenAI GPT-4o<br/>API & Judge]
    end

    subgraph Pipeline Core
        GEN[Generator<br/>generator.py]
        EVAL[Evaluator<br/>evaluate.py]
        JUDGE[LLM Judge<br/>judge.py]
        RETRY[Retry Loop<br/>retry_loop.py]
        CODERUN[Code Runner<br/>code_runner.py]
    end

    subgraph Outputs
        CONTENT[Content Directory<br/>JSON + PNG artifacts]
        SITE[Static Site<br/>HTML + CSS + JS]
        METRICS[Evaluation Metrics<br/>Quality reports]
    end

    subgraph Runtime API
        FLASK[Flask Server<br/>5 LLM-powered endpoints]
    end

    CONFIG --> GEN
    PROMPTS --> GEN
    SCHEMAS --> GEN
    GEN --> GEMINI
    GEN --> NANO
    GEMINI --> GEN
    NANO --> GEN
    GEN --> CONTENT

    CONTENT --> EVAL
    RUBRICS --> JUDGE
    REFS --> JUDGE
    EVAL --> JUDGE
    JUDGE --> RETRY
    RETRY --> EVAL
    EVAL --> METRICS
    CODERUN --> EVAL

    CONTENT --> SITE
    SITE --> FLASK
    OPENAI --> FLASK
    OPENAI --> JUDGE
```

### What to notice
- **Three distinct LLM providers** serve different purposes — text, images, and runtime/judge
- **Configuration flows in from the left** — the pipeline is data-driven, not code-driven
- **The evaluation pipeline is a closed loop** — judge results feed back into retry/revision
- **Two output paths**: static site (batch) and Flask API (runtime)

### Why it matters
This diagram shows the system isn't a simple "prompt → output" pipeline. It has **feedback loops**, **multi-provider routing**, and **separation between batch generation and runtime serving**.

---

## B. Detailed Pipeline Data Flow Diagram

### Mermaid Diagram

```mermaid
flowchart TD
    START([Pipeline Start]) --> LOAD_CONFIG[Load config.json<br/>Parse CLI args]
    LOAD_CONFIG --> FOR_TECH{For each technique}

    FOR_TECH --> PLAN[Stage 1: Generate Plan<br/>planner_prompt.md → Gemini]
    PLAN --> HASH_CHECK{Input hash<br/>matches manifest?}
    HASH_CHECK -->|Yes & !force| SKIP[Skip: return cached]
    HASH_CHECK -->|No or force| CALL_LLM[Call LLM Provider]
    CALL_LLM --> VALIDATE_SCHEMA{Schema<br/>valid?}
    VALIDATE_SCHEMA -->|No| RETRY_GEN[Retry with backoff<br/>2s, 4s, 8s]
    RETRY_GEN --> CALL_LLM
    VALIDATE_SCHEMA -->|Yes| SAVE_PLAN[Save plan.json<br/>Update manifest]

    SAVE_PLAN --> ARTIFACTS[Stage 2: Generate 4 Artifacts]
    SKIP --> ARTIFACTS

    ARTIFACTS --> OV[Overview<br/>overview_prompt.md]
    ARTIFACTS --> MATH[Math Deep Dive<br/>math_prompt.md]
    ARTIFACTS --> IMPL[Implementation<br/>implementation_prompt.md]
    ARTIFACTS --> INFOS[Infographic Spec<br/>infographic_prompt.md]

    OV --> VALIDATE[Content Validation]
    MATH --> VALIDATE
    IMPL --> VALIDATE
    INFOS --> VALIDATE

    VALIDATE --> SUMMARY[Stage 3: Homepage Summary<br/>Requires overview.summary]

    SUMMARY --> IMAGES{--skip-images?}
    IMAGES -->|No| IMG_GEN[Stage 4: Generate Images<br/>Nano Banana Pro]
    IMAGES -->|Yes| NEXT_TECH

    IMG_GEN --> IMG_VAL{Image ≥ 10KB?}
    IMG_VAL -->|Yes| NEXT_TECH[Next technique]
    IMG_VAL -->|No| IMG_RETRY[Retry image generation]
    IMG_RETRY --> IMG_GEN

    NEXT_TECH --> FOR_TECH

    FOR_TECH -->|All done| MATRIX{Full run?}
    MATRIX -->|Yes| GEN_MATRIX[Stage 5: Use-Case Matrix]
    MATRIX -->|No| EVAL_CHECK

    GEN_MATRIX --> EVAL_CHECK{--evaluate?}
    EVAL_CHECK -->|Yes| EVALUATION[Stage 6: Evaluation Pipeline]
    EVAL_CHECK -->|No| PUBLISH

    EVALUATION --> PUBLISH[Stage 7: Publish Static Site]
    PUBLISH --> DONE([Pipeline Complete])
```

### What to notice
- **Idempotency check** (hash comparison) happens before every LLM call
- **Retry logic** is at the LLM call level (API failures) and at the evaluation level (content quality)
- **Dependencies flow downward**: plan → artifacts → summary → images
- **Optional stages** (images, evaluation, matrix) are flag-controlled

### Why it matters
This shows the full execution path with all branch points and retry mechanisms. It demonstrates the pipeline isn't fragile — failures at any point are handled gracefully.

---

## C. Artifact Generation Flow

### Mermaid Diagram

```mermaid
flowchart LR
    subgraph Inputs
        TECH_NAME[Technique Name]
        PROMPT_TPL[Prompt Template .md]
        SCHEMA[JSON Schema]
        PLAN_DATA[plan.json data]
    end

    subgraph Hash & Cache
        COMPUTE[Compute SHA-256<br/>of all inputs]
        MANIFEST[(manifest.json)]
        COMPUTE --> CHECK{Hash in<br/>manifest?}
        CHECK -->|Match| REUSE[Return cached artifact]
        CHECK -->|Mismatch| GENERATE
    end

    subgraph Generate
        INJECT[Inject variables<br/>into prompt template]
        PROVIDER[Select provider<br/>from config mapping]
        LLM_CALL[LLM API Call]
        SCHEMA_VAL[Schema Validation]
        CONTENT_VAL[Content Validation]
        SAVE[Save artifact .json<br/>Update manifest]

        INJECT --> PROVIDER --> LLM_CALL
        LLM_CALL --> SCHEMA_VAL
        SCHEMA_VAL -->|Fail| LLM_CALL
        SCHEMA_VAL -->|Pass| CONTENT_VAL
        CONTENT_VAL --> SAVE
    end

    TECH_NAME --> COMPUTE
    PROMPT_TPL --> INJECT
    SCHEMA --> SCHEMA_VAL
    PLAN_DATA --> INJECT

    subgraph Storage
        ARTIFACT[content/slug/type.json]
        MANIFEST_UP[manifest.json updated]
    end

    SAVE --> ARTIFACT
    SAVE --> MANIFEST_UP

    subgraph Publishing
        JINJA[Jinja2 Template<br/>technique.html]
        MD_RENDER[Markdown → HTML<br/>with LaTeX protection]
        HTML_OUT[site/slug.html]
    end

    ARTIFACT --> JINJA
    JINJA --> MD_RENDER --> HTML_OUT
```

### What to notice
- **Input hashing** creates a deterministic fingerprint of all generation inputs
- **Manifest acts as a cache** — if inputs haven't changed, generation is skipped entirely
- **Schema validation is in the retry loop** — LLM output must conform before being accepted
- **Content validation is post-schema** — catches semantic issues (word count, LaTeX, pseudocode)
- **Publishing is a separate stage** — artifacts are JSON; HTML is rendered from templates

### Why it matters
This diagram shows that every artifact has a **provenance chain**: inputs → hash → generation → validation → storage → publishing. Nothing is ad-hoc.

---

## D. Judge / Evaluation Flow

### Mermaid Diagram

```mermaid
flowchart TD
    ARTIFACT[Generated Artifact] --> S1[Stage 1: Schema Validation<br/>schema_validate.py]
    S1 -->|Fail| BLOCKED1[❌ Status: schema_invalid<br/>Pipeline stops for this artifact]
    S1 -->|Pass| S2[Stage 2: Deterministic Checks<br/>evaluate.py]

    S2 -->|Fail| BLOCKED2[❌ Status: static_check_failed]
    S2 -->|Pass| S3{Artifact type =<br/>implementation?}

    S3 -->|Yes| S3A[Stage 3: Code Execution<br/>code_runner.py]
    S3 -->|No| S4

    S3A -->|Fail| BLOCKED3[❌ Status: code_runtime_error]
    S3A -->|Pass| S4

    S4[Stage 4: LLM Judge<br/>judge.py] --> LOAD_RUBRICS[Load rubrics.json<br/>4 criteria, weights, threshold]
    LOAD_RUBRICS --> LOAD_REF[Load reference/<slug>.json<br/>key_facts, forbidden_claims]
    LOAD_REF --> JUDGE_CALL[Call GPT-4o as Judge<br/>Score 1-10 on each criterion]

    JUDGE_CALL --> SCORE{overall_score<br/>≥ 7?}
    SCORE -->|Yes| PASS[✅ Status: passed<br/>Promote to content/]
    SCORE -->|No| ATTEMPT{Attempt<br/>< 3?}

    ATTEMPT -->|Yes| REVISE[Build Revision Prompt<br/>Include critiques +<br/>revision_instructions +<br/>current score]
    REVISE --> REGEN[Re-generate artifact<br/>via LLM]
    REGEN --> S1

    ATTEMPT -->|No| FAIL[⚠️ Status: persistent_failure<br/>Log and continue]

    subgraph Judge Criteria
        FA[Factual Accuracy<br/>weight: 0.30]
        MC[Math Correctness<br/>weight: 0.30]
        CL[Clarity<br/>weight: 0.25]
        CQ[Code Quality<br/>weight: 0.15]
    end

    JUDGE_CALL -.-> FA
    JUDGE_CALL -.-> MC
    JUDGE_CALL -.-> CL
    JUDGE_CALL -.-> CQ
```

### What to notice
- **Four stages, progressively expensive**: schema (instant) → static checks (instant) → code execution (30s max) → LLM judge (API call)
- **Each stage is a gate** — failure at any stage blocks subsequent stages
- **The retry loop feeds back** — judge output (critiques, instructions) becomes input for revision
- **Reference facts constrain the judge** — it knows what must be present and what must be absent
- **Implementation artifacts get extra validation** — sandboxed code execution

### Why it matters
This is the **core quality assurance mechanism**. It shows how the system achieves reliability from an inherently non-deterministic source (LLMs). The combination of deterministic and probabilistic checks is the key architectural insight.

---

## E. Extensibility Diagram

### Mermaid Diagram

```mermaid
graph TB
    subgraph "Add New Algorithm"
        NEW_TECH[1. Add name to<br/>config.json techniques[]]
        NEW_REF[2. Create reference/<br/>new-algo.json]
        NEW_TECH --> DONE_TECH[Pipeline generates<br/>all artifacts automatically]
        NEW_REF --> DONE_TECH
    end

    subgraph "Add New Artifact Type"
        NEW_SCHEMA[1. Add schema in<br/>schemas.py]
        NEW_PROMPT[2. Create prompt in<br/>prompts/new_type.md]
        NEW_VALIDATOR[3. Add validator in<br/>validator.py]
        NEW_CONFIG[4. Add provider mapping<br/>in config.json]
        NEW_TEMPLATE[5. Add section in<br/>technique.html template]
        NEW_SCHEMA --> DONE_ART[Pipeline generates<br/>new artifact type]
        NEW_PROMPT --> DONE_ART
        NEW_VALIDATOR --> DONE_ART
        NEW_CONFIG --> DONE_ART
        NEW_TEMPLATE --> DONE_ART
    end

    subgraph "Add New LLM Provider"
        NEW_CLASS[1. Subclass LLMProvider<br/>in llm_client.py]
        NEW_FACTORY[2. Register in<br/>get_provider() factory]
        NEW_PROV_CONFIG[3. Add to config.json<br/>providers section]
        NEW_CLASS --> DONE_PROV[New provider available<br/>for any artifact type]
        NEW_FACTORY --> DONE_PROV
        NEW_PROV_CONFIG --> DONE_PROV
    end

    subgraph "Add New API Endpoint"
        NEW_BP[1. Create blueprint<br/>in api/new_endpoint.py]
        NEW_REG[2. Register in<br/>api/app.py]
        NEW_BP --> DONE_API[Endpoint live<br/>at /api/new_endpoint]
        NEW_REG --> DONE_API
    end

    subgraph "Modify Evaluation"
        MOD_RUBRICS[Edit rubrics.json<br/>criteria, weights, threshold]
        MOD_REF[Edit reference/*.json<br/>key_facts, forbidden_claims]
        MOD_CHECKS[Add checks in<br/>evaluate.py or validator.py]
        MOD_RUBRICS --> DONE_EVAL[Evaluation behavior<br/>changes immediately]
        MOD_REF --> DONE_EVAL
        MOD_CHECKS --> DONE_EVAL
    end
```

### What to notice
- **Adding a new algorithm is 2 steps** — config entry + reference file. Zero code changes.
- **Adding an artifact type is 5 steps** — but each step is isolated (schema, prompt, validator, config, template)
- **Adding an LLM provider is 3 steps** — abstract base class makes this clean
- **Evaluation tuning is configuration-only** — rubrics and references are JSON files

### Why it matters
The pipeline was designed for extensibility at the **most common extension points**. The architect anticipated what would change most often (algorithms, artifact types, providers) and made those the easiest to modify.

---

## Diagram Summary for Presentation Use

| Diagram | Best used for | Slide position |
|---------|---------------|---------------|
| A. High-level system | Opening context, "what are we looking at" | Early (slide 3-4) |
| B. Pipeline data flow | Core walkthrough, step-by-step | Middle (slide 6-8) |
| C. Artifact generation | Explaining how content is created | Middle (slide 9-10) |
| D. Judge/evaluation | Explaining quality assurance | Late middle (slide 11-13) |
| E. Extensibility | Future potential, design quality | Near end (slide 15-16) |
