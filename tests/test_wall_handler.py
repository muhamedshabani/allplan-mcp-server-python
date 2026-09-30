"""Wall creation against the fake Allplan API: does the Schraffur land?"""

from __future__ import annotations

import pytest
from PythonHost.sandbox.executor import API_MODULES, load_api_modules


def create(handler, **overrides):
    request = {
        "start": [0, 0],
        "end": [5000, 0],
        "tiers": [{"thickness": 240, "hatch": 301}],
    }
    request.update(overrides)
    return handler.handle("/create-wall", request)


def test_the_hatch_reaches_the_wall_tier(handler, allplan):
    create(handler)

    tier = allplan.recorder.wall_properties[0].tiers[1]
    assert tier.hatch == 301
    assert tier.thickness == 240.0


def test_tiers_are_numbered_from_one(handler, allplan):
    # Allplan's GetWallTierProperties is 1-based; an off-by-one would silently
    # hatch the wrong Wandschicht.
    create(
        handler,
        tiers=[{"thickness": 240, "hatch": 301}, {"thickness": 80, "hatch": 305}],
    )

    tiers = allplan.recorder.wall_properties[0].tiers
    assert sorted(tiers) == [1, 2]
    assert tiers[1].hatch == 301
    assert tiers[2].hatch == 305


def test_the_other_surfaces_are_reset_before_one_is_set(handler, allplan):
    # WallInteractor resets all three, then sets the active one. Without the
    # reset a tier could carry a stale pattern alongside its hatch.
    create(handler)

    tier = allplan.recorder.wall_properties[0].tiers[1]
    assert tier.hatch == 301
    assert tier.pattern == 0
    assert tier.face_style == 0


def test_a_pattern_tier_leaves_hatch_at_zero(handler, allplan):
    create(handler, tiers=[{"thickness": 240, "pattern": 12}])

    tier = allplan.recorder.wall_properties[0].tiers[1]
    assert tier.pattern == 12
    assert tier.hatch == 0


def test_a_filling_tier_sets_the_background_colour(handler, allplan):
    create(handler, tiers=[{"thickness": 240, "filling": 7}])

    tier = allplan.recorder.wall_properties[0].tiers[1]
    assert tier.background_color == 7


def test_an_explicit_none_tier_stays_unhatched(handler, allplan):
    create(handler, tiers=[{"thickness": 240, "surface": "none"}])

    tier = allplan.recorder.wall_properties[0].tiers[1]
    assert tier.hatch == 0
    assert tier.pattern == 0
    assert tier.face_style == 0


def test_the_tier_count_is_declared(handler, allplan):
    create(
        handler,
        tiers=[{"thickness": 240, "hatch": 301}, {"thickness": 80, "hatch": 305}],
    )

    assert allplan.recorder.wall_properties[0].tier_count == 2


def test_elevations_reach_the_plane_references(handler, allplan):
    create(handler, bottom_elevation=100, top_elevation=3000)

    plane = allplan.recorder.wall_properties[0].tiers[1].plane_references
    assert plane.bottom == 100.0
    assert plane.top == 3000.0


def test_the_result_reports_the_schraffur(handler, allplan):
    result = create(handler)

    assert result["tiers"] == [
        {"tier": 1, "thickness": 240.0, "surface": "hatch", "surface_id": 301}
    ]
    assert result["thickness"] == 240.0


def test_the_wall_is_created_as_one_undo_step(handler, allplan):
    create(handler)

    assert allplan.recorder.create_calls[0]["create_undo_step"] is False
    assert allplan.recorder.undo_services[0].steps == 1


def test_the_created_wall_reports_its_uuid(handler, allplan):
    result = create(handler)

    assert result["created"] is True
    assert result["elements"][0]["uuid"]


def test_a_tier_without_a_surface_is_refused_before_allplan_is_touched(handler, allplan):
    with pytest.raises(Exception, match="does not say what its surface is"):
        create(handler, tiers=[{"thickness": 240}])

    assert allplan.recorder.wall_properties == []
    assert allplan.recorder.create_calls == []


def test_the_axis_endpoints_are_used(handler, allplan):
    create(handler, start=[100, 200], end=[5100, 200])

    axis = allplan.recorder.wall_elements[0].axis
    assert axis.points[0].xy == (100.0, 200.0)
    assert axis.points[1].xy == (5100.0, 200.0)


# -- module scope --------------------------------------------------------


def test_the_architecture_module_is_exposed_to_sandbox_code():
    # Without this there is no real Wand, only a cuboid with no Wandschichten
    # and therefore no possible Schraffur.
    assert "NemAll_Python_ArchElements" in API_MODULES


def test_the_reinforcement_module_is_exposed():
    # The bundled rebar skill documents this module.
    assert "NemAll_Python_Reinforcement" in API_MODULES


def test_the_utility_module_is_deliberately_not_exposed():
    # ShowMessageBox would open a modal dialog on the UI thread the bridge
    # marshals requests onto, deadlocking the host.
    assert "NemAll_Python_Utility" not in API_MODULES


def test_every_exposed_module_loads_under_the_fakes():
    scope, missing = load_api_modules()

    assert missing == []
    assert {"AllplanArchElements", "AllplanReinf", "AllplanEleAdapter"} <= set(scope)


def test_a_missing_module_is_skipped_rather_than_fatal(monkeypatch):
    # Older Allplan versions do not ship every module. Losing one must not take
    # the whole bridge down.
    import PythonHost.sandbox.executor as executor

    real = executor.importlib.import_module

    def fake(name):
        if name == "NemAll_Python_Reinforcement":
            raise ImportError("not in this version")
        return real(name)

    monkeypatch.setattr(executor.importlib, "import_module", fake)

    scope, missing = load_api_modules()

    assert missing == ["NemAll_Python_Reinforcement"]
    assert "AllplanReinf" not in scope
    assert "AllplanArchElements" in scope
