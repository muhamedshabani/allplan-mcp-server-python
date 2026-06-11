# Pile and pile cap orchestration

Use this note when the task is piles, pile caps, pile groups, or footings with pedestal dowels.

## Contracts

1. cap or footing host geometry
2. pile host geometry
3. cap or footing reinforcement
4. pile longitudinal bars
5. pile hoops or circular reinforcement
6. pedestal, column, or starter dowels when requested
7. result assembly

## Shared coordinate system

Do not create the cap and piles in unrelated coordinate systems.

Use cap-local pile centers:

```python
pile_centers = [
    (750.0, 750.0),
    (2250.0, 750.0),
    (750.0, 1750.0),
    (2250.0, 1750.0),
]
```

Every pile host, pile vertical bar, pile hoop, cap mat, and pedestal dowel should use these same `x, y` centers.

## Recommended order

1. define cap size, pile diameter, pile depth, cover, and pile centers
2. create pile cap host geometry if requested
3. create pile host geometry at each center if requested
4. create cap bottom and top mats
5. create cap ties or punching reinforcement if requested
6. create pile vertical bars around each center
7. create pile hoops or circumferential reinforcement for each pile
8. create pedestal or column dowels if requested
9. collect everything into one `CreateElementResult`

## Cap reinforcement

Use the footing recipe from `structural-recipes.md`:

- bottom X mat
- bottom Y mat
- optional top X mat
- optional top Y mat

For a pile cap, top mats are commonly requested together with bottom mats. Keep them as separate marks.

```python
cap_bottom_x = bottom_x
cap_bottom_y = bottom_y
cap_top_x = top_x
cap_top_y = top_y
```

If pile punching or local confinement is requested, use closed rectangular ties around the pile or pedestal footprint instead of changing the main mat.

## Pile host

Use a cylinder at each pile center:

```python
for pile_center_x, pile_center_y in pile_centers:
    placement = AllplanGeo.AxisPlacement3D(
        p(pile_center_x, pile_center_y, -pile_depth),
        AllplanGeo.Vector3D(1.0, 0.0, 0.0),
        AllplanGeo.Vector3D(0.0, 0.0, 1.0),
    )
    pile_brep = AllplanGeo.BRep3D.CreateCylinder(placement, pile_radius, pile_depth, True, True)
    model_ele_list.append_geometry_3d(pile_brep)
```

If your ALLPLAN version creates cylinders upward from origin, set the origin to the pile bottom or adjust the placement so the top aligns with the cap underside.

## Pile longitudinal bars

Use vertical straight bars around the pile radius:

```python
bar_radius = pile_radius - cover - diameter_main / 2.0
z0 = -pile_depth + cover
z1 = -cover
clear_vertical = z1 - z0

pile_vertical_bars = []
for pile_center_x, pile_center_y in pile_centers:
    for index in range(pile_bar_count):
        angle = 2.0 * math.pi * index / pile_bar_count
        x = pile_center_x + bar_radius * math.cos(angle)
        y = pile_center_y + bar_radius * math.sin(angle)
        shape = straight_bar_shape_z(clear_vertical, diameter_main, steel_grade, concrete_grade)
        shape.Move(vec(x, y, z0))
        pile_vertical_bars.append(AllplanReinf.BarPlacement(300 + index, 1, vec(0.0, 0.0, 0.0), p(0.0, 0.0, 0.0), p(0.0, 0.0, 0.0), shape))
```

In full PythonParts, import `math`. In `execute_python`, use the injected `math` name.

## Pile hoops

Use closed circular hoop shapes or `CircularAreaElement` for circumferential reinforcement:

```python
hoop_radius = pile_radius - cover - diameter_tie / 2.0

pile_hoops = []
for pile_center_x, pile_center_y in pile_centers:
    hoop_shape = circular_hoop_shape(hoop_radius, diameter_tie, steel_grade, concrete_grade)
    pile_hoops.append(
        LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
            400,
            hoop_shape,
            p(pile_center_x, pile_center_y, z0),
            p(pile_center_x, pile_center_y, z1),
            0.0,
            0.0,
            spacing_tie,
            StartEndPlacementRule.AdditionalCover,
            True,
        )
    )
```

Use `CircularAreaElement(...)` only after confirming the constructor for the target ALLPLAN version.

## Pedestal or column dowels on a cap

Use vertical straight bars above the cap:

```python
pedestal_x0 = cap_length / 2.0 - pedestal_length / 2.0 + cover
pedestal_x1 = cap_length / 2.0 + pedestal_length / 2.0 - cover
pedestal_y0 = cap_width / 2.0 - pedestal_width / 2.0 + cover
pedestal_y1 = cap_width / 2.0 + pedestal_width / 2.0 - cover

dowel_positions = [
    (pedestal_x0, pedestal_y0),
    (pedestal_x1, pedestal_y0),
    (pedestal_x1, pedestal_y1),
    (pedestal_x0, pedestal_y1),
]

dowels = []
for index, (x, y) in enumerate(dowel_positions):
    shape = straight_bar_shape_z(dowel_height, diameter_main, steel_grade, concrete_grade)
    shape.Move(vec(x, y, cap_height - cover))
    dowels.append(AllplanReinf.BarPlacement(500 + index, 1, vec(0.0, 0.0, 0.0), p(0.0, 0.0, 0.0), p(0.0, 0.0, 0.0), shape))
```

Add hooks or embedment only when the user provides those values.

## Footings without piles

A footing is the pile cap recipe without pile centers:

- cap host becomes footing host
- cap mats become footing mats
- omit pile host, pile vertical bars, and pile hoops
- keep pedestal dowels if requested

## Validation

- pile centers must be inside the cap footprint with enough edge cover
- pile diameter must fit the requested reinforcement cover
- cap mat bars must not intersect pile hoops unless the design intentionally overlaps
- vertical bars must start and stop at explicit Z coordinates
- top of pile cage should align with pile top or cap embedment requirement
