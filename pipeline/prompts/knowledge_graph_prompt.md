You are an expert in {{domain}}.

Given the following technique plans for all MCTS strategies in the portfolio, generate a knowledge graph that maps the relationships between them.

## Technique Plans
```json
{{all_plans_json}}
```

## Instructions

1. Create a **node** for each technique with:
   - `slug`: the technique slug (e.g., "uct-upper-confidence-bounds-for-trees")
   - `label`: the display name (e.g., "UCT (Upper Confidence Bounds for Trees)")
   - `category`: one of "selection-policy", "simulation-enhancement", "parallelization", "meta-optimization"
   - `summary`: a 1-sentence description of what makes this MCTS strategy unique

2. Create **edges** between techniques that share meaningful relationships:
   - Mathematical foundations (e.g., both use bandit-based selection)
   - Shared concepts (e.g., rollout enhancement, history heuristics)
   - Complementary use cases (e.g., one improves selection while the other improves simulation)
   - Build-upon relationships (e.g., RAVE extends UCT, NST enhances rollout policy)

3. Each edge should have:
   - `source` and `target`: technique slugs
   - `relationship`: a concise label (e.g., "shares population-based search", "gradient-free alternative")
   - `strength`: 0.0 to 1.0 indicating how strong the relationship is

Generate 10-20 meaningful edges. Focus on the most educational and insightful connections.

Return valid JSON only.
