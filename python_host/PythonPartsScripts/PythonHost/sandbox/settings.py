from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Annotated


SandboxFlag = Annotated[bool, "Sandbox feature flag"]


@dataclass(frozen=True)
class SandboxSettings:
    """Runtime settings for the Allplan sandbox."""

    exec_enabled: SandboxFlag

    @classmethod
    def from_environment(cls) -> "SandboxSettings":
        return cls(exec_enabled=os.getenv("ALLPLAN_MCP_ENABLE_PYTHON_EXEC", "0") == "1")
