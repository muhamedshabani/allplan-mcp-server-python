from __future__ import annotations

from typing import Annotated, Any

import NemAll_Python_AllplanSettings as AllplanSettings
import NemAll_Python_BaseElements as AllplanBaseEle
import NemAll_Python_BaseElements as AllplanBaseElements
import NemAll_Python_BasisElements as AllplanBasisElements
import NemAll_Python_Geometry as AllplanGeo
import NemAll_Python_IFW_Input as AllplanIFW

from .limits import SandboxLimits
from .runtime import SandboxRuntime
from .validator import SandboxValidator

SandboxRequest = Annotated[dict[str, Any], "Incoming execute_python request"]
SandboxResult = Annotated[dict[str, Any], "JSON-safe execution result"]


class SandboxExecutor:
    """Run sandbox code with the Allplan API in scope

    All validation, budgeting, and error shaping lives in SandboxRuntime, which
    has no Allplan dependency. This class only supplies the Allplan globals.
    """

    def __init__(
        self,
        coord_input: AllplanIFW.CoordinateInput,
        validator: SandboxValidator | None = None,
        limits: SandboxLimits | None = None,
    ) -> None:
        self.coord_input = coord_input
        self.runtime = SandboxRuntime(validator=validator, limits=limits)

    def api_scope(self) -> dict[str, Any]:
        """Build the Allplan globals exposed to sandbox code"""

        return {
            "coord_input": self.coord_input,
            "AllplanGeo": AllplanGeo,
            "AllplanIFW": AllplanIFW,
            "AllplanSettings": AllplanSettings,
            "AllplanBaseElements": AllplanBaseElements,
            "AllplanBasisElements": AllplanBasisElements,
            "AllplanBaseEle": AllplanBaseEle,
        }

    def execute(self, request: SandboxRequest) -> SandboxResult:
        return self.runtime.execute(request, self.api_scope())
