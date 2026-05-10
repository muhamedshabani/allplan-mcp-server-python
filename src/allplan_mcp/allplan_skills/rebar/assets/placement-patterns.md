# Rebar placement patterns

Use this note when choosing the placement class

## Single or linear bars

Start with `BarPlacement`

```python
placement = AllplanReinf.BarPlacement(
    position_number,
    bar_count,
    dist_vec,
    start_point,
    end_point,
    bending_shape,
)
```

Use this for:
- single bars
- simple linear runs
- straight top and bottom bars
- individual stirrups

For a single bar:
- `bar_count = 1`
- `dist_vec = AllplanGeo.Vector3D()`

## Spacing driven linear runs

Use `LinearBarPlacementBuilder.create_linear_bar_placement_from_to_by_dist(...)`

Use this for:
- beam stirrup regions
- slab or cap mats
- repeated bars where spacing is the main input

## Count driven linear runs

Use `LinearBarPlacementBuilder.create_linear_bar_placement_from_to_by_count(...)`

Use this when the user gives count instead of spacing

## Circular placements

Use `CircularAreaElement(...)` for circumferential reinforcement

Use this for:
- circular pile hoops
- cage style ring layouts

Do not use it for a normal rectangular beam

## Mesh placements

Use `MeshPlacement(...)` or `PlaneMeshPlacement(...)` for welded mesh

Do not model welded mesh as many individual bars unless there is a clear reason
