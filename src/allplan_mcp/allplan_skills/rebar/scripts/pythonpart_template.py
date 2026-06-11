"""Rebar PythonPart template.

Copy this file as a starting point for generated ALLPLAN PythonPart code.
Keep the final PythonPart self contained.

Core pattern:
- define host dimensions and rebar globals
- build local BendingShape objects
- move or place those shapes into the host coordinate system
- return concrete and reinforcement in one CreateElementResult
"""

from __future__ import annotations

import math
from typing import Annotated, Any


Point3DLike = Annotated[tuple[float, float, float], "3D point in model units"]
RebarObject = Annotated[Any, "ALLPLAN reinforcement object"]
ShapeObject = Annotated[Any, "ALLPLAN BendingShape object"]


def validate_positive(value: float, name: str) -> float:
    number = float(value)
    if number <= 0:
        raise ValueError(f"{name} must be greater than zero")
    return number


def validate_non_negative(value: float, name: str) -> float:
    number = float(value)
    if number < 0:
        raise ValueError(f"{name} must be zero or greater")
    return number


def validate_count(value: int, name: str) -> int:
    count = int(value)
    if count < 1:
        raise ValueError(f"{name} must be at least one")
    return count


def validate_clear_length(length: float, name: str) -> float:
    clear_length = validate_positive(length, name)
    if clear_length <= 1e-9:
        raise ValueError(f"{name} is too small after cover is applied")
    return clear_length


def p(geo: Any, x: float, y: float, z: float) -> Any:
    return geo.Point3D(float(x), float(y), float(z))


def vec(geo: Any, x: float, y: float, z: float) -> Any:
    return geo.Vector3D(float(x), float(y), float(z))


def polyline3d(geo: Any, points: list[Point3DLike]) -> Any:
    line = geo.Polyline3D()
    for x, y, z in points:
        line += p(geo, x, y, z)
    return line


def bending_rollers(geo: Any, points: list[Point3DLike], roller: float = 0.0) -> Any:
    segment_count = max(len(points) - 1, 1)
    return geo.VecDoubleList([float(roller)] * segment_count)


def straight_bar_shape_x(
    geo: Any,
    reinf: Any,
    length: float,
    diameter: float,
    steel_grade: int = -1,
    concrete_grade: int = -1,
) -> ShapeObject:
    """Create a local straight bar along X."""

    validate_clear_length(length, "length")
    validate_positive(diameter, "diameter")
    points = [(0.0, 0.0, 0.0), (float(length), 0.0, 0.0)]
    return reinf.BendingShape(
        polyline3d(geo, points),
        bending_rollers(geo, points),
        diameter,
        steel_grade,
        concrete_grade,
        reinf.BendingShapeType.LongitudinalBar,
    )


def straight_bar_shape_y(
    geo: Any,
    reinf: Any,
    length: float,
    diameter: float,
    steel_grade: int = -1,
    concrete_grade: int = -1,
) -> ShapeObject:
    """Create a local straight bar along Y."""

    validate_clear_length(length, "length")
    validate_positive(diameter, "diameter")
    points = [(0.0, 0.0, 0.0), (0.0, float(length), 0.0)]
    return reinf.BendingShape(
        polyline3d(geo, points),
        bending_rollers(geo, points),
        diameter,
        steel_grade,
        concrete_grade,
        reinf.BendingShapeType.LongitudinalBar,
    )


def straight_bar_shape_z(
    geo: Any,
    reinf: Any,
    length: float,
    diameter: float,
    steel_grade: int = -1,
    concrete_grade: int = -1,
) -> ShapeObject:
    """Create a local straight bar along Z."""

    validate_clear_length(length, "length")
    validate_positive(diameter, "diameter")
    points = [(0.0, 0.0, 0.0), (0.0, 0.0, float(length))]
    return reinf.BendingShape(
        polyline3d(geo, points),
        bending_rollers(geo, points),
        diameter,
        steel_grade,
        concrete_grade,
        reinf.BendingShapeType.LongitudinalBar,
    )


