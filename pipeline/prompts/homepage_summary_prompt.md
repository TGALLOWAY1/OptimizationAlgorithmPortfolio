You are an expert technical writer. Create a very short, scannable summary for a homepage card.

## Plan
```json
{{plan_json}}
```

## Overview Summary (for context)
{{overview_summary}}

## Requirements

Return a JSON object with one field:

- **bullets** (array of strings): Exactly 3–5 short bullet points that capture the essence of this optimization technique. Each bullet should be one concise phrase or short sentence (under 15 words). No long paragraphs. Focus on: what it is, when to use it, and one key strength or characteristic.

Example format:
```json
{
  "bullets": [
    "Model-based approach for expensive black-box functions",
    "Uses Gaussian Process surrogate and acquisition function",
    "Sample-efficient: few evaluations to find optimum",
    "Ideal for hyperparameter tuning and costly experiments"
  ]
}
```

Respond with ONLY the JSON object, no additional text.
