# Host geometry workflow

Use this note when the task also needs concrete host geometry

## Recommended order

1. define dimensions
2. define origin and local directions
3. build `AxisPlacement3D`
4. build `BRep3D`
5. wrap it in `ModelElement3D`
6. append to `ModelEleList`
7. return `CreateElementResult`

## Typical hosts

- beam as cuboid
- pile cap as cuboid
- pile as cylinder

## Guidance

- use millimeters unless told otherwise
- do not return raw `BRep3D`
- keep coordinate logic explicit
