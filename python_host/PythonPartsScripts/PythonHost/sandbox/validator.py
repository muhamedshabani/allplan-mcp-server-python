from __future__ import annotations

import ast
from typing import Annotated, Literal

from .const import blocked_attribute_names, blocked_builtin_names

SandboxMode = Annotated[Literal["exec", "eval"], "AST parse mode"]
PythonSource = Annotated[str, "Sandbox source text"]


class SandboxValidationError(Exception):
    """Sandbox validation error"""


class SandboxAstValidator(ast.NodeVisitor):
    """Block unsafe syntax

    The attribute rules are the load bearing part. Note that str.format does
    attribute traversal at runtime, invisible to this walk:

        "{0.__globals__}".format(some_function)

    reaches the real builtins even though no dunder appears as an AST attribute
    node. That is why 'format' and 'format_map' are refused outright. f-strings
    are the supported alternative, because their attribute access is a real AST
    node and is checked above.
    """

    def visit_Import(self, node: ast.Import) -> None:
        raise SandboxValidationError("import statements are not allowed in execute_python.")

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        raise SandboxValidationError("import statements are not allowed in execute_python.")

    def visit_Global(self, node: ast.Global) -> None:
        raise SandboxValidationError("global statements are not allowed in execute_python.")

    def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
        raise SandboxValidationError("nonlocal statements are not allowed in execute_python.")

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        raise SandboxValidationError("class definitions are not allowed in execute_python.")

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        raise SandboxValidationError("async functions are not allowed in execute_python.")

    def visit_Await(self, node: ast.Await) -> None:
        raise SandboxValidationError("await is not allowed in execute_python.")

    def visit_Yield(self, node: ast.Yield) -> None:
        raise SandboxValidationError("yield is not allowed in execute_python.")

    def visit_YieldFrom(self, node: ast.YieldFrom) -> None:
        raise SandboxValidationError("yield from is not allowed in execute_python.")

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr.startswith("_"):
            raise SandboxValidationError(
                f"attribute '{node.attr}' is not allowed in execute_python."
            )
        if node.attr in blocked_attribute_names:
            raise SandboxValidationError(
                f"attribute '{node.attr}' is not allowed in execute_python. "
                "Use an f-string instead, which this validator can inspect."
            )
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if node.id.startswith("_"):
            raise SandboxValidationError(
                f"name '{node.id}' is not allowed in execute_python."
            )
        if isinstance(node.ctx, ast.Load) and node.id in blocked_builtin_names:
            raise SandboxValidationError(
                f"builtin '{node.id}' is not allowed in execute_python."
            )
        self.generic_visit(node)


class SandboxValidator:
    """Validate sandbox code"""

    def validate_exec(self, source: PythonSource) -> None:
        self.validate_python_code(source, "exec")

    def validate_eval(self, source: PythonSource) -> None:
        self.validate_python_code(source, "eval")

    def validate_python_code(self, source: PythonSource, mode: SandboxMode) -> None:
        try:
            tree = ast.parse(source, filename="<sandbox>", mode=mode)
        except SyntaxError as error:
            raise SandboxValidationError(str(error)) from error

        SandboxAstValidator().visit(tree)
