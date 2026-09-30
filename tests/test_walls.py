"""Wall specs: a Wandschicht must say what its Schraffur is."""

from __future__ import annotations

import pytest
from PythonHost.walls import normalize_tier, normalize_wall, surface_report

BASE = {"start": [0, 0], "end": [5000, 0]}


def wall(**overrides):
    spec = dict(BASE)
    spec.setdefault("tiers", [{"thickness": 240, "hatch": 301}])
    spec.update(overrides)
    return spec


def test_a_tier_without_a_surface_is_rejected():
    # This is the reported bug: walls arriving in Allplan with no Schraffur.
    # Silence is not allowed to mean "no hatching".
    with pytest.raises(ValueError, match="does not say what its surface is"):
        normalize_wall(wall(tiers=[{"thickness": 240}]))


def test_the_rejection_explains_why_it_matters():
    with pytest.raises(ValueError, match="unreadable in section"):
        normalize_wall(wall(tiers=[{"thickness": 240}]))


def test_a_tier_may_declare_no_surface_explicitly():
    result = normalize_wall(wall(tiers=[{"thickness": 240, "surface": "none"}]))

    assert result["tiers"][0]["surface"] == "none"
    assert result["tiers"][0]["surface_id"] == 0


def test_hatch_is_carried_through():
    result = normalize_wall(wall(tiers=[{"thickness": 240, "hatch": 301}]))

    assert result["tiers"][0] == {
        "thickness": 240.0,
        "surface": "hatch",
        "surface_id": 301,
    }


@pytest.mark.parametrize(
    "key,expected", [("pattern", 12), ("face_style", 5), ("filling", 7)]
)
def test_the_other_surface_kinds_are_accepted(key, expected):
    result = normalize_wall(wall(tiers=[{"thickness": 240, key: expected}]))

    assert result["tiers"][0]["surface"] == key
    assert result["tiers"][0]["surface_id"] == expected


def test_two_surfaces_on_one_tier_are_rejected():
    # Allplan applies one surface per Wandschicht.
    with pytest.raises(ValueError, match="one surface per Wandschicht"):
        normalize_wall(wall(tiers=[{"thickness": 240, "hatch": 301, "pattern": 12}]))


def test_explicit_none_alongside_a_surface_is_rejected():
    with pytest.raises(ValueError, match="both"):
        normalize_wall(
            wall(tiers=[{"thickness": 240, "hatch": 301, "surface": "none"}])
        )


def test_hatch_zero_is_rejected_with_advice():
    # SetHatch(0) means "no hatching" - the exact default that caused the bug.
    # Asking for it by id is almost always a mistake.
    with pytest.raises(ValueError, match='"surface": "none"'):
        normalize_wall(wall(tiers=[{"thickness": 240, "hatch": 0}]))


def test_multiple_tiers_keep_their_own_surfaces():
    result = normalize_wall(
        wall(
            tiers=[
                {"thickness": 240, "hatch": 301},
                {"thickness": 80, "hatch": 305},
                {"thickness": 115, "surface": "none"},
            ]
        )
    )

    assert [t["surface_id"] for t in result["tiers"]] == [301, 305, 0]
    assert result["thickness"] == 435.0


def test_surface_report_makes_the_schraffur_visible_in_the_result():
    result = normalize_wall(
        wall(tiers=[{"thickness": 240, "hatch": 301}, {"thickness": 80, "pattern": 12}])
    )

    assert surface_report(result) == [
        {"tier": 1, "thickness": 240.0, "surface": "hatch", "surface_id": 301},
        {"tier": 2, "thickness": 80.0, "surface": "pattern", "surface_id": 12},
    ]


# -- geometry and elevations --------------------------------------------


def test_a_zero_length_axis_is_rejected():
    with pytest.raises(ValueError, match="no length"):
        normalize_wall(wall(start=[0, 0], end=[0, 0]))


@pytest.mark.parametrize("point", [[0], [0, 0, 0], "0,0", None])
def test_a_malformed_point_is_rejected(point):
    with pytest.raises(ValueError, match="two element list"):
        normalize_wall(wall(start=point))


def test_elevations_default_to_a_storey_height():
    result = normalize_wall(wall())

    assert result["bottom_elevation"] == 0.0
    assert result["top_elevation"] == 2750.0


def test_top_below_bottom_is_rejected():
    with pytest.raises(ValueError, match="above"):
        normalize_wall(wall(bottom_elevation=2750, top_elevation=0))


def test_empty_tiers_are_rejected():
    with pytest.raises(ValueError, match="non-empty"):
        normalize_wall(wall(tiers=[]))


def test_too_many_tiers_are_rejected():
    with pytest.raises(ValueError, match="at most"):
        normalize_wall(wall(tiers=[{"thickness": 10, "hatch": 1}] * 11))


@pytest.mark.parametrize("thickness", [0, -5, "240", True, None])
def test_a_bad_thickness_is_rejected(thickness):
    with pytest.raises(ValueError, match="thickness"):
        normalize_tier({"thickness": thickness, "hatch": 301}, 0)


def test_a_non_integer_hatch_id_is_rejected():
    with pytest.raises(ValueError, match="catalogue id"):
        normalize_tier({"thickness": 240, "hatch": "301"}, 0)


def test_a_layer_is_optional_but_validated():
    assert "layer" not in normalize_tier({"thickness": 240, "hatch": 301}, 0)

    with pytest.raises(ValueError, match="layer"):
        normalize_tier({"thickness": 240, "hatch": 301, "layer": "wall"}, 0)


def test_error_messages_name_the_offending_tier():
    with pytest.raises(ValueError, match=r"tiers\[1\]"):
        normalize_wall(
            wall(tiers=[{"thickness": 240, "hatch": 301}, {"thickness": 80}])
        )
