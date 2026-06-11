# Rebar shape definition

Use this note when choosing and building a `BendingShape`.

The most common agent mistake is to confuse shape geometry with placement geometry. The shape defines the actual bar path. Placement defines where copies of that shape are distributed.

## Base helpers

Use small helpers in generated snippets so point math stays visible:

```python
def p(x, y, z):
    return AllplanGeo.Point3D(float(x), float(y), float(z))

def vec(x, y, z):
    return AllplanGeo.Vector3D(float(x), float(y), float(z))

def polyline3d(points):
    line = AllplanGeo.Polyline3D()
    for x, y, z in points:
        line += p(x, y, z)
    return line

def bending_rollers(points, roller=0.0):
    segment_count = max(len(points) - 1, 1)
    return AllplanGeo.VecDoubleList([float(roller)] * segment_count)
```

Keep these helpers local to the generated PythonPart. They are not a separate shared dependency.

## Straight bars

For an actual straight bar, use a two-point polyline. Do not use a point shape unless an extrusion or sweep placement will create the length.

```python
def straight_bar_shape_x(length, diameter, steel_grade=-1, concrete_grade=-1):
    points = [(0.0, 0.0, 0.0), (float(length), 0.0, 0.0)]
    return AllplanReinf.BendingShape(
        polyline3d(points),
        bending_rollers(points),
        diameter,
        steel_grade,
        concrete_grade,
        AllplanReinf.BendingShapeType.LongitudinalBar,
    )
```

Use the same pattern for Y or Z bars:

```python
def straight_bar_shape_y(length, diameter, steel_grade=-1, concrete_grade=-1):
    points = [(0.0, 0.0, 0.0), (0.0, float(length), 0.0)]
    return AllplanReinf.BendingShape(
        polyline3d(points),
        bending_rollers(points),
        diameter,
        steel_grade,
        concrete_grade,
        AllplanReinf.BendingShapeType.LongitudinalBar,
    )

def straight_bar_shape_z(length, diameter, steel_grade=-1, concrete_grade=-1):
    points = [(0.0, 0.0, 0.0), (0.0, 0.0, float(length))]
    return AllplanReinf.BendingShape(
        polyline3d(points),
        bending_rollers(points),
        diameter,
        steel_grade,
        concrete_grade,
        AllplanReinf.BendingShapeType.LongitudinalBar,
    )
```

Move the shape into the host before creating a single placement:

```python
shape = straight_bar_shape_x(clear_length, diameter_main, steel_grade, concrete_grade)
shape.Move(vec(x0, y0, z0))
placement = AllplanReinf.BarPlacement(1, 1, vec(0.0, 0.0, 0.0), p(0.0, 0.0, 0.0), p(0.0, 0.0, 0.0), shape)
```

## Hooks

Add hooks only when the request explicitly needs them:

```python
shape.SetHookLengthStart(hook_length)
shape.SetHookLengthEnd(hook_length)
```

Do not invent hook lengths, angles, lap lengths, or development lengths. Ask for missing engineering values or keep them as explicit parameters.

## Rectangular stirrups and ties

Prefer the standard shape builder for rectangular stirrups and ties:

```python
roller = AllplanReinf.BendingRollerService.GetBendingRollerFactor(
    diameter_tie,
    steel_grade,
    -1,
    True,
)
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

Use the builder when the requested shape is a normal rectangular stirrup around a beam, column, pedestal, or pile cap tie.

## Custom closed ties

Use a closed polyline when the stirrup builder cannot express the requested shape:

```python
def closed_rect_tie_shape_yz(width_y, height_z, diameter, steel_grade=-1, concrete_grade=-1):
    points = [
        (0.0, 0.0, 0.0),
        (0.0, float(width_y), 0.0),
        (0.0, float(width_y), float(height_z)),
        (0.0, 0.0, float(height_z)),
        (0.0, 0.0, 0.0),
    ]
    return AllplanReinf.BendingShape(
        polyline3d(points),
        bending_rollers(points),
        diameter,
        steel_grade,
        concrete_grade,
        AllplanReinf.BendingShapeType.Stirrup,
    )
```

Use `closed_rect_tie_shape_yz` for beam stirrups placed along the X axis.

Use an XY-plane tie for column or pedestal ties placed along Z:

```python
def closed_rect_tie_shape_xy(width_x, depth_y, diameter, steel_grade=-1, concrete_grade=-1):
    points = [
        (0.0, 0.0, 0.0),
        (float(width_x), 0.0, 0.0),
        (float(width_x), float(depth_y), 0.0),
        (0.0, float(depth_y), 0.0),
        (0.0, 0.0, 0.0),
    ]
    return AllplanReinf.BendingShape(
        polyline3d(points),
        bending_rollers(points),
        diameter,
        steel_grade,
        concrete_grade,
        AllplanReinf.BendingShapeType.Stirrup,
    )
```

Move the tie into the concrete cover envelope before placing it. The tie plane should be perpendicular to the placement axis.

## Circular hoops

For pile hoops or circular column ties, create one circular polyline or use `CircularAreaElement` when the workflow is area based:

```python
def circular_hoop_shape(radius, diameter, steel_grade=-1, concrete_grade=-1, segment_count=32):
    points = []
    for index in range(segment_count + 1):
        angle = 2.0 * math.pi * index / segment_count
        points.append((radius * math.cos(angle), radius * math.sin(angle), 0.0))

    return AllplanReinf.BendingShape(
        polyline3d(points),
        bending_rollers(points),
        diameter,
        steel_grade,
        concrete_grade,
        AllplanReinf.BendingShapeType.Stirrup,
    )
```

In a full PythonPart, import `math`. In `execute_python`, use the injected `math` name.

## Point shapes

The point constructor is valid, but it is not the default for ordinary straight bars:

```python
point_shape = AllplanReinf.BendingShape(
    AllplanGeo.Point3D(0.0, 0.0, 0.0),
    diameter,
    steel_grade,
    concrete_grade,
)
```

Use point shapes when an extrusion, sweep, or other placement type supplies the path.

## Validation

- diameter must be positive
- cover must be zero or positive
- spacing must be positive
- point lists must be explicit
- closed stirrups and hoops repeat the first point at the end
- roller count follows segment count
- clear bar length must be greater than zero after cover is subtracted
