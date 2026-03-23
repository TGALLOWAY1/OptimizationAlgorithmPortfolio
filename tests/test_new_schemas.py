"""Tests for the updated math_deep_dive and implementation schemas."""

import pytest
import jsonschema

from pipeline.schemas import SCHEMAS


class TestMathDeepDiveSchemaUpdated:
    def _make_valid(self):
        return {
            "technique_slug": "gradient-descent",
            "artifact_type": "math_deep_dive",
            "markdown": "word " * 800 + " $x^2$",
            "key_equations": [
                {
                    "equation": "$$x_{t+1} = x_t - \\alpha \\nabla f(x_t)$$",
                    "label": "Update Rule",
                    "step_by_step_derivation": [
                        "Start with the Taylor expansion of f around x_t.",
                        "Take the negative gradient direction to minimize.",
                        "Scale by learning rate alpha to control step size.",
                    ],
                }
            ],
            "worked_examples": ["Example 1 with $x^2$"],
            "common_confusions": ["Confusion about learning rate"],
        }

    def test_valid_passes(self):
        jsonschema.validate(self._make_valid(), SCHEMAS["math_deep_dive"])

    def test_key_equation_missing_derivation_fails(self):
        data = self._make_valid()
        del data["key_equations"][0]["step_by_step_derivation"]
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(data, SCHEMAS["math_deep_dive"])

    def test_key_equation_too_few_derivation_steps_fails(self):
        data = self._make_valid()
        data["key_equations"][0]["step_by_step_derivation"] = ["Only one step"]
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(data, SCHEMAS["math_deep_dive"])

    def test_key_equation_missing_label_fails(self):
        data = self._make_valid()
        del data["key_equations"][0]["label"]
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(data, SCHEMAS["math_deep_dive"])


class TestImplementationSchemaUpdated:
    def _make_valid(self):
        return {
            "technique_slug": "gradient-descent",
            "artifact_type": "implementation",
            "markdown": "word " * 800 + " ```python\nprint()```",
            "python_examples": ["print('hello')"],
            "libraries": ["scipy.optimize"],
            "runtime_dependencies": ["scipy"],
            "pseudo_code": "FUNCTION optimize()\n  RETURN x",
            "code_variations": [
                {"framework": "numpy", "label": "NumPy Implementation", "code": "import numpy as np\n..."},
                {"framework": "pytorch", "label": "PyTorch Implementation", "code": "import torch\n..."},
                {"framework": "scipy", "label": "SciPy Implementation", "code": "from scipy import optimize\n..."},
            ],
        }

    def test_valid_passes(self):
        jsonschema.validate(self._make_valid(), SCHEMAS["implementation"])

    def test_missing_code_variations_fails(self):
        data = self._make_valid()
        del data["code_variations"]
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(data, SCHEMAS["implementation"])

    def test_missing_runtime_dependencies_fails(self):
        data = self._make_valid()
        del data["runtime_dependencies"]
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(data, SCHEMAS["implementation"])

    def test_too_few_variations_fails(self):
        data = self._make_valid()
        data["code_variations"] = data["code_variations"][:2]
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(data, SCHEMAS["implementation"])

    def test_too_many_variations_fails(self):
        data = self._make_valid()
        data["code_variations"].append(
            {"framework": "jax", "label": "JAX", "code": "import jax"}
        )
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(data, SCHEMAS["implementation"])

