"""Viewport capture: give the agent an image instead of an assumption."""

from __future__ import annotations

import base64
from pathlib import Path

import pytest
from fake_allplan import PNG_1X1
from PythonHost.capture import CaptureError, CaptureLimits, capture_viewport, clamp_dimension


def saver(payload: bytes = PNG_1X1, ok: bool = True, write: bool = True):
    calls: list[dict] = []

    def save(path: str, width, height) -> bool:
        calls.append({"path": path, "width": width, "height": height})
        if write:
            Path(path).write_bytes(payload)
        return ok

    save.calls = calls  # type: ignore[attr-defined]
    return save


def test_capture_returns_base64_png():
    save = saver()

    result = capture_viewport(save)

    assert result["format"] == "png"
    assert result["bytes"] == len(PNG_1X1)
    assert base64.b64decode(result["base64"]) == PNG_1X1


def test_omitting_both_dimensions_uses_the_viewport_resolution():
    save = saver()

    result = capture_viewport(save)

    assert save.calls[0]["width"] is None
    assert save.calls[0]["height"] is None
    assert result["width"] is None


def test_dimensions_are_passed_through():
    save = saver()

    capture_viewport(save, width=800, height=600)

    assert save.calls[0] == {
        "path": save.calls[0]["path"],
        "width": 800,
        "height": 600,
    }


def test_oversized_dimensions_are_clamped_not_rejected():
    limits = CaptureLimits(max_pixels=1024)
    save = saver()

    result = capture_viewport(save, width=99999, height=99999, limits=limits)

    assert result["width"] == 1024
    assert save.calls[0]["width"] == 1024


def test_one_dimension_alone_is_rejected():
    with pytest.raises(ValueError, match="both"):
        capture_viewport(saver(), width=800)


def test_non_integer_dimension_is_rejected():
    with pytest.raises(ValueError, match="must be an integer"):
        capture_viewport(saver(), width="800", height="600")


def test_boolean_is_not_accepted_as_a_dimension():
    with pytest.raises(ValueError, match="must be an integer"):
        clamp_dimension(True, CaptureLimits(), "width")


def test_tiny_dimension_is_rejected():
    with pytest.raises(ValueError, match="at least"):
        capture_viewport(saver(), width=1, height=1)


def test_allplan_reporting_failure_becomes_a_capture_error():
    with pytest.raises(CaptureError, match="reported failure"):
        capture_viewport(saver(ok=False))


def test_success_without_a_file_is_a_capture_error():
    with pytest.raises(CaptureError, match="wrote no image file"):
        capture_viewport(saver(write=False))


def test_empty_file_is_a_capture_error():
    with pytest.raises(CaptureError, match="empty image file"):
        capture_viewport(saver(payload=b""))


def test_a_raising_save_is_wrapped():
    def save(path, width, height):
        raise RuntimeError("viewport is gone")

    with pytest.raises(CaptureError, match="viewport is gone"):
        capture_viewport(save)


def test_an_image_over_budget_is_refused_with_advice():
    limits = CaptureLimits(max_bytes=10)

    with pytest.raises(CaptureError, match="smaller width and height"):
        capture_viewport(saver(payload=b"x" * 100), limits=limits)


def test_the_temp_file_does_not_survive_the_call():
    save = saver()

    capture_viewport(save)

    assert not Path(save.calls[0]["path"]).exists()
