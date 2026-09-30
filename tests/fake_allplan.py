"""A behavioural fake of the slice of the Allplan API the bridge touches.

The real API only exists inside Allplan on Windows. Empty stub modules are
enough to make imports work, but they cannot show that the handler groups undo
steps correctly or reports the UUIDs it was given. These fakes record what the
handler asked for, so the wiring is actually exercised.

Shapes are taken from Nemetschek's own PythonPartsExamples:
  CreateElements(doc, matrix, elements, [], None, createUndoStep=False)
  AllplanIFW.UndoRedoService(doc, True).CreateUndoStep()
  AllplanBaseElements.DrawingService.SaveWindowToImageFile(path, pixelWidth=, pixelHeight=)
"""

from __future__ import annotations

import base64
import sys
import types
from pathlib import Path
from typing import Any

# A real 1x1 PNG, so capture reads back bytes that are actually an image.
PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8"
    "z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)

MODULE_NAMES = (
    "NemAll_Python_AllplanSettings",
    "NemAll_Python_ArchElements",
    "NemAll_Python_BaseElements",
    "NemAll_Python_BasisElements",
    "NemAll_Python_Geometry",
    "NemAll_Python_IFW_ElementAdapter",
    "NemAll_Python_IFW_Input",
    "NemAll_Python_Reinforcement",
)


class Recorder:
    """Collect what the handler did, for assertions"""

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.create_calls: list[dict[str, Any]] = []
        self.undo_services: list[FakeUndoRedoService] = []
        self.save_calls: list[dict[str, Any]] = []
        self.redraw_calls: int = 0
        self.document_elements: list[FakeAdapter] = []
        self.next_created: list[FakeAdapter] | None = None
        self.save_succeeds: bool = True
        self.save_writes_file: bool = True
        self.save_payload: bytes = PNG_1X1
        self.save_raises: Exception | None = None
        self.minmax_raises: bool = False
        self.wall_properties: list[FakeWallProperties] = []
        self.wall_elements: list[FakeWallElement] = []
        self.create_accepts_undo_kwarg: bool = True
        self.version: str = "2026.0.0"


recorder = Recorder()


class FakeTypeName:
    def __init__(self, name: str) -> None:
        self._name = name

    def GetTypeName(self) -> str:
        return self._name


class FakeAdapter:
    """Stand-in for BaseElementAdapter"""

    def __init__(
        self,
        uuid: str = "uuid-1",
        name: str = "Cuboid",
        type_name: str = "Polyhedron3D",
        is_3d: bool = True,
    ) -> None:
        self.uuid = uuid
        self.name = name
        self.type_name = type_name
        self.is_3d = is_3d

    def GetModelElementUUID(self) -> str:
        return self.uuid

    def GetElementUUID(self) -> str:
        return f"element-{self.uuid}"

    def GetDisplayName(self) -> str:
        return self.name

    def GetElementAdapterType(self) -> FakeTypeName:
        return FakeTypeName(self.type_name)

    def Is3DElement(self) -> bool:
        return self.is_3d


class BrokenAdapter(FakeAdapter):
    """An element whose accessors raise, as real ones do for some types"""

    def GetElementAdapterType(self) -> FakeTypeName:
        raise RuntimeError("no adapter type for this element")

    def Is3DElement(self) -> bool:
        raise RuntimeError("not answerable")


class FakeWallTierProperties:
    """Records the Schraffur decisions made for one Wandschicht"""

    def __init__(self, index: int) -> None:
        self.index = index
        self.thickness: float | None = None
        self.hatch: int | None = None
        self.pattern: int | None = None
        self.face_style: int | None = None
        self.background_color: int | None = None
        self.common_properties: Any = None
        self.plane_references: Any = None

    def SetThickness(self, value: float) -> None:
        self.thickness = value

    def SetHatch(self, value: int) -> None:
        self.hatch = value

    def SetPattern(self, value: int) -> None:
        self.pattern = value

    def SetFaceStyle(self, value: int) -> None:
        self.face_style = value

    def SetBackgroundColor(self, value: int) -> None:
        self.background_color = value

    def SetCommonProperties(self, value: Any) -> None:
        self.common_properties = value

    def SetPlaneReferences(self, value: Any) -> None:
        self.plane_references = value


class FakeWallProperties:
    def __init__(self) -> None:
        self.tier_count = 0
        self.tiers: dict[int, FakeWallTierProperties] = {}
        self.axis: Any = None
        recorder.wall_properties.append(self)

    def SetTierCount(self, count: int) -> None:
        self.tier_count = count

    def SetAxis(self, axis: Any) -> None:
        self.axis = axis

    def GetWallTierProperties(self, index: int) -> FakeWallTierProperties:
        # Allplan numbers Wandschichten from 1.
        if index < 1:
            raise IndexError("wall tiers are numbered from 1")
        return self.tiers.setdefault(index, FakeWallTierProperties(index))


class FakePlaneReferences:
    def __init__(self, doc: Any, adapter: Any) -> None:
        self.bottom: float | None = None
        self.top: float | None = None

    def SetAbsBottomElevation(self, value: float) -> None:
        self.bottom = value

    def SetAbsTopElevation(self, value: float) -> None:
        self.top = value


class FakeWallElement:
    def __init__(self, properties: Any, axis: Any) -> None:
        self.properties = properties
        self.axis = axis
        recorder.wall_elements.append(self)


class FakePoint:
    def __init__(self, x: float, y: float, z: float) -> None:
        self.X = x
        self.Y = y
        self.Z = z


class FakeMinMax:
    def __init__(self, minimum: FakePoint, maximum: FakePoint) -> None:
        self.Min = minimum
        self.Max = maximum


