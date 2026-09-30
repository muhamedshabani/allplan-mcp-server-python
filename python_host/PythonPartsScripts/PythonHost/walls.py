"""Validate and normalize a wall specification before it reaches Allplan.

A Wand in Allplan is a tiered object: the Schraffur, Muster, Flächenstil, and
Füllfläche all live on the Wandschicht (WallTierProperties), not on the wall.
That is why a generic ModelElement3D cuboid can never carry a Schraffur - it
has no tiers to hang one on.

This module imports nothing from Allplan. The handler turns the normalized spec
into WallProperties and a WallElement.

Surface handling is deliberately strict. Walls arriving in Allplan with no
Schraffur is the failure this module exists to prevent, so a tier must say what
its surface is - including saying "none" out loud. Defaulting to no hatching is
what produced unreadable walls in the first place.
"""

from __future__ import annotations

from typing import Annotated, Any

WallSpec = Annotated[dict[str, Any], "Incoming wall request"]
TierSpec = Annotated[dict[str, Any], "One Wandschicht"]

# Exactly one of these per tier. Allplan's own WallInteractor treats them as
# mutually exclusive: it resets all three, then sets whichever is active.
SURFACE_KEYS = ("hatch", "pattern", "face_style", "filling")

DEFAULT_TOP_ELEVATION = 2750.0
MAX_TIERS = 10


def _number(value: Any, field: str) -> float:
    """Read a numeric field, rejecting booleans and strings"""

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"'{field}' must be a number.")
    return float(value)


def _point(value: Any, field: str) -> tuple[float, float]:
    """Read a 2D point given as [x, y]"""

    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValueError(f"'{field}' must be a two element list [x, y].")
    return _number(value[0], f"{field}[0]"), _number(value[1], f"{field}[1]")


def _surface_id(value: Any, field: str) -> int:
    """Read an Allplan catalogue id for a surface"""

    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"'{field}' must be an integer catalogue id.")
    if value <= 0:
        raise ValueError(
            f"'{field}' must be a positive catalogue id. Use \"surface\": \"none\" "
            "to state that this tier deliberately has no surface."
        )
    return value


def normalize_tier(tier: Any, index: int) -> TierSpec:
    """Validate one Wandschicht

    Requires an explicit surface. A tier that says nothing about its Schraffur
    is rejected rather than silently drawn blank.
    """

    where = f"tiers[{index}]"
    if not isinstance(tier, dict):
        raise ValueError(f"'{where}' must be an object.")

    thickness = _number(tier.get("thickness"), f"{where}.thickness")
    if thickness <= 0:
        raise ValueError(f"'{where}.thickness' must be greater than zero.")

    declared = [key for key in SURFACE_KEYS if tier.get(key) is not None]
    explicit_none = tier.get("surface") == "none"

    if len(declared) > 1:
        raise ValueError(
            f"'{where}' declares {', '.join(declared)}. Allplan applies one "
            "surface per Wandschicht - choose a single one."
        )

    if explicit_none and declared:
        raise ValueError(
            f"'{where}' sets both \"surface\": \"none\" and {declared[0]}."
        )

    if not declared and not explicit_none:
        raise ValueError(
            f"'{where}' does not say what its surface is. Set one of "
            f"{', '.join(SURFACE_KEYS)} to a catalogue id, or "
            '"surface": "none" if the Wandschicht genuinely has no Schraffur. '
            "Walls without a Schraffur are unreadable in section."
        )

    normalized: TierSpec = {
        "thickness": thickness,
        "surface": "none",
        "surface_id": 0,
    }

    if declared:
        key = declared[0]
        normalized["surface"] = key
        normalized["surface_id"] = _surface_id(tier[key], f"{where}.{key}")

    if tier.get("layer") is not None:
        layer = tier["layer"]
        if isinstance(layer, bool) or not isinstance(layer, int):
            raise ValueError(f"'{where}.layer' must be an integer.")
        normalized["layer"] = layer

    return normalized


def normalize_wall(spec: WallSpec) -> WallSpec:
    """Validate a whole wall request"""

    if not isinstance(spec, dict):
        raise ValueError("The wall request must be an object.")

    start = _point(spec.get("start"), "start")
    end = _point(spec.get("end"), "end")
    if start == end:
        raise ValueError("'start' and 'end' must differ; the wall axis has no length.")

    tiers = spec.get("tiers")
    if not isinstance(tiers, list) or not tiers:
        raise ValueError("'tiers' must be a non-empty list of Wandschichten.")
    if len(tiers) > MAX_TIERS:
        raise ValueError(f"'tiers' must hold at most {MAX_TIERS} Wandschichten.")

    normalized_tiers = [normalize_tier(tier, index) for index, tier in enumerate(tiers)]

    bottom = _number(spec.get("bottom_elevation", 0.0), "bottom_elevation")
    top = _number(spec.get("top_elevation", DEFAULT_TOP_ELEVATION), "top_elevation")
    if top <= bottom:
        raise ValueError("'top_elevation' must be above 'bottom_elevation'.")

    return {
        "start": start,
        "end": end,
        "tiers": normalized_tiers,
        "bottom_elevation": bottom,
        "top_elevation": top,
        "thickness": sum(tier["thickness"] for tier in normalized_tiers),
    }


def surface_report(wall: WallSpec) -> list[dict[str, Any]]:
    """Describe what surface each Wandschicht ended up with

    Returned to the caller so the Schraffur is visible in the tool result rather
    than something to discover after loading the drawing file in Allplan.
    """

    return [
        {
            "tier": index + 1,
            "thickness": tier["thickness"],
            "surface": tier["surface"],
            "surface_id": tier["surface_id"],
        }
        for index, tier in enumerate(wall["tiers"])
    ]
