You are a mathematics professor specializing in optimization theory. Create a detailed mathematical deep dive for the optimization technique described in the plan below.

## Plan Context
```json
{{plan_json}}
```

## Requirements

Return a JSON object with these fields:

- **technique_slug** (string): "{{technique_slug}}"
- **artifact_type** (string): "math_deep_dive"
- **markdown** (string): A rigorous mathematical treatment (minimum 800 words) covering:
  - Formal problem statement and notation
  - Core algorithm derivation with step-by-step reasoning
  - Convergence analysis or theoretical guarantees (where applicable)
  - Complexity analysis (time and space)
  - Mathematical connections to related methods
  Use LaTeX notation: inline math with `$...$` and display math with `$$...$$`.
  **Critical rule**: Every symbol must be defined before its first use.
- **key_equations** (array of strings): The most important equations in LaTeX format. Each equation should be self-contained with `$$...$$` delimiters.
- **worked_examples** (array of strings): At least 2 step-by-step worked examples showing the technique applied to concrete problems. Use LaTeX for all math.
- **common_confusions** (array of strings): At least 2 common misconceptions or points of confusion, with clarifications.

Use the notation conventions from the plan. Ensure mathematical rigor appropriate for the target audience.

Respond with ONLY the JSON object, no additional text.
