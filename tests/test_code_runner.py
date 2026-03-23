"""Tests for the code execution validation module."""

from pipeline.code_runner import (
    check_dependencies,
    extract_imports,
    run_code,
    validate_code_artifact,
)


class TestCheckDependencies:
    def test_allowed_dependencies_pass(self):
        result = check_dependencies(["math", "random", "json"])
        assert result["passed"] is True
        assert result["blocked"] == []

    def test_blocked_dependency_fails(self):
        result = check_dependencies(["requests"])
        assert result["passed"] is False
        assert "requests" in result["blocked"]

    def test_empty_dependencies_pass(self):
        result = check_dependencies([])
        assert result["passed"] is True

    def test_mixed_dependencies(self):
        result = check_dependencies(["numpy", "dangerous_lib"])
        assert result["passed"] is False
        assert "dangerous_lib" in result["blocked"]


class TestExtractImports:
    def test_extracts_top_level_imports(self):
        imports = extract_imports(
            "import numpy as np\nfrom scipy.optimize import minimize\nfrom sklearn.model_selection import train_test_split"
        )
        assert imports == {"numpy", "scipy", "sklearn"}


class TestRunCode:
    def test_successful_code_passes(self):
        result = run_code("print('hello world')")
        assert result["passed"] is True
        assert result["exit_code"] == 0
        assert "hello world" in result["stdout"]

    def test_syntax_error_fails(self):
        result = run_code("def broken(")
        assert result["passed"] is False
        assert result["exit_code"] != 0

    def test_runtime_error_fails(self):
        result = run_code("raise ValueError('test error')")
        assert result["passed"] is False
        assert "ValueError" in result["stderr"]

    def test_timeout_fails(self):
        result = run_code("import time; time.sleep(10)", timeout=1)
        assert result["passed"] is False
        assert "timed out" in result["stderr"].lower()

    def test_import_math(self):
        result = run_code("import math; print(math.pi)")
        assert result["passed"] is True
        assert "3.14" in result["stdout"]


class TestValidateCodeArtifact:
    def test_no_examples_passes(self):
        artifact = {"python_examples": [], "libraries": [], "runtime_dependencies": []}
        result = validate_code_artifact(artifact)
        assert result["passed"] is True

    def test_valid_examples_pass(self):
        artifact = {
            "python_examples": ["print('test')", "x = 1 + 2\nprint(x)"],
            "libraries": ["math"],
            "runtime_dependencies": [],
        }
        result = validate_code_artifact(artifact)
        assert result["passed"] is True
        assert len(result["results"]) == 2

    def test_failing_example_fails(self):
        artifact = {
            "python_examples": ["raise RuntimeError('fail')"],
            "libraries": [],
            "runtime_dependencies": [],
        }
        result = validate_code_artifact(artifact)
        assert result["passed"] is False

    def test_blocked_library_fails(self):
        artifact = {
            "python_examples": ["print('ok')"],
            "libraries": ["requests"],
            "runtime_dependencies": ["requests"],
        }
        result = validate_code_artifact(artifact)
        assert result["passed"] is False
        assert "dependency_check" in result

    def test_undeclared_import_fails(self):
        artifact = {
            "python_examples": ["import numpy as np\nprint(np.zeros(1))"],
            "libraries": ["NumPy - Numerical arrays"],
            "runtime_dependencies": [],
        }
        result = validate_code_artifact(artifact)
        assert result["passed"] is False
        assert "numpy" in result["undeclared_imports"]
