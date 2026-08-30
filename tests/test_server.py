from __future__ import annotations

import asyncio
from typing import Any

from fastmcp import Client

from allplan_mcp.server import _failure_hint, execute_python_description, mcp


def call(coroutine: Any) -> Any:
    return asyncio.run(coroutine)


async def list_tool_names() -> set[str]:
    async with Client(mcp) as client:
        return {tool.name for tool in await client.list_tools()}


async def call_tool(name: str, arguments: dict[str, Any]) -> Any:
    async with Client(mcp) as client:
        return await client.call_tool(name, arguments)


def test_skill_tools_are_registered() -> None:
    names = call(list_tool_names())

    assert {"list_allplan_skills", "search_allplan_skills", "read_allplan_skill"} <= names


def test_original_tools_are_still_registered() -> None:
    names = call(list_tool_names())

    assert {
        "allplan_health",
        "get_allplan_version",
        "get_all_object_names",
        "create_cube",
        "create_box",
        "execute_python",
    } <= names


def test_search_tool_returns_hits() -> None:
    result = call(call_tool("search_allplan_skills", {"query": "rebar shape", "limit": 3}))
    hits = result.data

    assert hits
    assert hits[0]["skill"] == "rebar"


def test_read_tool_returns_markdown() -> None:
    result = call(call_tool("read_allplan_skill", {"uri": "allplan://skills/geometry"}))

    assert "ALLPLAN" in result.data


class TestExecutePythonDescription:
    def test_names_every_bundled_skill(self) -> None:
        description = execute_python_description()

        for skill in ("api-reference", "geometry", "rebar", "utilities"):
            assert skill in description

    def test_points_at_the_search_tool(self) -> None:
        assert "search_allplan_skills" in execute_python_description()

    def test_is_used_as_the_registered_tool_description(self) -> None:
        async def describe() -> str | None:
            async with Client(mcp) as client:
                tools = await client.list_tools()
                return next(t.description for t in tools if t.name == "execute_python")

        assert "search_allplan_skills" in (call(describe()) or "")


class TestFailureHints:
    def test_validation_hint_explains_the_sandbox(self) -> None:
        hint = _failure_hint({"kind": "validation_error", "message": "no imports"})

        assert "Imports" in hint

    def test_timeout_hint_suggests_splitting_the_work(self) -> None:
        hint = _failure_hint({"kind": "timeout", "lineno": 4})

        assert "line 4" in hint
        assert "several execute_python calls" in hint

    def test_runtime_hint_names_the_exception(self) -> None:
        hint = _failure_hint({"kind": "runtime_error", "type": "ValueError", "lineno": 2})

        assert "ValueError" in hint
        assert "line 2" in hint
