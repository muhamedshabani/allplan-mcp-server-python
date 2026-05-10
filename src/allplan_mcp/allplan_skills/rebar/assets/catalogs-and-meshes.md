# Catalogs and meshes

Use this note when the task depends on standard diameters, catalog meshes, or welded mesh placement

## Catalog queries

Use `ReinforcementSettings` when the user asks for standard project values

Key lookups:
- `GetEngCatCrossSections()`
- `GetEngCatDiameters(catalog)`
- `GetEngCatMeshes(catalog)`

## When to query catalogs

Query catalogs when:
- the user asks for standard bar sizes
- the user asks for standard mesh families
- the workflow should follow project catalog data

Do not query catalogs if the user already gave explicit diameters and mesh definitions

## Mesh workflows

Use `MeshPlacement` or `PlaneMeshPlacement` when:
- the reinforcement is a welded mesh
- two orthogonal directions are part of one mesh object

Use individual bars when:
- the user wants explicit bars
- spacing differs by region
- hooks, laps, or custom bar geometry matter more than mesh convenience
