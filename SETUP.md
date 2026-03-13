# Manual Setup Steps

This document lists the steps **you** need to take before running the pipeline. These require credentials, accounts, or actions that cannot be automated.

---

## 1. Obtain API Keys

You need API keys from two providers:

### OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Sign in (or create an account)
3. Click **"Create new secret key"**
4. Copy the key (starts with `sk-`)
5. Ensure your account has billing enabled and sufficient credits for GPT-4o usage

### Google Gemini API Key
1. Go to https://aistudio.google.com/apikey
2. Sign in with a Google account
3. Click **"Create API Key"**
4. Copy the key
5. This single key is used for both **Gemini 3.1 Pro** (text) and **Nano Banana Pro** (image generation)

---

## 2. Set Environment Variables

Create a `.env` file in the project root (it is gitignored):

```bash
# .env
OPENAI_API_KEY=sk-your-openai-key-here
GEMINI_API_KEY=your-gemini-key-here
```

Then load them into your shell before running the pipeline:

```bash
export OPENAI_API_KEY="sk-your-openai-key-here"
export GEMINI_API_KEY="your-gemini-key-here"
```

Or use a tool like `direnv` or `dotenv` to load them automatically.

---

## 3. Install Python Dependencies

Requires **Python 3.11+**.

```bash
python -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Verify the install

```bash
python -c "import openai; print('openai OK')"
python -c "from google import genai; print('google-genai OK')"
python -c "import jsonschema, jinja2, markdown, PIL; print('all deps OK')"
```

---

## 4. Verify API Access

Run these quick checks to confirm your keys work:

### Test OpenAI
```bash
python -c "
from openai import OpenAI
import os
client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
r = client.chat.completions.create(
    model='gpt-4o',
    messages=[{'role': 'user', 'content': 'Say hello in JSON: {\"greeting\": \"...\"}'}],
    response_format={'type': 'json_object'},
    max_tokens=50
)
print('OpenAI OK:', r.choices[0].message.content)
"
```

### Test Gemini
```bash
python -c "
from google import genai
import os
client = genai.Client(api_key=os.environ['GEMINI_API_KEY'])
r = client.models.generate_content(
    model='gemini-3.1-pro-preview',
    contents='Say hello in one sentence.'
)
print('Gemini OK:', r.text)
"
```

### Test Nano Banana Pro (image generation)
```bash
python -c "
from google import genai
from google.genai import types
import os
client = genai.Client(api_key=os.environ['GEMINI_API_KEY'])
r = client.models.generate_content(
    model='nano-banana-pro',
    contents='Generate a simple blue square image.',
    config=types.GenerateContentConfig(response_modalities=['IMAGE'])
)
for part in r.candidates[0].content.parts:
    if part.inline_data:
        with open('/tmp/test_nb.png', 'wb') as f:
            f.write(part.inline_data.data)
        print('Nano Banana Pro OK: image saved to /tmp/test_nb.png')
        break
"
```

---

## 5. Run the Pipeline

Once all the above steps are complete:

```bash
# Generate all 8 techniques (all artifacts + infographic images)
python -m pipeline.generate

# Generate a single technique
python -m pipeline.generate --technique "Bayesian Optimization"

# Force regeneration of existing artifacts
python -m pipeline.generate --force

# Skip image generation (text artifacts only)
python -m pipeline.generate --skip-images

# Force all artifacts through OpenAI
python -m pipeline.generate --provider openai
```

---

## 6. Publish the Static Site

After content generation completes:

```bash
python -m pipeline.publish
```

This outputs static HTML to the `site/` directory. Open `site/index.html` in a browser to view.

To serve locally:

```bash
python -m http.server 8000 --directory site
# Then open http://localhost:8000
```

---

## 7. Run Tests

```bash
python -m pytest tests/ -v
```

All tests use mocks and do not require API keys.

---

## Cost Estimates

Approximate costs per full pipeline run (8 techniques, all artifacts):

| Provider | Artifacts | Est. Cost |
|----------|-----------|-----------|
| OpenAI GPT-4o | 16 (overview + math_deep_dive) | ~$2-5 |
| Gemini 3.1 Pro | 24 (plan + implementation + infographic_spec) | ~$1-3 |
| Nano Banana Pro | 8 images | ~$1-2 |
| **Total** | **48 artifacts** | **~$4-10** |

Costs depend on response length and may vary. Use `--skip-images` to reduce costs during development.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError: No module named 'google'` | Run `pip install google-genai` |
| `ModuleNotFoundError: No module named 'openai'` | Run `pip install openai` |
| `ValueError: Environment variable OPENAI_API_KEY is not set` | Export the key: `export OPENAI_API_KEY=sk-...` |
| `ValueError: Environment variable GEMINI_API_KEY is not set` | Export the key: `export GEMINI_API_KEY=...` |
| `openai.AuthenticationError` | Your OpenAI key is invalid or expired — regenerate at platform.openai.com |
| `google.api_core.exceptions.PermissionDenied` | Your Gemini key may not have the required API enabled |
| Image generation returns blank/tiny file | Nano Banana Pro may have rate limits — retry after a few seconds |
| Schema validation keeps failing | Run with `--force` to regenerate; check logs for the specific validation error |
