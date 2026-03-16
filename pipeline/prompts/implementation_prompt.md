You are a senior software engineer and optimization specialist. Create a comprehensive implementation guide for the optimization technique described in the plan below.

## Plan Context
```json
{{plan_json}}
```

## Requirements

Return a JSON object with these fields:

- **technique_slug** (string): "{{technique_slug}}"
- **artifact_type** (string): "implementation"
- **markdown** (string): A detailed implementation guide (minimum 800 words) covering:
  - Do NOT start with a redundant title (e.g. "# Comprehensive Implementation Guide..."); the section header is provided by the page.
  - Use `##` for main sections, `###` for subsections. Numbered lists need a blank line before the first item; each item on its own line.
  - Bold key terms in definition-style lists: `- **Term**: description` or `1. **Term**: description`.
  - Algorithm pseudocode with clear step numbering
  - Data structures and their rationale
  - Key implementation decisions and trade-offs
  - Performance optimization tips
  - Common pitfalls and how to avoid them
  - Testing and debugging strategies
- **python_examples** (array of strings): At least 2 complete, runnable Python code examples:
  - A minimal from-scratch implementation
  - A practical example using a popular library (e.g., scipy, scikit-optimize, optuna)
  Each example should include comments explaining key steps.
- **libraries** (array of strings): Relevant Python libraries with brief descriptions (e.g., "scipy.optimize - General-purpose optimization toolkit").
- **pseudo_code** (string): Language-agnostic pseudocode for the core algorithm. Use clear indentation and standard pseudocode keywords (FUNCTION, FOR, WHILE, IF, RETURN).
- **code_variations** (array of 3 objects): Three complete implementation variations using different frameworks. Each object has:
  - "framework" (string): One of "numpy", "pytorch", or "scipy" (use the most relevant trio for this technique — alternatives include "scikit-learn" in place of "scipy" if more appropriate).
  - "label" (string): A human-readable label (e.g., "NumPy Implementation", "PyTorch Implementation", "SciPy/Scikit-Learn Implementation").
  - "code" (string): A complete, runnable Python code example using that framework. Include imports, comments, and a brief usage example.

Respond with ONLY the JSON object, no additional text.
