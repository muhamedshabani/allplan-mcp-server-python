from __future__ import annotations

import builtins
import contextlib
from typing import Annotated, Any

from .const import allowed_builtin_names
from .errors import (
    RESULT_FILENAME,
    SANDBOX_FILENAME,
    runtime_error_payload,
    syntax_error_payload,
    timeout_error_payload,
    validation_error_payload,
)
from .limits import DeadlineWatchdog, SandboxLimits, SandboxTimeoutError, TruncatingStringIO
from .validator import SandboxValidationError, SandboxValidator

SandboxRequest = Annotated[dict[str, Any], "Incoming execute_python request"]
SandboxResult = Annotated[dict[str, Any], "JSON-safe execution result"]
ApiScope = Annotated[dict[str, Any], "Host supplied globals, e.g. Allplan modules"]

TRUNCATION_SUFFIX = "... [truncated]"


class ResultBudget:
    """Track how much of the result budget has been spent"""

    def __init__(self, limits: SandboxLimits) -> None:
        self.limits = limits
        self.chars = 0
        self.truncated = False

    def text(self, value: str) -> str:
        remaining = self.limits.max_result_chars - self.chars
        if remaining <= 0:
            self.truncated = True
            return TRUNCATION_SUFFIX

        if len(value) > remaining:
            self.chars = self.limits.max_result_chars
            self.truncated = True
            return value[:remaining] + TRUNCATION_SUFFIX

        self.chars += len(value)
        return value

    def items(self, values: list[Any]) -> list[Any]:
        if len(values) > self.limits.max_result_items:
            self.truncated = True
            return values[: self.limits.max_result_items]
        return values


class SandboxRuntime:
    """Validate and run sandbox code under time and size budgets

    This module deliberately imports nothing from Allplan. The host passes the
    Allplan modules in as ``api_scope``, which keeps the whole execution path
    importable - and testable - off a Windows Allplan install.
    """

    def __init__(
        self,
        validator: SandboxValidator | None = None,
        limits: SandboxLimits | None = None,
    ) -> None:
        self.validator = validator or SandboxValidator()
        self.limits = limits or SandboxLimits()
        self.limits.validate()

    def execute(self, request: SandboxRequest, api_scope: ApiScope) -> SandboxResult:
        code, result_expression = self.read_request(request)

        # Compile before validating. Compiling does not execute anything, and
        # doing it first means a SyntaxError keeps its line and column instead
        # of being flattened into a generic validation message.
        try:
            compiled_code = compile(code, SANDBOX_FILENAME, "exec")
            compiled_result = (
                compile(result_expression, RESULT_FILENAME, "eval")
                if result_expression
                else None
            )
        except SyntaxError as error:
            source = code if error.filename == SANDBOX_FILENAME else result_expression
            return self.failure(syntax_error_payload(error, source or code), "", False)

        try:
            self.validator.validate_exec(code)
            if result_expression:
                self.validator.validate_eval(result_expression)
        except SandboxValidationError as error:
            return self.failure(validation_error_payload(error), "", False)

        exec_scope: dict[str, Any] = {"__builtins__": self.safe_builtins()}
        exec_scope.update(api_scope)

        stdout_buffer = TruncatingStringIO(self.limits.max_stdout_chars)

        try:
            with (
                contextlib.redirect_stdout(stdout_buffer),
                DeadlineWatchdog(self.limits.timeout_seconds),
            ):
                exec(compiled_code, exec_scope, exec_scope)

                if compiled_result is not None:
                    result_value = eval(compiled_result, exec_scope, exec_scope)
                else:
                    result_value = exec_scope.get("result")
        except SandboxTimeoutError as error:
            return self.failure(
                timeout_error_payload(error, code),
                stdout_buffer.getvalue(),
                stdout_buffer.truncated,
            )
        except BaseException as error:
            return self.failure(
                runtime_error_payload(error, code),
                stdout_buffer.getvalue(),
                stdout_buffer.truncated,
            )

        budget = ResultBudget(self.limits)
        payload = self.make_json_safe(result_value, budget)

        return {
            "ok": True,
            "stdout": stdout_buffer.getvalue(),
            "stdout_truncated": stdout_buffer.truncated,
            "result": payload,
            "result_truncated": budget.truncated,
        }

    def read_request(self, request: SandboxRequest) -> tuple[str, str | None]:
        if not isinstance(request, dict):
            raise ValueError("Request body must be a JSON object.")

        code = request.get("code")
        result_expression = request.get("result_expression")

        if not isinstance(code, str) or not code.strip():
            raise ValueError("'code' must be a non-empty string.")

        if result_expression is not None and not isinstance(result_expression, str):
            raise ValueError("'result_expression' must be a string when provided.")

        return code, result_expression

    def failure(
        self,
        error: dict[str, Any],
        stdout: str,
        stdout_truncated: bool,
    ) -> SandboxResult:
        return {
            "ok": False,
            "stdout": stdout,
            "stdout_truncated": stdout_truncated,
            "result": None,
            "error": error,
        }

    def safe_builtins(self) -> dict[str, Any]:
        return {name: getattr(builtins, name) for name in allowed_builtin_names}

    def make_json_safe(self, value: Any, budget: ResultBudget) -> Any:
        if value is None or isinstance(value, bool):
            return value

        if isinstance(value, int):
            return value

        if isinstance(value, float):
            return value

        if isinstance(value, str):
            return budget.text(value)

        if isinstance(value, (list, tuple)):
            return [
                self.make_json_safe(item, budget)
                for item in budget.items(list(value))
            ]

        if isinstance(value, dict):
            entries = budget.items(list(value.items()))
            return {
                budget.text(str(key)): self.make_json_safe(item, budget)
                for key, item in entries
            }

        return budget.text(repr(value))
