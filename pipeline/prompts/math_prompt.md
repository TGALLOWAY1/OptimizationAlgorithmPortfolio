You are a mathematics professor specializing in {{domain}}. Create a detailed mathematical deep dive for the technique described in the plan below.

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
- **key_equations** (array of objects): The most important equations. Each object has:
  - "equation" (string): The equation in LaTeX with `$$...$$` delimiters.
  - "label" (string): A short descriptive label (e.g., "Update Rule", "Objective Function").
  - "step_by_step_derivation" (array of strings): An ordered array of derivation steps showing how this equation is derived. Each step should contain LaTeX math and a brief English explanation. Include at least 3 steps for complex equations. For simple definitions, provide at least 2 steps explaining the intuition.
- **worked_examples** (array of strings): At least 2 step-by-step worked examples showing the technique applied to concrete problems. Each example must start with `### Example N:` as a header. Use LaTeX for all math.
- **common_confusions** (array of strings): At least 2 common misconceptions or points of confusion, with clarifications.

Use the notation conventions from the plan. Ensure mathematical rigor appropriate for the target audience.

Respond with ONLY the JSON object, no additional text.
