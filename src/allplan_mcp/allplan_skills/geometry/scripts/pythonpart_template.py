"""Geometry PythonPart template

Copy this file as a starting point
Replace the placeholder values with the requested geometry
Keep the final PythonPart self contained

Definition guide
- geo.Point3D(x, y, z)
- geo.Vector3D(x, y, z)
- geo.AxisPlacement3D(origin, x_direction, z_direction)
- geo.BRep3D.CreateCuboid(placement, length, width, height)
- geo.BRep3D.CreateCylinder(placement, radius, height, closedTop, closedBottom)
- basis.ModelElement3D(common_properties, geometry_object)
"""

from __future__ import annotations


def validate_positive(value: float, name: str) -> float:
    number = float(value)
    if number <= 0:
        raise ValueError(f"{name} must be greater than zero")
    return number


def create_element(build_ele, doc):
    # Import ALLPLAN modules at runtime
    # Example
    # import NemAll_Python_BaseElements as AllplanBaseElements
    # import NemAll_Python_BasisElements as AllplanBasisElements
    # import NemAll_Python_Geometry as AllplanGeo
    # from CreateElementResult import CreateElementResult
    # from TypeCollections.ModelEleList import ModelEleList

    validate_positive(1000.0, "length")
    validate_positive(500.0, "width")
    validate_positive(300.0, "height")

    # Suggested flow
    # 1. Define origin and local directions
    # 2. Build an AxisPlacement3D
    # 3. Build a BRep3D solid like CreateCuboid or CreateCylinder
    # 4. Wrap the geometry in ModelElement3D
    # 5. Append the element to ModelEleList
    # 6. Return CreateElementResult

    raise NotImplementedError("Template only")
