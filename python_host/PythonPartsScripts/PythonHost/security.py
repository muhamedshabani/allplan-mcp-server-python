from __future__ import annotations

import contextlib
import hmac
import json
import os
import secrets
import stat
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, Any

TOKEN_HEADER = "X-Allplan-Token"
TOKEN_ENV_VAR = "ALLPLAN_HOST_TOKEN"
TOKEN_FILE_ENV_VAR = "ALLPLAN_HOST_TOKEN_FILE"
TOKEN_DIR_NAME = "AllplanMcpBridge"
TOKEN_FILE_NAME = "bridge-token.json"

LOOPBACK_HOSTNAMES: frozenset[str] = frozenset({"127.0.0.1", "localhost", "::1", "[::1]"})
JSON_CONTENT_TYPE = "application/json"

BridgeToken = Annotated[str, "Shared secret for the local Allplan bridge"]


class BridgeAuthError(Exception):
    """Raised when a bridge request fails authorization

    ``status`` is the HTTP status the bridge should return.
    """

    def __init__(self, message: str, status: int = 403) -> None:
        super().__init__(message)
        self.status = status


def token_file_path() -> Path:
    """Resolve the shared token file location

    Mirrored by ``allplan_mcp.bridge_auth``. The two sides cannot import each
    other: this module is copied into the Allplan PythonPartsScripts folder,
    while the MCP server runs from the installed package. Keep both in sync.
    """

    override = os.getenv(TOKEN_FILE_ENV_VAR)
    if override:
        return Path(override)

    local_app_data = os.getenv("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / TOKEN_DIR_NAME / TOKEN_FILE_NAME

    return Path.home() / ".allplan-mcp" / TOKEN_FILE_NAME


def generate_token() -> BridgeToken:
    """Create a fresh bridge token"""

    return secrets.token_urlsafe(32)


def write_token(token: BridgeToken, path: Path | None = None) -> Path:
    """Persist the bridge token for local MCP clients to read"""

    target = path or token_file_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({"token": token}), encoding="utf-8")

    # Best effort. Windows ACLs are not expressible through chmod.
    with contextlib.suppress(OSError):
        target.chmod(stat.S_IRUSR | stat.S_IWUSR)

    return target


def read_token(path: Path | None = None) -> BridgeToken | None:
    """Read the bridge token written by the running PythonPart"""

    env_token = os.getenv(TOKEN_ENV_VAR)
    if env_token:
        return env_token

    target = path or token_file_path()
    try:
        raw = target.read_text(encoding="utf-8")
    except OSError:
        return None

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None

    token = data.get("token") if isinstance(data, dict) else None
    return token if isinstance(token, str) and token else None


def hostname_of(host_header: str) -> str:
    """Strip the port from a Host header value"""

    value = host_header.strip()
    if value.startswith("["):
        closing = value.find("]")
        if closing != -1:
            return value[: closing + 1].lower()
        return value.lower()

    return value.rsplit(":", 1)[0].lower() if ":" in value else value.lower()


@dataclass(frozen=True)
class BridgeSecurityPolicy:
    """Authorize inbound bridge requests

    Three independent checks, each closing a different hole:

    - ``Host`` must be loopback, which defeats DNS rebinding. A rebound name
      resolving to 127.0.0.1 still carries the attacker's hostname here.
    - ``Origin`` must be absent. Browsers always attach it cross-origin, so any
      request carrying one came from a page rather than a local agent.
    - ``Content-Type`` must be JSON, which forces a CORS preflight and so blocks
      the simple-request form and text/plain POSTs a page could otherwise send.

    The token is then the actual authentication, protecting against other local
    processes rather than against the browser.
    """

    token: BridgeToken
    allowed_hostnames: frozenset[str] = field(default=LOOPBACK_HOSTNAMES)
    require_json_content_type: bool = True
    reject_browser_origin: bool = True

    def authorize(self, headers: Mapping[str, Any]) -> None:
        self.check_host(headers)
        self.check_origin(headers)
        self.check_content_type(headers)
        self.check_token(headers)

    def header(self, headers: Mapping[str, Any], name: str) -> str | None:
        value = headers.get(name)
        if value is None and hasattr(headers, "get"):
            value = headers.get(name.lower())
        return value if isinstance(value, str) else None

    def check_host(self, headers: Mapping[str, Any]) -> None:
        host = self.header(headers, "Host")
        if not host:
            raise BridgeAuthError("Missing Host header.", status=400)

        if hostname_of(host) not in self.allowed_hostnames:
            raise BridgeAuthError(
                f"Host '{host}' is not a loopback address. "
                "The Allplan bridge only serves local clients.",
                status=403,
            )

    def check_origin(self, headers: Mapping[str, Any]) -> None:
        if not self.reject_browser_origin:
            return

        origin = self.header(headers, "Origin")
        if origin:
            raise BridgeAuthError(
                "Requests carrying an Origin header are refused. "
                "The Allplan bridge is not reachable from a web page.",
                status=403,
            )

    def check_content_type(self, headers: Mapping[str, Any]) -> None:
        if not self.require_json_content_type:
            return

        content_type = self.header(headers, "Content-Type") or ""
        if content_type.split(";", 1)[0].strip().lower() != JSON_CONTENT_TYPE:
            raise BridgeAuthError(
                f"Content-Type must be {JSON_CONTENT_TYPE}.",
                status=415,
            )

    def check_token(self, headers: Mapping[str, Any]) -> None:
        supplied = self.header(headers, TOKEN_HEADER) or ""
        if not hmac.compare_digest(supplied, self.token):
            raise BridgeAuthError(
                f"Missing or invalid {TOKEN_HEADER} header.",
                status=401,
            )
