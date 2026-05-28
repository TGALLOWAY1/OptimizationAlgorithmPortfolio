# Decision Log

> Significant decisions, reconstructed from git history + code evidence. Items marked *(inferred)* are deduced from commits/code, not from a written ADR at the time.
> Last updated: 2026-05-28.

---

# Decision: Retarget the platform from numerical optimization to MCTS
- **Date:** Pre-2026-05-28 (commit `1637986` "Retarget pipeline from optimization algorithms to MCTS strategies")
- **Status:** Accepted (migration incomplete — see Consequences)
- **Context:** The platform originally covered 8 numerical-optimization algorithms (Bayesian Opt, GA, SA, PSO, Gradient Descent, Nelder-Mead, CMA-ES, DE). A prior decision had made the pipeline topic-agnostic via config (`0f860cb` "Make content pipeline topic-agnostic via config-driven domain"), enabling the switch.
- **Decision:** Change the topic to MCTS strategies via `config.json` (techniques, schema enums, technique hints).
- **Why:** Demonstrate the config-driven design on a fresh, advanced domain.
- **Alternatives considered:** *(inferred)* Keep optimization; add MCTS as a second topic.
- **Consequences:** `config.json` + `schemas.py` updated, but templates (playground, knowledge-graph legend), the judge revision prompt, several docs, and test fixtures were left on the optimization domain → the 6 failing tests, the broken playground, and the gray knowledge graph (see KNOWN_ISSUES #1/#2/#4).
- **Related files:** `pipeline/config.json`, `pipeline/schemas.py`, `pipeline/templates/*`.

# Decision: Replace OpenAI with Gemini for all LLM calls
- **Date:** Pre-2026-05-28 (commit `34c7930` "Replace all OpenAI services with Gemini")
- **Status:** Accepted
- **Context:** Earlier design routed some artifacts to OpenAI gpt-4o and others to Gemini/Nano Banana.
- **Decision:** Route everything to Google Gemini — `gemini` (pro), `gemini_flash`, `nano_banana` (image) — all on one `GEMINI_API_KEY`. Removed the OpenAI dependency.
- **Why:** *(inferred)* Single vendor/key simplicity; image + text on one platform.
- **Consequences:** `requirements.txt` has no `openai`; the `LLMProvider` ABC remains for extensibility but only Gemini providers exist. `SETUP.md`/`WOW_FACTOR_ANALYSIS.md`/`CLAUDE.md` still referenced OpenAI (stale — KNOWN_ISSUES #5; root CLAUDE.md corrected during this docs project). Single-vendor availability risk (RISK_REGISTER R6).
- **Related files:** `pipeline/llm_client.py`, `pipeline/config.json:24-37`.

# Decision: Tool-calling LLM judge + asymmetric model routing
- **Date:** Pre-2026-05-28 (commit `94e5f8e` "Add tool-calling judge and asymmetric model routing")
- **Status:** Accepted
- **Context:** Generated content needs quality verification beyond schema checks.
- **Decision:** Use an LLM-as-judge that can call tools (run code, check equations, look up references, verify imports), and route cheaper artifacts to `gemini_flash` while reserving `gemini` (pro) for harder ones (draft/review/edit, judge, API endpoints).
- **Why:** Better factual/code verification; cost control via model tiering.
- **Consequences:** Judge fail-closed on errors; cost multiplies through retry/judge loops; rubric weights are textual, not used for deterministic aggregation.
- **Related files:** `pipeline/judge.py`, `pipeline/judge_tools.py`, `config.json artifact_provider_map`.

# Decision: Two coexisting pipelines (single-shot + multi-agent)
- **Date:** Pre-2026-05-28 (commit `6b28d3c` "Add multi-agent content orchestration pipeline")
- **Status:** Accepted (multi-agent has no production consumer)
- **Context:** The single-shot `pipeline.generate` produces the published portfolio. A separate, more general multi-agent authoring workflow was added.
- **Decision:** Build `pipeline/content_pipeline/` + `agents/` as an **independent** subsystem, explicitly decoupled from `pipeline.generate` (`content_pipeline/__init__.py:7-9`).
- **Why:** *(inferred)* Demonstrate a gated, multi-stage agentic authoring pattern.
- **Consequences:** Fully built + tested but unused by the site/API; `cancel()` unimplemented. Role needs clarifying (BACKLOG B11).
- **Related files:** `pipeline/content_pipeline/`, `pipeline/agents/`, `examples/run_content_pipeline.py`.

# Decision: Recommender as a standalone Flask app, proxied into the unified app
- **Date:** *(inferred)* from current code
- **Status:** Accepted (flagged as debt)
- **Context:** The recommender predates the unified `api/app.py` and was written as its own `Flask(__name__)`.
- **Decision:** Rather than convert it to a blueprint, `api/app.py` proxies `/api/recommend` via `test_request_context` + `full_dispatch_request` into the recommender app.
- **Why:** *(inferred)* Least-change integration.
- **Consequences:** Two Flask apps in one process; dropped headers; inconsistent error handling (KNOWN_ISSUES #10, BACKLOG B6).
- **Related files:** `api/app.py:28-38`, `pipeline/recommender_api.py`.

# Decision: Strict, manifest-idempotent, schema-validated generation
- **Date:** Pre-2026-05-28 (commits `598e08a`, `ce1ab5f`)
- **Status:** Accepted
- **Decision:** Every artifact has a strict JSON Schema (`additionalProperties: False`); generation is idempotent via a per-technique `manifest.json` keyed on a SHA-256 input hash.
- **Why:** Reproducibility + cost control (skip unchanged artifacts).
- **Consequences:** Strong structure guarantees; chars-vs-words "800" inconsistency between schema and validator; content validation advisory at generation (KNOWN_ISSUES #9).
- **Related files:** `pipeline/schemas.py`, `pipeline/generator.py:112-160`.

# Decision: Remove the quiz feature
- **Date:** Pre-2026-05-28 (commit `2e75bd6` "refactor: remove quiz feature end-to-end")
- **Status:** Accepted
- **Context:** An earlier `quiz.json` artifact existed.
- **Decision:** Remove quiz generation end-to-end.
- **Consequences:** `CLAUDE.md` still listed `quiz.json` (stale — corrected in this docs project; KNOWN_ISSUES #12).

# Decision: Static-site + GitHub Pages deployment
- **Date:** Pre-2026-05-28 (commit `809b819` "Add GitHub Pages deployment workflow and build script")
- **Status:** Accepted (publishes placeholder in practice)
- **Decision:** Build `site/` via `build_site.py` and deploy to GitHub Pages on push to main.
- **Consequences:** Since CI doesn't run the content pipeline and `generated/` is gitignored, the live site is the placeholder; `/api/*` features aren't deployed (KNOWN_ISSUES #3).
- **Related files:** `.github/workflows/pages.yml`, `build_site.py`.

# Decision: Documentation as first-class infrastructure
- **Date:** 2026-05-28
- **Status:** Accepted
- **Context:** Stale, scattered docs (optimization/OpenAI claims) made the repo hard to understand and continue.
- **Decision:** Build a phased `docs/` system (overview, product, architecture, implementation, quality, planning, AI-context, history, visuals) with honest status labels and file:line evidence; correct the root `CLAUDE.md`.
- **Why:** Make the repo self-explaining and auditable for humans and AI agents.
- **Consequences:** This documentation set; legacy `SETUP.md`/`WOW_FACTOR_ANALYSIS.md` still need correction (BACKLOG B4).
- **Related files:** `docs/**`, `CLAUDE.md`.
