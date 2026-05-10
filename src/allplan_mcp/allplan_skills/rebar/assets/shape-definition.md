# Rebar shape definition

Use this note when choosing the `BendingShape` constructor

## Straight bars

Use the point constructor for longitudinal bars

```python
shape = AllplanReinf.BendingShape(
    AllplanGeo.Point3D(0.0, 0.0, 0.0),
    diameter,
    steel_grade,
    concrete_grade,
)
```

Use this when the actual bar length will be controlled by the placement start and end points

## Bent bars and stirrups

Use the polyline constructor for closed or bent bars

```python
polyline = AllplanGeo.Polyline3D()
polyline += AllplanGeo.Point3D(...)
rollers = AllplanGeo.VecDoubleList([0.0] * segment_count)
shape = AllplanReinf.BendingShape(
    polyline,
    rollers,
    diameter,
    steel_grade,
    concrete_grade,
    AllplanReinf.BendingShapeType.eH1,
)
```

Use `eH1` for a closed stirrup style shape when that enum exists in the target version

## Hooks

Add hooks only when the request explicitly needs them

```python
shape.SetHookLengthStart(length)
shape.SetHookLengthEnd(length)
```

Do not invent hook lengths or hook angles

## Validation

- diameter must be positive
- point lists must be explicit
- closed stirrups should repeat the first point at the end
- roller count should match the segment logic of the target shape
