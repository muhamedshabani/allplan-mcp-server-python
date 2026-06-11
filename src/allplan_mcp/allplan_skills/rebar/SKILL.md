---
name: allplan-rebar
description: Use this skill when the agent needs to write ALLPLAN PythonPart code for reinforcement shapes, placements, and reinforced concrete elements
---

# ALLPLAN rebar

Use this skill when the output must create 3D concrete elements and reinforcement, not just describe them.

The agent should work from snippets and contracts:

1. Define the host concrete geometry.
2. Define global rebar values once.
3. Build each `BendingShape` in a local coordinate system.
4. Place the shape with `BarPlacement` or `LinearBarPlacementBuilder`.
5. Return concrete and reinforcement together through `CreateElementResult`.

## Official references

- Reinforcement placement:
  - <https://pythonparts.allplan.com/2025/manual/features/reinforcement/placement/>
  - Use for single placements, linear placements, regions, polygonal placement, extrude, sweep, and circular placement.
- Reinforcement shape definition:
  - <https://pythonparts.allplan.com/2025/manual/features/reinforcement/shape_definition/>
  - Use for `BendingShape`, `GeneralReinfShapeBuilder`, `ReinforcementShapeBuilder`, hooks, rollers, and local rotations.
- `BendingShape` API:
  - <https://pythonparts.allplan.com/2026/api_reference/InterfaceStubs/NemAll_Python_Reinforcement/BendingShape/>
  - Use for exact constructor overloads.
- `BarPlacement` API:
  - <https://pythonparts.allplan.com/2023/api_reference/InterfaceStubs/NemAll_Python_Reinforcement/BarPlacement/>
  - Use for exact constructor overloads.
- `CircularAreaElement` API:
  - <https://pythonparts.allplan.com/2026/api_reference/InterfaceStubs/NemAll_Python_Reinforcement/CircularAreaElement/>
  - Use for circular pile or cage style reinforcement.
- Solids:
  - <https://pythonparts.allplan.com/2026/manual/features/geometry/solids/>
  - Use when the host beam, footing, pile cap, pile, pedestal, column, or slab also needs to be created.

## Asset pack

Read these in order for non-trivial reinforcement:

- `assets/shape-definition.md`
- `assets/placement-patterns.md`
- `assets/structural-recipes.md`
- `assets/beam-orchestration.md`
- `assets/pile-and-pile-cap-orchestration.md`
- `assets/catalogs-and-meshes.md`

## Runtime imports

Use this import block in full PythonPart scripts:

```python
import NemAll_Python_Geometry as AllplanGeo
import NemAll_Python_Reinforcement as AllplanReinf
import NemAll_Python_BaseElements as AllplanBaseElements

import StdReinfShapeBuilder.GeneralReinfShapeBuilder as GeneralShapeBuilder
import StdReinfShapeBuilder.LinearBarPlacementBuilder as LinearBarBuilder

from CreateElementResult import CreateElementResult
from StdReinfShapeBuilder.ConcreteCoverProperties import ConcreteCoverProperties
from StdReinfShapeBuilder.LinearBarPlacementBuilder import StartEndPlacementRule
from StdReinfShapeBuilder.ReinforcementShapeProperties import ReinforcementShapeProperties
from TypeCollections.ModelEleList import ModelEleList
from Utils.RotationUtil import RotationUtil
```

For `execute_python`, imports are blocked by the sandbox. Use the names already exposed by the host, such as `AllplanGeo`, `AllplanReinf`, `AllplanBaseElements`, and `AllplanBasisElements`.

## Global contract

Define these values once near the top of the generated script or extract them from `build_ele`:

```python
steel_grade = -1
concrete_grade = -1
cover = 50.0
diameter_main = 16.0
diameter_tie = 8.0
spacing_main = 150.0
spacing_tie = 200.0
```

Use `-1` for steel or concrete grade when the project should use current ALLPLAN settings.

Keep dimensions in millimeters unless the user says otherwise.

## Geometry convention

Use one coordinate convention across the whole element:

- `X`: member length or footing/cap length.
- `Y`: member width.
- `Z`: height, thickness, or depth.
- Origin: lower-left-bottom corner of the concrete host.
- Concrete cover: measured from concrete faces to the outside of the relevant bar layer.

Do not mix local systems between concrete, bars, and ties. Derive every point from host dimensions, cover, diameter, and spacing.

## Shape selection

Use these rules before choosing an API:

- Straight bar with explicit length:
  - Build a two-point `Polyline3D`.
  - Use `BendingShape(polyline, rollers, diameter, steel_grade, concrete_grade, BendingShapeType.LongitudinalBar)`.
- Closed rectangular tie or stirrup:
  - Prefer `GeneralReinfShapeBuilder.create_stirrup(...)`.
  - Use a closed polyline only when the builder does not match the shape.
- Point shape:
  - Use `BendingShape(Point3D(...), ...)` mainly for extrusion or sweep workflows.
  - Do not use point shape as the default straight bar recipe.
- Pile hoop or circular area:
  - Use a circular polyline plus `CircularAreaElement(...)` when the reinforcement is circumferential.
  - Use closed stirrup/hoop placements when the requested result is discrete rings.
