# Architecture elements

Use this note for walls, slabs and openings. A `ModelElement3D` cuboid is
not a wall: it has no tier, so it can never carry a hatch, and a wall
without hatching is unreadable in section. Build architecture elements
from `AllplanArchElements` (alias `AllplanArchEle`).

Shapes below are from the PythonParts API reference (Allplan 2026) and
Nemetschek's `PythonPartsExamples` (ArchitectureExamples/Objects).

## Wall

```python
doc = coord_input.GetInputViewDocument()
no_ref = AllplanElementAdapter.BaseElementAdapter()
dep = AllplanArchElements.PlaneReferences.PlaneReferenceDependency

ref = AllplanArchElements.PlaneReferences(doc, no_ref)   # (DocumentAdapter, BaseElementAdapter)
ref.SetBottomPlaneDependency(dep.eAbsElevation)
ref.SetTopPlaneDependency(dep.eAbsElevation)
ref.SetAbsBottomElevation(3110.0)                        # mm, absolute
ref.SetAbsTopElevation(5870.0)

props = AllplanArchElements.WallProperties()
props.TierCount = 1
props.StartNewJoinedWallGroup = True                     # False on later walls joins them

axis = AllplanArchElements.AxisProperties()
axis.OnTier = 1
axis.Position = AllplanArchElements.WallAxisPosition.eCenter
axis.Distance = 364.0 / 2                                # eLeft: 0, eCenter: t/2, eRight: t
axis.Extension = 1                                       # default 0 is invalid; use 1 or -1
props.Axis = axis

tier = props.GetWallTierProperties(1)                    # wall tiers start at 1
tier.Thickness = 364.0
tier.SetHatch(301)                                       # per tier; 0 means no hatch
tier.SetPattern(0)                                       # hatch, pattern, face style are exclusive
tier.SetFaceStyle(0)
tier.SetPlaneReferences(ref)

line = AllplanGeo.Line2D(AllplanGeo.Point2D(0.0, 11180.0), AllplanGeo.Point2D(10994.0, 11180.0))
wall = AllplanArchElements.WallElement(props, line)
```

Create it with `AllplanBaseElements.CreateElements(doc, AllplanGeo.Matrix3D(),
[wall], [], None)`. One element per call gives you that element's adapter
back, which you need for openings.

## Openings

An opening is cut into an existing element, so the host wall must be
created first and passed as its adapter.

```python
props = AllplanArchElements.WindowOpeningProperties()    # or DoorOpeningProperties
props.PlaneReferences = ref_sill_to_head                 # PlaneReferences with the sill and head levels
geo = props.GetGeometryProperties()                      # VerticalOpeningGeometryProperties
geo.Shape = AllplanArchElements.VerticalOpeningShapeType.eRectangle
geo.Width = 2383.0
geo.Depth = 364.0                                        # through the wall
opening = AllplanArchElements.WindowOpeningElement(props, wall_adapter, start_2d, end_2d, False)
```

The last argument is `drawPlacementPreview`; `False` creates the opening
with its wall adaptions.

## Slab

```python
props = AllplanArchElements.SlabProperties()
props.PlaneReferences = ref
props.TierCount = 1
tier = props.GetSlabTierProperties(0)                    # slab tiers start at 0 (walls at 1)
tier.Thickness = 220.0
props.SetHatch(302)
poly = AllplanGeo.Polygon3D()
for x, y in corners_closed:                              # repeat the first point to close
    poly += AllplanGeo.Point3D(float(x), float(y), z0)
ok, outline = AllplanGeo.ConvertTo2D(poly)
slab = AllplanArchElements.SlabElement(props, outline)
```

A rectangular Durchbruch is `SlabOpeningProperties(SlabOpeningType.eOpening)`
with `SetShapeType(ShapeType.eRectangular)` and `SetSize(width, depth)`,
placed by `SlabOpeningElement(props, point_2d, slab_adapter.GetModelElementUUID())`.

## Guidance

- Set the hatch on every tier. Allplan's default is 0, which is no hatch.
- Hatch numbers are the office's catalogue numbers; do not guess them.
- Use absolute plane references unless the task says which reference
  planes the drawing file uses.
- Check `allplan_health()` first: a host without `AllplanArchElements` in
  its `api_scope` cannot build any of this.
