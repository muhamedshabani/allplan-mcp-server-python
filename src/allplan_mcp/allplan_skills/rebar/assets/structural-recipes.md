# Structural rebar recipes

Use this note to generalize the same rebar primitives across footings, beams, piles, pile caps, pedestals, columns, and slabs.

The agent should always produce code from this structure:

1. host dimensions
2. global rebar defaults
3. derived cover coordinates
4. shape snippets
5. placement snippets
6. result assembly

## Shared globals

Use a single parameter block and derive all coordinates from it:

```python
length = 3000.0
width = 2000.0
height = 600.0
cover = 50.0

steel_grade = -1
concrete_grade = -1

diameter_main = 16.0
diameter_secondary = 12.0
diameter_tie = 8.0

spacing_main = 150.0
spacing_secondary = 200.0
spacing_tie = 200.0
```

Use named marks instead of hidden counters:

```python
marks = {
    "bottom_x": 1,
    "bottom_y": 2,
    "top_x": 3,
    "top_y": 4,
    "ties": 10,
    "vertical": 20,
    "hoops": 40,
}
```

This is easier for agents to modify safely than a global `next_mark()` function.

## Concrete host snippets

Cuboid host for footing, beam, pile cap, pedestal, column, or slab:

```python
common_properties = AllplanBaseElements.CommonProperties()
common_properties.GetGlobalProperties()
placement = AllplanGeo.AxisPlacement3D(
    AllplanGeo.Point3D(0.0, 0.0, 0.0),
    AllplanGeo.Vector3D(1.0, 0.0, 0.0),
    AllplanGeo.Vector3D(0.0, 0.0, 1.0),
)
host_brep = AllplanGeo.BRep3D.CreateCuboid(placement, length, width, height)
```

Cylinder host for a pile or circular column:

```python
placement = AllplanGeo.AxisPlacement3D(
    AllplanGeo.Point3D(pile_center_x, pile_center_y, 0.0),
    AllplanGeo.Vector3D(1.0, 0.0, 0.0),
    AllplanGeo.Vector3D(0.0, 0.0, 1.0),
)
pile_brep = AllplanGeo.BRep3D.CreateCylinder(placement, pile_radius, pile_depth, True, True)
```

If the target ALLPLAN version uses `Polyhedron3D.CreateCuboid`, follow the geometry skill fallback.

## Footing recipe

Use for isolated footings and rectangular foundation pads.

Minimum contract:

- host cuboid
- bottom X bars
- bottom Y bars
- optional top X/Y bars
- optional pedestal dowels

Derived values:

```python
x0 = cover
x1 = length - cover
y0 = cover
y1 = width - cover
bottom_z_x = cover + diameter_main / 2.0
bottom_z_y = cover + diameter_main * 1.5
top_z_x = height - cover - diameter_main * 1.5
top_z_y = height - cover - diameter_main / 2.0
```

Bottom mats:

```python
bottom_x_shape = straight_bar_shape_x(x1 - x0, diameter_main, steel_grade, concrete_grade)
bottom_x = LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
    marks["bottom_x"],
    bottom_x_shape,
    p(x0, y0, bottom_z_x),
    p(x0, y1, bottom_z_x),
    0.0,
    0.0,
    spacing_main,
    StartEndPlacementRule.AdditionalCover,
    True,
)

bottom_y_shape = straight_bar_shape_y(y1 - y0, diameter_secondary, steel_grade, concrete_grade)
bottom_y = LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
    marks["bottom_y"],
    bottom_y_shape,
    p(x0, y0, bottom_z_y),
    p(x1, y0, bottom_z_y),
    0.0,
    0.0,
    spacing_secondary,
    StartEndPlacementRule.AdditionalCover,
    True,
)
```

For top mats, reuse the same shapes and placement directions with `top_z_x` and `top_z_y`.

## Slab recipe

Use the footing mat recipe with these slab-specific choices:

- bottom mat only for simple one-way or two-way bottom reinforcement
- top mat near supports or over the full slab when requested
- mesh placement only when the user asks for welded mesh
- keep layer offsets explicit so top and bottom bars do not overlap

For a one-way slab:

```python
main_shape = straight_bar_shape_x(x1 - x0, diameter_main, steel_grade, concrete_grade)
main_bottom = LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
    marks["bottom_x"],
    main_shape,
    p(x0, y0, bottom_z_x),
    p(x0, y1, bottom_z_x),
    0.0,
    0.0,
    spacing_main,
    StartEndPlacementRule.AdditionalCover,
    True,
)
```

Add distribution bars in the transverse direction only when requested or required by the design prompt.

## Beam recipe

Minimum contract:

- host cuboid
- bottom longitudinal bars
- top longitudinal bars
- stirrup regions along length

Coordinate convention:

- `X` = beam axis
- `Y` = section width
- `Z` = section height

Longitudinal bars as explicit single placements:

