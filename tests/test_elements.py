"""Element summaries: the UUIDs that make created geometry referenceable."""

from __future__ import annotations

import pytest
from fake_allplan import BrokenAdapter, FakeAdapter, FakeMinMax, FakePoint
from PythonHost.elements import (
    describe_elements,
    element_summary,
    element_uuid,
    find_by_uuid,
    minmax_to_dict,
    point_to_dict,
)


def test_summary_carries_the_uuid_and_descriptive_fields():
    summary = element_summary(FakeAdapter(uuid="abc", name="Beam", type_name="BRep3D"))

    assert summary == {
        "uuid": "abc",
        "name": "Beam",
        "type": "BRep3D",
        "is_3d": True,
    }


def test_a_raising_accessor_degrades_one_field_not_the_whole_summary():
    # Allplan adapters are a union of many element types; not every accessor
    # answers for every element. One bad field must not lose the UUID.
    summary = element_summary(BrokenAdapter(uuid="abc", name="Odd"))

    assert summary["uuid"] == "abc"
    assert summary["name"] == "Odd"
    assert summary["type"] is None
    assert summary["is_3d"] is None


def test_missing_accessor_is_tolerated():
    class Bare:
        def GetDisplayName(self):
            return "bare"

    assert element_summary(Bare()) == {
        "uuid": None,
        "name": "bare",
        "type": None,
        "is_3d": None,
    }


def test_empty_uuid_reads_as_absent():
    class Empty:
        def GetModelElementUUID(self):
            return ""

    assert element_uuid(Empty()) is None


def test_describe_elements_reports_truncation():
    adapters = [FakeAdapter(uuid=f"u{i}") for i in range(10)]

    summaries, truncated = describe_elements(adapters, limit=4)

    assert [s["uuid"] for s in summaries] == ["u0", "u1", "u2", "u3"]
    assert truncated is True


def test_describe_elements_under_the_limit_is_not_truncated():
    summaries, truncated = describe_elements([FakeAdapter()], limit=4)

    assert len(summaries) == 1
    assert truncated is False


def test_describe_elements_rejects_a_negative_limit():
    with pytest.raises(ValueError, match="must not be negative"):
        describe_elements([], limit=-1)


def test_bounding_box_becomes_plain_floats_with_a_size():
    box = minmax_to_dict(FakeMinMax(FakePoint(0, 0, 0), FakePoint(1000, 500, 300)))

    assert box == {
        "min": {"x": 0.0, "y": 0.0, "z": 0.0},
        "max": {"x": 1000.0, "y": 500.0, "z": 300.0},
        "size": {"x": 1000.0, "y": 500.0, "z": 300.0},
    }


def test_bounding_box_of_none_is_none():
    assert minmax_to_dict(None) is None


def test_malformed_point_is_none_rather_than_an_error():
    class NotAPoint:
        X = "left"
        Y = 0
        Z = 0

    assert point_to_dict(NotAPoint()) is None


def test_find_by_uuid_matches_and_misses():
    adapters = [FakeAdapter(uuid="a"), FakeAdapter(uuid="b")]

    assert find_by_uuid(adapters, "b").uuid == "b"
    assert find_by_uuid(adapters, "c") is None


def test_find_by_uuid_ignores_surrounding_whitespace():
    assert find_by_uuid([FakeAdapter(uuid="a")], "  a  ").uuid == "a"


def test_find_by_uuid_rejects_a_blank_uuid():
    with pytest.raises(ValueError, match="non-empty"):
        find_by_uuid([FakeAdapter()], "   ")
