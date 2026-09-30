# Wall tiers and Schraffur

Read this before creating any wall.

## The Schraffur lives on the tier

In ALLPLAN a `Wand` is a tiered object. The Schraffur, Muster, Flächenstil, and
Füllfläche all belong to the `Wandschicht`, not to the wall:

```python
tier = wall_prop.GetWallTierProperties(index + 1)
tier.SetHatch(hatch_id)
```

`GetWallTierProperties` counts from 1. Passing a 0-based index either raises or
hatches the wrong Wandschicht.

## One surface per tier

`SetHatch`, `SetPattern`, `SetFaceStyle`, and `SetBackgroundColor` are mutually
exclusive. ALLPLAN's own `WallInteractor` resets the first three and then sets
whichever is active:

```python
tier.SetHatch(0)
tier.SetPattern(0)
tier.SetFaceStyle(0)

if is_hatch:
    tier.SetHatch(hatch_id)
elif is_pattern:
    tier.SetPattern(pattern_id)
elif is_face_style:
    tier.SetFaceStyle(face_style_id)
elif is_filling:
    tier.SetBackgroundColor(filling_id)
```

Without the reset a tier can carry a stale surface alongside the intended one.

## `SetHatch(0)` means no hatching

Zero is not a hatch id. It is the "no Schraffur" state and it is the default.

A wall that reaches ALLPLAN with every tier at `SetHatch(0)` is geometrically
correct and professionally useless: in section it reads blank, so the material
cannot be told from the drawing. In German Werkplanung the Schraffur is what
distinguishes Stahlbeton from Mauerwerk from Dämmung.

Treat a missing Schraffur as an incomplete wall, not a cosmetic detail.

## Multi-layer walls

Each layer of the construction is one tier, outermost first. A 240mm concrete
wall with 80mm insulation is two tiers with two different Schraffuren, not one
tier 320mm thick.

## Heights

Tiers take their vertical extent from `PlaneReferences`:

```python
plane_ref = AllplanArchElements.PlaneReferences(doc, AllplanEleAdapter.BaseElementAdapter())
plane_ref.SetAbsBottomElevation(bottom)
plane_ref.SetAbsTopElevation(top)
tier.SetPlaneReferences(plane_ref)
```
