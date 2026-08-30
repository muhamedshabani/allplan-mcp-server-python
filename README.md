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
- `list_allplan_skills`: lists the bundled skill documents and their URIs.
- `search_allplan_skills`: ranked full text search across the bundled skills.
- `read_allplan_skill`: reads one skill, asset note, or sample script by URI.

## Skill resources

Bundled skills are exposed both as MCP **tools** and as MCP **resources**.

The tools are what actually get used. Most clients never fetch a resource on their
own initiative, so a skill that exists only as a resource tends to go unread while
the model guesses at the Allplan API instead. The three tools above make the same
content reachable through the path a model already takes, and the skills index is
inlined into the `execute_python` description so it is visible at the moment the
model reaches for that tool.

The resources remain for clients that do browse them.

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
- `str.format` and `format_map` are blocked, because they perform attribute
  traversal at runtime that the AST walk cannot see. Use f-strings, whose
  attribute access is a real AST node and is checked.
- Only a restricted builtin whitelist is available at runtime
- Code runs under a wall clock budget and is aborted when it overruns
- Captured stdout and returned results are capped

### Budgets

`SandboxLimits` controls the runtime budgets:

| Budget | Default | Purpose |
| --- | --- | --- |
| `timeout_seconds` | 10 | Aborts runaway code |
| `max_stdout_chars` | 64000 | Caps captured stdout |
| `max_result_chars` | 64000 | Caps the returned result |
| `max_result_items` | 5000 | Caps list and dict length |

The timeout is enforced with `sys.settrace`, so it is checked between Python
bytecode lines. A single long running call into a native Allplan API cannot be
interrupted. This stops the common failure - generated code looping forever and
freezing the Allplan UI thread, which runs every bridge request - but it is not
a hard kill.

### Structured errors

Failures come back as data rather than as an HTTP 500 carrying a stack trace, so
the model can correct itself:

```json
{
  "ok": false,
  "stdout": "progress\n",
  "result": null,
  "error": {
    "kind": "runtime_error",
    "type": "ZeroDivisionError",
    "message": "division by zero",
    "lineno": 3,
    "line": "result = a / b",
    "frames": [{"lineno": 3, "name": "<module>", "line": "result = a / b"}]
  },
  "hint": "The code raised ZeroDivisionError at line 3."
}
```

`kind` is one of `validation_error`, `syntax_error`, `runtime_error`, or
`timeout`. Line numbers refer to the submitted code; bridge internals are
stripped from the traceback.

## Bridge authentication

The bridge listens on loopback, but loopback alone is not a trust boundary. Any
other process on the machine could reach it, and so could any web page the user
visits, since a browser can POST to `127.0.0.1` without a CORS preflight if the
content type is simple.

Four checks now guard every request:

| Check | Blocks |
| --- | --- |
| `Host` must be loopback | DNS rebinding |
| `Origin` must be absent | Any request originating from a web page |
| `Content-Type` must be `application/json` | Simple-request POSTs that skip preflight |
| `X-Allplan-Token` must match | Other local processes |

`StartPythonHost` mints a random token each time it starts and writes it to:

```text
%LOCALAPPDATA%\AllplanMcpBridge\bridge-token.json
```

The MCP server reads the same file, so a local `uv run allplan-mcp` needs no
configuration. The token is removed when the PythonPart stops.

Overrides:

```bash
ALLPLAN_HOST_TOKEN=<token>        # supply the token directly
ALLPLAN_HOST_TOKEN_FILE=<path>    # read it from somewhere else
```

Restart the PythonPart if the MCP server reports a rejected token; that mints a
fresh one.

Do not expose `execute_python` through ngrok or a shared agent setup. The token
raises the bar against local processes and browsers, it does not make the bridge
safe to publish.

## Development

```bash
uv sync --all-groups
uv run pytest
uv run ruff check .
uv run mypy
```

The test suite runs on macOS and Linux without Allplan. `tests/conftest.py`
stubs the `NemAll_Python_*` modules, and the sandbox execution path is kept in
`sandbox/runtime.py`, which imports nothing from Allplan. `sandbox/executor.py`
is the only piece that touches the Allplan API, and it just supplies the globals.
