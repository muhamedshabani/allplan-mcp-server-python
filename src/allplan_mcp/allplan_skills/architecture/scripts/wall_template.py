"""Template for an ALLPLAN wall with an explicit Schraffur per Wandschicht.

Copy the shape, adjust the tiers, and take the hatch ids from the plan being
modelled. Do not invent them - see assets/surface-catalogues.md.
"""


def create_wall(doc, coord_input):
    """Build one wall with two Wandschichten"""

    import NemAll_Python_ArchElements as AllplanArchElements
    import NemAll_Python_Geometry as AllplanGeo
    import NemAll_Python_IFW_ElementAdapter as AllplanEleAdapter

    # -- tiers, outermost first: (thickness, hatch id) ----------------------
    tiers = [
        (240.0, 301),   # Stahlbeton, per the plan legend
        (80.0, 305),    # Dämmung, per the plan legend
    ]

    bottom_elevation = 0.0
    top_elevation = 2750.0

    start = AllplanGeo.Point2D(0.0, 0.0)
    end = AllplanGeo.Point2D(5000.0, 0.0)

    # -- wall properties ----------------------------------------------------
    wall_prop = AllplanArchElements.WallProperties()

    axis_prop = AllplanArchElements.AxisProperties()
    axis_prop.Distance = 0.0
    axis_prop.Extension = -1
    axis_prop.Position = AllplanArchElements.WallAxisPosition.eFree

    wall_prop.SetTierCount(len(tiers))
    wall_prop.SetAxis(axis_prop)

    plane_ref = AllplanArchElements.PlaneReferences(
        doc, AllplanEleAdapter.BaseElementAdapter()
    )
    plane_ref.SetAbsBottomElevation(bottom_elevation)
    plane_ref.SetAbsTopElevation(top_elevation)

    # -- one Wandschicht at a time; tiers count from 1 ----------------------
    for index, (thickness, hatch_id) in enumerate(tiers):
        tier = wall_prop.GetWallTierProperties(index + 1)
        tier.SetThickness(thickness)

        # Reset all three, then set the one that applies. They are exclusive.
        tier.SetHatch(0)
        tier.SetPattern(0)
        tier.SetFaceStyle(0)
        tier.SetHatch(hatch_id)

        tier.SetPlaneReferences(plane_ref)

    axis = AllplanGeo.Line2D(start, end)

    return AllplanArchElements.WallElement(wall_prop, axis)
