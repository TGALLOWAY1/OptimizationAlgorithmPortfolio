You are a visual information designer specializing in technical education. Create a detailed infographic specification for the technique described in the plan below.

## Plan Context
```json
{{plan_json}}
```

## Requirements

Return a JSON object with these fields:

- **technique_slug** (string): "{{technique_slug}}"
- **artifact_type** (string): "infographic_spec"
- **title** (string): A compelling title for the infographic.
- **panels** (array of objects): At least 4 panels, each with:
  - "title" (string): Panel heading (short — 5 words or fewer)
  - "content" (string): A brief description of what this panel shows visually. Focus on what diagram, chart, or illustration to draw — NOT paragraphs of explanatory text. Keep to 1-2 short sentences.
  - "visual_type" (string): Type of visual (e.g., "flowchart", "graph", "diagram", "comparison_table", "icon_grid", "process_illustration", "annotated_figure")
- **visual_metaphors** (array of strings): At least 2 visual metaphors or analogies to make the technique intuitive. Each should be something that can be drawn as an illustration, not just described in words.
- **color_palette** (string): A description of the color scheme (e.g., "Deep blue (#1a237e) primary, teal (#00897b) accent, light gray (#f5f5f5) background").
- **layout** (string): Description of the overall layout (e.g., "Vertical scroll, 2-column grid for panels, full-width header and footer").
- **typography** (string): Font and sizing guidance (e.g., "Title: 32pt bold sans-serif, Body: 14pt regular, Equations: 16pt serif italic").
- **key_equations** (array of strings): The 2-3 most visually important equations in LaTeX, to be rendered prominently in the infographic. Only include the final result forms — no derivation steps.

**Important**: Design for visual impact. Each panel should be dominated by a diagram, chart, or illustration — not by text. The infographic will be generated as an image, so text-heavy panels will be unreadable. Prefer flowcharts, annotated diagrams, process illustrations, and comparison charts over textual explanations.

Respond with ONLY the JSON object, no additional text.
