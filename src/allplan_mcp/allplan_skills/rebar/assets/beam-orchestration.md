# Reinforced beam orchestration

Use this note when the task is a reinforced beam

## Contracts

Treat the problem as four contracts

1. host geometry
2. stirrup shape
3. longitudinal bar placement
4. result assembly

## Recommended order

1. define beam length, width, height, and cover
2. derive the stirrup envelope from cover
3. build one stirrup `BendingShape`
4. place stirrup regions along the beam
5. build top longitudinal bars
6. build bottom longitudinal bars
7. add optional side bars or support bars
8. collect placements into `ModelEleList`
9. return `CreateElementResult`

## Region logic

Beam reinforcement is usually not one uniform region

Typical split:
- left support zone
- midspan zone
- right support zone

Each region should usually be its own placement object

## Coordinate logic

Derive coordinates from:
- beam section
- concrete cover
- stirrup diameter
- longitudinal bar diameter

Do not hardcode free floating points when they should come from cover logic

## Minimal output contract

The final script should:
- create the host beam geometry if requested
- create stirrup placements
- create top and bottom bar placements
- return everything through one `CreateElementResult`
