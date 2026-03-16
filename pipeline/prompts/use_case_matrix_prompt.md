# Optimization Algorithm Use Case Matrix — Generation Prompt

You are an expert in optimization algorithms. Create a comprehensive comparison table showing which optimization techniques are well-suited (or poorly suited) for different problem spaces and use cases.

## Techniques to Compare

The following 8 optimization algorithms must appear in the matrix:

- Bayesian Optimization
- Genetic Algorithm
- Simulated Annealing
- Particle Swarm Optimization
- Gradient Descent
- Nelder-Mead Simplex
- CMA-ES
- Differential Evolution

## Problem Spaces / Use Cases

Define 12–18 distinct problem spaces or use-case categories that practitioners commonly encounter. Examples of dimensions to consider (adapt or expand as appropriate):

- **Search space type**: Continuous, discrete/combinatorial, mixed-integer
- **Objective characteristics**: Differentiable, black-box (no gradients), noisy, multi-modal
- **Evaluation cost**: Cheap (milliseconds), expensive (minutes to days)
- **Dimensionality**: Low (< 10), medium (10–100), high (> 100)
- **Constraints**: Unconstrained, box/bounds, general nonlinear constraints
- **Problem structure**: Convex, non-convex, rugged, separable vs. non-separable
- **Domain examples**: Hyperparameter tuning, neural network training, TSP, protein folding, materials discovery, robotics control

Choose problem spaces that create meaningful distinctions between the algorithms (i.e., not every algorithm gets the same rating).

## Output Format

Return a JSON object with this structure:

```json
{
  "title": "Optimization Algorithm Use Case Matrix",
  "description": "A brief 1–2 sentence description of what this table shows.",
  "problem_spaces": [
    {
      "id": "continuous-differentiable",
      "label": "Continuous, differentiable objectives",
      "description": "Short explanation of this problem space (1 sentence)."
    }
  ],
  "matrix": {
    "Bayesian Optimization": {
      "continuous-differentiable": "unsuitable",
      "black-box-expensive": "ideal"
    },
    "Genetic Algorithm": { ... }
  }
}
```

## Rating Rules

For each (algorithm, problem_space) pair, use exactly one of:

- **"ideal"** — The algorithm is among the best choices for this use case. Use ✅ when rendering.
- **"suitable"** — The algorithm works well but may not be the top choice. Use ✅ when rendering.
- **"unsuitable"** — The algorithm is a poor fit (e.g., wrong problem type, scales badly). Use ❌ when rendering.

Be rigorous: an algorithm should be "ideal" or "suitable" only when it genuinely fits. Mark "unsuitable" when the problem space violates core assumptions (e.g., Gradient Descent for black-box, Genetic Algorithm for high-dimensional continuous with cheap evaluations).

## Requirements

- Every (algorithm, problem_space) cell must have a rating.
- Ensure variety: no algorithm should be ideal for everything, and no problem space should have zero ideal/suitable algorithms.
- Base ratings on established knowledge of each algorithm's strengths and limitations.
- Use concise, practitioner-friendly labels for problem spaces (e.g., "Black-box, expensive evaluations" not "Functions f where ∇f is unavailable and f(x) costs > 1 min").

Respond with ONLY the JSON object, no additional text or markdown fences.