def closed_rect_tie_shape_yz(
    geo: Any,
    reinf: Any,
    width_y: float,
    height_z: float,
    diameter: float,
    steel_grade: int = -1,
    concrete_grade: int = -1,
) -> ShapeObject:
    """Create a local rectangular tie in the YZ plane for beam stirrups."""

    validate_clear_length(width_y, "width_y")
    validate_clear_length(height_z, "height_z")
    validate_positive(diameter, "diameter")
    points = [
        (0.0, 0.0, 0.0),
        (0.0, float(width_y), 0.0),
        (0.0, float(width_y), float(height_z)),
        (0.0, 0.0, float(height_z)),
        (0.0, 0.0, 0.0),
    ]
    return reinf.BendingShape(
        polyline3d(geo, points),
        bending_rollers(geo, points),
        diameter,
        steel_grade,
        concrete_grade,
        reinf.BendingShapeType.Stirrup,
    )


def closed_rect_tie_shape_xy(
    geo: Any,
    reinf: Any,
    width_x: float,
    depth_y: float,
    diameter: float,
    steel_grade: int = -1,
    concrete_grade: int = -1,
) -> ShapeObject:
    """Create a local rectangular tie in the XY plane for column or pedestal ties."""

    validate_clear_length(width_x, "width_x")
    validate_clear_length(depth_y, "depth_y")
    validate_positive(diameter, "diameter")
    points = [
        (0.0, 0.0, 0.0),
        (float(width_x), 0.0, 0.0),
        (float(width_x), float(depth_y), 0.0),
        (0.0, float(depth_y), 0.0),
        (0.0, 0.0, 0.0),
    ]
    return reinf.BendingShape(
        polyline3d(geo, points),
        bending_rollers(geo, points),
        diameter,
        steel_grade,
        concrete_grade,
        reinf.BendingShapeType.Stirrup,
    )


def circular_hoop_shape(
    geo: Any,
    reinf: Any,
    radius: float,
    diameter: float,
    steel_grade: int = -1,
    concrete_grade: int = -1,
    segment_count: int = 32,
) -> ShapeObject:
    """Create a local circular hoop in the XY plane."""

    validate_clear_length(radius, "radius")
    validate_positive(diameter, "diameter")
    validate_count(segment_count, "segment_count")
    points: list[Point3DLike] = []
    for index in range(segment_count + 1):
        angle = 2.0 * math.pi * index / segment_count
        points.append((radius * math.cos(angle), radius * math.sin(angle), 0.0))

    return reinf.BendingShape(
        polyline3d(geo, points),
        bending_rollers(geo, points),
        diameter,
        steel_grade,
        concrete_grade,
        reinf.BendingShapeType.Stirrup,
    )


def single_shape_placement(
    geo: Any,
    reinf: Any,
    position: int,
    shape: ShapeObject,
) -> RebarObject:
    """Place one already-positioned shape."""

    validate_count(position, "position")
    return reinf.BarPlacement(
        position,
        1,
        vec(geo, 0.0, 0.0, 0.0),
        p(geo, 0.0, 0.0, 0.0),
        p(geo, 0.0, 0.0, 0.0),
        shape,
    )


def linear_by_spacing(
    builder: Any,
    rule: Any,
    geo: Any,
    position: int,
    shape: ShapeObject,
    start: Point3DLike,
    end: Point3DLike,
    spacing: float,
    cover_start: float = 0.0,
    cover_end: float = 0.0,
    global_move: bool = True,
) -> RebarObject:
    """Place repeated bars by spacing using ALLPLAN's linear builder."""

    validate_count(position, "position")
    validate_positive(spacing, "spacing")
    validate_non_negative(cover_start, "cover_start")
    validate_non_negative(cover_end, "cover_end")
    return builder.create_linear_bar_placement_from_to_by_dist(
        position,
        shape,
        p(geo, *start),
        p(geo, *end),
        cover_start,
        cover_end,
        spacing,
        rule.AdditionalCover,
        global_move,
    )


def linear_by_count(
    builder: Any,
    rule: Any,
    geo: Any,
    position: int,
    shape: ShapeObject,
    start: Point3DLike,
    end: Point3DLike,
    bar_count: int,
    cover_start: float = 0.0,
    cover_end: float = 0.0,
    global_move: bool = True,
) -> RebarObject:
    """Place repeated bars by count using ALLPLAN's linear builder."""

    validate_count(position, "position")
    validate_count(bar_count, "bar_count")
    validate_non_negative(cover_start, "cover_start")
    validate_non_negative(cover_end, "cover_end")
    return builder.create_linear_bar_placement_from_to_by_count(
        position,
        shape,
        p(geo, *start),
        p(geo, *end),
        cover_start,
        cover_end,
        bar_count,
        rule.AdditionalCover,
        global_move,
    )


