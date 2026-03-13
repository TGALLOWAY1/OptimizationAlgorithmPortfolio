You are an expert technical writer specializing in optimization algorithms. Create a comprehensive overview of the optimization technique described in the plan below.

## Plan Context
```json
{{plan_json}}
```

## Requirements

Return a JSON object with these fields:

- **technique_slug** (string): "{{technique_slug}}"
- **artifact_type** (string): "overview"
- **title** (string): A descriptive title for this overview article.
- **summary** (string): A 2-3 sentence executive summary of the technique.
- **markdown** (string): A comprehensive markdown article (minimum 800 words) covering:
  - What the technique is and its historical context
  - How it works at a high level (intuition before formalism)
  - When to use it vs. alternatives
  - Key parameters and their effects
  - Practical considerations and tips
- **use_cases** (array of strings): At least 3 real-world applications.
- **strengths** (array of strings): At least 3 advantages of this technique.
- **limitations** (array of strings): At least 3 limitations or drawbacks.
- **comparisons** (array of strings): At least 2 comparisons with related techniques.

Use the notation conventions from the plan. Write for the target audience specified in the plan.

Respond with ONLY the JSON object, no additional text.
