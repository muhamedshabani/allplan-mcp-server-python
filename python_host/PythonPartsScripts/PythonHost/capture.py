"""Capture the active Allplan viewport as a PNG the agent can actually look at.

Allplan writes the snapshot to a file. The bridge is an HTTP service, so the
file is read back, budgeted, base64 encoded, and deleted. Nothing here imports
Allplan: the handler passes in the save function.
"""

from __future__ import annotations

import base64
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any

SaveFunction = Annotated[
    Callable[[str, int | None, int | None], bool],
    "Writes the viewport to a path, returns success",
]
CaptureResult = Annotated[dict[str, Any], "JSON-safe capture result"]


class CaptureError(RuntimeError):
    """Raised when the viewport could not be captured"""


@dataclass(frozen=True)
class CaptureLimits:
    """Bound the size of a captured image

    max_bytes keeps a large viewport from blowing up the MCP response. Base64
    inflates by about a third, so the encoded payload stays near 5.3 MB.
    """

    min_pixels: int = 64
    max_pixels: int = 4096
    max_bytes: int = 4_000_000


def clamp_dimension(value: Any, limits: CaptureLimits, field: str) -> int:
    """Validate and clamp one requested pixel dimension"""

    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"'{field}' must be an integer when provided.")
    if value < limits.min_pixels:
        raise ValueError(f"'{field}' must be at least {limits.min_pixels}.")
    return min(value, limits.max_pixels)


def capture_viewport(
    save: SaveFunction,
    width: Any = None,
    height: Any = None,
    limits: CaptureLimits | None = None,
) -> CaptureResult:
    """Capture the active viewport and return it as base64 PNG

    Width and height are optional. When both are omitted Allplan uses the
    viewport's own resolution, which is the sane default: it matches what the
    user is looking at.
    """

    limits = limits or CaptureLimits()

    if (width is None) != (height is None):
        raise ValueError("Provide both 'width' and 'height', or neither.")

    pixel_width = None if width is None else clamp_dimension(width, limits, "width")
    pixel_height = None if height is None else clamp_dimension(height, limits, "height")

    with tempfile.TemporaryDirectory(prefix="allplan-capture-") as directory:
        target = Path(directory) / "viewport.png"

        try:
            ok = save(str(target), pixel_width, pixel_height)
        except Exception as error:
            raise CaptureError(f"Allplan failed to capture the viewport: {error}") from error

        if not ok:
            raise CaptureError(
                "Allplan reported failure capturing the viewport. Check that a "
                "viewport is active and visible."
            )

        if not target.is_file():
            raise CaptureError("Allplan reported success but wrote no image file.")

        payload = target.read_bytes()

    if not payload:
        raise CaptureError("Allplan wrote an empty image file.")

    if len(payload) > limits.max_bytes:
        raise CaptureError(
            f"Captured image is {len(payload)} bytes, over the {limits.max_bytes} "
            "byte budget. Request a smaller width and height."
        )

    return {
        "format": "png",
        "bytes": len(payload),
        "width": pixel_width,
        "height": pixel_height,
        "base64": base64.b64encode(payload).decode("ascii"),
    }
