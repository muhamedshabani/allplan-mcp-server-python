---
name: allplan-rebar
description: Use this skill when the agent needs to write ALLPLAN PythonPart code for reinforcement shapes and bar placements
---

# ALLPLAN rebar

Use this skill for bending shapes, bar placements, mesh placements, and bending schedule style outputs

## Executive summary

ALLPLAN PythonParts has strong reinforcement support
The core object is `BendingShape` for geometry, diameter, steel grade, and hooks
The main placement objects are `BarPlacement`, `ExtrudeBarPlacement`, `SweepBarPlacement`, `MeshPlacement`, and `PlaneMeshPlacement`
The API also includes helpers for standard bar and mesh catalogs through `ReinforcementSettings`
Use this skill when the agent needs to turn reinforcement intent into PythonPart code instead of only describing it

## Official references

- Reinforcement placement
  - <https://pythonparts.allplan.com/2025/manual/features/reinforcement/placement/>
  - Use for single, linear, radial, circumferential, and extrusion placement patterns

- Reinforcement shape definition
  - <https://pythonparts.allplan.com/2025/manual/features/reinforcement/shape_definition/>
  - Use for `BendingShape` constructors and shape types

- BarPlacement API
  - <https://pythonparts.allplan.com/2023/api_reference/InterfaceStubs/NemAll_Python_Reinforcement/BarPlacement/>
  - Use for exact constructor signatures

- CircularAreaElement API
  - <https://pythonparts.allplan.com/2026/api_reference/InterfaceStubs/NemAll_Python_Reinforcement/CircularAreaElement/>
  - Use for circumferential pile or cage style reinforcement

- Solids
  - <https://pythonparts.allplan.com/2026/manual/features/geometry/solids/>
  - Use when the host beam, pile cap, or pile geometry also needs to be created

- BRep3D API
  - <https://pythonparts.allplan.com/2024/api_reference/InterfaceStubs/NemAll_Python_Geometry/BRep3D/>
  - Use for exact cuboid and cylinder geometry calls

- AxisPlacement3D API
  - <https://pythonparts.allplan.com/2026/api_reference/InterfaceStubs/NemAll_Python_Geometry/AxisPlacement3D/>
  - Use for local placement systems for host geometry

## Asset pack

Read these asset notes before writing non-trivial reinforcement code

- `assets/shape-definition.md`
- `assets/placement-patterns.md`
- `assets/beam-orchestration.md`
- `assets/pile-and-pile-cap-orchestration.md`
- `assets/catalogs-and-meshes.md`

## Rebar definitions

Define the shorthand once per script

```python
import NemAll_Python_Geometry as AllplanGeo
import NemAll_Python_Reinforcement as AllplanReinf
```

### Shape creation

- `AllplanReinf.BendingShape(AllplanGeo.Point3D(x, y, z), diameter, steel_grade, concrete_grade) -> shape`
  - Use for a straight bar or a point shape

- `AllplanReinf.BendingShape(polyline3d, rollers, diameter, steel_grade, concrete_grade, bending_shape_type) -> shape`
  - Use for stirrups, hoops, and bent bars
  - `rollers` is often `AllplanGeo.VecDoubleList([...])`
  - `bending_shape_type` can be `AllplanReinf.BendingShapeType.eH1` for a closed stirrup

- `shape.SetHookLengthStart(length)`
- `shape.SetHookLengthEnd(length)`
  - Use only when the requested bar actually needs hooks

### Bar placement

- `AllplanReinf.BarPlacement(position_number, bar_count, dist_vec, start_point, end_point, bending_shape) -> placement`
  - Use for single bars and linear placements
  - For a single bar use:
    - `bar_count = 1`
    - `dist_vec = AllplanGeo.Vector3D(0.0, 0.0, 0.0)`
  - This is the first API to try for most rebar code

- `LinearBarPlacementBuilder.create_linear_bar_placement_from_to_by_dist(...) -> BarPlacement`
  - Use when the user gives spacing
  - Prefer this over manual loops for dense linear mats

- `LinearBarPlacementBuilder.create_linear_bar_placement_from_to_by_count(...) -> BarPlacement`
  - Use when the user gives bar count

### 3D and special placements

- `AllplanReinf.ExtrudeBarPlacement(...) -> placement`
  - Use for path based 3D cages and extrusion style reinforcement

- `AllplanReinf.SweepBarPlacement(...) -> placement`
  - Use for multiple path continuous reinforcement

- `AllplanReinf.CircularAreaElement(...) -> placement`
  - Use for circular hoops or circumferential layouts

### Mesh placement

- `AllplanReinf.MeshPlacement(...) -> mesh`
  - Use for planar welded mesh placement

- `AllplanReinf.PlaneMeshPlacement(...) -> mesh`
  - Use when the workflow is driven by mesh data objects

### Catalog and utility lookups

