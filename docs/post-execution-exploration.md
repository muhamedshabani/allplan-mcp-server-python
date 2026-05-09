# POST execution exploration

## Current architecture

The system already executes Allplan actions through HTTP POST calls:

```text
agent -> FastMCP /mcp -> allplan_mcp.server tool -> AllplanHostClient.post(...)
      -> Allplan Python host on 127.0.0.1:5679 -> RequestHandler.handle(...)
```

The Allplan Python host currently exposes these POST paths:

- `/get-allplan-version`
- `/get-all-object-names`
- `/create-box`

Each path is a command handler. For example, the MCP `create_cube(size)` tool
posts to `/create-box` with equal `length`, `width`, and `height`.

## Can we execute code through arbitrary POST?

Technically yes. The Allplan host runs Python inside the Allplan process, so a
POST handler could call `exec`, `eval`, dynamic imports, or dispatch arbitrary
method names.

That should not be exposed as a default endpoint.

Reasons:

- It would become remote code execution inside the Allplan process.
- If the MCP server is later exposed through ngrok, an agent-accessible tool
  could mutate files, projects, models, or the local machine.
- It would be difficult to validate what code is safe before execution.
- Debugging failures inside Allplan would be harder than debugging explicit
  command handlers.

## Recommended pattern

Use explicit POST commands and expose those commands as MCP tools.

Good:

```text
POST /create-box
POST /create-wall
POST /select-elements
POST /export-current-document
```

Avoid:

```text
POST /execute-python
POST /eval
POST /run-anything
```

This keeps the bridge powerful but inspectable. Each command gets typed inputs,
small validation, and a clear return shape.

## Development-only option

If a raw Python execution endpoint is needed for local experiments, keep it out
of the normal MCP tool list and require all of these controls:

- Bind the Allplan host to `127.0.0.1` only.
- Enable it with an explicit environment variable, for example
  `ALLPLAN_MCP_ENABLE_PYTHON_EXEC=1`.
- Require a strong per-session token in the POST body or header.
- Return only JSON-serializable values.
- Disable it before using ngrok or any shared agent.

Even then, prefer using it only as a temporary debugging aid and replace it with
explicit command handlers once the workflow is known.

## Practical next step

For this project, the safer path is to add more bridge commands as needed:

1. Add a POST route in `PythonHostHandler.handle`.
2. Implement a `handle_<command>` method using Allplan APIs.
3. Add a typed MCP tool in `src/allplan_mcp/server.py`.
4. Keep ngrok pointed at the MCP server, not the raw Allplan host.
