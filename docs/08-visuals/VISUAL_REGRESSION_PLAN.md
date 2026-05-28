# Visual Regression Plan

> A lightweight, repeatable process for visually auditing the site over time. Designed for a server-rendered static site + Flask-backed interactive widgets.
> Last updated: 2026-05-28.

## Why
Several defects here are *visual* and wouldn't be caught by the unit tests: the playground rendering the wrong algorithm, gray knowledge-graph nodes, broken responsive layouts, missing artifact sections. Screenshots make these reviewable over time.

## Prerequisites
1. `GEMINI_API_KEY` set, content generated: `python -m pipeline.generate` (use `--skip-images` for speed if images aren't under review).
2. Site published: `python -m pipeline.publish`.
3. For interactive widgets: `python api/app.py` (serves static site + `/api/*`).
4. A headless browser driver (Playwright recommended) — not currently a project dependency.

## Capture procedure (manual / scriptable)
For each entry in `SCREENSHOT_MANIFEST.md`:
1. Open the route at the listed viewport(s): desktop 1440×900, mobile 390×844.
2. For interactive states, perform the action (e.g., submit a recommender query) and wait for the result to settle.
3. Save to `docs/08-visuals/screenshots/<name>-<viewport>.png`.
4. Update the manifest row: `Last captured` + status.

### Suggested Playwright skeleton (not yet committed)
```python
# scripts/capture_screenshots.py  (proposed)
from playwright.sync_api import sync_playwright
PAGES = [("/", "home"), ("/uct-upper-confidence-bounds-for-trees.html", "technique-uct"),
         ("/compare.html", "compare"), ("/use-case-matrix.html", "use-case-matrix")]
VIEWPORTS = {"desktop": (1440, 900), "mobile": (390, 844)}
with sync_playwright() as p:
    b = p.chromium.launch()
    for path, name in PAGES:
        for vp, (w, h) in VIEWPORTS.items():
            pg = b.new_page(viewport={"width": w, "height": h})
            pg.goto(f"http://localhost:5000{path}")
            pg.wait_for_timeout(1500)  # let KaTeX/D3 render
            pg.screenshot(path=f"docs/08-visuals/screenshots/{name}-{vp}.png", full_page=True)
    b.close()
```

## Comparison procedure
- **Baseline:** the committed screenshots are the baseline.
- **On a UI change:** recapture, then visually diff against the committed baseline (eyeball, or a pixel-diff tool like `pixelmatch`/`odiff`). Investigate any unexpected change; intended changes update the baseline.
- Tie this into `docs/04-quality/REGRESSION_CHECKLIST.md` (Visual section).

## What to watch specifically
- Knowledge-graph node colors + legend (KNOWN_ISSUES #4).
- Playground content per technique (KNOWN_ISSUES #2).
- Responsive layout at 390px: Math Tutor sidebar full-width, matrix horizontal scroll, card grid reflow.
- Graceful omission of missing artifact sections.
- CDN-dependent rendering (KaTeX math, highlight.js) — verify online.

## Current limitation
No screenshots are committed yet (no content/API in this environment; no browser driver). When the capture script is added, commit the initial baselines and reference them here.
