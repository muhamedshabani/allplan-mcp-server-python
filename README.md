# Allplan MCP Server

A Model Context Protocol server for ALLPLAN that exposes a local ALLPLAN PythonPart bridge as MCP tools and resources.

This repository runs a FastMCP server outside ALLPLAN and forwards requests to a PythonPart bridge running inside ALLPLAN on `127.0.0.1:5679`.

## Key Features

- HTTP MCP server for ALLPLAN
- Local bridge to the running ALLPLAN PythonPart host
- Sandboxed `execute_python` tool for local experiments
- Bundled MCP skill resources for geometry, rebar, utilities, and API lookup
- Simple install from source with `uv`

## Prerequisites

- Windows machine with ALLPLAN installed
- ALLPLAN able to run PythonParts
- Python 3.11 or newer
- `uv` installed

Important:

- The ALLPLAN bridge currently binds to `127.0.0.1:5679`
- The MCP server and ALLPLAN bridge should run on the same machine
- The MCP server currently exposes HTTP transport at `/mcp`

## Quick Start with Claude Code

### 1. Install `uv`

If `uv` is not installed yet:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Clone the repository

```powershell
git clone https://github.com/AlejoDuarte23/allplan-mcp-server-python.git
cd allplan-mcp-server-python
```

### 3. Install Python dependencies

```powershell
uv sync
```

### 4. Register the ALLPLAN PythonPart bridge

Run on the Windows machine where ALLPLAN is installed:

```cmd
utils\register_python_host.cmd
```

For a different ALLPLAN version:

```cmd
utils\register_python_host.cmd --allplan-version 2025
```

By default the script copies the bridge to:

```text
%USERPROFILE%\Documents\Nemetschek\Allplan\2026\Usr\Local\PythonParts\PythonHost
%USERPROFILE%\Documents\Nemetschek\Allplan\2026\Usr\Local\PythonPartsScripts\PythonHost
```

### 5. Start the bridge in ALLPLAN

Inside ALLPLAN:

1. Open the PythonParts library
2. Insert `StartPythonHost`
3. Keep it running while the MCP server is in use

### 6. Start the MCP server

```powershell
uv run allplan-mcp
```

Default MCP URL:

```text
http://127.0.0.1:8888/mcp
```

### 7. Add the server to Claude Code

```powershell
claude mcp add --transport http allplan http://127.0.0.1:8888/mcp
```

Then open a new Claude Code session and ask it to interact with ALLPLAN.

Tip:

- Keep ALLPLAN open
- Keep `StartPythonHost` running
- Keep a working document open before starting MCP-driven tasks

## Other Clients

Any MCP client that supports remote HTTP MCP servers can connect to:

```text
http://127.0.0.1:8888/mcp
```

Examples:

- Claude Code: use `claude mcp add --transport http ...`
- VS Code or GitHub Copilot: add a remote HTTP MCP server and use the URL above
- Other MCP clients: configure the same HTTP endpoint

## Transport

This server currently runs with HTTP transport only.

Default runtime settings:

```text
ALLPLAN_HOST_URL=http://127.0.0.1:5679
MCP_HOST=127.0.0.1
MCP_PORT=8888
MCP_PATH=/mcp
```

## Optional Remote Access with ngrok

You can expose the MCP server with ngrok:

```powershell
ngrok http 8888
```

Then use:

```text
https://your-ngrok-domain.ngrok-free.app/mcp
```

Important:

- This is only reasonable for trusted private use
- The current server does not add bearer token authentication
- `execute_python` is exposed on the MCP server
- Do not expose this server publicly unless you add your own network or auth controls

## Available MCP Tools

- `allplan_health`
- `get_allplan_version`
- `get_all_object_names`
- `create_cube`
- `create_box`
- `execute_python`

## Available MCP Skill Resources

The server also exposes bundled skill resources through MCP.

Skill layout:

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

## Security Notes

- The raw ALLPLAN bridge accepts `POST /execute-python`
- The MCP server exposes `execute_python(...)`
- Imports are blocked by AST validation
- Private and dunder attribute access are blocked by AST validation
- Only a restricted builtin whitelist is available at runtime

This is a local-first setup, not a hardened multi-tenant service.

## Development Setup

### 1. Clone the repository

```powershell
git clone https://github.com/AlejoDuarte23/allplan-mcp-server-python.git
cd allplan-mcp-server-python
```

### 2. Install dependencies

```powershell
uv sync
```

### 3. Run the server from source

```powershell
uv run allplan-mcp
```

### 4. Lint

```powershell
uvx ruff check src/allplan_mcp python_host/PythonPartsScripts/PythonHost/PythonHostHandler.py python_host/PythonPartsScripts/PythonHost/sandbox
```

### 5. Type check

```powershell
uvx ty check src
```

### 6. Compile check

```powershell
python -m py_compile src/allplan_mcp/server.py src/allplan_mcp/skills.py
```

## Notes

- [POST execution exploration](docs/post-execution-exploration.md)
