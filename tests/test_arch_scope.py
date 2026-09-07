"""The architecture modules in the sandbox scope.

Without NemAll_Python_ArchElements a script can only place generic solids,
which have no wall tier and therefore no hatch. These tests pin down that
the modules are in scope, that the host reports what it has, and that a
tiered, hatched wall can be built through the sandbox against the API
shapes Nemetschek documents.
"""

from __future__ import annotations

import fake_allplan
import pytest
from PythonHost.sandbox.executor import OPTIONAL_MODULES, SandboxExecutor

ARCH_NAMES = {"AllplanArchElements", "AllplanArchEle", "AllplanElementAdapter", "AllplanReinf"}

# The shape of a wall script as a client would send it: functions, a
# try/except fallback, an f-string, absolute plane references, and one
# hatch per tier. No imports, no classes, nothing dunder.
WALL_SCRIPT = """
doc = coord_input.GetInputViewDocument()
no_ref = AllplanElementAdapter.BaseElementAdapter()
dep = AllplanArchElements.PlaneReferences.PlaneReferenceDependency


def planes(z0, z1):
    ref = AllplanArchElements.PlaneReferences(doc, no_ref)
    ref.SetBottomPlaneDependency(dep.eAbsElevation)
    ref.SetTopPlaneDependency(dep.eAbsElevation)
    ref.SetAbsBottomElevation(float(z0))
    ref.SetAbsTopElevation(float(z1))
    return ref


def wall(x0, y0, x1, y1, thickness, z0, z1, hatch):
    props = AllplanArchElements.WallProperties()
    props.TierCount = 1
    axis = AllplanArchElements.AxisProperties()
    axis.Position = AllplanArchElements.WallAxisPosition.eCenter
    axis.Distance = float(thickness) / 2.0
    axis.Extension = 1
    props.Axis = axis
    tier = props.GetWallTierProperties(1)
    tier.Thickness = float(thickness)
    tier.SetHatch(hatch)
    tier.SetPlaneReferences(planes(z0, z1))
    return AllplanArchElements.WallElement(props, (x0, y0, x1, y1))


def create(element):
    try:
        made = AllplanBaseElements.CreateElements(doc, AllplanGeo.Matrix3D(), [element], [], None,
                                                  createUndoStep=False)
    except Exception:
        made = AllplanBaseElements.CreateElements(doc, AllplanGeo.Matrix3D(), [element], [], None)
    made = list(made)
    if len(made) != 1:
        raise ValueError(f"expected one element, got {len(made)}")
    return made[0]


created = []
for name, x0, y0, x1, y1, t, z0, z1, hatch in [("AW-N", 0, 11180, 10994, 11180, 364, 3110, 5870, 301)]:
    adapter = create(wall(x0, y0, x1, y1, t, z0, z1, hatch))
    created.append({"name": name, "uuid": str(adapter.GetModelElementUUID())})
result = {"created": created}
"""


@pytest.fixture
def executor(allplan):
    return SandboxExecutor(allplan.FakeCoordinateInput())


def test_the_architecture_modules_are_in_scope(executor: SandboxExecutor) -> None:
    scope = executor.api_scope()

    assert set(scope) >= ARCH_NAMES
    assert scope["AllplanArchElements"] is scope["AllplanArchEle"]
    assert executor.absent_modules == {}


def test_scope_names_are_what_the_host_reports(executor: SandboxExecutor, handler) -> None:
    response = handler.handle("/get-allplan-version", {})

    assert response["api_scope"] == executor.scope_names()
    assert set(response["api_scope"]) >= ARCH_NAMES
    assert response["absent_modules"] == {}


def test_a_tiered_hatched_wall_can_be_built_through_the_sandbox(handler, allplan) -> None:
    allplan.recorder.next_created = [fake_allplan.FakeAdapter(uuid="wall-1", name="Wand")]

    response = handler.handle("/execute-python", {"code": WALL_SCRIPT})

    assert response["ok"] is True, response.get("error")
    assert response["result"] == {"created": [{"name": "AW-N", "uuid": "wall-1"}]}
    assert response["undo_step"] is True

    (wall,) = allplan.recorder.walls
    tier = wall.Properties.GetWallTierProperties(1)
    assert tier.hatch == 301  # not Allplan's default 0, which is "no Schraffur"
    assert tier.Thickness == 364.0
    assert (tier.plane_references.bottom, tier.plane_references.top) == (3110.0, 5870.0)
    assert wall.Properties.Axis.Extension == 1  # the default 0 draws nothing
    assert allplan.recorder.create_calls[0]["create_undo_step"] is False


def test_a_host_without_arch_elements_starts_and_says_so(allplan) -> None:
    fake_allplan.install(without=("NemAll_Python_ArchElements",))
    try:
        executor = SandboxExecutor(allplan.FakeCoordinateInput())

        assert "AllplanArchElements" not in executor.api_scope()
        assert "AllplanArchEle" not in executor.api_scope()
        assert "AllplanElementAdapter" in executor.api_scope()
        assert set(executor.absent_modules) == {"AllplanArchElements", "AllplanArchEle"}
        assert "NemAll_Python_ArchElements" in executor.absent_modules["AllplanArchElements"]

        # and a script that needs it fails as data, naming the module
        response = executor.execute({"code": "result = AllplanArchElements"})
        assert response["ok"] is False
        assert response["error"]["kind"] == "runtime_error"
        assert "AllplanArchElements" in response["error"]["message"]
    finally:
        fake_allplan.install()


def test_every_optional_module_has_a_nemall_name() -> None:
    assert all(name.startswith("NemAll_Python_") for name in OPTIONAL_MODULES.values())