```python
bar_x0 = cover
bar_x1 = length - cover
clear_bar_length = bar_x1 - bar_x0
bottom_z = cover + diameter_main / 2.0
top_z = height - cover - diameter_main / 2.0
left_y = cover + diameter_main / 2.0
right_y = width - cover - diameter_main / 2.0

bottom_shape_left = straight_bar_shape_x(clear_bar_length, diameter_main, steel_grade, concrete_grade)
bottom_shape_left.Move(vec(bar_x0, left_y, bottom_z))
bottom_left = AllplanReinf.BarPlacement(101, 1, vec(0.0, 0.0, 0.0), p(0.0, 0.0, 0.0), p(0.0, 0.0, 0.0), bottom_shape_left)

bottom_shape_right = straight_bar_shape_x(clear_bar_length, diameter_main, steel_grade, concrete_grade)
bottom_shape_right.Move(vec(bar_x0, right_y, bottom_z))
bottom_right = AllplanReinf.BarPlacement(102, 1, vec(0.0, 0.0, 0.0), p(0.0, 0.0, 0.0), p(0.0, 0.0, 0.0), bottom_shape_right)
```

For more than two bars per layer, distribute Y positions between `left_y` and `right_y` and create one single placement per bar.

Stirrups:

```python
stirrup_width = width - 2.0 * cover
stirrup_height = height - 2.0 * cover
stirrup_shape = closed_rect_tie_shape_yz(stirrup_width, stirrup_height, diameter_tie, steel_grade, concrete_grade)
stirrup_shape.Move(vec(0.0, cover, cover))

stirrups = LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
    marks["ties"],
    stirrup_shape,
    p(cover, 0.0, 0.0),
    p(length - cover, 0.0, 0.0),
    0.0,
    0.0,
    spacing_tie,
    StartEndPlacementRule.AdditionalCover,
    True,
)
```

Use three tie regions when the prompt gives support and midspan spacing.

## Pedestal and rectangular column recipe

Minimum contract:

- host cuboid
- vertical bars at corners or distributed around perimeter
- closed rectangular ties along height

Vertical corner bars:

```python
z0 = cover
z1 = height - cover
clear_vertical = z1 - z0
bar_positions = [
    (cover + diameter_main / 2.0, cover + diameter_main / 2.0),
    (width - cover - diameter_main / 2.0, cover + diameter_main / 2.0),
    (width - cover - diameter_main / 2.0, length - cover - diameter_main / 2.0),
    (cover + diameter_main / 2.0, length - cover - diameter_main / 2.0),
]

vertical_bars = []
for index, (x, y) in enumerate(bar_positions):
    shape = straight_bar_shape_z(clear_vertical, diameter_main, steel_grade, concrete_grade)
    shape.Move(vec(x, y, z0))
    vertical_bars.append(AllplanReinf.BarPlacement(200 + index, 1, vec(0.0, 0.0, 0.0), p(0.0, 0.0, 0.0), p(0.0, 0.0, 0.0), shape))
```

Column ties along height:

```python
tie_shape = closed_rect_tie_shape_xy(width - 2.0 * cover, length - 2.0 * cover, diameter_tie, steel_grade, concrete_grade)
tie_shape.Move(vec(cover, cover, 0.0))

ties = LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
    marks["ties"],
    tie_shape,
    p(0.0, 0.0, cover),
    p(0.0, 0.0, height - cover),
    0.0,
    0.0,
    spacing_tie,
    StartEndPlacementRule.AdditionalCover,
    True,
)
```

Use denser tie regions at top and bottom when the prompt provides confinement zones.

## Circular pile recipe

Minimum contract:

- cylinder host
- vertical bars around radius
- hoops along depth

Derived values:

```python
pile_radius = pile_diameter / 2.0
bar_radius = pile_radius - cover - diameter_main / 2.0
hoop_radius = pile_radius - cover - diameter_tie / 2.0
z0 = cover
z1 = pile_depth - cover
```

Use the pile longitudinal and hoop snippets from `placement-patterns.md`.

If a pile is below a cap, use the cap coordinate system:

```python
pile_center_x = cap_origin_x + local_pile_x
pile_center_y = cap_origin_y + local_pile_y
```

Do not create pile cages in a different origin than the pile cap.

## Pile cap recipe

Minimum contract:

- cap host cuboid
- cap bottom/top mats
- pile center list
- optional pile hosts and pile cages
- optional pedestal or column dowels

Cap mats use the footing recipe. Piles use the circular pile recipe. The important part is coordinate sharing:

```python
pile_centers = [
    (750.0, 750.0),
    (2250.0, 750.0),
    (750.0, 1750.0),
    (2250.0, 1750.0),
]
```

For each pile center:

```python
for pile_center_x, pile_center_y in pile_centers:
    # create pile host at this center
    # create vertical cage bars at this center
    # create hoops at this center
    pass
```

Add cap top bars only if requested or if the user asks for a full reinforced pile cap.

## Result assembly

Collect host and reinforcement in separate lists, then return one result:

```python
model_ele_list = ModelEleList(common_properties)
model_ele_list.append_geometry_3d(host_brep)

reinf_ele_list = ModelEleList()
reinf_ele_list.append(bottom_x)
reinf_ele_list.append(bottom_y)
reinf_ele_list.append(ties)
for bar in vertical_bars:
    reinf_ele_list.append(bar)

return CreateElementResult(elements=model_ele_list + reinf_ele_list)
```

## Agent checklist

- keep global dimensions and rebar defaults visible
- derive bar coordinates from cover and diameter
- use one coordinate convention for host and bars
- use one mark per logical bar group
- split regions when spacing changes
- never hand-place every repeated mat bar when a placement builder can do it
- do not mix mesh and individual bars unless the prompt asks for both
- include the concrete host when the user asks to create the 3D element
