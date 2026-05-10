"""Rebar PythonPart template

Copy this file as a starting point
Replace the placeholder geometry and placement values
Keep the final PythonPart self contained

Definition guide
- BendingShape(Point3D, diameter, steel_grade, concrete_grade) for straight bars
- BendingShape(Polyline3D, VecDoubleList, diameter, steel_grade, concrete_grade, bending_shape_type) for bent bars
- BarPlacement(position_number, bar_count, dist_vec, start_point, end_point, bending_shape) for single and linear bars
- LinearBarPlacementBuilder.create_linear_bar_placement_from_to_by_dist for spacing driven layouts
- LinearBarPlacementBuilder.create_linear_bar_placement_from_to_by_count for count driven layouts
"""

from __future__ import annotations

from typing import Annotated, Any


PointList3D = Annotated[list[tuple[float, float, float]], "3D centerline points in model units"]
PointList2D = Annotated[list[tuple[float, float]], "2D centerline points in model units"]
RebarObject = Annotated[Any, "ALLPLAN reinforcement object"]
HostElement = Annotated[Any, "ALLPLAN host element"]


def validate_positive(value: float, name: str) -> float:
    number = float(value)
    if number <= 0:
        raise ValueError(f"{name} must be greater than zero")
    return number


def validate_count(value: int, name: str) -> int:
    count = int(value)
    if count < 1:
        raise ValueError(f"{name} must be at least one")
    return count


def create_bar_2d(
    position: Annotated[int, "Mark number"],
    polyline: PointList2D,
    diameter: Annotated[float, "Bar diameter"],
    steel_grade: Annotated[int, "Steel grade id"],
    hook_start: Annotated[float, "Start hook length"] = 0.0,
    hook_end: Annotated[float, "End hook length"] = 0.0,
) -> RebarObject:
    """Template for a 2D bar"""

    validate_count(position, "position")
    validate_positive(diameter, "diameter")
    validate_positive(len(polyline), "polyline point count")

    # Runtime import pattern
    # import NemAll_Python_Geometry as AllplanGeo
    # import NemAll_Python_Reinforcement as AllplanReinf
    #
    # Convert the 2D points into the expected ALLPLAN polyline
    # Create a BendingShape
    # Apply hook lengths with SetHookLengthStart and SetHookLengthEnd when needed
    # Create and return a BarPlacement

    raise NotImplementedError("Template only")


def create_bar_3d(
    position: Annotated[int, "Mark number"],
    path: PointList3D,
    diameter: Annotated[float, "Bar diameter"],
    steel_grade: Annotated[int, "Steel grade id"],
) -> RebarObject:
    """Template for a 3D bar"""

    validate_count(position, "position")
    validate_positive(diameter, "diameter")
    validate_positive(len(path), "path point count")

    # Runtime import pattern
    # import NemAll_Python_Geometry as AllplanGeo
    # import NemAll_Python_Reinforcement as AllplanReinf
    #
    # Build Polyline3D from the path
    # Create the BendingShape
    # Create and return a BarPlacement

    raise NotImplementedError("Template only")


def create_linear_bar_placement(
    bending_shape: RebarObject,
    start_point: Annotated[tuple[float, float, float], "Placement start point"],
    end_point: Annotated[tuple[float, float, float], "Placement end point"],
    bar_count: Annotated[int, "Number of bars"] | None = None,
    spacing: Annotated[float, "Spacing between bars"] | None = None,
) -> RebarObject:
    """Template for repeated bars"""

    if bar_count is None and spacing is None:
        raise ValueError("Provide bar_count or spacing")

    if bar_count is not None:
        validate_count(bar_count, "bar_count")
    if spacing is not None:
        validate_positive(spacing, "spacing")

    # Runtime import pattern
    # import NemAll_Python_Geometry as AllplanGeo
    # import NemAll_Python_Reinforcement as AllplanReinf
    #
    # Build the placement line
    # Use BarPlacement directly or a standard builder helper
    # Return the created placement

    raise NotImplementedError("Template only")


def create_mesh_placement(
    length_direction: Annotated[tuple[float, float, float], "Length direction vector"],
    width_direction: Annotated[tuple[float, float, float], "Width direction vector"],
    spacing_length: Annotated[float, "Length direction spacing"],
    count_length: Annotated[int, "Length direction count"],
    spacing_width: Annotated[float, "Width direction spacing"],
    count_width: Annotated[int, "Width direction count"],
) -> RebarObject:
    """Template for planar mesh reinforcement"""

    validate_positive(spacing_length, "spacing_length")
    validate_count(count_length, "count_length")
    validate_positive(spacing_width, "spacing_width")
    validate_count(count_width, "count_width")

    # Runtime import pattern
    # import NemAll_Python_Reinforcement as AllplanReinf
    #
    # Create MeshPlacement or PlaneMeshPlacement
    # Configure the two mesh directions
    # Return the created mesh object

    raise NotImplementedError("Template only")


def rebar_set_properties(
    rebar: RebarObject,
    layer: Annotated[str | None, "Target layer"] = None,
    pen: Annotated[int | None, "Pen index"] = None,
    color: Annotated[int | None, "Color index"] = None,
    material: Annotated[int | None, "Material id"] = None,
) -> None:
    """Template for common properties"""

    # Set only the properties you actually need
    # Some properties may live on common properties or attribute services
    # The exact API shape can vary by ALLPLAN version
    return None


def place_rebar_on_element(
    rebar: RebarObject,
    host_element: HostElement,
) -> None:
    """Template for host association"""

    # Use the relevant attachment or association service
    # The exact service depends on the element type and workflow
    return None


def generate_bending_schedule(
    bars: Annotated[list[RebarObject], "Created bar objects"],
) -> list[dict[str, Any]]:
    """Template for schedule rows"""

    # Walk through the created bars
    # Read geometry from the BendingShape
    # Read diameter, hooks, count, and position number
    # Return plain Python rows for CSV or table export
    return []


def export_rebar_to_ifc(
    bars: Annotated[list[RebarObject], "Created bar objects"],
    filename: Annotated[str, "Target IFC path"],
) -> None:
    """Template for export flow"""

    # Use the project export service that matches your environment
    # Reinforcement export may require project settings or licensed modules
    return None


def create_element(build_ele, doc):
    # Import ALLPLAN modules at runtime
    # Example
    # import NemAll_Python_Geometry as AllplanGeo
    # import NemAll_Python_Reinforcement as AllplanReinf
    # from CreateElementResult import CreateElementResult
    # from TypeCollections.ModelEleList import ModelEleList

    # Suggested flow
    # 1. Build one BendingShape
    # 2. Build one placement
    # 3. Apply properties
    # 4. Append to ModelEleList
    # 5. Return CreateElementResult

    raise NotImplementedError("Template only")
