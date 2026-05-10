# Allplan MCP Server

FastMCP server that exposes the local Allplan Python host as MCP tools.

The existing Allplan PythonPart starts a small local HTTP host at `127.0.0.1:5679`.
This package adds a FastMCP server in front of it, so agents can call MCP tools
over Streamable HTTP at `/mcp`.

## Setup

```bash
uv sync
```

Register the Allplan PythonPart bridge on the Windows machine where Allplan is
installed:

```cmd
utils\register_python_host.cmd
```

By default this copies the bridge to:

```text
%USERPROFILE%\Documents\Nemetschek\Allplan\2026\Usr\Local\PythonParts\PythonHost
%USERPROFILE%\Documents\Nemetschek\Allplan\2026\Usr\Local\PythonPartsScripts\PythonHost
```

For a different Allplan version:

```cmd
utils\register_python_host.cmd --allplan-version 2025
```

In Allplan, start the `StartPythonHost` PythonPart after registration. It must
keep running while the MCP server is being used.

## Run locally

```bash
uv run allplan-mcp
```

By default this starts the MCP server at:

```text
http://127.0.0.1:8888/mcp
```

Useful environment variables:

```bash
ALLPLAN_HOST_URL=http://127.0.0.1:5679
MCP_HOST=127.0.0.1
MCP_PORT=8888
MCP_PATH=/mcp
```

## Tools

- `allplan_health`: checks whether the Allplan host is reachable.
- `get_allplan_version`: returns the running Allplan version.
- `get_all_object_names`: returns display names for elements in the current document.
- `create_cube`: creates a cube in the current document.
- `create_box`: creates a rectangular cuboid in the current document.
- `execute_python`: executes sandboxed Python inside the running Allplan host

## Skill resources

Bundled skills are also exposed through MCP resources so clients can discover and read
them through the protocol.

Simple folder layout:

```text
src/allplan_mcp/allplan_skills/
  api-reference/
    SKILL.md
    assets/
    scripts/
  geometry/
    SKILL.md
    assets/
    scripts/
  rebar/
    SKILL.md
    assets/
    scripts/
  utilities/
    SKILL.md
    assets/
    scripts/
```

Resource URIs:

- `allplan://skills`
- `allplan://skills/api-reference`
- `allplan://skills/geometry`
- `allplan://skills/rebar`
- `allplan://skills/utilities`
- `allplan://skills/{skill_name}/assets/{asset_name}`
- `allplan://skills/{skill_name}/scripts/{script_name}`

The scripts are simple templates. They are meant to guide generated code and do not
depend on cross imports between skill folders.

## Notes

- [POST execution exploration](docs/post-execution-exploration.md)

## Sandboxed exec

The bridge exposes a sandboxed Python execution path for local experiments.

Behavior:

- The raw Allplan bridge accepts `POST /execute-python`
- The external MCP server exposes `execute_python(...)`
- The endpoint remains bound to `127.0.0.1`
- Imports are blocked by AST validation
- Private and dunder attribute access is blocked by AST validation
- Only a restricted builtin whitelist is available at runtime

Do not expose `execute_python` through ngrok or a shared agent setup.
