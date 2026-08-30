from __future__ import annotations

import contextlib
from typing import Any

import NemAll_Python_AllplanSettings as AllplanSettings
import NemAll_Python_BaseElements as AllplanBaseElements
import NemAll_Python_BasisElements as AllplanBasisElements
import NemAll_Python_Geometry as AllplanGeo
import NemAll_Python_IFW_Input as AllplanIFW

from .capture import CaptureLimits, capture_viewport
from .elements import (
    DEFAULT_ELEMENT_LIMIT,
    describe_elements,
    element_summary,
    find_by_uuid,
    minmax_to_dict,
)
from .sandbox import SandboxExecutor
from .undo import undo_step

AllplanBaseEle = AllplanBaseElements


class RequestHandler:
    """Handle bridge requests"""

    def __init__(self, coord_input: AllplanIFW.CoordinateInput) -> None:
        """Build the handler"""

        self.coord_input = coord_input
        self.sandbox_executor = SandboxExecutor(coord_input)
        self.capture_limits = CaptureLimits()

    def handle(self, path: str, request: dict) -> Any:
        """Route one bridge request"""

        match path:
            case "/get-allplan-version":
                return self.handle_get_allplan_version(request)

            case "/get-all-object-names":
                return self.handle_get_all_object_names(request)

            case "/get-elements":
                return self.handle_get_elements(request)

            case "/get-element-info":
                return self.handle_get_element_info(request)

            case "/create-box":
                return self.handle_create_box(request)

            case "/execute-python":
                return self.handle_execute_python(request)

            case "/capture-viewport":
                return self.handle_capture_viewport(request)

            case _:
                raise Exception(f"Unknown request path: {path}")

    # -- helpers ---------------------------------------------------------

    def document(self) -> Any:
        """Get the document behind the active view"""

        return self.coord_input.GetInputViewDocument()

    def all_elements(self, doc: Any) -> Any:
        """Select every element in the document"""

        return AllplanBaseElements.ElementsSelectService.SelectAllElements(doc)

    def undo_service_factory(self, doc: Any):
        """Build the factory for one undo step"""

        return lambda: AllplanIFW.UndoRedoService(doc, True)

    def create_elements(
        self,
        doc: Any,
        matrix: Any,
        model_ele_list: list,
        undo_active: bool,
    ) -> Any:
        """Create elements, suppressing the per-call undo step when batching

        createUndoStep is not accepted by every Allplan version, so a TypeError
        falls back to the plain call. The batch then produces one undo step per
        create instead of one per request, which is worse but still correct.
        """

        if undo_active:
            try:
                return AllplanBaseElements.CreateElements(
                    doc, matrix, model_ele_list, [], None, createUndoStep=False
                )
            except TypeError:
                pass

        return AllplanBaseElements.CreateElements(doc, matrix, model_ele_list, [], None)

    def element_limit(self, request: dict) -> int:
        """Read the element count budget from a request"""

        limit = request.get("limit", DEFAULT_ELEMENT_LIMIT)
        if isinstance(limit, bool) or not isinstance(limit, int):
            raise Exception("'limit' must be an integer when provided.")
        if limit <= 0:
            raise Exception("'limit' must be greater than zero.")
        return limit

    # -- handlers --------------------------------------------------------

    def handle_get_allplan_version(self, request: dict) -> dict:
        """Get the Allplan version"""

        version = AllplanSettings.AllplanVersion.Version()
        return {"version": version}

    def handle_get_all_object_names(self, request: dict) -> dict:
        """Get object names"""

        doc = self.document()
        base_elements = self.all_elements(doc)

        names = [base_element.GetDisplayName() for base_element in base_elements]
        return {"names": names}

    def handle_get_elements(self, request: dict) -> dict:
        """Describe the elements in the document, with UUIDs"""

        limit = self.element_limit(request)
        doc = self.document()
        elements, truncated = describe_elements(self.all_elements(doc), limit)

        return {
            "elements": elements,
            "count": len(elements),
            "truncated": truncated,
        }

    def handle_get_element_info(self, request: dict) -> dict:
        """Describe one element by UUID, including its bounding box"""

        uuid = request.get("uuid")
        if not isinstance(uuid, str) or not uuid.strip():
            raise Exception("'uuid' must be a non-empty string.")

        doc = self.document()
        adapter = find_by_uuid(self.all_elements(doc), uuid)
        if adapter is None:
            raise Exception(
                f"No element with UUID {uuid!r} in the current document. "
                "Call get_elements for the current UUIDs."
            )

        info = element_summary(adapter)
        try:
            info["bounding_box"] = minmax_to_dict(
                AllplanBaseElements.GetMinMaxBox([adapter])
            )
        except Exception:
            info["bounding_box"] = None

        return {"element": info}

    def handle_create_box(self, request: dict) -> dict:
        """Create a box and report what was created"""

        length = request["length"]
        width = request["width"]
        height = request["height"]

        cuboid = AllplanGeo.Polyhedron3D.CreateCuboid(length, width, height)

        com_prop = AllplanBaseElements.CommonProperties()
        com_prop.GetGlobalProperties()
        model_ele_list = [AllplanBasisElements.ModelElement3D(com_prop, cuboid)]
        doc = self.document()

        with undo_step(self.undo_service_factory(doc)) as undo_active:
            created = self.create_elements(
                doc, AllplanGeo.Matrix3D(), model_ele_list, undo_active
            )

        elements, truncated = describe_elements(created or [], DEFAULT_ELEMENT_LIMIT)

        return {
            "created": bool(elements),
            "elements": elements,
            "count": len(elements),
            "truncated": truncated,
        }

    def handle_execute_python(self, request: dict) -> dict:
        """Run sandbox code as one undo step"""

        undo_enabled = request.get("undo", True)
        if not isinstance(undo_enabled, bool):
            raise Exception("'undo' must be a boolean when provided.")

        doc = self.document()

        with undo_step(self.undo_service_factory(doc), undo_enabled) as undo_active:
            result = self.sandbox_executor.execute(request)

        result["undo_step"] = undo_active
        return result

    def handle_capture_viewport(self, request: dict) -> dict:
        """Capture the active viewport as a PNG"""

        if request.get("redraw", True):
            # A stale view is better than a failed capture.
            with contextlib.suppress(Exception):
                AllplanBaseElements.DrawingService.RedrawAll(self.document())

        def save(path: str, width: int | None, height: int | None) -> bool:
            if width is None or height is None:
                return bool(
                    AllplanBaseElements.DrawingService.SaveWindowToImageFile(path)
                )
            return bool(
                AllplanBaseElements.DrawingService.SaveWindowToImageFile(
                    path, pixelWidth=width, pixelHeight=height
                )
            )

        return capture_viewport(
            save,
            width=request.get("width"),
            height=request.get("height"),
            limits=self.capture_limits,
        )
