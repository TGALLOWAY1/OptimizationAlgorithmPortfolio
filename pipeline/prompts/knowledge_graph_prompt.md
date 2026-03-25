You are an expert in {{domain}}.

Given the following technique plans for all optimization algorithms in the portfolio, generate a knowledge graph that maps the relationships between them.

## Technique Plans
```json
{{all_plans_json}}
```

## Instructions

1. Create a **node** for each technique with:
   - `slug`: the technique slug (e.g., "bayesian-optimization")
   - `label`: the display name (e.g., "Bayesian Optimization")
   - `category`: one of "evolutionary", "gradient-based", "probabilistic", "direct-search"
   - `summary`: a 1-sentence description of what makes this algorithm unique

2. Create **edges** between techniques that share meaningful relationships:
   - Mathematical foundations (e.g., both use gradient information)
   - Shared concepts (e.g., population-based, stochastic search)
   - Complementary use cases (e.g., one works where the other fails)
   - Historical lineage (e.g., one inspired or evolved from the other)

3. Each edge should have:
   - `source` and `target`: technique slugs
   - `relationship`: a concise label (e.g., "shares population-based search", "gradient-free alternative")
   - `strength`: 0.0 to 1.0 indicating how strong the relationship is

Generate 10-20 meaningful edges. Focus on the most educational and insightful connections.

Return valid JSON only.
