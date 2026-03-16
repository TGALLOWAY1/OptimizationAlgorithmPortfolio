You are an expert educator in optimization algorithms. Create a quiz and flashcard set for the optimization technique described in the plan below.

## Plan Context
```json
{{plan_json}}
```

## Requirements

Return a JSON object with these fields:

- **technique_slug** (string): "{{technique_slug}}"
- **artifact_type** (string): "quiz"
- **multiple_choice** (array of 3-5 objects): Multiple-choice questions testing understanding of this technique. Each object has:
  - "question" (string): A clear question about the technique's concepts, math, or application.
  - "choices" (array of 4 strings): Four answer options, only one of which is correct.
  - "correct_index" (integer 0-3): The index of the correct answer in the choices array.
  - "explanation" (string): A brief explanation of why the correct answer is right and why the distractors are wrong.
- **flashcards** (array of 3-8 objects): Flashcard Q&A pairs for spaced repetition study. Each object has:
  - "front" (string): A concise question or term (can include LaTeX with `$...$`).
  - "back" (string): The answer or definition (can include LaTeX with `$...$`).

Cover a range of difficulty levels: basic recall, conceptual understanding, and application. Use LaTeX notation where appropriate for mathematical content.

Respond with ONLY the JSON object, no additional text.
