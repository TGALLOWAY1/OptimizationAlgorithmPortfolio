"""Tool registry for the tool-calling judge.

Each tool exposes a Python callable plus a JSON-Schema declaration. The
GeminiProvider tool-use loop dispatches by name into TOOL_REGISTRY, executes
the callable with the LLM-supplied arguments, and feeds the result back to
the model.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Callable

from pipeline.code_runner import check_dependencies, run_code
from pipeline.paths import REFERENCE_DIR

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def run_python_code(code: str, timeout_s: int = 15) -> dict[str, Any]:
    """Execute a Python snippet in the existing subprocess sandbox."""
    if not isinstance(code, str) or not code.strip():
        return {"error": "code must be a non-empty string"}
    if timeout_s <= 0 or timeout_s > 30:
        timeout_s = 15
    result = run_code(code, timeout=timeout_s)
    return {
        "passed": result["passed"],
        "exit_code": result["exit_code"],
        "stdout": result["stdout"][:2000],
        "stderr": result["stderr"][:2000],
        "timeout_s": timeout_s,
    }


_LATEX_DELIM_RE = re.compile(r"^\s*(\$\$|\$|\\\(|\\\[)|(\$\$|\$|\\\)|\\\])\s*$")
_KNOWN_COMMANDS = {
    "frac", "sqrt", "sum", "prod", "int", "lim", "log", "ln", "exp", "sin", "cos",
    "tan", "cot", "sec", "csc", "arcsin", "arccos", "arctan", "sinh", "cosh", "tanh",
    "alpha", "beta", "gamma", "delta", "epsilon", "varepsilon", "zeta", "eta", "theta",
    "vartheta", "iota", "kappa", "lambda", "mu", "nu", "xi", "pi", "rho", "sigma",
    "tau", "upsilon", "phi", "varphi", "chi", "psi", "omega", "Gamma", "Delta",
    "Theta", "Lambda", "Xi", "Pi", "Sigma", "Upsilon", "Phi", "Psi", "Omega",
    "infty", "partial", "nabla", "cdot", "times", "div", "pm", "mp", "leq", "geq",
    "neq", "approx", "sim", "equiv", "in", "notin", "subset", "subseteq", "supset",
    "supseteq", "cup", "cap", "emptyset", "forall", "exists", "rightarrow", "leftarrow",
    "Rightarrow", "Leftarrow", "leftrightarrow", "Leftrightarrow", "mapsto", "to",
    "left", "right", "big", "Big", "bigg", "Bigg", "mathbb", "mathbf", "mathcal",
    "mathrm", "text", "textbf", "textit", "boldsymbol", "hat", "tilde", "bar", "vec",
    "dot", "ddot", "underline", "overline", "begin", "end", "argmax", "argmin", "max",
    "min", "sup", "inf", "det", "dim", "ker", "Pr", "mathbb",
}


def check_equation(latex: str) -> dict[str, Any]:
    """Run syntactic validity checks on a LaTeX equation string.

    Returns ``parsable`` False when delimiters are unbalanced or unknown
    commands appear; the model can then revise the artifact accordingly.
    """
    if not isinstance(latex, str) or not latex.strip():
        return {"error": "latex must be a non-empty string"}

    errors: list[str] = []
    body = _LATEX_DELIM_RE.sub("", latex.strip()).strip()

    pairs = [("{", "}"), ("[", "]"), ("(", ")")]
    for opener, closer in pairs:
        opens = body.count(opener)
        closes = body.count(closer)
        if opens != closes:
            errors.append(
                f"Unbalanced '{opener}{closer}': {opens} opens vs {closes} closes"
            )

    unknown: set[str] = set()
    for match in re.finditer(r"\\([A-Za-z]+)", body):
        cmd = match.group(1)
        if cmd not in _KNOWN_COMMANDS:
            unknown.add(cmd)
    if unknown:
        errors.append(f"Unknown LaTeX commands: {sorted(unknown)}")

    if re.search(r"\\([A-Za-z]+)\1\b", body):
        errors.append("Possible duplicated command name (e.g. \\fracfrac)")

    return {
        "parsable": len(errors) == 0,
        "errors": errors,
        "body_length": len(body),
    }


def lookup_reference(technique_slug: str) -> dict[str, Any]:
    """Return canonical reference facts for a technique, if available."""
    if not isinstance(technique_slug, str) or not technique_slug.strip():
        return {"error": "technique_slug must be a non-empty string"}

    ref_path = REFERENCE_DIR / f"{technique_slug}.json"
    if not ref_path.exists():
        return {
            "found": False,
            "technique_slug": technique_slug,
            "message": f"No reference file at {ref_path}",
        }

    import json

    try:
        data = json.loads(ref_path.read_text())
    except (json.JSONDecodeError, OSError) as e:
        return {"error": f"Failed to load reference: {e}"}

    return {
        "found": True,
        "technique_slug": technique_slug,
        "key_facts": data.get("key_facts", []),
        "forbidden_claims": data.get("forbidden_claims", []),
    }


def verify_imports(deps: list[str]) -> dict[str, Any]:
    """Check whether a list of declared dependencies is allowlisted and importable."""
    if not isinstance(deps, list):
        return {"error": "deps must be a list of strings"}
    deps_clean = [d for d in deps if isinstance(d, str) and d.strip()]
    return check_dependencies(deps_clean)


# ---------------------------------------------------------------------------
# Tool registry — schemas in JSON Schema form
# ---------------------------------------------------------------------------

TOOL_REGISTRY: dict[str, dict[str, Any]] = {
    "run_python_code": {
        "function": run_python_code,
        "description": (
            "Execute a Python snippet in a sandboxed subprocess and return "
            "stdout, stderr, and exit_code. Use this to verify that "
            "implementation code in an artifact actually runs."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python source code to execute.",
                },
                "timeout_s": {
                    "type": "integer",
                    "description": "Timeout in seconds (1-30, default 15).",
                },
            },
            "required": ["code"],
        },
    },
    "check_equation": {
        "function": check_equation,
        "description": (
            "Validate a LaTeX equation for balanced delimiters and known "
            "commands. Returns parsable=false with a list of errors if "
            "the equation is malformed."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "latex": {
                    "type": "string",
                    "description": "The LaTeX equation, with or without delimiters.",
                },
            },
            "required": ["latex"],
        },
    },
    "lookup_reference": {
        "function": lookup_reference,
        "description": (
            "Fetch canonical key_facts and forbidden_claims for a technique. "
            "Use this to ground factual claims in the artifact against "
            "trusted reference material."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "technique_slug": {
                    "type": "string",
                    "description": "Slug like 'uct-upper-confidence-bounds-for-trees'.",
                },
            },
            "required": ["technique_slug"],
        },
    },
    "verify_imports": {
        "function": verify_imports,
        "description": (
            "Check whether declared Python dependencies are allowlisted and "
            "importable. Use this to detect hallucinated imports in "
            "implementation artifacts."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "deps": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of module names declared by the artifact.",
                },
            },
            "required": ["deps"],
        },
    },
}


def dispatch_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Dispatch a tool call by name. Tool errors are returned as data, not raised."""
    entry = TOOL_REGISTRY.get(name)
    if entry is None:
        return {"error": f"Unknown tool: {name}"}
    fn: Callable[..., dict[str, Any]] = entry["function"]
    try:
        return fn(**arguments)
    except TypeError as e:
        return {"error": f"Bad arguments for {name}: {e}"}
    except Exception as e:  # noqa: BLE001 — surface to model rather than crash loop
        logger.exception("Tool %s raised", name)
        return {"error": f"{type(e).__name__}: {e}"}


def tool_declarations() -> list[dict[str, Any]]:
    """Return the tool schemas in the shape Gemini's function calling expects."""
    return [
        {
            "name": name,
            "description": entry["description"],
            "parameters": entry["parameters"],
        }
        for name, entry in TOOL_REGISTRY.items()
    ]
