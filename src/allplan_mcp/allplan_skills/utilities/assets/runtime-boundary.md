# Runtime boundary

Use this note when deciding where ALLPLAN imports should live

## Rule

Keep ALLPLAN specific imports at the runtime boundary unless the file is already the final PythonPart script

Typical boundary:
- `create_element(build_ele, doc)`

For MCP `execute_python`, import statements are blocked by the sandbox. Use the names injected by the Python host instead.

Injected names include:

- `AllplanGeo`
- `AllplanReinf`
- `AllplanBaseElements`
- `AllplanBasisElements`
- `AllplanSettings`
- `GeneralShapeBuilder`
- `LinearBarBuilder`
- `ConcreteCoverProperties`
- `ReinforcementShapeProperties`
- `RotationUtil`
- `StartEndPlacementRule`
- `math`

## Why

- easier local testing
- fewer broken imports outside ALLPLAN
- cleaner generated code
- sandbox snippets can still create geometry and reinforcement without import statements
