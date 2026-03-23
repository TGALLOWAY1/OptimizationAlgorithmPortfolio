# Judge Method and Evaluation

## Overview

The evaluation system is a **4-stage quality pipeline** that combines deterministic checks with LLM-based judgment to validate generated educational content. It is the most architecturally interesting part of the system.

**Core question it answers:** "Is this generated content good enough to publish?"

---

## What Is Being Judged

Every generated JSON artifact (overview, math_deep_dive, implementation, infographic_spec) is evaluated for:
- **Structural correctness** — Does it match the expected JSON Schema?
- **Content quality** — Does it meet minimum word counts, contain required elements (LaTeX, pseudocode), avoid off-topic content?
- **Code correctness** — Do Python examples actually run? Are dependencies declared?
- **Factual accuracy** — Are claims about the algorithm correct? Are forbidden misconceptions absent?
- **Pedagogical quality** — Is the content clear, well-organized, and progressively built?

---

## The 4-Stage Evaluation Pipeline

### Stage 1: Schema Validation (Deterministic)

**Code:** `pipeline/schema_validate.py` → `validate_schema()`

**What it does:**
- Validates artifact JSON against the strict JSON Schema defined in `pipeline/schemas.py`
- Checks required fields, types, array lengths, string minimums, `additionalProperties: false`

**Result:** `{passed: bool, errors: [str]}`

**Controlling:** Yes — schema failure blocks all subsequent stages.

**Cost:** Zero (no API calls, instant)

---

### Stage 2: Deterministic Static Checks (Deterministic)

**Code:** `pipeline/evaluate.py` → `run_deterministic_checks()`

**What it checks:**

