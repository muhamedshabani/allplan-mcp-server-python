
from __future__ import annotations

import contextlib
import io
import os

import NemAll_Python_Geometry as AllplanGeo
import NemAll_Python_IFW_Input as AllplanIFW
import NemAll_Python_AllplanSettings as AllplanSettings
import NemAll_Python_BaseElements as AllplanBaseElements
import NemAll_Python_BasisElements as AllplanBasisElements
import NemAll_Python_BaseElements as AllplanBaseEle


class RequestHandler:
    """ Handles requests from the client application
    """

    def __init__(self,
                 coord_input : AllplanIFW.CoordinateInput):
        """ Create the handler

        Args:
            coord_input: API object for the coordinate input, element selection, ... in the Allplan view
        """

        self.coord_input = coord_input
        self.exec_enabled = os.getenv("ALLPLAN_MCP_ENABLE_PYTHON_EXEC", "0") == "1"
        self.exec_token = os.getenv("ALLPLAN_MCP_EXEC_TOKEN", "")

    def handle(self, path: str, request : dict, headers: dict | None = None):
        """ Handles request from the client allplication

        Args:
            path:    url path relative to the base address
            request: request parameters dicitionary
            headers: request headers

        Raises:
            Exception: raised in case if path couldn't be matched to any handler function

        Returns:
            response parameters dicitionary
        """

        match path:
            case "/get-allplan-version":
                return self.handle_get_allplan_version(request)
            
            case "/get-all-object-names":
                return self.handle_get_all_object_names(request)
            
            case "/create-box":
                return self.handle_create_box(request)

            case "/execute-python":
                return self.handle_execute_python(request, headers or {})
            
            case _:
                raise Exception(f"Unknown request path: {path}") 
        
    def handle_get_allplan_version(self, request : dict):
        """ Handles request to get Allplan version

        Returns:
            response parameters dicitionary (version)
        """

        version = AllplanSettings.AllplanVersion.Version()
        return { "version": version }

    def handle_get_all_object_names(self, request : dict):
        """ Handles request to get all object names in document

        Returns:
            response parameters dicitionary (names)
        """

        # get object names
        doc = self.coord_input.GetInputViewDocument()
        base_elements = AllplanBaseEle.ElementsSelectService.SelectAllElements(doc)  
        
        # create response
        names = [base_element.GetDisplayName() for base_element in base_elements]
        return { "names": names }

    def handle_create_box(self, request : dict):
        """ Handles request to create a cuboid object on default coordinates

        Args:
            request: request parameters dicitionary (length, width, height)
        """

        # get request parameters
        length = request["length"]
        width = request["width"]
        height = request["height"]

        # create cuboid in memory
        cuboid = AllplanGeo.Polyhedron3D.CreateCuboid(length, width, height) 

        # place cuboid inside document
        com_prop = AllplanBaseElements.CommonProperties()
        com_prop.GetGlobalProperties()
        model_ele_list = [AllplanBasisElements.ModelElement3D(com_prop, cuboid)]
        doc = self.coord_input.GetInputViewDocument()

        AllplanBaseElements.CreateElements(doc, AllplanGeo.Matrix3D(), model_ele_list, [], None)

    def handle_execute_python(self, request: dict, headers: dict):
        """Executes Python code inside Allplan for local development only."""

        if not self.exec_enabled:
            raise Exception("Python execution endpoint is disabled.")

        token = headers.get("X-Allplan-Exec-Token", "")
        if not self.exec_token or token != self.exec_token:
            raise Exception("Invalid execution token.")

        if not isinstance(request, dict):
            raise Exception("Request body must be a JSON object.")

        code = request.get("code")
        result_expression = request.get("result_expression")

        if not isinstance(code, str) or not code.strip():
            raise Exception("'code' must be a non-empty string.")

        if result_expression is not None and not isinstance(result_expression, str):
            raise Exception("'result_expression' must be a string when provided.")

        exec_scope = {
            "__builtins__": __builtins__,
            "coord_input": self.coord_input,
            "AllplanGeo": AllplanGeo,
            "AllplanIFW": AllplanIFW,
            "AllplanSettings": AllplanSettings,
            "AllplanBaseElements": AllplanBaseElements,
            "AllplanBasisElements": AllplanBasisElements,
            "AllplanBaseEle": AllplanBaseEle,
        }
        stdout_buffer = io.StringIO()

        with contextlib.redirect_stdout(stdout_buffer):
            exec(code, exec_scope, exec_scope)

            if result_expression:
                result_value = eval(result_expression, exec_scope, exec_scope)
            else:
                result_value = exec_scope.get("result")

        return {
            "ok": True,
            "stdout": stdout_buffer.getvalue(),
            "result": self._make_json_safe(result_value),
        }

    def _make_json_safe(self, value):
        if value is None or isinstance(value, (bool, int, float, str)):
            return value

        if isinstance(value, list):
            return [self._make_json_safe(item) for item in value]

        if isinstance(value, tuple):
            return [self._make_json_safe(item) for item in value]

        if isinstance(value, dict):
            return {
                str(key): self._make_json_safe(item)
                for key, item in value.items()
            }

        return repr(value)
