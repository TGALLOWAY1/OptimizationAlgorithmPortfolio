# State Management

> Where state lives and how it persists. There is no database and no server session state — state is files on disk.
> Last updated: 2026-05-28.

## Categories of state

| State | Where | Lifetime | Tracked in git? |
|---|---|---|---|
| Config | `pipeline/config.json` | Source-controlled | Yes |
| Judge inputs | `content/reference/<slug>.json`, `content/rubrics.json` | Source-controlled | Yes |
| Generated artifacts | `generated/techniques/<slug>/*.json`, `*.png`, `manifest.json` | Regenerated on demand | No (gitignored) |
| Cross-technique data | `generated/knowledge_graph.json`, `generated/use_case_matrix.json` | Regenerated | No |
| Evaluation results | `generated/evaluations/`, `generated/logs/`, `evaluation_latest_*.json` | Per eval run | No |
| Multi-agent runs | `outputs/runs/<run_id>/run.json`, `<stage>.json`, derived `.md` | Per pipeline run | No |
| Published site | `site/*.html`, `site/images/<slug>/` | Per publish | No |
| Browser UI state | in-page JS (no persistence) | Page lifetime | n/a |

## Idempotency via `manifest.json`

`generator.py` writes a per-technique `manifest.json` (`MANIFEST_FILENAME`, `:30`) recording, per artifact: `file`, `generated_at`, `input_hash`, `provider_class`, `model`, plus a top-level `artifact_version` (currently `"2"`, `:29`) and `updated_at`. The `input_hash` is a SHA-256 over version + prompt + schema + config slice + material inputs (`:112-128`). On rerun, `_can_reuse_artifact` (`:141-160`) skips regeneration when the hash matches — `--force` overrides, `--clean` wipes first. This is the project's "is it up to date?" mechanism in lieu of a build system.

## Generated-root override

`OPTIMIZATION_PORTFOLIO_GENERATED_ROOT` relocates the `generated/` tree (`paths.py:17-31`). **Caveat:** `build_site.py` hardcodes its own `generated/techniques` path (`:17`) and ignores the env var — so a relocated root will make the Pages builder fall back to the placeholder page even when content exists.

## Multi-agent run state

`content_pipeline/state.py` defines `ContentPipelineRun`/`StageRun` with status enums (`PipelineStatus`, `StageStatus`) and atomic persistence (`save_run` writes `.tmp` then `os.replace`, `:94-102`). `run_id` = UTC timestamp + 6 hex chars (`pipeline.py:140-144`). `history.py:list_runs` browses prior runs newest-first; `resume_run_id` reloads and skips already-succeeded stages whose output file exists (`pipeline.py:82-98`). `cancel()` is unimplemented (`pipeline.py:132-136`, raises `NotImplementedError`).

## "Promotion" is a no-op

`evaluate.py` defines `CANDIDATES_DIR`, `VALIDATED_DIR`, and `CONTENT_DIR` — but all three alias `GENERATED_TECHNIQUES_DIR` (`:29-31`). `promote_artifact` (`:238-258`) therefore rewrites the file in place; there is no candidate→validated staging separation despite the naming. Treat it as vestigial.

## Concurrency notes

- The LLM provider cache `_providers` (`llm_client.py:245`) is a process-global dict, populated unguarded (`:285`) — not thread-safe under Flask's threaded server. In practice the Gemini client is generally safe to share, but the cache-populate race is real under load.
- The static site and CLI generation are single-process batch operations; no locking is implemented (or needed) for the file outputs.
