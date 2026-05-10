# Geometry core definitions

Use this note when choosing the geometry constructors

## Shorthand

```python
import NemAll_Python_Geometry as AllplanGeo
import NemAll_Python_BaseElements as AllplanBaseElements
import NemAll_Python_BasisElements as AllplanBasisElements
from CreateElementResult import CreateElementResult
from TypeCollections.ModelEleList import ModelEleList

geo = AllplanGeo
base = AllplanBaseElements
basis = AllplanBasisElements
```

## Core calls

- `geo.Point3D(x, y, z)`
- `geo.Vector3D(x, y, z)`
- `geo.AxisPlacement3D(origin, x_direction, z_direction)`
- `geo.BRep3D.CreateCuboid(placement, length, width, height)`
- `geo.BRep3D.CreateCylinder(placement, radius, height, closedTop, closedBottom)`
- `basis.ModelElement3D(common_properties, geometry_object)`

## Output contract

Always wrap geometry in a model element and return it through `CreateElementResult`
