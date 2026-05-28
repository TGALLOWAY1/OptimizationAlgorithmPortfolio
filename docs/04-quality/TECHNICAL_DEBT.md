# Technical Debt

> Maintainability/consistency debt (distinct from user-facing defects in KNOWN_ISSUES.md).
> Last updated: 2026-05-28. Each item: severity, area, evidence, mitigation.

## 1. Four duplicate slugify implementations
- **Severity:** Medium · **Area:** Duplication/consistency
- **Evidence:** `generator.slugify` (`generator.py:55`), `publish._slugify` (`publish.py:39`, with redundant inline `import re`), `build_site._slugify` (`build_site.py:21`), plus re-slugging at `publish.py:344`. Identical regex, independently maintained.
- **Why it matters:** Drift would silently break slug↔file matching between generation, publishing, and the API.
- **Mitigation:** One canonical `slugify` in `pipeline/paths.py` (or `text_utils.py`); import everywhere; delete duplicates.

## 2. Duplicated, already-drifted math-tutor prompt construction
- **Severity:** Medium · **Area:** Duplication/drift
- **Evidence:** Prompt built inline in `math_tutor()` (`api/math_tutor.py:44-58`) and again in `_build_math_tutor_prompts()` (`:81-93`); the two already differ (non-stream appends a JSON instruction the stream omits). Same split in `study_plan.py` (`:119` vs `:157`).
- **Mitigation:** Single shared prompt-builder used by both JSON and SSE routes.

## 3. Duplicated input validation in `/stream` endpoints
- **Severity:** Low/Medium · **Area:** Duplication/inconsistent errors
- **Evidence:** `math_tutor` validates lengths inline (`:32-41`) and again in `_build_math_tutor_prompts` (`:78`); stream route returns generic `"Invalid input."` while non-stream returns specific messages. Same in `study_plan.py`.
- **Mitigation:** Extract a `validate_and_build() -> (prompts, error_response)` helper shared by both routes.

## 4. Pervasive broad `except Exception`
- **Severity:** Medium · **Area:** Error handling/debuggability
- **Evidence:** ~27 broad handlers, concentrated in `generate.py` (8: lines 119,146,168,183,198,216,231,260), `llm_client.py:309,330`, `retry_loop.py:110,156`, `judge.py:273,311`, and the API endpoints. Several mask root causes behind generic 500s.
- **Mitigation:** Narrow to expected types (SDK errors, `json.JSONDecodeError`, `jsonschema.ValidationError`, `OSError`); keep broad catches only at orchestration boundaries with `logger.exception`.

## 5. Large, low-cohesion modules
- **Severity:** Medium · **Area:** Maintainability
- **Evidence (`wc -l`):** `generator.py` 653, `schemas.py` 601, `publish.py` 450, `evaluate.py` 368, `judge.py` 357, `generate.py` 342, `llm_client.py` 341, `content_pipeline/pipeline.py` 331.
- **Mitigation:** Split `generator.py` (generators vs manifest/hash utils) and `publish.py` (rendering vs page assembly vs data loading) first — both are large and under-tested.

## 6. `build_site.py` re-implements path constants
- **Severity:** Medium · **Area:** Coupling
- **Evidence:** `build_site.py:15-25` redefines `PROJECT_ROOT`/`SITE_DIR`/`GENERATED_TECHNIQUES_DIR`/`_slugify` instead of importing `pipeline.paths`. Ignores `OPTIMIZATION_PORTFOLIO_GENERATED_ROOT`.
- **Mitigation:** Import from `pipeline.paths`.

## 7. Vestigial evaluate "promotion"
- **Severity:** Low · **Area:** Dead concept
- **Evidence:** `CANDIDATES_DIR`/`VALIDATED_DIR`/`CONTENT_DIR` all alias `GENERATED_TECHNIQUES_DIR` (`evaluate.py:29-31`); `promote_artifact` rewrites in place.
- **Mitigation:** Either implement real staging or remove the candidate/validated naming.

## 8. Process-global, non-thread-safe provider cache
- **Severity:** Low · **Area:** Concurrency
- **Evidence:** `_providers` dict populated unguarded (`llm_client.py:245,285`) under Flask threaded serving.
- **Mitigation:** Guard with a lock or accept the benign race (document it).

## 9. No CI to catch a red suite
- **Severity:** Medium · **Area:** Process
- **Evidence:** No workflow runs tests (`CLAUDE.md:129`); 6 failures went undetected.
- **Mitigation:** Add a GitHub Actions job running `pytest tests/ -q` on push/PR.

## 10. `--provider` cannot select `gemini_flash`
- **Severity:** Low · **Area:** CLI ergonomics/cost
- **Evidence:** `generate.py:60-64` restricts `--provider` to `gemini`; forcing it overrides the cheaper flash default for text artifacts with no way back.
- **Mitigation:** Allow `gemini_flash` (and `nano_banana`) as choices, or remove the override.

## Notes
- **No `TODO`/`FIXME`/`HACK` debt comments** exist in source — the only matches are intentional placeholder-detection regexes (`evaluate.py:41-54`, `quality_gates.py:17`).
- **No obvious dead code** found beyond the vestigial promotion concept (#7).
