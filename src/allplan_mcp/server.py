from __future__ import annotations

import os
from typing import Any

from fastmcp import FastMCP

from allplan_mcp.allplan_client import AllplanHostClient


DEFAULT_ALLPLAN_HOST_URL = "http://127.0.0.1:5679"
DEFAULT_MCP_HOST = "127.0.0.1"
DEFAULT_MCP_PORT = 8000
DEFAULT_MCP_PATH = "/mcp"

mcp = FastMCP("Allplan MCP Server")


def _allplan_client() -> AllplanHostClient:
    return AllplanHostClient(
        base_url=os.getenv("ALLPLAN_HOST_URL", DEFAULT_ALLPLAN_HOST_URL),
        timeout=float(os.getenv("ALLPLAN_HOST_TIMEOUT", "30")),
    )


def _python_exec_enabled() -> bool:
    return os.getenv("ALLPLAN_MCP_ENABLE_PYTHON_EXEC", "0") == "1"


@mcp.tool
def allplan_health() -> dict[str, Any]:
    """Check that the Allplan Python host is reachable."""

    response = _allplan_client().post("/get-allplan-version")
    return {
        "ok": True,
        "allplan_version": response.get("version"),
        "allplan_host_url": os.getenv("ALLPLAN_HOST_URL", DEFAULT_ALLPLAN_HOST_URL),
    }


@mcp.tool
def get_allplan_version() -> str:
    """Get the version of the running Allplan instance."""

    response = _allplan_client().post("/get-allplan-version")
    return str(response["version"])


@mcp.tool
def get_all_object_names() -> list[str]:
    """Get display names for all elements in the current Allplan document."""

    response = _allplan_client().post("/get-all-object-names")
    names = response.get("names", [])
    if not isinstance(names, list):
        raise ValueError(f"Unexpected Allplan response for names: {response!r}")

    return [str(name) for name in names]


@mcp.tool
def create_cube(size: float) -> dict[str, Any]:
    """Create a cube in the current Allplan document."""

    if size <= 0:
        raise ValueError("size must be greater than zero.")

    _allplan_client().post(
        "/create-box",
        {
            "length": size,
            "width": size,
            "height": size,
        },
    )
    return {
        "created": True,
        "type": "cube",
        "dimensions": {
            "length": size,
            "width": size,
            "height": size,
        },
    }


@mcp.tool
def create_box(length: float, width: float, height: float) -> dict[str, Any]:
    """Create a cuboid in the current Allplan document."""

    if length <= 0 or width <= 0 or height <= 0:
        raise ValueError("length, width, and height must be greater than zero.")

    _allplan_client().post(
        "/create-box",
        {
            "length": length,
            "width": width,
            "height": height,
        },
    )
    return {
        "created": True,
        "type": "cuboid",
        "dimensions": {
            "length": length,
            "width": width,
            "height": height,
        },
    }


if _python_exec_enabled():

    @mcp.tool
    def execute_python(
        code: str,
        result_expression: str | None = None,
    ) -> dict[str, Any]:
        """Execute Python inside Allplan for local development only."""

        if not code.strip():
            raise ValueError("code must be a non-empty string.")

        payload: dict[str, Any] = {"code": code}
        if result_expression is not None:
            payload["result_expression"] = result_expression

        return _allplan_client().post("/execute-python", payload)


def main() -> None:
    host = os.getenv("MCP_HOST", DEFAULT_MCP_HOST)
    port = int(os.getenv("MCP_PORT", str(DEFAULT_MCP_PORT)))
    path = os.getenv("MCP_PATH", DEFAULT_MCP_PATH)

    mcp.run(transport="http", host=host, port=port, path=path)


if __name__ == "__main__":
    main()
