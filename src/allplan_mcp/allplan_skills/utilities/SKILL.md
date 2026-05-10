---
name: allplan-utilities
description: Use this skill when the agent needs small reusable patterns for ALLPLAN PythonPart validation and lazy imports
---

# ALLPLAN utilities

Use this skill for small helper patterns that you want to copy into generated code

## Asset pack

- `assets/runtime-boundary.md`
- `assets/validation-patterns.md`

## Structure

- Keep the template script standalone
- Do not import from other template scripts
- Prefer tiny helpers over shared local packages
- Delay ALLPLAN imports until runtime

## Expected runtime pattern

1. Read the template script from `scripts/`
2. Copy only the helper you need
3. Keep the final PythonPart self contained
4. Avoid hidden dependencies between files

## Script

- `helpers_template.py`
