# Runtime boundary

Use this note when deciding where ALLPLAN imports should live

## Rule

Keep ALLPLAN specific imports at the runtime boundary unless the file is already the final PythonPart script

Typical boundary:
- `create_element(build_ele, doc)`

## Why

- easier local testing
- fewer broken imports outside ALLPLAN
- cleaner generated code
