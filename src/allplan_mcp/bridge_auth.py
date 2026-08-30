from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Annotated

TOKEN_HEADER = "X-Allplan-Token"
TOKEN_ENV_VAR = "ALLPLAN_HOST_TOKEN"
TOKEN_FILE_ENV_VAR = "ALLPLAN_HOST_TOKEN_FILE"
TOKEN_DIR_NAME = "AllplanMcpBridge"
TOKEN_FILE_NAME = "bridge-token.json"

BridgeToken = Annotated[str, "Shared secret for the local Allplan bridge"]


def token_file_path() -> Path:
    """Resolve the shared token file location

    Mirrors ``PythonHost.security.token_file_path``. The bridge is copied into
    the Allplan PythonPartsScripts folder and cannot import this package, so the
    path rule is intentionally duplicated. Keep both in sync.
    """

    override = os.getenv(TOKEN_FILE_ENV_VAR)
    if override:
        return Path(override)

    local_app_data = os.getenv("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / TOKEN_DIR_NAME / TOKEN_FILE_NAME

    return Path.home() / ".allplan-mcp" / TOKEN_FILE_NAME


def read_token(path: Path | None = None) -> BridgeToken | None:
    """Read the token published by the running StartPythonHost PythonPart"""

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
