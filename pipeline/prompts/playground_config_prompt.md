You are an expert in {{domain}}.

Given the following plan for the MCTS strategy "{{technique_name}}", generate a playground configuration that defines interactive parameters users can adjust to visualize the strategy's behavior in a game tree.

## Technique Plan
```json
{{plan_json}}
```

## Instructions

1. Choose 2-4 key **parameters** that are most educational to adjust interactively:
   - Each parameter needs: name (camelCase), label (display), min, max, default, step, description
   - Pick parameters that visibly change the strategy's behavior in a game tree search
   - Examples: explorationConstant, raveK, rolloutDepth, numWorkers, progressiveWidthAlpha

2. Choose the best **objective_function** (game tree scenario) for demonstrating this strategy:
   - "game_tree": Standard game tree with branching factor and depth (good for UCT, RAVE, selection policies)
   - "random_tree": Randomly structured tree with variable branching (good for adaptive strategies)
   - "adversarial_tree": Tree with deceptive rewards and traps (good for opponent modeling, loss avoidance)
   - "blokus_position": Blokus-style position with high branching factor (good for progressive widening, parallelization)

3. Choose the best **visualization_type**:
   - "tree_expansion": Animated tree growth showing node selection and expansion (UCT, RAVE, progressive widening)
   - "visit_heatmap": Heatmap of visit counts across tree nodes (good for comparing exploration patterns)
   - "convergence_curve": Win rate or value estimate over iterations (any strategy)
   - "win_rate_over_time": Win rate progression across multiple games (opponent modeling, meta-optimization)

Return valid JSON only.
