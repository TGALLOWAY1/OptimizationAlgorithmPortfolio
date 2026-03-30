You are a senior software engineer specializing in {{domain}}. Create a comprehensive implementation guide for the technique described in the plan below.

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
  - A minimal from-scratch implementation of the MCTS technique
  - A practical example demonstrating the technique in a game-playing context (e.g., Tic-Tac-Toe, Connect Four, or a simple board game)
  Each example should include comments explaining key steps.
- **libraries** (array of strings): Reader-facing library guidance with brief descriptions (e.g., "scipy.optimize - General-purpose optimization toolkit").
- **runtime_dependencies** (array of strings): Raw Python import names needed to run the examples (e.g., ["math"], ["numpy", "scipy"], ["sklearn"]). Use importable module names only, with no descriptions.
- **pseudo_code** (string): Language-agnostic pseudocode for the core algorithm. Use clear indentation and standard pseudocode keywords (FUNCTION, FOR, WHILE, IF, RETURN).
- **code_variations** (array of 3 objects): Three complete implementation variations using different approaches. Each object has:
  - "framework" (string): One of "pure_python", "numpy", or "multiprocessing" (use the most relevant trio for this MCTS technique — "pure_python" for a clean from-scratch implementation, "numpy" for vectorized/batch operations, "multiprocessing" for parallelized variants).
  - "label" (string): A human-readable label (e.g., "Pure Python Implementation", "NumPy-Accelerated Implementation", "Multiprocessing Implementation").
  - "code" (string): A complete, runnable Python code example using that approach. Include imports, comments, and a brief usage example demonstrating the technique on a game tree.

Respond with ONLY the JSON object, no additional text.
