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
http://127.0.0.1:8000/mcp
```

Useful environment variables:

```bash
ALLPLAN_HOST_URL=http://127.0.0.1:5679
MCP_HOST=127.0.0.1
MCP_PORT=8000
MCP_PATH=/mcp
ALLPLAN_MCP_ENABLE_PYTHON_EXEC=0
```

## Tools

- `allplan_health`: checks whether the Allplan host is reachable.
- `get_allplan_version`: returns the running Allplan version.
- `get_all_object_names`: returns display names for elements in the current document.
- `create_cube`: creates a cube in the current document.
- `create_box`: creates a rectangular cuboid in the current document.
- `execute_python`: available only when `ALLPLAN_MCP_ENABLE_PYTHON_EXEC=1`

## Notes

- [POST execution exploration](docs/post-execution-exploration.md)

## Development-only exec

The branch now supports a guarded development-only Python execution path for
local experiments.

Requirements:

```bash
ALLPLAN_MCP_ENABLE_PYTHON_EXEC=1
```

Set those variables before starting:

1. The Allplan `StartPythonHost` PythonPart bridge
2. The external FastMCP server

Behavior:

- The raw Allplan bridge accepts `POST /execute-python`
- The external MCP server exposes `execute_python(...)`
- The endpoint remains bound to `127.0.0.1`
- If the flag is missing, the MCP tool is not registered
- Imports are blocked by AST validation
- Private and dunder attribute access is blocked by AST validation
- Only a restricted builtin whitelist is available at runtime

Keep this disabled when using ngrok or any shared agent setup.
