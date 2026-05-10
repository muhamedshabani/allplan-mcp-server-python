from __future__ import annotations

import builtins
import contextlib
import io
from typing import Annotated, Any

import NemAll_Python_AllplanSettings as AllplanSettings
import NemAll_Python_BaseElements as AllplanBaseEle
import NemAll_Python_BaseElements as AllplanBaseElements
import NemAll_Python_BasisElements as AllplanBasisElements
import NemAll_Python_Geometry as AllplanGeo
import NemAll_Python_IFW_Input as AllplanIFW

from .const import allowed_builtin_names
from .validator import SandboxValidator


SandboxRequest = Annotated[dict[str, Any], "Incoming execute_python request"]
SandboxResult = Annotated[dict[str, Any], "JSON-safe execution result"]


class SandboxExecutor:
    """Run sandbox code"""

    def __init__(
        self,
        coord_input: AllplanIFW.CoordinateInput,
        validator: SandboxValidator | None = None,
    ) -> None:
        self.coord_input = coord_input
        self.validator = validator or SandboxValidator()

    def execute(self, request: SandboxRequest) -> SandboxResult:
        if not isinstance(request, dict):
            raise Exception("Request body must be a JSON object.")

        code = request.get("code")
        result_expression = request.get("result_expression")

        if not isinstance(code, str) or not code.strip():
            raise Exception("'code' must be a non-empty string.")

        if result_expression is not None and not isinstance(result_expression, str):
            raise Exception("'result_expression' must be a string when provided.")

        self.validator.validate_exec(code)
        if result_expression:
            self.validator.validate_eval(result_expression)

        exec_scope = {
            "__builtins__": self.safe_builtins(),
            "coord_input": self.coord_input,
            "AllplanGeo": AllplanGeo,
            "AllplanIFW": AllplanIFW,
            "AllplanSettings": AllplanSettings,
            "AllplanBaseElements": AllplanBaseElements,
            "AllplanBasisElements": AllplanBasisElements,
            "AllplanBaseEle": AllplanBaseEle,
        }
        stdout_buffer = io.StringIO()

        with contextlib.redirect_stdout(stdout_buffer):
            exec(code, exec_scope, exec_scope)

            if result_expression:
                result_value = eval(result_expression, exec_scope, exec_scope)
            else:
                result_value = exec_scope.get("result")

        return {
            "ok": True,
            "stdout": stdout_buffer.getvalue(),
            "result": self.make_json_safe(result_value),
        }

    def safe_builtins(self) -> dict[str, Any]:
        return {
            name: getattr(builtins, name)
            for name in allowed_builtin_names
        }

    def make_json_safe(self, value: Any) -> Any:
        if value is None or isinstance(value, (bool, int, float, str)):
            return value

        if isinstance(value, list):
            return [self.make_json_safe(item) for item in value]

        if isinstance(value, tuple):
            return [self.make_json_safe(item) for item in value]

        if isinstance(value, dict):
            return {
                str(key): self.make_json_safe(item)
                for key, item in value.items()
            }

        return repr(value)
