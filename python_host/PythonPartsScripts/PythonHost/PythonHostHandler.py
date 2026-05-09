
from __future__ import annotations

import ast
import builtins
import contextlib
import io
import os

import NemAll_Python_Geometry as AllplanGeo
import NemAll_Python_IFW_Input as AllplanIFW
import NemAll_Python_AllplanSettings as AllplanSettings
import NemAll_Python_BaseElements as AllplanBaseElements
import NemAll_Python_BasisElements as AllplanBasisElements
import NemAll_Python_BaseElements as AllplanBaseEle


BLOCKED_BUILTIN_NAMES = frozenset(
    {
        "__import__",
        "breakpoint",
        "compile",
        "delattr",
        "dir",
        "eval",
        "exec",
        "getattr",
        "globals",
        "hasattr",
        "input",
        "locals",
        "open",
        "setattr",
        "vars",
    }
)

ALLOWED_BUILTIN_NAMES = frozenset(
    {
        "abs",
        "all",
        "any",
        "bool",
        "dict",
        "enumerate",
        "Exception",
        "filter",
        "float",
        "int",
        "isinstance",
        "len",
        "list",
        "map",
        "max",
        "min",
        "print",
        "range",
        "repr",
        "reversed",
        "round",
        "set",
        "sorted",
        "str",
        "sum",
        "tuple",
        "ValueError",
        "zip",
    }
)


class SandboxValidationError(Exception):
    """Raised when sandbox code violates static validation rules."""


class SandboxAstValidator(ast.NodeVisitor):
    """Rejects obvious escape hatches before code reaches exec()."""

    def visit_Import(self, node):
        raise SandboxValidationError("import statements are not allowed in execute_python.")

    def visit_ImportFrom(self, node):
        raise SandboxValidationError("import statements are not allowed in execute_python.")

    def visit_Global(self, node):
        raise SandboxValidationError("global statements are not allowed in execute_python.")

    def visit_Nonlocal(self, node):
        raise SandboxValidationError("nonlocal statements are not allowed in execute_python.")

    def visit_ClassDef(self, node):
        raise SandboxValidationError("class definitions are not allowed in execute_python.")

    def visit_AsyncFunctionDef(self, node):
        raise SandboxValidationError("async functions are not allowed in execute_python.")

    def visit_Await(self, node):
        raise SandboxValidationError("await is not allowed in execute_python.")

    def visit_Yield(self, node):
        raise SandboxValidationError("yield is not allowed in execute_python.")

    def visit_YieldFrom(self, node):
        raise SandboxValidationError("yield from is not allowed in execute_python.")

    def visit_Attribute(self, node):
        if node.attr.startswith("_"):
            raise SandboxValidationError(
                f"attribute '{node.attr}' is not allowed in execute_python."
            )
        self.generic_visit(node)

    def visit_Name(self, node):
        if node.id.startswith("_"):
            raise SandboxValidationError(
                f"name '{node.id}' is not allowed in execute_python."
            )
        if isinstance(node.ctx, ast.Load) and node.id in BLOCKED_BUILTIN_NAMES:
            raise SandboxValidationError(
                f"builtin '{node.id}' is not allowed in execute_python."
            )
        self.generic_visit(node)


def _validate_python_code(source: str, mode: str) -> None:
    try:
        tree = ast.parse(source, filename="<sandbox>", mode=mode)
    except SyntaxError as error:
        raise SandboxValidationError(str(error))

    SandboxAstValidator().visit(tree)


def _safe_builtins():
    return {
        name: getattr(builtins, name)
        for name in ALLOWED_BUILTIN_NAMES
    }


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

    def handle(self, path: str, request : dict):
        """ Handles request from the client allplication

        Args:
            path:    url path relative to the base address
            request: request parameters dicitionary

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
                return self.handle_execute_python(request)
            
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

    def handle_execute_python(self, request: dict):
        """Executes Python code inside Allplan for local development only."""

        if not self.exec_enabled:
            raise Exception("Python execution endpoint is disabled.")

        if not isinstance(request, dict):
            raise Exception("Request body must be a JSON object.")

        code = request.get("code")
        result_expression = request.get("result_expression")

        if not isinstance(code, str) or not code.strip():
            raise Exception("'code' must be a non-empty string.")

        if result_expression is not None and not isinstance(result_expression, str):
            raise Exception("'result_expression' must be a string when provided.")

        _validate_python_code(code, "exec")
        if result_expression:
            _validate_python_code(result_expression, "eval")

        exec_scope = {
            "__builtins__": _safe_builtins(),
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