| Check | Logic | Applies To |
|-------|-------|------------|
| Placeholder detection | Regex for TODO, TBD, FIXME, XXX, [INSERT, PLACEHOLDER | All artifacts |
| LaTeX balance | Count `$` pairs, `$$` pairs, `\(` vs `\)` | math_deep_dive, overview, implementation |
| Duplicated paragraphs | Paragraphs >50 chars appearing twice | All artifacts |
| Content validation | Word count ≥800, LaTeX presence, pseudocode keywords, off-topic terms, technique-specific terms | Type-specific (via `validator.py`) |

**Placeholder patterns (regex):**
```python
PLACEHOLDER_PATTERNS = [
    r"\bTODO\b", r"\bTBD\b", r"\bFIXME\b", r"\bXXX\b",
    r"\[INSERT\b", r"\bPLACEHOLDER\b",
]
```

**Off-topic detection:**
```python
OFF_TOPIC_HINTS = {
    "technical co-founder", "startup", "venture capital", "go-to-market",
    "seed round", "product roadmap", "customer acquisition",
}
```

**Result:** `{passed: bool, errors: [str]}`

**Controlling:** Yes — static check failure blocks judge evaluation.

**Cost:** Zero (no API calls, instant)

---

### Stage 3: Code Execution (Deterministic, Implementation Only)

**Code:** `pipeline/code_runner.py` → `validate_code_artifact()`

**What it checks:**

1. **Dependency allowlist** — Are declared `runtime_dependencies` in the allowed set?
   ```python
   ALLOWED_LIBRARIES = {
       "numpy", "scipy", "pandas", "matplotlib", "scikit-learn", "sklearn",
       "torch", "tensorflow", "math", "random", "itertools", "functools",
       "collections", "typing", "copy", "json", "os", "sys", "time"
   }
   ```

2. **Import extraction** — AST-parse each `python_examples[]` entry to find imports

3. **Undeclared import detection** — Imports used in code but not listed in `runtime_dependencies`

4. **Blocked import detection** — Imports not in `ALLOWED_LIBRARIES` (e.g., `requests`, `subprocess`)

5. **Code execution** — Run each example in a subprocess with 30-second timeout
   - Captures stdout (≤5000 chars) and stderr (≤5000 chars)
   - Returns exit code

**Result:** `{passed: bool, results: [{exit_code, stdout, stderr}], dependency_check: {}, undeclared_imports: [], blocked_imports: []}`

**Controlling:** Yes — code execution failure blocks judge evaluation.

**Cost:** CPU time only (subprocess execution, no API calls)

---

### Stage 4: LLM Judge + Retry Loop (Probabilistic)

**Code:** `pipeline/judge.py` → `evaluate_artifact()`, `pipeline/retry_loop.py` → `retry_loop()`

#### 4a. Rubric Loading

**File:** `content/rubrics.json`

```json
{
  "pass_threshold": 7,
  "criteria": {
    "factual_accuracy": {
      "weight": 0.30,
      "description": "Are all factual claims accurate and verifiable? Does the content correctly describe the algorithm's behavior, properties, and applications?"
    },
    "math_correctness": {
      "weight": 0.30,
      "description": "Are mathematical expressions, derivations, and notation correct? Are equations properly formatted and steps logically sound?"
    },
    "clarity": {
      "weight": 0.25,
      "description": "Is the content clear, well-organized, and pedagogically effective? Does it build understanding progressively?"
    },
    "code_quality": {
      "weight": 0.15,
      "description": "Is the code correct, readable, well-documented, and pedagogically aligned with the explanatory text?"
    }
  },
  "artifact_criteria_map": {
    "overview": ["factual_accuracy", "clarity"],
    "math_deep_dive": ["factual_accuracy", "math_correctness", "clarity"],
    "implementation": ["factual_accuracy", "code_quality", "clarity"],
    "infographic_spec": ["factual_accuracy", "clarity"]
  }
}
```

**Key design:** Not all criteria apply to all artifact types. An overview is scored on factual_accuracy and clarity, not math_correctness or code_quality.

#### 4b. Reference Loading

**Files:** `content/reference/<slug>.json` (one per technique)

```json
{
  "name": "Bayesian Optimization",
  "key_facts": [
    "Uses a surrogate model (typically Gaussian Process) to model the objective function",
    "Acquisition function (e.g., Expected Improvement, UCB) guides the next sampling point",
    "Designed for expensive-to-evaluate black-box functions",
    "..."
  ],
  "forbidden_claims": [
    "Requires gradient information",
    "Guarantees finding the global optimum",
    "Scales well to high-dimensional spaces (>20 dimensions) without modification",
    "Is a type of evolutionary algorithm"
  ]
}
```

**Purpose:** Anchors the judge with ground truth. The judge must verify key facts appear and forbidden claims do not.

#### 4c. Judge Prompt Construction

**Code:** `pipeline/judge.py` → `_build_judge_prompt()`

The judge prompt is **dynamically assembled** (not a template file). It includes:

1. **System prompt:**
   - Role: "expert evaluator of educational content about optimization algorithms"
   - Task: score 1-10 on each criterion
   - Pass condition: `overall_score >= pass_threshold`
   - Instruction to provide critiques and revision instructions on failure

2. **User prompt:**
   - Artifact type
   - Criteria descriptions (from rubrics)
   - Pass threshold
   - Reference facts (if available)
   - Forbidden claims (if available)
   - Artifact content (truncated to 8000 chars)

#### 4d. Judge Output Schema

```json
{
  "passed": true,
  "overall_score": 8,
  "criteria_scores": {
    "factual_accuracy": 9,
    "math_correctness": 8,
    "clarity": 7,
    "code_quality": 8
  },
  "critiques": [],
  "revision_instructions": []
}
```

**Score range:** 1-10 per criterion, 1-10 overall

**Pass threshold:** 7 (configurable in `rubrics.json`)

**Key output fields on failure:**
- `critiques[]` — What's wrong (e.g., "Missing explanation of acquisition function trade-offs")
- `revision_instructions[]` — What to fix (e.g., "Add a comparison between Expected Improvement and Upper Confidence Bound")

#### 4e. Retry / Revision Loop

**Code:** `pipeline/retry_loop.py` → `retry_loop()`

**Flow:**
```
Attempt 1:
  Schema validation → Judge evaluation → Pass? ✅ Done
                                        → Fail? → Revision

Attempt 2:
  Build revision prompt (include score, critiques, instructions)
  → Re-generate artifact via LLM
  → Schema validation → Judge evaluation → Pass? ✅ Done
                                          → Fail? → Revision

Attempt 3:
  Build revision prompt (include latest score, critiques, instructions)
  → Re-generate artifact via LLM
  → Schema validation → Judge evaluation → Pass? ✅ Done
                                          → Fail? ⚠️ Persistent failure
```

**Max attempts:** 3 (configurable)

**Revision prompt construction** (`build_revision_prompt()`):
- System: "Revise this artifact based on the improvement instructions. Maintain the same JSON structure."
- User: "Current score: 5/10. Critiques: [...]. Revision instructions: [...]. Current artifact: {truncated content}"

**Result structure:**
```json
{
  "artifact": {...},
  "status": "passed" | "persistent_failure",
  "attempts": 2,
  "judge_history": [
    {"attempt": 1, "stage": "judge", "result": {"passed": false, "overall_score": 5, ...}},
    {"attempt": 2, "stage": "judge", "result": {"passed": true, "overall_score": 8, ...}}
  ]
}
```

---

## How Judge Results Are Consumed

1. **Artifact promotion:** Passing artifacts are written to `content/<slug>/<type>.json`
2. **Metrics recording:** All results saved to `content/evaluations/` with timestamps
3. **Log recording:** Detailed per-artifact logs saved to `content/logs/evaluation/`
4. **Quality report:** Published as `site/quality-report.html` with pass/fail badges and attempt counts
5. **Pipeline continuation:** Persistent failures are logged but don't crash the pipeline; other techniques continue

---

## Strengths of the Judge Method

1. **Multi-layered defense** — Cheap deterministic checks filter obvious issues before expensive LLM calls
2. **Reference-grounded** — Judge decisions are anchored by curated key facts and forbidden claims, not pure LLM opinion
3. **Actionable feedback** — Critiques and revision instructions are specific enough to guide re-generation
4. **Configurable** — Criteria weights, pass threshold, and per-artifact criteria can be tuned via JSON
5. **Transparent** — Full judge history is logged, enabling audit of quality decisions
6. **Code execution** — Implementation artifacts are actually run, not just reviewed
7. **Artifact-appropriate criteria** — Not all criteria apply to all types (overview doesn't need code_quality score)

---

## Limitations of the Judge Method

1. **LLM judge is probabilistic** — Same artifact may receive different scores on different runs
2. **8000 char truncation** — Long artifacts may have issues in later sections that the judge never sees
3. **No inter-artifact consistency check** — Judge evaluates artifacts individually, not as a coherent set
4. **Judge uses same model as API** — GPT-4o judges content often generated by Gemini; cross-model evaluation may have blind spots
5. **Criteria weights exist but aren't used** — Weights (0.30, 0.30, 0.25, 0.15) are defined in rubrics but the judge prompt asks for a holistic `overall_score`, not a weighted average
6. **Revision may drift** — Revision prompts include the full current artifact; revisions could change parts that were already correct
7. **No human-in-the-loop** — The pipeline has no mechanism for human review or override of judge decisions
8. **Code execution is local** — No true sandboxing; malicious generated code could theoretically affect the host system (mitigated by allowed library list)

---

## How Trustworthy Is the Method?

**For structural/syntactic issues:** Very trustworthy. Schema validation and deterministic checks are deterministic and well-tested.

**For content quality:** Moderately trustworthy. The LLM judge with reference facts catches factual errors and missing content, but:
- Scores may vary across runs
- Truncation may miss issues
- The judge is one model's opinion, not ground truth

**For code correctness:** Highly trustworthy for basic correctness (runs without errors). Less trustworthy for algorithmic correctness (code may run but compute the wrong thing).

**Overall:** The multi-stage approach is significantly more trustworthy than any single method. The combination of deterministic gates + reference-grounded LLM judge + retry loop produces meaningfully better content than unvalidated LLM output.

---

## How to Explain the Judge Method on a Slide

### One-Slide Version

**Title:** "4-Stage Quality Pipeline: From Structure to Semantics"

**Content:**

> Every generated artifact passes through 4 quality gates before publishing:
>
> 1. **Schema Validation** — Does the output match the expected JSON structure? (instant, deterministic)
> 2. **Static Checks** — Are there placeholders, unbalanced LaTeX, duplicated paragraphs, or off-topic content? (instant, deterministic)
> 3. **Code Execution** — Do the Python examples actually run? Are imports safe? (30s max, sandboxed)
> 4. **LLM Judge** — Is the content factually accurate, mathematically correct, clear, and well-coded? Scored 1-10 against curated reference facts. (GPT-4o, rubric-based)
>
> If the judge fails an artifact (score < 7/10), the system automatically extracts critiques and revision instructions, re-generates the content, and re-evaluates — up to 3 total attempts.

### Two-Slide Version

**Slide 1:** Show the 4 stages as a funnel diagram (wide at top, narrow at bottom). Each stage filters out more issues. Label each stage with cost: free → free → CPU → API call.

**Slide 2:** Show the retry loop as a circular flow: Generate → Judge → Score < 7 → Extract Critiques → Revision Prompt → Re-Generate → Re-Judge. Include a real example of critiques and revision instructions from a judge output.
