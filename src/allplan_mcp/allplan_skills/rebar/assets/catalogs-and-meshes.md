# Catalogs and meshes

Use this note when the task depends on standard diameters, catalog meshes, or welded mesh placement.

## Catalog queries

Use `ReinforcementSettings` when the user asks for standard project values.

Key lookups:

```python
catalogs = AllplanReinf.ReinforcementSettings.GetEngCatCrossSections()
diameters = AllplanReinf.ReinforcementSettings.GetEngCatDiameters(catalog)
meshes = AllplanReinf.ReinforcementSettings.GetEngCatMeshes(catalog)
```

## When to query catalogs

Query catalogs when:

- the user asks for standard bar sizes
- the user asks for standard mesh families
- the generated code should follow project catalog data
- the prompt gives names such as B500, M335, Q257, or local mesh families without numeric values

Do not query catalogs if the user already gave explicit diameters, spacings, and mesh definitions.

## Bar catalog fallback

When catalog lookup is not available in the execution context, keep the bar sizes explicit:

```python
diameter_main = 16.0
diameter_secondary = 12.0
diameter_tie = 8.0
steel_grade = -1
concrete_grade = -1
```

Use `-1` for project defaults and do not invent a local steel grade.

## Mesh workflows

Use `MeshPlacement` or `PlaneMeshPlacement` when:

- the reinforcement is a welded mesh
- two orthogonal directions are one manufactured mesh object
- the user asks for a catalog mesh
- the output should schedule as mesh rather than individual bars

Use individual bars when:

- the user asks for explicit bars
- spacing differs by region
- hooks, laps, or custom geometry matter
- top and bottom layers use different marks or offsets

## Mesh as slab or footing reinforcement

For a simple mesh layer, treat it like a mat layer:

```python
mesh_origin = p(cover, cover, cover)
mesh_length = length - 2.0 * cover
mesh_width = width - 2.0 * cover
```

Then create `MeshPlacement` or `PlaneMeshPlacement` with the target mesh type. Check the exact constructor in the target ALLPLAN version before generating final code.

## Do not mix meanings

Do not model a welded mesh as many `BarPlacement` objects unless the user explicitly wants individual wires. It makes the generated model heavier and the schedule less accurate.
