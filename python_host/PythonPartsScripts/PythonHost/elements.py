"""Shape Allplan element adapters into JSON-safe summaries.

This module deliberately imports nothing from Allplan. Everything here works on
duck-typed adapter objects, which keeps it testable off a Windows install. The
handler supplies the real ``BaseElementAdapter`` instances.
"""

from __future__ import annotations

from typing import Annotated, Any

ElementAdapter = Annotated[Any, "Allplan BaseElementAdapter, duck-typed"]
ElementSummary = Annotated[dict[str, Any], "JSON-safe element description"]

DEFAULT_ELEMENT_LIMIT = 500


def _call(adapter: ElementAdapter, name: str) -> Any:
    """Call an adapter accessor, tolerating the ones a given element lacks

    Allplan adapters are a union of many element types and not every accessor is
    meaningful for every element. A missing or raising accessor should degrade
    one field, not fail the whole request.
    """

    accessor = getattr(adapter, name, None)
    if accessor is None:
        return None
    try:
        return accessor()
    except Exception:
        return None


def element_uuid(adapter: ElementAdapter) -> str | None:
    """Read the model element UUID as a string

    GetModelElementUUID is the identifier that survives across requests, which
    is what makes it useful as a handle to hand back to an agent.
    """

    value = _call(adapter, "GetModelElementUUID")
    if value is None:
        return None
    text = str(value)
    return text or None


def element_type(adapter: ElementAdapter) -> str | None:
    """Read the adapter type name"""

    adapter_type = _call(adapter, "GetElementAdapterType")
    if adapter_type is None:
        return None
    name = getattr(adapter_type, "GetTypeName", None)
    if name is None:
        return None
    try:
        return str(name())
    except Exception:
        return None


def element_summary(adapter: ElementAdapter) -> ElementSummary:
    """Describe one element"""

    display_name = _call(adapter, "GetDisplayName")
    is_3d = _call(adapter, "Is3DElement")

    return {
        "uuid": element_uuid(adapter),
        "name": None if display_name is None else str(display_name),
        "type": element_type(adapter),
        "is_3d": None if is_3d is None else bool(is_3d),
    }


def describe_elements(
    adapters: Any,
    limit: int = DEFAULT_ELEMENT_LIMIT,
) -> tuple[list[ElementSummary], bool]:
    """Describe a sequence of elements under a count budget

    Returns the summaries and whether the list was truncated. A drawing file can
    hold far more elements than belong in a single tool response.
    """

    if limit < 0:
        raise ValueError("limit must not be negative.")

    summaries: list[ElementSummary] = []
    truncated = False

    for index, adapter in enumerate(adapters):
        if index >= limit:
            truncated = True
            break
        summaries.append(element_summary(adapter))

    return summaries, truncated


def point_to_dict(point: Any) -> dict[str, float] | None:
    """Convert an Allplan point to plain floats"""

    if point is None:
        return None
    try:
        return {
            "x": float(point.X),
            "y": float(point.Y),
            "z": float(point.Z),
        }
    except Exception:
        return None


def minmax_to_dict(minmax: Any) -> dict[str, Any] | None:
    """Convert a MinMax3D bounding box to plain floats"""

    if minmax is None:
        return None

    minimum = point_to_dict(getattr(minmax, "Min", None))
    maximum = point_to_dict(getattr(minmax, "Max", None))
    if minimum is None or maximum is None:
        return None

    return {
        "min": minimum,
        "max": maximum,
        "size": {
            "x": maximum["x"] - minimum["x"],
            "y": maximum["y"] - minimum["y"],
            "z": maximum["z"] - minimum["z"],
        },
    }


def find_by_uuid(adapters: Any, uuid: str) -> ElementAdapter | None:
    """Find one element by its model element UUID"""

    wanted = uuid.strip()
    if not wanted:
        raise ValueError("uuid must be a non-empty string.")

    for adapter in adapters:
        if element_uuid(adapter) == wanted:
            return adapter
    return None
