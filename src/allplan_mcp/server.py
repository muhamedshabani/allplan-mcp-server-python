from __future__ import annotations

import os
from typing import Annotated, Any

from fastmcp import FastMCP

from allplan_mcp.allplan_client import AllplanHostClient
from allplan_mcp.skills import SkillsManager

DEFAULT_ALLPLAN_HOST_URL = "http://127.0.0.1:5679"
DEFAULT_MCP_HOST = "127.0.0.1"
DEFAULT_MCP_PORT = 8888
DEFAULT_MCP_PATH = "/mcp"

mcp = FastMCP("Allplan MCP Server")
skills_manager = SkillsManager()


def _allplan_client() -> AllplanHostClient:
    return AllplanHostClient(
        base_url=os.getenv("ALLPLAN_HOST_URL", DEFAULT_ALLPLAN_HOST_URL),
        timeout=float(os.getenv("ALLPLAN_HOST_TIMEOUT", "30")),
    )


@mcp.resource(
    "allplan://skills",
    name="allplan-skills",
    title="ALLPLAN skills index",
    description="Index of bundled ALLPLAN skills and sample scripts",
    mime_type="text/markdown",
)
def allplan_skills_index() -> str:
    """Read the skills index"""

    return skills_manager.index_text()


@mcp.resource(
    "allplan://skills/{skill_name}",
    name="allplan-skill",
    title="ALLPLAN skill",
    description="Read one bundled ALLPLAN skill",
    mime_type="text/markdown",
)
def allplan_skill(skill_name: Annotated[str, "Skill folder name"]) -> str:
    """Read one skill"""

    return skills_manager.skill_text(skill_name)


@mcp.resource(
    "allplan://skills/{skill_name}/assets/{asset_name}",
    name="allplan-skill-asset",
    title="ALLPLAN skill asset",
    description="Read one bundled ALLPLAN asset note",
    mime_type="text/markdown",
)
def allplan_skill_asset(
    skill_name: Annotated[str, "Skill folder name"],
    asset_name: Annotated[str, "Asset file name"],
) -> str:
    """Read one asset"""

    return skills_manager.asset_text(skill_name, asset_name)


@mcp.resource(
    "allplan://skills/{skill_name}/scripts/{script_name}",
    name="allplan-skill-script",
    title="ALLPLAN skill script",
    description="Read one bundled ALLPLAN sample script",
    mime_type="text/x-python",
)
def allplan_skill_script(
    skill_name: Annotated[str, "Skill folder name"],
    script_name: Annotated[str, "Script file name"],
) -> str:
    """Read one sample script"""

    return skills_manager.script_text(skill_name, script_name)


READ_ONLY = {"readOnlyHint": True}


def execute_python_description() -> str:
    """Build the execute_python description, with the skills index inlined

    The bundled skills are also MCP resources, but most clients never fetch a
    resource on their own. Naming them here, in the description of the tool the
    model actually reaches for, is what gets them read.
    """

    lines = [
        "Execute Python inside the running Allplan process.",
        "",
        "The Allplan API modules are already in scope, no imports are allowed:",
        "AllplanGeo, AllplanIFW, AllplanSettings, AllplanBaseElements,",
        "AllplanBasisElements, AllplanBaseEle, and coord_input.",
        "",
        "Set a variable named 'result' or pass result_expression to return a value.",
        "Code runs under a wall clock budget and its stdout is captured.",
        "",
        "Before writing Allplan API code, read the bundled skills. Call",
        "search_allplan_skills(query) to find the relevant one, then",
        "read_allplan_skill(uri) to read it. Available skills:",
        "",
    ]
    for entry in skills_manager.entries.values():
        lines.append(f"- {entry.name}: {entry.description}")
    return "\n".join(lines)


@mcp.tool(annotations=READ_ONLY)
def list_allplan_skills() -> list[dict[str, str]]:
    """List the bundled ALLPLAN skill documents and their resource URIs.

    Covers reinforcement detailing, geometry, API reference lookup, and runtime
    helpers. Read these before writing Allplan API code with execute_python.
    """

    return skills_manager.documents()


@mcp.tool(annotations=READ_ONLY)
def search_allplan_skills(
    query: Annotated[str, "Free text query, e.g. 'rebar bending shape' or 'polyhedron'"],
    limit: Annotated[int, "Maximum number of hits"] = 5,
) -> list[dict[str, Any]]:
    """Search the bundled ALLPLAN skill documentation.

    Returns ranked hits with a snippet and a URI. Pass the URI to
    read_allplan_skill to read the full document.
    """

    if limit <= 0:
        raise ValueError("limit must be greater than zero.")

    return skills_manager.search(query, limit=limit)


@mcp.tool(annotations=READ_ONLY)
def read_allplan_skill(
    uri: Annotated[str, "Resource URI from list_allplan_skills or search_allplan_skills"],
) -> str:
    """Read one bundled ALLPLAN skill, asset note, or sample script in full."""

    return skills_manager.read_uri(uri)


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


@mcp.tool(description=execute_python_description())
def execute_python(
    code: Annotated[str, "Python source executed inside Allplan"],
    result_expression: Annotated[
        str | None, "Optional expression evaluated after the code runs"
    ] = None,
) -> dict[str, Any]:
    if not code.strip():
        raise ValueError("code must be a non-empty string.")

    payload: dict[str, Any] = {"code": code}
    if result_expression is not None:
        payload["result_expression"] = result_expression

    response = _allplan_client().post("/execute-python", payload)

    if response.get("ok") is False:
        error = response.get("error", {})
        if isinstance(error, dict):
            response["hint"] = _failure_hint(error)

    return response


def _failure_hint(error: dict[str, Any]) -> str:
    """Turn a sandbox failure into one actionable sentence"""

    kind = error.get("kind")
    lineno = error.get("lineno")
    location = f" at line {lineno}" if lineno else ""

    if kind == "validation_error":
        return (
            "The sandbox rejected this code before running it"
            f"{location}. Imports, class definitions, and underscore-prefixed "
            "names are not allowed. The Allplan modules are already in scope."
        )
    if kind == "syntax_error":
        return f"The submitted code does not parse{location}."
    if kind == "timeout":
        return (
            "The code exceeded its time budget and was aborted"
            f"{location}. Avoid unbounded loops, and split long jobs into "
            "several execute_python calls."
        )
    return f"The code raised {error.get('type', 'an exception')}{location}."


def main() -> None:
    host = os.getenv("MCP_HOST", DEFAULT_MCP_HOST)
    port = int(os.getenv("MCP_PORT", str(DEFAULT_MCP_PORT)))
    path = os.getenv("MCP_PATH", DEFAULT_MCP_PATH)

    mcp.run(transport="http", host=host, port=port, path=path)


if __name__ == "__main__":
    main()
