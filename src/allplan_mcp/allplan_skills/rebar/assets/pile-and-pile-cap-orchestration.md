# Pile and pile cap orchestration

Use this note when the task is piles, a pile cap, or both

## Contracts

1. host geometry
2. cap reinforcement
3. pile longitudinal bars
4. pile hoops or circular reinforcement
5. result assembly

## Recommended order

1. define cap size, pile diameter, pile depth, cover, and pile centers
2. create pile cap host geometry if requested
3. create pile host geometry if requested
4. create cap bottom and top mats
5. create cap stirrups or ties if required
6. create pile vertical bars
7. create pile hoops or circumferential reinforcement
8. collect everything into one `CreateElementResult`

## Cap reinforcement

For the cap:
- use straight bars for top and bottom mats
- use repeated placements when spacing is regular
- use a closed stirrup pattern if the cap needs ties

## Pile reinforcement

For the pile:
- use vertical straight bars on the pile radius minus cover
- use closed hoops or `CircularAreaElement` for circumferential reinforcement

## Coordinate logic

Coordinates should come from:
- cap extents
- pile centers
- pile radius
- cover
- depth

Do not place cap and pile reinforcement with unrelated coordinate systems
