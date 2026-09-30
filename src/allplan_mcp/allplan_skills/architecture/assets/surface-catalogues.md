# Surface catalogues

## The ids are not universal

`SetHatch(301)` refers to entry 301 of the Schraffur catalogue configured for
the current ALLPLAN project or office standard. The same number means different
things in different offices.

Do not assume a mapping from material to id. `301` appears in ALLPLAN's own
example scripts, but only as an example.

## Where to get the right id

In order of preference:

1. The plan being modelled. A Werkplan legend states which Schraffur belongs to
   which material.
2. An existing element in the same drawing file. Read a comparable wall's tier
   properties and reuse its id.
3. The user. Ask which Schraffur applies rather than guessing.

An id invented by the model will produce a wall that is hatched, looks
plausible, and is wrong - which is harder to spot than a wall with no
Schraffur at all.

## Kinds of surface

- `Schraffur` - line hatching, the usual choice for materials in section
- `Muster` - a repeated symbol pattern
- `Flächenstil` - a surface style combining several representations
- `Füllfläche` - a solid background colour

Pick one per Wandschicht.
