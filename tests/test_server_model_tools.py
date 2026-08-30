"""The MCP tools that let an agent verify what it built."""

from __future__ import annotations

import asyncio
import base64
from typing import Any

import pytest
from fake_allplan import PNG_1X1
from fastmcp import Client
from mcp.types import ImageContent

from allplan_mcp import server
from allplan_mcp.server import _creation_result, mcp


def call(coroutine: Any) -> Any:
    return asyncio.run(coroutine)


async def call_tool(name: str, arguments: dict[str, Any]) -> Any:
    async with Client(mcp) as client:
        return await client.call_tool(name, arguments)


async def tool_names() -> set[str]:
    async with Client(mcp) as client:
        return {tool.name for tool in await client.list_tools()}


class FakeClient:
    """Stand in for the bridge client, recording what was posted"""

    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.calls: list[tuple[str, dict[str, Any] | None]] = []

    def post(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        self.calls.append((path, payload))
        return self.response


@pytest.fixture
def bridge(monkeypatch):
    def install(response: dict[str, Any]) -> FakeClient:
        client = FakeClient(response)
        monkeypatch.setattr(server, "_allplan_client", lambda: client)
        return client

    return install


def test_the_new_tools_are_registered():
    assert {"get_elements", "get_element_info", "capture_viewport"} <= call(tool_names())


def test_get_elements_passes_the_limit_through(bridge):
    client = bridge({"elements": [], "count": 0, "truncated": False})

    call(call_tool("get_elements", {"limit": 25}))

    assert client.calls == [("/get-elements", {"limit": 25})]


def test_get_elements_rejects_a_non_positive_limit(bridge):
    bridge({"elements": []})

    with pytest.raises(Exception, match="greater than zero"):
        call(call_tool("get_elements", {"limit": 0}))


def test_get_element_info_passes_the_uuid(bridge):
    client = bridge({"element": {"uuid": "a"}})

    call(call_tool("get_element_info", {"uuid": "a"}))

    assert client.calls == [("/get-element-info", {"uuid": "a"})]


def test_get_element_info_rejects_a_blank_uuid(bridge):
    bridge({"element": {}})

    with pytest.raises(Exception, match="non-empty"):
        call(call_tool("get_element_info", {"uuid": "   "}))


def test_capture_viewport_returns_image_content(bridge):
    bridge({"base64": base64.b64encode(PNG_1X1).decode("ascii"), "format": "png"})

    result = call(call_tool("capture_viewport", {}))

    image = next(c for c in result.content if isinstance(c, ImageContent))
    assert image.mimeType == "image/png"
    assert base64.b64decode(image.data) == PNG_1X1


def test_capture_viewport_sends_no_size_by_default(bridge):
    client = bridge({"base64": base64.b64encode(PNG_1X1).decode("ascii")})

    call(call_tool("capture_viewport", {}))

    assert client.calls == [("/capture-viewport", {})]


def test_capture_viewport_sends_both_dimensions(bridge):
    client = bridge({"base64": base64.b64encode(PNG_1X1).decode("ascii")})

    call(call_tool("capture_viewport", {"width": 800, "height": 600}))

    assert client.calls == [("/capture-viewport", {"width": 800, "height": 600})]


def test_capture_viewport_rejects_a_lone_dimension(bridge):
    bridge({"base64": ""})

    with pytest.raises(Exception, match="both"):
        call(call_tool("capture_viewport", {"width": 800}))


def test_capture_viewport_reports_a_missing_image(bridge):
    bridge({"ok": True})

    with pytest.raises(Exception, match="no image data"):
        call(call_tool("capture_viewport", {}))


def test_execute_python_sends_the_undo_flag(bridge):
    client = bridge({"ok": True, "result": 1})

    call(call_tool("execute_python", {"code": "result = 1", "undo": False}))

    assert client.calls[0][1]["undo"] is False


def test_execute_python_groups_undo_by_default(bridge):
    client = bridge({"ok": True, "result": 1})

    call(call_tool("execute_python", {"code": "result = 1"}))

    assert client.calls[0][1]["undo"] is True


# -- creation result shaping --------------------------------------------


def test_creation_result_lists_uuids():
    result = _creation_result(
        {"elements": [{"uuid": "a"}, {"uuid": "b"}]}, "cuboid", length=1.0
    )

    assert result["created"] is True
    assert result["uuids"] == ["a", "b"]
    assert result["dimensions"] == {"length": 1.0}


def test_creation_result_is_not_created_without_elements():
    # A request that did not raise is not the same as geometry in the document.
    result = _creation_result({"elements": []}, "cuboid", length=1.0)

    assert result["created"] is False
    assert result["uuids"] == []


def test_creation_result_tolerates_a_malformed_response():
    result = _creation_result({}, "cube", size=1.0)

    assert result["created"] is False
    assert result["elements"] == []


def test_creation_result_skips_elements_without_a_uuid():
    result = _creation_result(
        {"elements": [{"uuid": "a"}, {"name": "no uuid"}, {"uuid": None}]},
        "cuboid",
        length=1.0,
    )

    assert result["uuids"] == ["a"]


def test_create_box_surfaces_uuids(bridge):
    bridge({"elements": [{"uuid": "box-1", "name": "Cuboid"}], "count": 1})

    result = call(call_tool("create_box", {"length": 1, "width": 2, "height": 3}))

    assert result.data["uuids"] == ["box-1"]
    assert result.data["created"] is True
