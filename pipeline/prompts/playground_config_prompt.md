You are an expert in {{domain}}.

Given the following plan for the optimization algorithm "{{technique_name}}", generate a playground configuration that defines interactive parameters users can adjust to visualize the algorithm's behavior.

## Technique Plan
```json
{{plan_json}}
```

## Instructions

1. Choose 2-4 key **parameters** that are most educational to adjust interactively:
   - Each parameter needs: name (camelCase), label (display), min, max, default, step, description
   - Pick parameters that visibly change the algorithm's behavior on a 2D function
   - Examples: learning_rate, population_size, mutation_rate, temperature, inertia_weight

2. Choose the best **objective_function** for demonstrating this algorithm:
   - "rosenbrock": Narrow curved valley (good for gradient methods)
   - "rastrigin": Many local minima (good for global optimizers)
   - "sphere": Simple convex (good for demonstrating convergence)
   - "ackley": Nearly flat with deep center (good for exploration vs exploitation)

3. Choose the best **visualization_type**:
   - "contour_trajectory": Single-point path on contour plot (gradient descent, simulated annealing, nelder-mead)
   - "population_scatter": Multiple points moving on contour (genetic algorithm, PSO, differential evolution, CMA-ES)
   - "convergence_curve": Best value over iterations (any algorithm)

Return valid JSON only.
