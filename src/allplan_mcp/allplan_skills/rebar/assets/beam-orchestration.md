# Reinforced beam orchestration

Use this note when the task is a reinforced concrete beam.

Coordinate convention:

- `X`: beam axis
- `Y`: section width
- `Z`: section height
- origin: start, left, bottom corner of the concrete beam

## Contracts

Treat a reinforced beam as five contracts:

1. host cuboid
2. global rebar defaults
3. longitudinal bar shapes and positions
4. stirrup shape and regions
5. result assembly

## Recommended order

1. define beam length, width, height, cover, diameters, and spacings
2. create the host cuboid if the user asked for the 3D beam
3. derive `x0`, `x1`, clear length, and section bar coordinates
4. create bottom longitudinal bars
5. create top longitudinal bars
6. create side bars only if requested
7. create the stirrup shape from the cover envelope
8. place stirrups in one or more regions along X
9. collect concrete and reinforcement into one `CreateElementResult`

## Longitudinal bars

Use explicit single placements for top and bottom bars. This is easier for agents than trying to force bar count placement into a section.

```python
bar_x0 = cover
bar_x1 = length - cover
clear_bar_length = bar_x1 - bar_x0

bottom_z = cover + diameter_main / 2.0
top_z = height - cover - diameter_main / 2.0
left_y = cover + diameter_main / 2.0
right_y = width - cover - diameter_main / 2.0

bottom_positions = [
    (left_y, bottom_z),
    (right_y, bottom_z),
]
top_positions = [
    (left_y, top_z),
    (right_y, top_z),
]

beam_bars = []
for index, (y, z) in enumerate(bottom_positions + top_positions):
    shape = straight_bar_shape_x(clear_bar_length, diameter_main, steel_grade, concrete_grade)
    shape.Move(vec(bar_x0, y, z))
    beam_bars.append(AllplanReinf.BarPlacement(100 + index, 1, vec(0.0, 0.0, 0.0), p(0.0, 0.0, 0.0), p(0.0, 0.0, 0.0), shape))
```

For 3, 4, or more bars in one layer, generate `y` positions between `left_y` and `right_y` and keep the same `z`.

## Stirrup envelope

Derive the stirrup from cover, not from free-floating points:

```python
stirrup_width = width - 2.0 * cover
stirrup_height = height - 2.0 * cover
stirrup_shape = closed_rect_tie_shape_yz(stirrup_width, stirrup_height, diameter_tie, steel_grade, concrete_grade)
stirrup_shape.Move(vec(0.0, cover, cover))
```

This creates one stirrup shape in the YZ section. It can then be placed along X.

## One-region stirrup placement

Use when the prompt gives one stirrup spacing:

```python
stirrups = LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
    10,
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

## Region logic

Beam reinforcement is usually not one uniform region.

Typical split:

- left support zone
- midspan zone
- right support zone

Use separate placements when spacing changes:

```python
support_len = 700.0
left_ties = LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
    11,
    stirrup_shape,
    p(cover, 0.0, 0.0),
    p(support_len, 0.0, 0.0),
    0.0,
    0.0,
    spacing_support,
    StartEndPlacementRule.AdditionalCover,
    True,
)

mid_ties = LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
    12,
    stirrup_shape,
    p(support_len, 0.0, 0.0),
    p(length - support_len, 0.0, 0.0),
    0.0,
    0.0,
    spacing_mid,
    StartEndPlacementRule.AdditionalCover,
    True,
)

right_ties = LinearBarBuilder.create_linear_bar_placement_from_to_by_dist(
    13,
    stirrup_shape,
    p(length - support_len, 0.0, 0.0),
    p(length - cover, 0.0, 0.0),
    0.0,
    0.0,
    spacing_support,
    StartEndPlacementRule.AdditionalCover,
    True,
)
```

## Beam checklist

- do not hardcode bar coordinates without cover logic
- place top and bottom bars as explicit bars unless the requested layout is very dense
- use side bars only when requested
- split stirrups into support and midspan regions when spacing changes
- keep all shapes in the same beam coordinate system
- return host, longitudinal bars, and stirrups together
