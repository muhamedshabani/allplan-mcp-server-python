from __future__ import annotations

import pytest
from PythonHost.sandbox.limits import SandboxLimits
from PythonHost.sandbox.runtime import SandboxRuntime


def run(runtime: SandboxRuntime, code: str, result_expression: str | None = None):
    request = {"code": code}
    if result_expression is not None:
        request["result_expression"] = result_expression
    return runtime.execute(request, {"marker": object()})


def test_returns_the_result_variable(runtime: SandboxRuntime) -> None:
    response = run(runtime, "result = 6 * 7")

    assert response["ok"] is True
    assert response["result"] == 42
    assert "error" not in response


def test_evaluates_a_result_expression(runtime: SandboxRuntime) -> None:
    response = run(runtime, "value = 10", "value + 5")

    assert response["ok"] is True
    assert response["result"] == 15


def test_captures_stdout(runtime: SandboxRuntime) -> None:
    response = run(runtime, "print('hello allplan')\nresult = 1")

    assert response["stdout"] == "hello allplan\n"
    assert response["stdout_truncated"] is False


def test_host_scope_is_available_to_the_code(runtime: SandboxRuntime) -> None:
    response = run(runtime, "result = marker is not None")

    assert response["result"] is True


def test_host_scope_does_not_leak_real_builtins(runtime: SandboxRuntime) -> None:
    response = run(runtime, "result = 1", "print")

    assert response["ok"] is True


class TestFailures:
    def test_validation_failure_is_data_not_an_exception(
        self, runtime: SandboxRuntime
    ) -> None:
        response = run(runtime, "import os\nresult = 1")

        assert response["ok"] is False
        assert response["error"]["kind"] == "validation_error"
        assert "import statements" in response["error"]["message"]

    def test_syntax_error_reports_the_offending_line(
        self, runtime: SandboxRuntime
    ) -> None:
        response = run(runtime, "result = 1\nresult = = 2\n")

        assert response["ok"] is False
        error = response["error"]
        assert error["kind"] == "syntax_error"
        assert error["lineno"] == 2

    def test_runtime_error_reports_the_line_the_agent_wrote(
        self, runtime: SandboxRuntime
    ) -> None:
        code = "a = 1\nb = 0\nresult = a / b\n"
        response = run(runtime, code)

        error = response["error"]
        assert response["ok"] is False
        assert error["kind"] == "runtime_error"
        assert error["type"] == "ZeroDivisionError"
        assert error["lineno"] == 3
        assert error["line"] == "result = a / b"

    def test_traceback_hides_bridge_internals(self, runtime: SandboxRuntime) -> None:
        response = run(runtime, "def go():\n    raise ValueError('nope')\ngo()\n")

        frames = response["error"]["frames"]
        assert [frame["name"] for frame in frames] == ["<module>", "go"]
        assert all("runtime.py" not in str(frame) for frame in frames)

    def test_stdout_is_kept_when_the_code_fails(self, runtime: SandboxRuntime) -> None:
        response = run(runtime, "print('progress')\nraise ValueError('late')\n")

        assert response["ok"] is False
        assert response["stdout"] == "progress\n"

    def test_unbounded_loop_is_aborted(self) -> None:
        runtime = SandboxRuntime(limits=SandboxLimits(timeout_seconds=0.25))
        response = run(runtime, "while True:\n    pass\n")

        assert response["ok"] is False
        assert response["error"]["kind"] == "timeout"

    def test_rejects_an_empty_request(self, runtime: SandboxRuntime) -> None:
        with pytest.raises(ValueError):
            runtime.execute({"code": "   "}, {})


class TestBudgets:
    def test_stdout_is_capped(self) -> None:
        runtime = SandboxRuntime(limits=SandboxLimits(max_stdout_chars=50))
        response = run(runtime, "for n in range(1000):\n    print('noise')\n")

        assert response["ok"] is True
        assert response["stdout_truncated"] is True
        assert len(response["stdout"]) == 50

    def test_long_result_strings_are_truncated(self) -> None:
        runtime = SandboxRuntime(limits=SandboxLimits(max_result_chars=20))
        response = run(runtime, "result = 'x' * 5000")

        assert response["result_truncated"] is True
        assert len(response["result"]) < 100

    def test_long_result_lists_are_truncated(self) -> None:
        runtime = SandboxRuntime(limits=SandboxLimits(max_result_items=10))
        response = run(runtime, "result = list(range(500))")

        assert response["result_truncated"] is True
        assert len(response["result"]) == 10


class TestJsonSafety:
    def test_nested_structures_survive(self, runtime: SandboxRuntime) -> None:
        response = run(runtime, "result = {'a': [1, 2.5, True, None], 'b': (3, 4)}")

        assert response["result"] == {"a": [1, 2.5, True, None], "b": [3, 4]}

    def test_unserializable_objects_become_repr(self, runtime: SandboxRuntime) -> None:
        response = run(runtime, "result = marker")

        assert isinstance(response["result"], str)
        assert "object" in response["result"]

    def test_dict_keys_are_stringified(self, runtime: SandboxRuntime) -> None:
        response = run(runtime, "result = {1: 'one'}")

        assert response["result"] == {"1": "one"}
