---
name: allplan-architecture
description: Use this skill when the agent needs to create ALLPLAN architectural objects - walls, slabs, columns - rather than generic 3D solids, and must set the Schraffur correctly
---

# ALLPLAN architecture

Use this skill for `Wand`, `Decke`, and `Stütze`. Use the geometry skill only
for generic solids that are not architectural objects.

## The distinction that matters

A cuboid and a wall are not the same object.

- `AllplanGeo.Polyhedron3D.CreateCuboid(...)` wrapped in `ModelElement3D` is a
  generic 3D solid. It has no Wandschichten, carries no Schraffur, and reads as
  blank in section.
- `AllplanArchElements.WallElement(wall_prop, axis)` is a real Wand. It has
  tiers, each of which carries its own surface.

If the user asks for a wall, build a wall. A cuboid that looks like a wall in
the 3D view is not a Werkplan wall.

## Asset pack

- `assets/wall-tiers-and-schraffur.md` - read before creating any wall
- `assets/surface-catalogues.md` - where the ids come from

## Modules

```python
import NemAll_Python_ArchElements as AllplanArchElements
import NemAll_Python_IFW_ElementAdapter as AllplanEleAdapter
```

Both are in scope inside `execute_python`; no import statement is allowed there.

## Wall creation

Prefer the `create_wall` MCP tool. It validates the tier surfaces before
anything reaches Allplan and reports the Schraffur it applied.

Drop to `execute_python` only for walls the tool cannot express - curved axes,
joined wall groups, openings.

## Minimal wall

```python
wall_prop = AllplanArchElements.WallProperties()

axis_prop = AllplanArchElements.AxisProperties()
axis_prop.Distance  = 0.0
axis_prop.Extension = -1
axis_prop.Position  = AllplanArchElements.WallAxisPosition.eFree

wall_prop.SetTierCount(1)
wall_prop.SetAxis(axis_prop)

doc = coord_input.GetInputViewDocument()
plane_ref = AllplanArchElements.PlaneReferences(doc, AllplanEleAdapter.BaseElementAdapter())
plane_ref.SetAbsBottomElevation(0.0)
plane_ref.SetAbsTopElevation(2750.0)

tier = wall_prop.GetWallTierProperties(1)          # Wandschichten count from 1
tier.SetThickness(240.0)
tier.SetHatch(0)
tier.SetPattern(0)
tier.SetFaceStyle(0)
tier.SetHatch(301)                                  # the Schraffur
tier.SetPlaneReferences(plane_ref)

axis = AllplanGeo.Line2D(AllplanGeo.Point2D(0.0, 0.0), AllplanGeo.Point2D(5000.0, 0.0))
wall = AllplanArchElements.WallElement(wall_prop, axis)
```

## Guidance

- Millimetres, unless the user says otherwise.
- Wandschichten are numbered from 1, not 0.
- Reset hatch, pattern and face style on every tier, then set the one that
  applies. They are mutually exclusive.
- Never leave a tier at `SetHatch(0)` unless the plan really shows no hatching.
- Take the hatch from the plan being modelled, not from a guess.

## Script

- `wall_template.py`
