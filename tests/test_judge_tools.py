"""Tests for the tool-calling judge: tool functions, dispatch, and the loop."""

import json
from unittest.mock import MagicMock, patch

import pytest

from pipeline.judge import evaluate_artifact
from pipeline.judge_tools import (
    TOOL_REGISTRY,
    check_equation,
    dispatch_tool,
    lookup_reference,
    run_python_code,
    tool_declarations,
    verify_imports,
)


class TestRunPythonCode:
    def test_happy_path(self):
        result = run_python_code("print('hello')")
        assert result["passed"] is True
        assert "hello" in result["stdout"]
        assert result["exit_code"] == 0

    def test_runtime_error_captured(self):
        result = run_python_code("raise ValueError('boom')")
        assert result["passed"] is False
        assert "ValueError" in result["stderr"]

    def test_rejects_empty(self):
        assert run_python_code("")["error"]
        assert run_python_code("   ")["error"]

    def test_rejects_non_string(self):
        # type: ignore[arg-type] — exercising the type guard
        assert run_python_code(123)["error"]  # type: ignore[arg-type]

    def test_clamps_timeout(self):
        result = run_python_code("print(1)", timeout_s=999)
        assert result["timeout_s"] == 15  # clamped to default
        assert result["passed"] is True


class TestCheckEquation:
    def test_well_formed(self):
        result = check_equation(r"$\sum_{i=1}^n x_i = \frac{a}{b}$")
        assert result["parsable"] is True
        assert result["errors"] == []

    def test_unbalanced_braces(self):
        result = check_equation(r"\frac{a}{b")
        assert result["parsable"] is False
        assert any("Unbalanced '{}'" in e for e in result["errors"])

    def test_unknown_command(self):
        result = check_equation(r"$\fract{a}{b}$")
        assert result["parsable"] is False
        assert any("Unknown LaTeX commands" in e for e in result["errors"])

    def test_rejects_empty(self):
        assert "error" in check_equation("")
        assert "error" in check_equation("   ")


class TestLookupReference:
    def test_missing_file(self):
        result = lookup_reference("nonexistent-technique-xyz")
        assert result["found"] is False

    def test_existing_file(self, tmp_path, monkeypatch):
        ref_file = tmp_path / "demo-technique.json"
        ref_file.write_text(json.dumps({
            "key_facts": ["Fact A", "Fact B"],
            "forbidden_claims": ["Lie 1"],
        }))
        monkeypatch.setattr("pipeline.judge_tools.REFERENCE_DIR", tmp_path)
        result = lookup_reference("demo-technique")
        assert result["found"] is True
        assert result["key_facts"] == ["Fact A", "Fact B"]
        assert result["forbidden_claims"] == ["Lie 1"]

    def test_rejects_empty(self):
        assert "error" in lookup_reference("")


class TestVerifyImports:
    def test_allowed_library(self):
        # Use stdlib modules so the test passes regardless of optional deps
        result = verify_imports(["math", "json"])
        assert result["passed"] is True
        assert result["blocked"] == []
        assert result["missing"] == []

    def test_blocked_library(self):
        result = verify_imports(["requests"])  # not in allowlist
        assert result["passed"] is False
        assert "requests" in result["blocked"]

    def test_rejects_non_list(self):
        # type: ignore[arg-type]
        assert "error" in verify_imports("numpy")  # type: ignore[arg-type]


class TestDispatch:
    def test_routes_known_tool(self):
        result = dispatch_tool("run_python_code", {"code": "print('ok')"})
        assert result["passed"] is True

    def test_unknown_tool(self):
        result = dispatch_tool("not_a_tool", {})
        assert "Unknown tool" in result["error"]

    def test_bad_arguments(self):
        result = dispatch_tool("run_python_code", {"wrong_arg": "x"})
        assert "Bad arguments" in result["error"]

    def test_tool_exception_swallowed(self):
        original = TOOL_REGISTRY["check_equation"]["function"]
        TOOL_REGISTRY["check_equation"]["function"] = MagicMock(
            side_effect=RuntimeError("boom")
        )
        try:
            result = dispatch_tool("check_equation", {"latex": "x"})
            assert "RuntimeError" in result["error"]
        finally:
            TOOL_REGISTRY["check_equation"]["function"] = original


class TestToolDeclarations:
    def test_lists_all_tools(self):
        decls = tool_declarations()
        names = {d["name"] for d in decls}
        assert names == {
            "run_python_code",
            "check_equation",
            "lookup_reference",
            "verify_imports",
        }

    def test_each_has_required_fields(self):
        for decl in tool_declarations():
            assert decl["name"]
            assert decl["description"]
            assert decl["parameters"]["type"] == "object"