class FakeUndoRedoService:
    """Stand-in for AllplanIFW.UndoRedoService"""

    def __init__(self, doc: Any, *args: Any) -> None:
        self.doc = doc
        self.args = args
        self.steps = 0
        recorder.undo_services.append(self)

    def CreateUndoStep(self) -> None:
        self.steps += 1


class FakeDocument:
    pass


class FakeCoordinateInput:
    """Stand-in for AllplanIFW.CoordinateInput"""

    def __init__(self) -> None:
        self.doc = FakeDocument()

    def GetInputViewDocument(self) -> FakeDocument:
        return self.doc


def _create_elements(
    doc: Any,
    matrix: Any,
    elements: Any,
    reference: Any,
    association: Any,
    **kwargs: Any,
) -> list[FakeAdapter]:
    if kwargs and not recorder.create_accepts_undo_kwarg:
        raise TypeError("CreateElements() got an unexpected keyword argument")

    recorder.create_calls.append(
        {
            "doc": doc,
            "count": len(list(elements)),
            "create_undo_step": kwargs.get("createUndoStep"),
            "kwargs": kwargs,
        }
    )

    if recorder.next_created is not None:
        return recorder.next_created
    return [FakeAdapter(uuid=f"created-{len(recorder.create_calls)}")]


def _save_window_to_image_file(
    path: str,
    pixelWidth: int | None = None,
    pixelHeight: int | None = None,
) -> bool:
    recorder.save_calls.append(
        {"path": path, "width": pixelWidth, "height": pixelHeight}
    )

    if recorder.save_raises is not None:
        raise recorder.save_raises

    if recorder.save_writes_file:
        Path(path).write_bytes(recorder.save_payload)

    return recorder.save_succeeds


def _redraw_all(doc: Any) -> None:
    recorder.redraw_calls += 1


def _get_min_max_box(elements: Any) -> FakeMinMax:
    if recorder.minmax_raises:
        raise RuntimeError("no bounding box available")
    return FakeMinMax(FakePoint(0.0, 0.0, 0.0), FakePoint(1000.0, 500.0, 300.0))


def _select_all_elements(doc: Any) -> list[FakeAdapter]:
    return list(recorder.document_elements)


def build_modules() -> dict[str, types.ModuleType]:
    """Build the fake Allplan modules"""

    modules = {name: types.ModuleType(name) for name in MODULE_NAMES}

    settings = modules["NemAll_Python_AllplanSettings"]
    version_class = type(
        "AllplanVersion", (), {"Version": staticmethod(lambda: recorder.version)}
    )
    settings.AllplanVersion = version_class  # type: ignore[attr-defined]

    base = modules["NemAll_Python_BaseElements"]
    base.CreateElements = _create_elements  # type: ignore[attr-defined]
    base.GetMinMaxBox = _get_min_max_box  # type: ignore[attr-defined]
    base.CommonProperties = type(  # type: ignore[attr-defined]
        "CommonProperties", (), {"GetGlobalProperties": lambda self: None}
    )
    base.ElementsSelectService = type(  # type: ignore[attr-defined]
        "ElementsSelectService",
        (),
        {"SelectAllElements": staticmethod(_select_all_elements)},
    )
    base.DrawingService = type(  # type: ignore[attr-defined]
        "DrawingService",
        (),
        {
            "SaveWindowToImageFile": staticmethod(_save_window_to_image_file),
            "RedrawAll": staticmethod(_redraw_all),
        },
    )

    basis = modules["NemAll_Python_BasisElements"]
    basis.ModelElement3D = type(  # type: ignore[attr-defined]
        "ModelElement3D",
        (),
        {"__init__": lambda self, common, geometry: None},
    )

    geo = modules["NemAll_Python_Geometry"]
    geo.Matrix3D = type("Matrix3D", (), {})  # type: ignore[attr-defined]
    geo.Polyhedron3D = type(  # type: ignore[attr-defined]
        "Polyhedron3D",
        (),
        {"CreateCuboid": staticmethod(lambda length, width, height: ("cuboid", length, width, height))},
    )

    geo.Point2D = type(  # type: ignore[attr-defined]
        "Point2D", (), {"__init__": lambda self, x, y: setattr(self, "xy", (x, y))}
    )
    geo.Line2D = type(  # type: ignore[attr-defined]
        "Line2D",
        (),
        {"__init__": lambda self, start, end: setattr(self, "points", (start, end))},
    )

    arch = modules["NemAll_Python_ArchElements"]
    arch.WallProperties = FakeWallProperties  # type: ignore[attr-defined]
    arch.PlaneReferences = FakePlaneReferences  # type: ignore[attr-defined]
    arch.WallElement = FakeWallElement  # type: ignore[attr-defined]
    arch.AxisProperties = type("AxisProperties", (), {})  # type: ignore[attr-defined]
    arch.WallAxisPosition = type(  # type: ignore[attr-defined]
        "WallAxisPosition", (), {"eFree": 0}
    )

    adapter = modules["NemAll_Python_IFW_ElementAdapter"]
    adapter.BaseElementAdapter = type(  # type: ignore[attr-defined]
        "BaseElementAdapter", (), {}
    )

    ifw = modules["NemAll_Python_IFW_Input"]
    ifw.UndoRedoService = FakeUndoRedoService  # type: ignore[attr-defined]
    ifw.CoordinateInput = FakeCoordinateInput  # type: ignore[attr-defined]

    return modules


def install() -> None:
    """Put the fakes on sys.modules, replacing any earlier stubs"""

    for name, module in build_modules().items():
        sys.modules[name] = module