- Welded mesh:
  - Use `MeshPlacement` or `PlaneMeshPlacement` instead of modeling every wire as a bar.

## Placement selection

- One already-defined bar at one location:
  - `BarPlacement(position, 1, Vector3D(), Point3D(), Point3D(), shape)`.
  - Move or rotate the shape before placement when needed.
- Repeated bars by spacing:
  - `LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(...)`.
- Repeated bars by count:
  - `LinearBarBuilder.create_linear_bar_placement_from_to_by_count(...)`.
- Beam or column tie zones:
  - Split into regions. Each spacing or diameter region should be a separate placement.
- Pile cage:
  - Longitudinal bars are vertical straight shapes placed around the pile radius.
  - Hoops are circular or closed ring placements along depth.

## Minimal snippets

Create a straight local shape:

```python
def p(x, y, z):
    return AllplanGeo.Point3D(float(x), float(y), float(z))

def straight_shape_x(length, diameter, steel_grade=-1, concrete_grade=-1):
    polyline = AllplanGeo.Polyline3D()
    polyline += p(0.0, 0.0, 0.0)
    polyline += p(length, 0.0, 0.0)
    rollers = AllplanGeo.VecDoubleList([0.0])
    return AllplanReinf.BendingShape(
        polyline,
        rollers,
        diameter,
        steel_grade,
        concrete_grade,
        AllplanReinf.BendingShapeType.LongitudinalBar,
    )
```

Move a single bar shape into the host:

```python
shape = straight_shape_x(clear_length, diameter_main, steel_grade, concrete_grade)
shape.Move(AllplanGeo.Vector3D(x0, y0, z0))
placement = AllplanReinf.BarPlacement(1, 1, AllplanGeo.Vector3D(), AllplanGeo.Point3D(), AllplanGeo.Point3D(), shape)
```

Place a straight bar shape repeatedly across a slab, footing, or cap:

```python
shape = straight_shape_x(clear_length_x, diameter_main, steel_grade, concrete_grade)
placement = LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
    1,
    shape,
    p(x0, y0, z0),
    p(x0, y1, z0),
    0.0,
    0.0,
    spacing_main,
    StartEndPlacementRule.AdditionalCover,
    True,
)
```

Create a stirrup or rectangular tie shape:

```python
roller = AllplanReinf.BendingRollerService.GetBendingRollerFactor(diameter_tie, steel_grade, -1, True)
shape_props = ReinforcementShapeProperties.rebar(
    diameter_tie,
    roller,
    steel_grade,
    concrete_grade,
    AllplanReinf.BendingShapeType.Stirrup,
)
cover_props = ConcreteCoverProperties.all(cover)
stirrup_shape = GeneralShapeBuilder.create_stirrup(
    section_width,
    section_height,
    RotationUtil(90, 0, 0),
    shape_props,
    cover_props,
)
```

Place stirrups along a beam or ties along a column:

```python
ties = LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
    2,
    stirrup_shape,
    p(0.0, 0.0, 0.0),
    p(length, 0.0, 0.0),
    cover,
    cover,
    spacing_tie,
    StartEndPlacementRule.AdditionalCover,
    True,
)
```

## Structural mapping

- Footing:
  - Host cuboid.
  - Bottom X mat, bottom Y mat, optional top X/Y mats.
  - Pedestal dowels or column starter bars if requested.
- Beam:
  - Host cuboid.
  - Top and bottom longitudinal bars.
  - Stirrups along length, usually split into support and midspan regions.
- Pile:
  - Host cylinder.
  - Vertical bars around radius.
  - Hoops or `CircularAreaElement` along depth.
- Pile cap:
  - Host cuboid with pile center coordinates.
  - Cap bottom/top mats.
  - Optional punching/shear ties around piles or pedestal.
  - Pile cages aligned to the same centers.
- Pedestal or column:
  - Host cuboid or cylinder.
  - Vertical corner/perimeter bars.
  - Ties/hoops along height, with denser end zones if needed.
- Slab:
  - Host cuboid.
  - Bottom and top X/Y mats.
  - Use mesh only when the user requests welded mesh or standard mesh.

## Result assembly

Return concrete and reinforcement together:

```python
model_ele_list = ModelEleList(common_properties)
model_ele_list.append_geometry_3d(host_brep)

reinf_ele_list = ModelEleList()
reinf_ele_list.append(bottom_x)
reinf_ele_list.append(bottom_y)

return CreateElementResult(elements=model_ele_list + reinf_ele_list)
```

## Documentation workflow

When the API shape is not obvious:

1. Read `shape-definition.md`.
2. Read `placement-patterns.md`.
3. Read `structural-recipes.md`.
4. Read exact API pages only for constructors or enum names.
5. Generate a small PythonPart with explicit derived values.

## Script

- `pythonpart_template.py`

## Risks and assumptions

- Enum names and helper modules can vary by ALLPLAN version.
- Reinforcement catalogs depend on the local installation and project setup.
- Some services only work inside the ALLPLAN runtime on Windows.
- A shape's geometry and a placement's distribution are different concepts. Do not expect placement lines to stretch a too-short shape.