class TestEvaluateArtifactWithTools:
    """End-to-end: evaluate_artifact uses generate_with_tools when available."""

    def _build_mock_provider(self, loop_result):
        provider = MagicMock()
        provider.generate_with_tools = MagicMock(return_value=loop_result)
        return provider

    def test_passes_through_tool_calls(self):
        judge_payload = {
            "passed": True,
            "overall_score": 8,
            "criteria_scores": {
                "factual_accuracy": 8,
                "math_correctness": 8,
                "clarity": 8,
                "code_quality": 8,
            },
            "critiques": [],
            "revision_instructions": [],
        }
        loop_result = {
            "text": json.dumps(judge_payload),
            "tool_calls": [
                {
                    "name": "run_python_code",
                    "args": {"code": "print(1)"},
                    "result": {"passed": True, "stdout": "1\n"},
                    "iteration": 1,
                }
            ],
            "iterations": 2,
        }
        provider = self._build_mock_provider(loop_result)

        with patch("pipeline.judge.get_provider", return_value=provider):
            result = evaluate_artifact(
                "uct-upper-confidence-bounds-for-trees",
                "implementation",
                {"markdown": "stub", "python_examples": ["print(1)"]},
            )

        assert result["passed"] is True
        assert result["overall_score"] == 8
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["name"] == "run_python_code"
        assert result["iterations"] == 2

    def test_handles_unparseable_text(self):
        provider = self._build_mock_provider({
            "text": "I cannot decide.",
            "tool_calls": [],
            "iterations": 1,
        })
        with patch("pipeline.judge.get_provider", return_value=provider):
            result = evaluate_artifact(
                "uct-upper-confidence-bounds-for-trees",
                "overview",
                {"summary": "x"},
            )
        assert result["passed"] is False
        assert "did not return valid JSON" in result["critiques"][0]

    def test_handles_schema_invalid_json(self):
        provider = self._build_mock_provider({
            "text": json.dumps({"passed": "yes"}),  # wrong types
            "tool_calls": [],
            "iterations": 1,
        })
        with patch("pipeline.judge.get_provider", return_value=provider):
            result = evaluate_artifact(
                "uct-upper-confidence-bounds-for-trees",
                "overview",
                {"summary": "x"},
            )
        assert result["passed"] is False
        assert "schema validation" in result["critiques"][0]

    def test_extracts_json_from_fenced_block(self):
        judge_payload = {
            "passed": False,
            "overall_score": 3,
            "criteria_scores": {
                "factual_accuracy": 3,
                "math_correctness": 3,
                "clarity": 3,
                "code_quality": 3,
            },
            "critiques": ["Missing math"],
            "revision_instructions": ["Add LaTeX"],
        }
        loop_result = {
            "text": f"Here is my evaluation:\n```json\n{json.dumps(judge_payload)}\n```",
            "tool_calls": [],
            "iterations": 1,
        }
        provider = self._build_mock_provider(loop_result)
        with patch("pipeline.judge.get_provider", return_value=provider):
            result = evaluate_artifact(
                "uct-upper-confidence-bounds-for-trees",
                "math_deep_dive",
                {"markdown": "x"},
            )
        assert result["passed"] is False
        assert result["overall_score"] == 3

    def test_legacy_path_when_use_tools_false(self):
        provider = MagicMock()
        provider.generate.return_value = {
            "passed": True,
            "overall_score": 9,
            "criteria_scores": {},
            "critiques": [],
            "revision_instructions": [],
        }
        # Provider must NOT have generate_with_tools called
        with patch("pipeline.judge.get_provider", return_value=provider), \
             patch("pipeline.judge.load_reference", return_value=None):
            result = evaluate_artifact(
                "uct-upper-confidence-bounds-for-trees",
                "overview",
                {"summary": "x"},
                use_tools=False,
            )
        assert result["passed"] is True
        assert result["tool_calls"] == []
        provider.generate.assert_called()


class TestGenerateWithToolsLoop:
    """Verify the GeminiProvider tool-use loop dispatches correctly."""

    def _make_provider(self):
        from pipeline.llm_client import GeminiProvider

        with patch.dict("os.environ", {"GEMINI_API_KEY": "fake"}), \
             patch("pipeline.llm_client.genai") as mock_genai:
            mock_client = MagicMock()
            mock_genai.Client.return_value = mock_client
            provider = GeminiProvider(model="gemini-test", api_key_env="GEMINI_API_KEY")
            return provider, mock_client

    def _make_response(self, *, text=None, function_calls=None):
        candidate = MagicMock()
        parts = []
        if function_calls:
            for name, args in function_calls:
                p = MagicMock()
                p.text = None
                fc = MagicMock()
                fc.name = name
                fc.args = args
                p.function_call = fc
                parts.append(p)
        if text:
            p = MagicMock()
            p.text = text
            p.function_call = None
            parts.append(p)
        candidate.content.parts = parts
        response = MagicMock()
        response.candidates = [candidate]
        return response

    def test_terminates_on_text_only_response(self):
        provider, mock_client = self._make_provider()
        mock_client.models.generate_content.return_value = self._make_response(
            text='{"final": true}'
        )
        dispatch = MagicMock()
        result = provider.generate_with_tools(
            system_prompt="sys",
            user_prompt="user",
            tools=tool_declarations(),
            dispatch=dispatch,
        )
        assert result["text"] == '{"final": true}'
        assert result["tool_calls"] == []
        assert result["iterations"] == 1
        dispatch.assert_not_called()

    def test_dispatches_function_call_then_finalizes(self):
        provider, mock_client = self._make_provider()
        mock_client.models.generate_content.side_effect = [
            self._make_response(function_calls=[("run_python_code", {"code": "print(1)"})]),
            self._make_response(text='{"score": 7}'),
        ]
        dispatch = MagicMock(return_value={"passed": True, "stdout": "1\n"})
        result = provider.generate_with_tools(
            system_prompt="sys",
            user_prompt="user",
            tools=tool_declarations(),
            dispatch=dispatch,
        )
        dispatch.assert_called_once_with("run_python_code", {"code": "print(1)"})
        assert result["text"] == '{"score": 7}'
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["name"] == "run_python_code"
        assert result["iterations"] == 2

    def test_respects_max_iterations(self):
        provider, mock_client = self._make_provider()
        mock_client.models.generate_content.return_value = self._make_response(
            function_calls=[("run_python_code", {"code": "x"})]
        )
        dispatch = MagicMock(return_value={"passed": False})
        result = provider.generate_with_tools(
            system_prompt="sys",
            user_prompt="user",
            tools=tool_declarations(),
            dispatch=dispatch,
            max_iterations=3,
        )
        assert result["iterations"] == 3
        assert result.get("max_iterations_reached") is True
        assert dispatch.call_count == 3
