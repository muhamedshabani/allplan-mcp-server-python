# Rebar placement patterns

Use this note when choosing the placement class and when deciding what the placement line means.

Rule of thumb:

- Shape points define the bar itself.
- Placement points define the distribution of copies.
- Host geometry defines the cover envelope.

## Single placement

Use `BarPlacement` for a shape that is already located in model coordinates:

```python
shape = straight_bar_shape_x(clear_length, diameter_main, steel_grade, concrete_grade)
shape.Move(AllplanGeo.Vector3D(x0, y0, z0))

placement = AllplanReinf.BarPlacement(
    position_number,
    1,
    AllplanGeo.Vector3D(0.0, 0.0, 0.0),
    AllplanGeo.Point3D(0.0, 0.0, 0.0),
    AllplanGeo.Point3D(0.0, 0.0, 0.0),
    shape,
)
```

Use this for:

- one top or bottom beam bar
- one column or pile vertical bar
- one starter or dowel bar
- one custom bar that was already moved into place

## Spacing-driven linear placement

Use the linear builder when spacing is the input:

```python
placement = LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
    position_number,
    shape,
    p(x0, y0, z0),
    p(x1, y1, z1),
    cover_left,
    cover_right,
    spacing,
    StartEndPlacementRule.AdditionalCover,
    True,
)
```

Use this for:

- slab mats
- footing mats
- pile cap mats
- beam stirrup regions
- column tie regions
- repeated dowels

Set `global_move=True` when the shape was defined locally at the origin and the builder should move it to `from_point`.

## Count-driven linear placement

Use the count builder when count is fixed:

```python
placement = LinearBarBuilder.create_linear_bar_placement_from_to_by_count(
    position_number,
    shape,
    p(x0, y0, z0),
    p(x1, y1, z1),
    cover_left,
    cover_right,
    bar_count,
    StartEndPlacementRule.AdditionalCover,
    True,
)
```

Use count placement for exact bar counts such as 4 bottom beam bars, 8 pile cage vertical bars, or a specified number of dowels.

## Mat placement recipe

For bottom X bars in a footing, cap, or slab:

```python
x0 = cover
x1 = length - cover
y0 = cover
y1 = width - cover
z0 = cover + diameter_main / 2.0

shape = straight_bar_shape_x(x1 - x0, diameter_main, steel_grade, concrete_grade)
bottom_x = LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
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

For bottom Y bars:

```python
z1 = cover + diameter_main * 1.5
shape = straight_bar_shape_y(y1 - y0, diameter_main, steel_grade, concrete_grade)
bottom_y = LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
    2,
    shape,
    p(x0, y0, z1),
    p(x1, y0, z1),
    0.0,
    0.0,
    spacing_main,
    StartEndPlacementRule.AdditionalCover,
    True,
)
```

For top mats, mirror the Z coordinates:

```python
top_z_x = thickness - cover - diameter_main * 1.5
top_z_y = thickness - cover - diameter_main / 2.0
```

Keep the two layers separated by at least one diameter so they do not occupy the same plane.

## Beam or column tie regions

Do not place all stirrups with one spacing when the design has end zones:

```python
left_ties = LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
    10,
    stirrup_shape,
    p(0.0, 0.0, 0.0),
    p(left_zone_length, 0.0, 0.0),
    cover,
    0.0,
    spacing_support,
    StartEndPlacementRule.AdditionalCover,
    True,
)

mid_ties = LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
    11,
    stirrup_shape,
    p(left_zone_length, 0.0, 0.0),
    p(length - right_zone_length, 0.0, 0.0),
    0.0,
    0.0,
    spacing_mid,
    StartEndPlacementRule.AdditionalCover,
    True,
)

right_ties = LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
    12,
    stirrup_shape,
    p(length - right_zone_length, 0.0, 0.0),
    p(length, 0.0, 0.0),
    0.0,
    cover,
    spacing_support,
    StartEndPlacementRule.AdditionalCover,
    True,
)
```

Adjust the axis to `Z` for vertical column or pedestal tie regions.

## Pile longitudinal bars

Create vertical bar shapes and move each copy around the pile radius:

```python
bar_radius = pile_radius - cover - diameter_main / 2.0
clear_depth = pile_depth - 2.0 * cover
shape_template = straight_bar_shape_z(clear_depth, diameter_main, steel_grade, concrete_grade)

placements = []
for index in range(bar_count):
    angle = 2.0 * math.pi * index / bar_count
    shape = straight_bar_shape_z(clear_depth, diameter_main, steel_grade, concrete_grade)
    shape.Move(vec(
        pile_center_x + bar_radius * math.cos(angle),
        pile_center_y + bar_radius * math.sin(angle),
        cover,
    ))
    placements.append(AllplanReinf.BarPlacement(30 + index, 1, vec(0.0, 0.0, 0.0), p(0.0, 0.0, 0.0), p(0.0, 0.0, 0.0), shape))
```

In full PythonParts, import `math`. In `execute_python`, use the injected `math` name.

## Circular placements

Use `CircularAreaElement(...)` for area-based circular reinforcement, especially pile hoops or cage rings. Check the exact constructor for the target ALLPLAN version.

For discrete hoop rings along depth, a practical fallback is:

1. build one circular hoop shape in the XY plane
2. move it to the pile center and first Z
3. place copies along Z by spacing

```python
hoop = circular_hoop_shape(pile_radius - cover - diameter_tie / 2.0, diameter_tie, steel_grade, concrete_grade)
hoops = LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
    40,
    hoop,
    p(pile_center_x, pile_center_y, cover),
    p(pile_center_x, pile_center_y, pile_depth - cover),
    0.0,
    0.0,
    spacing_tie,
    StartEndPlacementRule.AdditionalCover,
    True,
)
```

## Mesh placements

Use `MeshPlacement` or `PlaneMeshPlacement` when the user asks for welded mesh or a catalog mesh. Do not model welded mesh as individual bars unless hooks, nonuniform spacing, or explicit bar marks are required.

## Placement validation

- `spacing > 0`
- `bar_count >= 1`
- `clear_length > 0`
- `from_point` and `to_point` must differ for repeated placements
- start and end cover must not consume the whole placement line
- spacing regions must not overlap unless the design intentionally does so
