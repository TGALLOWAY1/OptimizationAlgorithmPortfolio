# Screenshot Manifest

> Catalog of screens to capture for visual auditing. **No screenshots are captured yet** — the full content site requires `GEMINI_API_KEY` + a pipeline run, which isn't available in the documentation environment, and no browser automation tool was available. The placeholder build was verified (see note). Capture process: `VISUAL_REGRESSION_PLAN.md`.
> Last updated: 2026-05-28.

## Verified without screenshots
- `python build_site.py` (no API key needed) produces `site/index.html` titled "MCTS Strategy Portfolio" with 8 "Coming Soon" technique cards — the **placeholder** build that the live deploy serves. Confirmed 2026-05-28.

## To capture (once content is generated + Flask is running)

Store images under `docs/08-visuals/screenshots/<name>-<viewport>.png`.

### Homepage (full build)
- **Route:** `/`
- **Viewport:** desktop 1440px · mobile 390px
- **State:** content present; knowledge graph + recommender visible
- **Screenshot path:** `screenshots/home-desktop.png`, `screenshots/home-mobile.png`
- **Last captured:** —
- **Known visual issues:** KG nodes likely render gray (legend mismatch, KNOWN_ISSUES #4)
- **How to reproduce:** generate content → `python api/app.py` → open `/`

### Homepage (placeholder build)
- **Route:** `/` (no generated content)
- **Viewport:** desktop · mobile
- **Screenshot path:** `screenshots/home-placeholder-desktop.png`
- **How to reproduce:** `python build_site.py` (no key) → open `site/index.html`

### Technique detail page
- **Route:** `/uct-upper-confidence-bounds-for-trees.html`
- **Viewport:** desktop · mobile
- **State:** overview + math (KaTeX) + implementation tabs + playground
- **Screenshot path:** `screenshots/technique-uct-desktop.png`
- **Known visual issues:** playground shows gradient descent (KNOWN_ISSUES #2)

### Compare page
- **Route:** `/compare.html` (with Flask running, after selecting two techniques)
- **Screenshot path:** `screenshots/compare-desktop.png`

### Use-case matrix
- **Route:** `/use-case-matrix.html`
- **Screenshot path:** `screenshots/use-case-matrix-desktop.png`

### Quality report
- **Route:** `/quality-report.html` (after an `--evaluate` run)
- **Screenshot path:** `screenshots/quality-report-desktop.png`

### Interactive states (Flask)
- Recommender results, Study Plan wizard timeline, Math Tutor sidebar, Adapt Code modal — capture each populated state.

## Status legend for captures
`—` not captured · `OK` current · `STALE` needs recapture after a UI change.
