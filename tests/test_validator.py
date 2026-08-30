from __future__ import annotations

import pytest
from PythonHost.sandbox.validator import SandboxValidationError, SandboxValidator


@pytest.fixture
def validator() -> SandboxValidator:
    return SandboxValidator()


ACCEPTED = [
    "result = 1 + 1",
    "result = AllplanGeo.Polyhedron3D.CreateCuboid(1, 2, 3)",
    "values = [n * 2 for n in range(5)]\nresult = sum(values)",
    "def helper(value):\n    return value * 2\nresult = helper(4)",
    'name = "beam"\nresult = f"{name} ok"',
]


REJECTED = [
    ("import os", "import statements"),
    ("from os import path", "import statements"),
    ("result = open('x')", "builtin 'open'"),
    ("result = eval('1')", "builtin 'eval'"),
    ("result = getattr(AllplanGeo, 'x')", "builtin 'getattr'"),
    ("class Thing:\n    pass", "class definitions"),
    ("async def go():\n    pass", "async functions"),
    ("def go():\n    yield 1", "yield"),
    ("global x", "global statements"),
    ("result = ().__class__", "__class__"),
    ("f = lambda: 1\nresult = f.__globals__", "__globals__"),
    ("result = _secret", "name '_secret'"),
]


@pytest.mark.parametrize("source", ACCEPTED)
def test_accepts_ordinary_allplan_code(validator: SandboxValidator, source: str) -> None:
    validator.validate_exec(source)


@pytest.mark.parametrize("source,expected", REJECTED)
def test_rejects_unsafe_code(
    validator: SandboxValidator, source: str, expected: str
) -> None:
    with pytest.raises(SandboxValidationError) as error:
        validator.validate_exec(source)

    assert expected in str(error.value)


# Regression: str.format performs attribute traversal at runtime, which the AST
# walk cannot see. Before this was blocked, the first case below reached the
# real builtins dict through a function's __globals__.
FORMAT_ESCAPES = [
    'f = lambda: 1\nresult = "{0.__globals__}".format(f)',
    'result = "{0.__class__.__base__.__subclasses__}".format(())',
    'result = "{0.__globals__}".format_map({0: print})',
]


@pytest.mark.parametrize("source", FORMAT_ESCAPES)
def test_rejects_format_based_reflection(
    validator: SandboxValidator, source: str
) -> None:
    with pytest.raises(SandboxValidationError):
        validator.validate_exec(source)


def test_syntax_error_is_reported_as_validation_error(
    validator: SandboxValidator,
) -> None:
    with pytest.raises(SandboxValidationError):
        validator.validate_exec("result = (")
