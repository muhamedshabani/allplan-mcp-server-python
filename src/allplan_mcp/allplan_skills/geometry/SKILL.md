---
name: allplan-geometry
description: Use this skill when the agent needs to write ALLPLAN PythonPart code for 3D solids and model elements
---

# ALLPLAN geometry

Use this skill for cuboids, cylinders, points, vectors, and simple model element creation

## Not for architectural objects

A `Wand`, `Decke`, or `Stütze` is not a generic solid. A cuboid has no
Wandschichten, so it can never carry a Schraffur and reads as blank in section.
For those, use the `allplan-architecture` skill and the `create_wall` tool.

## Asset pack

Read these asset notes before writing non-trivial host geometry

- `assets/core-definitions.md`
- `assets/host-geometry-workflow.md`

## Geometry definitions

Define the shorthand once per script

```python
import NemAll_Python_Geometry as AllplanGeo
import NemAll_Python_BaseElements as AllplanBaseElements
import NemAll_Python_BasisElements as AllplanBasisElements
from CreateElementResult import CreateElementResult
from TypeCollections.ModelEleList import ModelEleList

geo = AllplanGeo
base = AllplanBaseElements
basis = AllplanBasisElements
```

### Points and vectors

- `geo.Point3D() -> Point3D`
- `geo.Point3D(x, y, z) -> Point3D`
- `geo.Vector3D() -> Vector3D`
- `geo.Vector3D(x, y, z) -> Vector3D`
- `geo.Vector3D(start_point, end_point) -> Vector3D`

Use explicit `Point3D` and `Vector3D` values instead of inventing helper abstractions too early

### Local coordinate systems

- `geo.AxisPlacement3D() -> AxisPlacement3D`
- `geo.AxisPlacement3D(origin) -> AxisPlacement3D`
- `geo.AxisPlacement3D(origin, x_direction, z_direction) -> AxisPlacement3D`

Default placement for simple solids:

```python
origin = geo.Point3D(0.0, 0.0, 0.0)
placement = geo.AxisPlacement3D(origin, geo.Vector3D(1.0, 0.0, 0.0), geo.Vector3D(0.0, 0.0, 1.0))
```

### Curves and outlines

- `geo.Line3D(point1, point2) -> Line3D`
- `geo.Polyline3D() -> Polyline3D`
- `geo.Polyline3D([Point3D, ...]) -> Polyline3D`
- `geo.Polygon3D() -> Polygon3D`
- `geo.Polygon3D([Point3D, ...]) -> Polygon3D`

For `Polygon3D`, repeat the first point at the end when the shape should be closed

### Solid creation

- `geo.BRep3D.CreateCuboid(placement, length, width, height) -> BRep3D`
- `geo.BRep3D.CreateCylinder(placement, radius, height, closedTop=True, closedBottom=True) -> BRep3D`
- `geo.BRep3D.CreateSphere(placement, radius) -> BRep3D`
- `geo.BRep3D.CreateCone(cone, closed=True) -> BRep3D`

### Model elements

- `base.CommonProperties() -> CommonProperties`
- `basis.ModelElement3D(common_properties, geometry_object) -> ModelElement3D`

Minimal pattern:

```python
common = base.CommonProperties()
brep = geo.BRep3D.CreateCuboid(placement, 1000.0, 500.0, 300.0)
element = basis.ModelElement3D(common, brep)
model_ele_list = ModelEleList()
model_ele_list.append(element)
return CreateElementResult(model_ele_list)
```

## Structure

- Keep the template script standalone
- Do not import from other template scripts
- Import ALLPLAN modules inside `create_element`
- Return model elements through `CreateElementResult`

## Expected runtime pattern

1. Read the template script from `scripts/`
2. Copy the shape that matches the user request
3. Adjust dimensions and placement
4. Keep validation close to the input values
5. Return a `CreateElementResult`

## Guidance

- Use millimeters unless the user says otherwise
- Build raw geometry first and wrap it as `ModelElement3D`
- Do not return raw `BRep3D` objects
- Prefer `CreateCuboid` and `CreateCylinder` before more complex BRep workflows
- Keep ALLPLAN imports inside `create_element(build_ele, doc)` unless the file itself is already the final PythonPart script

## Canonical patterns

- Cuboid pattern:
  - `AxisPlacement3D(origin, x_dir, z_dir)`
  - `BRep3D.CreateCuboid(...)`
  - `ModelElement3D(common, brep)`

- Cylinder pattern:
  - `AxisPlacement3D(origin, x_dir, z_dir)`
  - `BRep3D.CreateCylinder(...)`
  - `ModelElement3D(common, brep)`

## Script

- `pythonpart_template.py`
