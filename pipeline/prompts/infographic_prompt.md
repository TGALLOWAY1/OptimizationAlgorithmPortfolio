You are a visual information designer specializing in technical education. Create a detailed infographic specification for the optimization technique described in the plan below.

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
  - "title" (string): Panel heading
  - "content" (string): Text content for this panel
  - "visual_type" (string): Type of visual (e.g., "flowchart", "graph", "diagram", "comparison_table")
- **visual_metaphors** (array of strings): At least 2 visual metaphors or analogies to make the technique intuitive.
- **color_palette** (string): A description of the color scheme (e.g., "Deep blue (#1a237e) primary, teal (#00897b) accent, light gray (#f5f5f5) background").
- **layout** (string): Description of the overall layout (e.g., "Vertical scroll, 2-column grid for panels, full-width header and footer").
- **typography** (string): Font and sizing guidance (e.g., "Title: 32pt bold sans-serif, Body: 14pt regular, Equations: 16pt serif italic").
- **key_equations** (array of strings): The 2-4 most visually important equations in LaTeX, to be rendered prominently in the infographic.

Respond with ONLY the JSON object, no additional text.
