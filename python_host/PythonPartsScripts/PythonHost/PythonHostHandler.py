
from __future__ import annotations

import NemAll_Python_Geometry as AllplanGeo
import NemAll_Python_IFW_Input as AllplanIFW
import NemAll_Python_AllplanSettings as AllplanSettings
import NemAll_Python_BaseElements as AllplanBaseElements
import NemAll_Python_BasisElements as AllplanBasisElements
import NemAll_Python_BaseElements as AllplanBaseEle

from .sandbox import SandboxExecutor


class RequestHandler:
    """Handle bridge requests"""

    def __init__(self,
                 coord_input : AllplanIFW.CoordinateInput):
        """Build the handler"""

        self.coord_input = coord_input
        self.sandbox_executor = SandboxExecutor(coord_input)

    def handle(self, path: str, request : dict):
        """Route one bridge request"""

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
        """Get the Allplan version"""

        version = AllplanSettings.AllplanVersion.Version()
        return { "version": version }

    def handle_get_all_object_names(self, request : dict):
        """Get object names"""

        # get object names
        doc = self.coord_input.GetInputViewDocument()
        base_elements = AllplanBaseEle.ElementsSelectService.SelectAllElements(doc)  
        
        # create response
        names = [base_element.GetDisplayName() for base_element in base_elements]
        return { "names": names }

    def handle_create_box(self, request : dict):
        """Create a box"""

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
        """Run sandbox code"""

        return self.sandbox_executor.execute(request)