def footing_bottom_mats(
    geo: Any,
    reinf: Any,
    builder: Any,
    rule: Any,
    length: float,
    width: float,
    cover: float,
    diameter_x: float,
    diameter_y: float,
    spacing_x: float,
    spacing_y: float,
    steel_grade: int = -1,
    concrete_grade: int = -1,
) -> list[RebarObject]:
    """Create bottom X and Y mat placements for a footing, cap, or slab."""

    validate_positive(length, "length")
    validate_positive(width, "width")
    validate_non_negative(cover, "cover")

    x0 = cover
    x1 = length - cover
    y0 = cover
    y1 = width - cover
    bottom_z_x = cover + diameter_x / 2.0
    bottom_z_y = cover + diameter_x + diameter_y / 2.0

    bottom_x_shape = straight_bar_shape_x(geo, reinf, x1 - x0, diameter_x, steel_grade, concrete_grade)
    bottom_x = linear_by_spacing(
        builder,
        rule,
        geo,
        1,
        bottom_x_shape,
        (x0, y0, bottom_z_x),
        (x0, y1, bottom_z_x),
        spacing_y,
    )

    bottom_y_shape = straight_bar_shape_y(geo, reinf, y1 - y0, diameter_y, steel_grade, concrete_grade)
    bottom_y = linear_by_spacing(
        builder,
        rule,
        geo,
        2,
        bottom_y_shape,
        (x0, y0, bottom_z_y),
        (x1, y0, bottom_z_y),
        spacing_x,
    )

    return [bottom_x, bottom_y]


def append_rebars(model_ele_list: Any, rebars: list[RebarObject]) -> None:
    for rebar in rebars:
        model_ele_list.append(rebar)


def create_element(build_ele, doc):
    # Full PythonPart imports:
    # import NemAll_Python_Geometry as AllplanGeo
    # import NemAll_Python_Reinforcement as AllplanReinf
    # import NemAll_Python_BaseElements as AllplanBaseElements
    # import StdReinfShapeBuilder.LinearBarPlacementBuilder as LinearBarBuilder
    # from CreateElementResult import CreateElementResult
    # from StdReinfShapeBuilder.LinearBarPlacementBuilder import StartEndPlacementRule
    # from TypeCollections.ModelEleList import ModelEleList

    # Global dimensions and rebar defaults:
    length = 3000.0
    width = 2000.0
    height = 600.0
    cover = 50.0
    diameter_main = 16.0
    diameter_secondary = 12.0
    spacing_main = 150.0
    spacing_secondary = 200.0
    steel_grade = -1
    concrete_grade = -1

    validate_positive(length, "length")
    validate_positive(width, "width")
    validate_positive(height, "height")
    validate_non_negative(cover, "cover")

    # Example footing or slab flow:
    # common_properties = AllplanBaseElements.CommonProperties()
    # common_properties.GetGlobalProperties()
    # placement = AllplanGeo.AxisPlacement3D(
    #     p(AllplanGeo, 0.0, 0.0, 0.0),
    #     vec(AllplanGeo, 1.0, 0.0, 0.0),
    #     vec(AllplanGeo, 0.0, 0.0, 1.0),
    # )
    # host_brep = AllplanGeo.BRep3D.CreateCuboid(placement, length, width, height)
    # model_ele_list = ModelEleList(common_properties)
    # model_ele_list.append_geometry_3d(host_brep)
    #
    # rebar_list = footing_bottom_mats(
    #     AllplanGeo,
    #     AllplanReinf,
    #     LinearBarBuilder,
    #     StartEndPlacementRule,
    #     length,
    #     width,
    #     cover,
    #     diameter_main,
    #     diameter_secondary,
    #     spacing_main,
    #     spacing_secondary,
    #     steel_grade,
    #     concrete_grade,
    # )
    # append_rebars(model_ele_list, rebar_list)
    # return CreateElementResult(elements=model_ele_list)

    raise NotImplementedError("Template only")
