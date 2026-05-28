# Flow Diagrams

> Mermaid + text diagrams of the system's key flows. Render in any Mermaid-aware viewer.
> Last updated: 2026-05-28.

## Content generation pipeline (single-shot)

```mermaid
flowchart TD
  A[python -m pipeline.generate] --> B[load config.json]
  B --> C{for each technique}
  C --> D[generate_plan -> plan.json]
  D --> E[generate_artifact x4\noverview, math, implementation, infographic_spec]
  E --> F[homepage_summary]
  F --> G{--skip-images?}
  G -- no --> H[infographic.png + preview.png\nNanoBanana]
  G -- yes --> I[playground_config]
  H --> I
  I --> C
  C -- done --> J[knowledge_graph.json]
  J --> K{--evaluate?}
  K -- yes --> L[schema -> static -> code -> judge -> revise]
  K -- no --> M[generated/ ready]
  L --> M
```

Each `generate_*` step: render `{{var}}` prompt → `get_provider(key)` → `generate_with_retry` (validate + ≤3 retries) → write JSON + manifest hash. Validation errors at this stage are logged, not blocking.

## Publish + serve

```mermaid
flowchart LR
  G[generated/] --> P[pipeline.publish]
  P --> S[site/*.html + images]
  S --> GP[GitHub Pages\nstatic only]
  S --> FL[api/app.py\nstatic + /api/*]
  FL -->|per request| GEM[(Gemini)]
  GP -.->|/api/* 404| X[interactive tools broken]
```

Note: CI publishes the **placeholder** (no generated content committed), so the Pages box is effectively the placeholder page.

## Multi-agent content pipeline (independent)

```mermaid
flowchart TD
  IN[raw_input] --> I[intake +IntakeGate]
  I --> R[research]
  R --> O[outline +OutlineGate]
  O --> D[draft +DraftGate]
  D --> TR[technical_review +TechnicalReviewGate]
  TR --> ED[editor]
  ED --> RP[repurposing optional]
  RP --> QA[publishing_qa optional +FinalQAGate]
  QA --> OUT[outputs/runs/&lt;run_id&gt;/]
```

Gate failure with attempts left → NEEDS_REVISION (feedback fed back, stage re-run). Exhausted gate → SKIPPED (optional) or FAILED. Resume skips already-succeeded stages.

## Request flow — an API endpoint (e.g. /api/compare)

```mermaid
sequenceDiagram
  participant U as Browser
  participant F as Flask (api/app.py)
  participant G as Gemini
  U->>F: POST /api/compare {slug_a, slug_b}
  F->>F: validate slugs + read both techniques' artifacts
  F->>G: get_provider("compare").generate(prompt, COMPARE_SCHEMA)
  G-->>F: JSON (schema-enforced)
  F-->>U: 200 comparison  | 400 bad input | 404 unknown | 500 error
```

## LLM-as-judge (tool-using)

```mermaid
flowchart TD
  A[evaluate_artifact] --> B[build tool-using judge prompt]
  B --> C[generate_with_tools max 5 turns]
  C --> D{model calls a tool?}
  D -- yes --> E[dispatch: run_python_code / check_equation /\nlookup_reference / verify_imports]
  E --> C
  D -- no --> F[parse JSON -> validate JUDGE_OUTPUT_SCHEMA]
  F --> G{passed >= threshold?}
  G -- no --> H[build_revision_prompt -> revise -> re-judge\n(retry_loop, max 3)]
  G -- yes --> I[promote]
```

## Diagram maintenance
Update these when a pipeline stage, endpoint, or routing rule changes. They are intentionally coarse — see the architecture docs for file:line detail.
