"""The bridge handler, against a behavioural fake of the Allplan API."""

from __future__ import annotations

import base64

import pytest
from fake_allplan import PNG_1X1, BrokenAdapter, FakeAdapter
from PythonHost.capture import CaptureError

# -- element UUIDs -------------------------------------------------------


def test_create_box_reports_the_elements_it_created(handler, allplan):
    allplan.recorder.next_created = [FakeAdapter(uuid="box-1", name="Cuboid")]

    result = handler.handle("/create-box", {"length": 1000, "width": 500, "height": 300})

    assert result["created"] is True
    assert result["count"] == 1
    assert result["elements"][0]["uuid"] == "box-1"


def test_create_box_reports_not_created_when_allplan_returns_nothing(handler, allplan):
    # The old handler returned None unconditionally and the tool claimed
    # success regardless. `created` now reflects the document.
    allplan.recorder.next_created = []

    result = handler.handle("/create-box", {"length": 1, "width": 1, "height": 1})

    assert result["created"] is False
    assert result["count"] == 0


def test_get_elements_returns_uuids(handler, allplan):
    allplan.recorder.document_elements = [
        FakeAdapter(uuid="a", name="Wall"),
        FakeAdapter(uuid="b", name="Slab"),
    ]

    result = handler.handle("/get-elements", {})

    assert [e["uuid"] for e in result["elements"]] == ["a", "b"]
    assert result["truncated"] is False


def test_get_elements_honours_the_limit(handler, allplan):
    allplan.recorder.document_elements = [FakeAdapter(uuid=f"u{i}") for i in range(20)]

    result = handler.handle("/get-elements", {"limit": 5})

    assert result["count"] == 5
    assert result["truncated"] is True


@pytest.mark.parametrize("limit", [0, -1, "10", True])
def test_get_elements_rejects_a_bad_limit(handler, limit):
    with pytest.raises(Exception, match="limit"):
        handler.handle("/get-elements", {"limit": limit})


def test_get_element_info_includes_the_bounding_box(handler, allplan):
    allplan.recorder.document_elements = [FakeAdapter(uuid="a")]

    result = handler.handle("/get-element-info", {"uuid": "a"})

    assert result["element"]["uuid"] == "a"
    assert result["element"]["bounding_box"]["size"] == {
        "x": 1000.0,
        "y": 500.0,
        "z": 300.0,
    }


def test_get_element_info_survives_a_missing_bounding_box(handler, allplan):
    allplan.recorder.document_elements = [FakeAdapter(uuid="a")]
    allplan.recorder.minmax_raises = True

    result = handler.handle("/get-element-info", {"uuid": "a"})

    assert result["element"]["bounding_box"] is None
    assert result["element"]["uuid"] == "a"


def test_get_element_info_on_an_unknown_uuid_says_how_to_recover(handler, allplan):
    allplan.recorder.document_elements = [FakeAdapter(uuid="a")]

    with pytest.raises(Exception, match="get_elements"):
        handler.handle("/get-element-info", {"uuid": "missing"})


@pytest.mark.parametrize("uuid", ["", "   ", None, 7])
def test_get_element_info_rejects_a_bad_uuid(handler, uuid):
    with pytest.raises(Exception, match="uuid"):
        handler.handle("/get-element-info", {"uuid": uuid})


def test_broken_elements_do_not_fail_the_listing(handler, allplan):
    allplan.recorder.document_elements = [BrokenAdapter(uuid="a"), FakeAdapter(uuid="b")]

    result = handler.handle("/get-elements", {})

    assert [e["uuid"] for e in result["elements"]] == ["a", "b"]


# -- undo grouping -------------------------------------------------------


def test_create_box_suppresses_the_per_call_undo_step(handler, allplan):
    handler.handle("/create-box", {"length": 1, "width": 1, "height": 1})

    assert allplan.recorder.create_calls[0]["create_undo_step"] is False


