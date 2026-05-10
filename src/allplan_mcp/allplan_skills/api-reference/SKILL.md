---
name: allplan-api-reference
description: Use this skill when the agent needs exact ALLPLAN API names, signatures, versions, or fallback research beyond the curated geometry and rebar skills
---

# ALLPLAN API reference

Use this skill when the agent is not sure about an ALLPLAN class name, constructor, enum, or helper module

## Asset pack

- `assets/research-workflow.md`

## Purpose

- Find exact API names before writing code
- Check version specific differences
- Separate broad reference lookup from the focused geometry and rebar skills
- Keep the generated PythonPart small and move lookup work into preparation

## Workflow

1. Start with the geometry or rebar skill when the request is common
2. Switch to this skill when a class or method is unclear
3. Prefer exact signatures from official docs over guessed names
4. Feed only the final relevant definitions back into generated code

## What to verify

- Constructor signature
- Enum name
- Helper module name
- Whether the API belongs to geometry, reinforcement, utility, or another module
- Whether the call shape changes by ALLPLAN version

## Script

- `reference_lookup_template.py`
