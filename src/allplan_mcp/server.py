from __future__ import annotations

import base64
import os
from typing import Annotated, Any

from fastmcp import FastMCP
from fastmcp.utilities.types import Image

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
        "Everything one call creates collapses into a single Allplan undo step,",
        "so the user can back out the whole change at once. Pass undo=False only",
        "when the code deliberately should not be undoable as one unit.",
        "",
        "After changing the model, verify it instead of assuming: capture_viewport()",
        "returns an image of the result, and get_elements() returns element UUIDs",
        "that get_element_info(uuid) expands into a bounding box.",
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

    response = _allplan_client().post(
        "/create-box",
        {
            "length": size,
            "width": size,
            "height": size,
        },
    )
    return _creation_result(response, "cube", length=size, width=size, height=size)


@mcp.tool
def create_box(length: float, width: float, height: float) -> dict[str, Any]:
    """Create a cuboid in the current Allplan document."""

    if length <= 0 or width <= 0 or height <= 0:
        raise ValueError("length, width, and height must be greater than zero.")

    response = _allplan_client().post(
        "/create-box",
        {
            "length": length,
            "width": width,
            "height": height,
        },
    )
    return _creation_result(
        response, "cuboid", length=length, width=width, height=height
    )


@mcp.tool(description=execute_python_description())
def execute_python(
    code: Annotated[str, "Python source executed inside Allplan"],
    result_expression: Annotated[
        str | None, "Optional expression evaluated after the code runs"
    ] = None,
    undo: Annotated[
        bool,
        "Group everything this code creates into a single Allplan undo step",
    ] = True,
) -> dict[str, Any]:
    if not code.strip():
        raise ValueError("code must be a non-empty string.")

    payload: dict[str, Any] = {"code": code, "undo": undo}
    if result_expression is not None:
        payload["result_expression"] = result_expression

    response = _allplan_client().post("/execute-python", payload)

    if response.get("ok") is False:
        error = response.get("error", {})
        if isinstance(error, dict):
            response["hint"] = _failure_hint(error)

    return response


@mcp.tool
def create_wall(
    start: Annotated[list[float], "Axis start point as [x, y] in mm"],
    end: Annotated[list[float], "Axis end point as [x, y] in mm"],
    tiers: Annotated[
        list[dict[str, Any]],
        "Wandschichten, outermost first. Each needs a thickness and exactly one "
        "surface: hatch, pattern, face_style, or filling (an Allplan catalogue "
        'id), or "surface": "none" to state it deliberately has none.',
    ],
    bottom_elevation: Annotated[float, "Bottom elevation in mm"] = 0.0,
    top_elevation: Annotated[float, "Top elevation in mm"] = 2750.0,
) -> dict[str, Any]:
    """Create an architectural wall (Wand) with a Schraffur on each tier.

    Use this for walls, not create_box. A cuboid is a generic 3D solid with no
    Wandschichten, so it can never carry a Schraffur and reads as blank in
    section.

    Every tier must say what its surface is. A tier that omits it is rejected
    rather than drawn blank, because a wall without a Schraffur is unreadable in
    a Werkplan. Take the hatch id from the plan being modelled.

    Example: a 240mm reinforced concrete wall with 80mm insulation.

        tiers=[{"thickness": 240, "hatch": 301},
               {"thickness": 80, "hatch": 305}]
    """

    payload: dict[str, Any] = {
        "start": start,
        "end": end,
        "tiers": tiers,
        "bottom_elevation": bottom_elevation,
        "top_elevation": top_elevation,
    }
    return _allplan_client().post("/create-wall", payload)


@mcp.tool(annotations=READ_ONLY)
def get_elements(
    limit: Annotated[int, "Maximum number of elements to return"] = 500,
) -> dict[str, Any]:
    """List the elements in the current Allplan document with their UUIDs.

    Each element carries a stable `uuid`, which is the handle to pass to
    get_element_info. Prefer this over get_all_object_names, which returns
    display names only and gives no way to refer to an element afterwards.
    """

    if limit <= 0:
        raise ValueError("limit must be greater than zero.")

    return _allplan_client().post("/get-elements", {"limit": limit})


@mcp.tool(annotations=READ_ONLY)
def get_element_info(
    uuid: Annotated[str, "Model element UUID, from get_elements or a create tool"],
) -> dict[str, Any]:
    """Describe one Allplan element, including its bounding box.

    Use this to check what was actually built - position and extent - instead of
    assuming the code did what was intended.
    """

    if not uuid.strip():
        raise ValueError("uuid must be a non-empty string.")

    return _allplan_client().post("/get-element-info", {"uuid": uuid})


@mcp.tool(annotations=READ_ONLY)
def capture_viewport(
    width: Annotated[int | None, "Image width in pixels"] = None,
    height: Annotated[int | None, "Image height in pixels"] = None,
) -> Image:
    """Capture the active Allplan viewport as a PNG image.

    Use this to see the model after changing it, rather than inferring the
    result from code that ran. Omit width and height to capture at the
    viewport's own resolution, which matches what the user is looking at.
    """

    payload: dict[str, Any] = {}
    if (width is None) != (height is None):
        raise ValueError("Provide both width and height, or neither.")
    if width is not None and height is not None:
        if width <= 0 or height <= 0:
            raise ValueError("width and height must be greater than zero.")
        payload["width"] = width
        payload["height"] = height

    response = _allplan_client().post("/capture-viewport", payload)

    encoded = response.get("base64")
    if not isinstance(encoded, str) or not encoded:
        raise ValueError(f"Allplan returned no image data: {response!r}")

    return Image(data=base64.b64decode(encoded), format="png")


def _creation_result(
    response: dict[str, Any],
    shape: str,
    **dimensions: float,
) -> dict[str, Any]:
    """Report what the bridge actually created

    The bridge returns the created elements, so `created` reflects the document
    rather than the fact that the request did not raise.
    """

    elements = response.get("elements")
    elements = elements if isinstance(elements, list) else []

    return {
        "created": bool(elements),
        "type": shape,
        "dimensions": dimensions,
        "elements": elements,
        "uuids": [
            element["uuid"]
            for element in elements
            if isinstance(element, dict) and element.get("uuid")
        ],
    }


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
