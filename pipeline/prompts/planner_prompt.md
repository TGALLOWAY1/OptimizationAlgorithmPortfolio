You are an expert in {{domain}}. Your task is to create a structured plan for generating educational content about the technique: **{{technique_name}}**.

Return a JSON object with the following fields:

- **technique_name** (string): The full name of the technique.
- **slug** (string): A URL-safe lowercase slug (e.g., "bayesian-optimization").
- **aliases** (array of strings): Alternative names or abbreviations for this technique.
- **problem_type** (string): The class of problems this technique addresses (e.g., "black-box optimization", "continuous optimization").
- **notation_conventions** (array of strings): Mathematical notation conventions to use consistently across all artifacts (e.g., "f(x) for objective function", "x* for optimal solution").
- **assumptions** (array of strings): Key assumptions or prerequisites for applying this technique.
- **target_audience** (string): The intended audience level (e.g., "graduate students in CS/ML with calculus and probability background").
- **artifacts_required** (array of strings): List of artifact types to generate: ["overview", "math_deep_dive", "implementation", "infographic_spec"].

Respond with ONLY the JSON object, no additional text.
