# Security & Privacy Notes

> Honest security posture. This is an educational-content tool, not a hardened service. Last updated: 2026-05-28.

## Threat model summary

The intended deployment is: offline content generation by an operator + a static public site, with the Flask API run **locally**. Most risks below are acceptable for local/dev use but **block public hosting of the API**.

## Findings

### No authentication or authorization (High)
None of the 8 endpoints check identity, keys, or rate limits. There are no per-user resources (so no ownership checks to miss), but nothing prevents unbounded unauthenticated Gemini spend. `api/app.py`, all `api/*.py`, `recommender_api.py`.

### Open CORS (High, compounds the above)
`CORS(app)` with no origin restriction (`api/app.py:19`, `recommender_api.py:20`) — any website can call these paid endpoints cross-origin.

### `debug=True` in Flask entry points (High if exposed)
`app.run(debug=True, host=0.0.0.0)` (`api/app.py:66`, `recommender_api.py:105`) enables the Werkzeug interactive debugger → remote code execution on unhandled errors if reachable beyond localhost.

### Path traversal in `/api/compare` (Medium)
`slug_a`/`slug_b` are joined into a filesystem path without format validation (`compare.py:37`); mitigated only by `is_dir()` + `*.json` existence checks. Validate slug format/membership.

### Executing LLM-generated code (Medium, contained)
`code_runner.run_code` runs model-produced Python via `subprocess.run([sys.executable, ...], timeout=30)` (`code_runner.py:112-118`) with no real sandbox (same user, network + filesystem access). The import allowlist (`ALLOWED_LIBRARIES`) is enforced on *declared* dependencies, not on the executed code string, and includes `os`. **Not reachable from any HTTP endpoint** — only the offline `--evaluate` path uses it, on trusted-model output. `/api/adapt_code` returns code as text and never executes it.

### Prompt injection (Medium)
User input is interpolated into prompts (`adapt_code`, `math_tutor`, `study_plan`, `recommend`), and the non-tool Gemini path merges system+user into one string (`llm_client.py:91`), so there's no system/user trust boundary. The multi-agent pipeline also feeds LLM output as downstream input. Treat all generated text as untrusted before rendering.

### Unvalidated streamed output (Low/Medium)
`/stream` endpoints emit raw model tokens with no schema validation (`math_tutor.py:111`, `study_plan.py:157`). Free text to the browser.

## Privacy / secrets

- **Secrets:** `GEMINI_API_KEY` is the only secret, read from env/`.env` (gitignored). No key is logged. Do not commit `.env`.
- **User data:** API inputs (queries, code, background/goals) are sent to Google Gemini. No persistence of user inputs server-side beyond request scope; no analytics. If hosted publicly, disclose Gemini data flow to users.
- **Error hygiene:** endpoints catch broad `Exception`, log server-side via `logger.exception`, and return generic messages — no stack traces leak through JSON responses (but `debug=True` would expose them on unhandled errors).

## Hardening checklist before any public API hosting

- [ ] Set `debug=False`; never bind `0.0.0.0` with debug on.
- [ ] Add auth (API key/token) + per-IP rate limiting.
- [ ] Restrict CORS to known origins.
- [ ] Validate/whitelist `compare` slugs.
- [ ] Sandbox or disable code execution; enforce the allowlist on executed code.
- [ ] Set a request body size limit (`MAX_CONTENT_LENGTH`).
- [ ] Disclose the Gemini data flow in a privacy note.