- `AllplanReinf.ReinforcementSettings.GetEngCatCrossSections()`
  - Use to query available bar and mesh catalogs

- `AllplanReinf.ReinforcementSettings.GetEngCatDiameters(catalog)`
  - Use to query standard diameters from a catalog

- `AllplanReinf.ReinforcementSettings.GetEngCatMeshes(catalog)`
  - Use to query standard mesh types from a catalog

## Core API inventory

- `BendingShape`
  - Use for bar geometry, diameter, steel grade, and start or end hooks
- `BarPlacement`
  - Use for straight bars, stirrups, and repeated linear placements
- `ExtrudeBarPlacement`
  - Use for 3D cages, frames, and path based bar groups
- `SweepBarPlacement`
  - Use for multi path continuous reinforcement
- `MeshPlacement`
  - Use for flat reinforcement meshes
- `PlaneMeshPlacement`
  - Use for mesh data driven planar mesh placement
- `ReinforcementSettings`
  - Use to query standard bar diameters, bar catalogs, and mesh catalogs
- `StdReinfShapeBuilder`
  - Use when a high level builder already matches the requested pattern

## Geometry inputs to prefer

- Keep point lists explicit
- Use `Polyline2D` or `Polyline3D` for bending shapes
- Use `Point3D`, `Vector3D`, `Path3D`, and `Path3DList` for placement geometry
- Convert 2D shape intent into 3D only at the runtime boundary
- Keep cover, spacing, diameter, hook length, and bar count as explicit inputs

## Structure

- Keep the template script standalone
- Do not import from other template scripts
- Build the bending shape first
- Build the placement second
- Return placements through `CreateElementResult`
- Keep schedule or export helpers separate from geometry creation

## Expected runtime pattern

1. Read the template script from `scripts/`
2. Keep point lists explicit
3. Validate diameter spacing and count
4. Create a `BendingShape`
5. Create one or more placement objects
6. Apply common properties and attributes only after the reinforcement object exists

## Documentation workflow

Use the docs in this order when the API shape is not obvious

1. Read reinforcement shape definition
2. Read reinforcement placement
3. Read the exact `BarPlacement` or `CircularAreaElement` API page
4. Read geometry pages only if the host concrete geometry also needs to be created
5. Feed only the exact confirmed constructors back into generated code

The docs are enough for the contracts
- shape definition
- placement definition
- host geometry creation
- result assembly

The docs are usually not enough for the full orchestration of a reinforced beam, pile cap, or pile cage in one page
That orchestration still needs to be encoded in skill guidance or templates

## Function map

| Function | Purpose |
| --- | --- |
| `create_bar_2d` | Build a bar from a 2D path and optional hooks |
| `create_bar_3d` | Build a bar from explicit 3D points |
| `create_linear_bar_placement` | Distribute one bending shape by count or spacing |
| `create_mesh_placement` | Build a planar mesh from two directions |
| `rebar_set_properties` | Apply layer, pen, color, or material style metadata |
| `place_rebar_on_element` | Attach or associate reinforcement to a host element |
| `generate_bending_schedule` | Extract schedule style rows from created bars |
| `export_rebar_to_ifc` | Hand off created bars to an export path when needed |

## Guidance

- Prefer `BarPlacement` for the simplest answer
- Prefer `BendingShape(Point3D, ...)` plus `BarPlacement(...)` for straight bars
- Prefer `BendingShape(polyline, rollers, ..., eH1)` plus `BarPlacement(...)` for closed stirrups and hoops
- Use `ExtrudeBarPlacement` only when the path logic is truly 3D
- Use `MeshPlacement` or `PlaneMeshPlacement` when the user is asking for welded mesh rather than individual bars
- Query `ReinforcementSettings` when the user asks for standard diameters or catalog meshes
- Use builder helpers only when they reduce real complexity
- If the user asks for a bending schedule, extract geometry and hooks from the created `BendingShape` objects instead of recomputing from text
- For many repeated bars, prefer a builder or one placement object over manual element by element loops
- For beam style reinforcement, treat the problem as four contracts
  - host geometry
  - bending shape
  - placement
  - result assembly

## Canonical patterns

- Straight bar pattern:
  - `BendingShape(Point3D(...), diameter, steel, concrete)`
  - `BarPlacement(position, 1, Vector3D(), start, end, shape)`

- Closed bar pattern:
  - build `Polyline3D`
  - build `VecDoubleList`
  - `BendingShape(polyline, rollers, diameter, steel, concrete, BendingShapeType.eH1)`
  - `BarPlacement(position, 1, Vector3D(), start, start, shape)`

## Script

- `pythonpart_template.py`

## Risks and assumptions

- API names can vary across ALLPLAN versions
- Reinforcement catalogs depend on the local installation and project setup
- Export and host association flows may depend on licensed modules
- Some reinforcement services are only meaningful on Windows inside the ALLPLAN runtime
