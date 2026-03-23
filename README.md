# Optimization Algorithm Portfolio

An automated educational content platform that generates comprehensive learning materials for optimization algorithms using LLM-powered content pipelines.

## Overview

This project combines:
- **LLM-driven content generation** — Automatically creates educational materials using OpenAI GPT-4o, Gemini 3.1 Pro, and Nano Banana Pro
- **Interactive Flask API** — Real-time algorithm recommendations, comparisons, math tutoring, and code adaptation
- **Static site publisher** — Generates a mobile-responsive educational website

## Features

### Content Generation
- Generates structured educational content for 8 optimization algorithms
- Creates multiple artifact types: overviews, math deep dives, implementations, and infographics
- Schema-validated JSON output with retry logic

### Interactive Learning Tools
- **Algorithm Recommender** — Get personalized algorithm suggestions based on your problem description
- **Study Plan Generator** — Create customized learning roadmaps
- **Math Tutor** — Interactive explanations of mathematical concepts and derivations
- **Algorithm Comparator** — Side-by-side comparison of different optimization approaches
- **Code Adapter** — Transform implementations between frameworks (NumPy, PyTorch, JAX, etc.)

### Educational Website
- Mobile-responsive design with modern UI
- Expandable mathematical derivations
- Code examples with framework tabs
- Use-case comparison matrix

## Optimization Techniques Covered

1. **Bayesian Optimization** — Probabilistic surrogate-based optimization
2. **Genetic Algorithm** — Evolutionary computation inspired by natural selection
3. **Simulated Annealing** — Probabilistic technique for approximating global optima
4. **Particle Swarm Optimization** — Swarm intelligence optimization
5. **Gradient Descent** — First-order iterative optimization
6. **Nelder-Mead Simplex** — Derivative-free simplex method
7. **CMA-ES** — Covariance Matrix Adaptation Evolution Strategy
8. **Differential Evolution** — Stochastic population-based optimizer

## Quick Start

### Prerequisites
- Python 3.11+
- OpenAI API key
- Google Gemini API key

### Installation

```bash
# Clone the repository
git clone https://github.com/TGALLOWAY1/OptimizationAlgorithmPortfolio.git
cd OptimizationAlgorithmPortfolio

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cat > .env << EOF
OPENAI_API_KEY=sk-your-key-here
GEMINI_API_KEY=your-gemini-key-here
EOF
```

### Generate Content

```bash
# Generate all techniques
python3 -m pipeline.generate

# Generate a single technique
python3 -m pipeline.generate --technique "Bayesian Optimization"

# Skip image generation (faster, lower cost)
python3 -m pipeline.generate --skip-images
```

### Publish Static Site

```bash
python3 -m pipeline.publish
```

### Run the Application

```bash
# Start Flask server (serves both API and static site)
python3 api/app.py

# Open http://localhost:5000 in your browser
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/recommend` | POST | Get algorithm recommendations for a problem |
| `/api/compare` | POST | Compare two algorithms side-by-side |
| `/api/math_tutor` | POST | Get explanations for math concepts |
| `/api/study_plan` | POST | Generate a personalized study plan |
| `/api/adapt_code` | POST | Adapt code between frameworks |

### Example: Algorithm Recommendation

```bash
curl -X POST http://localhost:5000/api/recommend \
  -H "Content-Type: application/json" \
  -d '{"problem": "I need to tune hyperparameters for a neural network with expensive evaluations"}'
```

## Project Structure

```
OptimizationAlgorithmPortfolio/
├── api/                        # Flask API blueprints
│   ├── app.py                  # Main app, serves API + static site
│   ├── adapt_code.py           # Code adaptation endpoint
│   ├── compare.py              # Algorithm comparison endpoint
│   ├── math_tutor.py           # Math tutoring endpoint
│   └── study_plan.py           # Study plan generation endpoint
├── pipeline/                   # Content generation pipeline
│   ├── generate.py             # CLI orchestrator
│   ├── generator.py            # Artifact generation engine
│   ├── llm_client.py           # Multi-provider LLM client
│   ├── publish.py              # Static HTML publisher
│   ├── schemas.py              # JSON Schema definitions
│   ├── prompts/                # Prompt templates
│   └── templates/              # Jinja2 HTML templates
├── tests/                      # Test suite (70 tests)
├── content/                    # Generated artifacts (gitignored)
├── site/                       # Published HTML (gitignored)
├── requirements.txt            # Python dependencies
├── SETUP.md                    # Detailed setup instructions
└── CLAUDE.md                   # Codebase documentation
```

## Architecture

### Multi-Provider LLM Routing

The pipeline routes different artifact types to appropriate LLM providers:

| Provider | Use Case |
|----------|----------|
| OpenAI GPT-4o | Complex content (overviews, math deep dives) |
| Gemini 3.1 Pro | Structured content (plans, implementations) |
| Nano Banana Pro | Image generation (infographics) |

### Content Pipeline

1. **Config-driven** — `config.json` maps techniques to providers
2. **Idempotent** — Skips existing artifacts unless `--force` is used
3. **Schema-validated** — All JSON outputs validated against strict schemas
4. **Retry logic** — Exponential backoff for API calls

## Testing

```bash
# Run all tests (no API keys required — all LLM calls are mocked)
python3 -m pytest tests/ -v

# Run specific test file
python3 -m pytest tests/test_api_endpoints.py -v

# Run with coverage
python3 -m pytest tests/ --cov=pipeline --cov=api
```

## Cost Estimates

Full pipeline run (8 techniques, all artifacts):

| Provider | Artifacts | Est. Cost |
|----------|-----------|-----------|
| OpenAI GPT-4o | 16 | ~$2-5 |
| Gemini 3.1 Pro | 24 | ~$1-3 |
| Nano Banana Pro | 8 images | ~$1-2 |
| **Total** | **48** | **~$4-10** |

Use `--skip-images` during development to reduce costs.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests to ensure nothing breaks (`python3 -m pytest tests/`)
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## License

This project is available under the MIT License. See [LICENSE](LICENSE) for details.