def test_create_box_closes_exactly_one_undo_step(handler, allplan):
    handler.handle("/create-box", {"length": 1, "width": 1, "height": 1})

    assert len(allplan.recorder.undo_services) == 1
    assert allplan.recorder.undo_services[0].steps == 1


def test_an_older_allplan_without_the_kwarg_still_creates(handler, allplan):
    # createUndoStep is not accepted by every version. The fallback keeps the
    # element creation working, just with coarser undo behaviour.
    allplan.recorder.create_accepts_undo_kwarg = False

    result = handler.handle("/create-box", {"length": 1, "width": 1, "height": 1})

    assert result["created"] is True
    assert allplan.recorder.create_calls[-1]["create_undo_step"] is None


def test_execute_python_wraps_the_whole_script_in_one_undo_step(handler, allplan):
    result = handler.handle("/execute-python", {"code": "result = 1 + 1"})

    assert result["result"] == 2
    assert result["undo_step"] is True
    assert allplan.recorder.undo_services[0].steps == 1


def test_execute_python_can_opt_out_of_undo_grouping(handler, allplan):
    result = handler.handle("/execute-python", {"code": "result = 1", "undo": False})

    assert result["undo_step"] is False
    assert allplan.recorder.undo_services == []


def test_failing_code_still_closes_its_undo_step(handler, allplan):
    # The script may already have created elements before raising.
    result = handler.handle("/execute-python", {"code": "raise ValueError('x')"})

    assert result["ok"] is False
    assert allplan.recorder.undo_services[0].steps == 1


def test_execute_python_rejects_a_non_boolean_undo(handler):
    with pytest.raises(Exception, match="undo"):
        handler.handle("/execute-python", {"code": "result = 1", "undo": "yes"})


# -- viewport capture ----------------------------------------------------


def test_capture_returns_the_image(handler, allplan):
    result = handler.handle("/capture-viewport", {})

    assert base64.b64decode(result["base64"]) == PNG_1X1
    assert result["format"] == "png"


def test_capture_redraws_first_by_default(handler, allplan):
    handler.handle("/capture-viewport", {})

    assert allplan.recorder.redraw_calls == 1


def test_capture_can_skip_the_redraw(handler, allplan):
    handler.handle("/capture-viewport", {"redraw": False})

    assert allplan.recorder.redraw_calls == 0


def test_a_failing_redraw_does_not_fail_the_capture(handler, allplan):
    def boom(doc):
        raise RuntimeError("no view")

    allplan.sys.modules["NemAll_Python_BaseElements"].DrawingService.RedrawAll = staticmethod(boom)
    try:
        result = handler.handle("/capture-viewport", {})
        assert result["format"] == "png"
    finally:
        allplan.install()


def test_capture_passes_requested_dimensions(handler, allplan):
    handler.handle("/capture-viewport", {"width": 800, "height": 600})

    assert allplan.recorder.save_calls[0]["width"] == 800
    assert allplan.recorder.save_calls[0]["height"] == 600


def test_capture_without_dimensions_uses_the_viewport_resolution(handler, allplan):
    handler.handle("/capture-viewport", {})

    assert allplan.recorder.save_calls[0]["width"] is None


def test_capture_failure_is_surfaced(handler, allplan):
    allplan.recorder.save_succeeds = False

    with pytest.raises(CaptureError):
        handler.handle("/capture-viewport", {})


# -- routing -------------------------------------------------------------


def test_unknown_path_is_rejected(handler):
    with pytest.raises(Exception, match="Unknown request path"):
        handler.handle("/nope", {})


def test_version_still_works(handler, allplan):
    allplan.recorder.version = "2026.1"

    assert handler.handle("/get-allplan-version", {}) == {"version": "2026.1"}


def test_object_names_still_works(handler, allplan):
    allplan.recorder.document_elements = [FakeAdapter(name="Wall")]

    assert handler.handle("/get-all-object-names", {}) == {"names": ["Wall"]}
