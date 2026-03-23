# Executive Overview: Optimization Algorithm Portfolio

## What It Is

The **Optimization Algorithm Portfolio** is an automated educational content generation platform that produces comprehensive, publication-ready learning materials for 8 mathematical optimization algorithms. It combines a multi-provider LLM pipeline, automated quality evaluation, interactive Flask API, and static site publishing into a single end-to-end system.

**In one sentence:** A config-driven pipeline that uses LLMs to generate, validate, judge, revise, and publish structured educational content about optimization algorithms — with zero manual content authoring.

---

## The Problem It Solves

Creating high-quality educational content about mathematical optimization is expensive:

- **Subject matter expertise** is required for correctness (equations, derivations, algorithm behavior)
- **Multiple artifact types** are needed (overviews, math deep dives, implementation guides, infographics, quizzes)
- **Consistency** across 8 algorithms is hard to maintain manually
- **Quality assurance** requires reviewing math, code, and prose independently
- **Updates** require re-authoring across all artifact types

This pipeline automates the entire workflow: generation, validation, judgment, revision, and publishing.

---

## Who It Is For

- **Learners** studying optimization algorithms (the end-user audience)
- **Educators** who want structured, validated content without manual authoring
- **Developers** interested in LLM pipeline architecture patterns

---

## What Goes In

| Input | Source |
|-------|--------|
| 8 technique names | `pipeline/config.json` |
| 10 prompt templates | `pipeline/prompts/*.md` |
| 6 JSON Schemas | `pipeline/schemas.py` |
| Provider configuration | `pipeline/config.json` |
| Scoring rubrics | `content/rubrics.json` |
| Reference fact sheets | `content/reference/*.json` (8 files) |

---

## What Comes Out

| Output | Format | Count |
|--------|--------|-------|
| Learning plans | JSON | 8 |
| Algorithm overviews | JSON → HTML | 8 |
| Math deep dives | JSON → HTML | 8 |
| Implementation guides | JSON → HTML | 8 |
| Infographic specifications | JSON → HTML | 8 |
| Homepage summaries | JSON → HTML | 8 |
| Infographic images | PNG | 8 |
| Preview thumbnails | PNG | 8 |
| Use-case comparison matrix | JSON → HTML | 1 |
| Quality evaluation report | JSON → HTML | 1 |
| Complete static website | HTML + CSS + JS | ~15 pages |

**Total: 65+ generated artifacts from a single pipeline run.**

---

## What Makes It Technically Interesting

### 1. Multi-Stage Quality Pipeline
Content doesn't just get generated — it gets **validated, judged, revised, and re-judged** through a 4-stage evaluation pipeline:
- Schema validation (structural)
- Deterministic static checks (LaTeX balance, placeholder detection, off-topic detection)
- Code execution (runs Python examples in sandboxed subprocess)
- LLM judge evaluation (rubric-based scoring against reference facts)

### 2. Config-Driven Architecture
Everything is configuration, not code:
- Techniques → `config.json`
- Artifact-to-provider mapping → `config.json`
- Prompt templates → `prompts/*.md`
- Scoring criteria → `rubrics.json`
- Reference facts → `reference/*.json`

Adding a new algorithm or swapping an LLM provider requires zero code changes.

### 3. Intelligent Retry Loop
When the LLM judge fails an artifact (score < 7/10), the system automatically:
1. Extracts critiques and revision instructions from the judge
2. Constructs a revision prompt with the score and feedback
3. Re-generates the artifact
4. Re-evaluates (up to 3 total attempts)

### 4. Multi-Provider LLM Routing
Different artifact types route to different LLM providers:
- **Gemini 3.1 Pro** → text content (plans, overviews, math, implementation)
- **Nano Banana Pro (Gemini 3.1 Flash)** → image generation (infographics, thumbnails)
- **OpenAI GPT-4o** → API endpoints and judge evaluation

### 5. Idempotent Generation with Manifest Tracking
Every artifact's inputs are SHA-256 hashed. The pipeline skips regeneration when inputs haven't changed — enabling safe reruns and incremental updates.

### 6. Full Interactive Web Application
Beyond static content, the site includes live LLM-powered features:
- Algorithm recommender (describe your problem → get algorithm suggestions)
- Algorithm comparison (head-to-head pros/cons analysis)
- Math tutor (highlight an equation → get an explanation)
- Study plan generator (describe your background → get a personalized learning roadmap)
- Code adapter (convert code between NumPy/PyTorch/SciPy frameworks)

---

## Why the Pipeline Architecture Matters

This isn't "call an LLM and dump the output." It's a **production-grade content pipeline** with:

- **Separation of concerns**: generation, validation, evaluation, publishing are independent stages
- **Deterministic + probabilistic quality gates**: schema checks catch structure issues; LLM judge catches content issues
- **Feedback loops**: judge output drives revision, not just pass/fail
- **Reproducibility**: manifest hashing, input tracking, provenance metadata
- **Extensibility**: abstract base classes, factory patterns, config-driven routing

The architecture demonstrates how to build reliable, repeatable, high-quality content systems on top of inherently non-deterministic LLM outputs.

---

## Key Numbers

| Metric | Value |
|--------|-------|
| Optimization algorithms covered | 8 |
| Artifact types per algorithm | 6-8 |
| Total generated artifacts | 65+ |
| Prompt templates | 10 |
| JSON Schemas | 6 |
| LLM providers | 3 |
| API endpoints | 5 |
| Test cases (all mocked, no API keys) | 70+ |
| Judge pass threshold | 7/10 |
| Max retry attempts | 3 |
| Estimated pipeline cost | $4-10 in API credits |
