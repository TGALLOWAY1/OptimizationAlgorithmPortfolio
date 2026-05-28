# Configuration & Environment

> How the project is configured, what env vars it needs, and how it deploys.
> Last updated: 2026-05-28.

## Environment variables

| Variable | Required for | Used by | Notes |
|---|---|---|---|
| `GEMINI_API_KEY` | All LLM generation + all API endpoints | `pipeline/llm_client.py:85-86` (every provider) | **The only key actually used.** All three providers (`gemini`, `gemini_flash`, `nano_banana`) read it (`config.json:27,31,35`). |
| `OPTIMIZATION_PORTFOLIO_GENERATED_ROOT` | Optional | `pipeline/paths.py:17-31` | Overrides the `generated/` output root. Note: `build_site.py` does **not** honor it (uses a hardcoded path). |
| `PORT` | Optional | `api/app.py:64`, `pipeline/recommender_api.py:104` | Flask listen port, default 5000. |

> **Stale doc warning:** `SETUP.md` and `CLAUDE.md` instruct setting `OPENAI_API_KEY` and testing OpenAI. **OpenAI is not used anywhere** — it is not in `requirements.txt` and there is no OpenAI provider in `pipeline/llm_client.py`. Ignore those instructions. See `docs/04-quality/KNOWN_ISSUES.md`.

Env vars load from a `.env` file via `python-dotenv` (gitignored). Tests require no keys (all LLM calls are mocked).

## `pipeline/config.json` — the central config

| Key | Purpose |
|---|---|
| `topic` | Domain framing — name "MCTS Strategy Portfolio", domain, expert/curriculum roles. Injected into prompts via `load_topic()`. |
| `techniques` | The 8 MCTS techniques generated (`config.json:8-17`). |
| `artifact_types` | Per-technique artifacts: `overview`, `math_deep_dive`, `implementation`, `infographic_spec` (`config.json:18-23`). |
| `providers` | 3 Gemini model definitions, each → `GEMINI_API_KEY` (`config.json:24-37`). |
| `technique_hints` | Per-technique keyword lists used by `validator.py` off-topic detection (`config.json:38-47`). |
| `implementation_disallowed_terms` | Currently empty `{}` (`config.json:48`) — the disallowed-term validator branch is a no-op. |
| `artifact_provider_map` | Maps 23 artifact/endpoint keys → provider name (`config.json:49-73`). This drives `get_provider()` routing. |

### Provider routing summary (`artifact_provider_map`)

- **`gemini_flash`** (cheaper): plan, overview, math_deep_dive, implementation, infographic_spec, homepage_summary, knowledge_graph, playground_config, and agent_intake/research/outline/repurposing/publishing_qa
- **`gemini`** (pro): recommender, math_tutor, compare, study_plan, adapt_code, judge, and agent_draft/technical_review/editor
- **`nano_banana`** (image): infographic_image

## Dependencies (`requirements.txt`)

```
python-dotenv>=1.0.0   google-genai>=1.0.0   jsonschema>=4.0.0
jinja2>=3.0.0          markdown>=3.0.0       Pillow>=10.0.0
flask>=3.0.0           flask-cors>=4.0.0     pytest>=7.0.0
```

> No `openai` dependency — confirming the OpenAI references in SETUP.md/CLAUDE.md are stale.

### Fresh-container gotcha (verified 2026-05-28)

On a clean container, pytest collection can panic with `pyo3_runtime.PanicException: No module named '_cffi_backend'`. The system `cryptography` (pulled in transitively by `google-genai`) needs `cffi`. Fix:

```bash
pip install cffi
```

This is an environment quirk, not a code defect.

## On-disk layout (`pipeline/paths.py`)

| Path | Contents | Tracked? |
|---|---|---|
| `content/reference/<slug>.json`, `content/rubrics.json` | Source inputs for the judge (key facts, forbidden claims, rubrics) | **Tracked** |
| `generated/techniques/<slug>/` | Per-technique JSON artifacts + PNGs + `manifest.json` | gitignored |
| `generated/knowledge_graph.json`, `generated/use_case_matrix.json` | Cross-technique data | gitignored |
| `generated/evaluations/`, `generated/logs/`, `evaluation_latest_*.json` | Evaluation outputs | gitignored |
| `outputs/runs/<run_id>/` | Multi-agent pipeline run state + stage JSON + markdown | gitignored |
| `site/` | Published static HTML + `site/images/<slug>/` | gitignored |

`.gitignore` excludes: `.env`, `.venv/`, `site/`, `generated/`, `outputs/`, `content/techniques/`, `content/evaluation_metrics.json`, `content/use_case_matrix.json`, plus the usual Python caches.

## Deployment (`.github/workflows/pages.yml`)

- **Trigger:** push to `main`/`master`, or manual `workflow_dispatch`.
- **Build job:** checkout → Python 3.11 → `pip install -r requirements.txt` → `python build_site.py` → upload `site/` as a Pages artifact.
- **Deploy job:** `actions/deploy-pages@v4` to the `github-pages` environment.

> **Critical deployment reality:** The workflow never runs `pipeline.generate` (no API keys in CI) and `generated/` is gitignored. So `build_site.py` finds no content and publishes the **placeholder landing page** (`build_site.py:42-116`) — static cards with "Coming Soon" badges, no interactive widgets. The full content site and all `/api/*`-backed features (recommend, compare, study_plan, math_tutor, adapt_code) only work when running the Flask app locally with generated content present. See `docs/02-architecture/INTEGRATIONS.md` and `docs/04-quality/KNOWN_ISSUES.md`.
