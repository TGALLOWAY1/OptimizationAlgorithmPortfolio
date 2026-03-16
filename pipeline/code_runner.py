"""Python code execution validation for the evaluation pipeline."""

import logging
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Trusted scientific library allowlist (V1)
ALLOWED_LIBRARIES = {
    "numpy",
    "scipy",
    "pandas",
    "matplotlib",
    "scikit-learn",
    "sklearn",
    "torch",
    "tensorflow",
    "math",
    "random",
    "itertools",
    "functools",
    "collections",
    "typing",
    "copy",
    "json",
    "os",
    "sys",
    "time",
}

DEFAULT_TIMEOUT_SECONDS = 30


def check_dependencies(dependencies: list[str]) -> dict[str, Any]:
    """Check if declared dependencies are in the allowlist and available.

    Args:
        dependencies: List of library names declared by the artifact.

    Returns:
        Dict with passed (bool) and missing/blocked lists.
    """
    blocked = [dep for dep in dependencies if dep.lower() not in ALLOWED_LIBRARIES]
    missing: list[str] = []

    for dep in dependencies:
        if dep.lower() in blocked:
            continue
        # Map common names to import names
        import_name = dep
        if dep.lower() == "scikit-learn":
            import_name = "sklearn"
        try:
            __import__(import_name)
        except ImportError:
            missing.append(dep)

    return {
        "passed": len(blocked) == 0 and len(missing) == 0,
        "blocked": blocked,
        "missing": missing,
    }


def run_code(
    code: str,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Execute Python code in a subprocess and capture results.

    Args:
        code: Python source code to execute.
        timeout: Maximum execution time in seconds.

    Returns:
        Dict with passed (bool), exit_code (int), stdout (str), stderr (str).
    """
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, dir=tempfile.gettempdir()
    ) as f:
        f.write(code)
        f.flush()
        script_path = f.name

    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=tempfile.gettempdir(),
        )
        return {
            "passed": result.returncode == 0,
            "exit_code": result.returncode,
            "stdout": result.stdout[:5000],
            "stderr": result.stderr[:5000],
        }
    except subprocess.TimeoutExpired:
        return {
            "passed": False,
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Execution timed out after {timeout}s",
        }
    except Exception as e:
        return {
            "passed": False,
            "exit_code": -1,
            "stdout": "",
            "stderr": str(e),
        }
    finally:
        Path(script_path).unlink(missing_ok=True)


def validate_code_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
    """Validate an implementation artifact by running its Python examples.

    Args:
        artifact: The implementation artifact data.

    Returns:
        Dict with passed (bool), results (list of per-example results).
    """
    python_examples = artifact.get("python_examples", [])
    if not python_examples:
        return {"passed": True, "results": [], "note": "No Python examples to run"}

    # Check declared dependencies
    libraries = artifact.get("libraries", [])
    dep_check = check_dependencies(libraries)
    if not dep_check["passed"]:
        logger.warning(
            "Dependency check failed: blocked=%s, missing=%s",
            dep_check["blocked"],
            dep_check["missing"],
        )
        return {
            "passed": False,
            "results": [],
            "dependency_check": dep_check,
        }

    results: list[dict[str, Any]] = []
    all_passed = True

    for i, code in enumerate(python_examples):
        logger.info("Running Python example %d/%d", i + 1, len(python_examples))
        result = run_code(code)
        result["example_index"] = i
        results.append(result)
        if not result["passed"]:
            all_passed = False
            logger.warning(
                "Python example %d failed: exit_code=%d, stderr=%s",
                i,
                result["exit_code"],
                result["stderr"][:200],
            )

    return {"passed": all_passed, "results": results}
