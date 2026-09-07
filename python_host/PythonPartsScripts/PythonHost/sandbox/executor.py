from __future__ import annotations

import importlib
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
ScopeName = Annotated[str, "Name a sandbox script sees the module under"]

# The architecture modules. Without ArchElements a script can only make a
# generic ModelElement3D solid, which has no wall tier and so can never
# carry a Schraffur; that was the observed bug behind every "geometry
# arrived unhatched" report. Both aliases are offered because Nemetschek's
# own examples use both. ElementAdapter is what an opening needs to name
# its host wall and what an amendment needs to find an element again;
# Reinforcement is the sibling every wall detail eventually asks for.
#
# They are loaded per host rather than at import time so a host on a
# release that lacks one still starts, and reports what it lacks instead
# of failing to load the PythonPart at all.
OPTIONAL_MODULES: dict[ScopeName, str] = {
    "AllplanArchElements": "NemAll_Python_ArchElements",
    "AllplanArchEle": "NemAll_Python_ArchElements",
    "AllplanElementAdapter": "NemAll_Python_IFW_ElementAdapter",
    "AllplanReinf": "NemAll_Python_Reinforcement",
}


def load_optional_modules() -> tuple[dict[ScopeName, Any], dict[ScopeName, str]]:
    """Import the optional modules that are present

    Returns (present, absent): the loaded modules by scope name, and for each
    missing one the import error text, so a client can tell "this host cannot
    build a wall" from "this host is down".
    """

    present: dict[ScopeName, Any] = {}
    absent: dict[ScopeName, str] = {}
    for alias, module_name in OPTIONAL_MODULES.items():
        try:
            present[alias] = importlib.import_module(module_name)
        except ImportError as error:
            absent[alias] = f"{module_name}: {error}"
    return present, absent


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
        self.optional_modules, self.absent_modules = load_optional_modules()

    def api_scope(self) -> dict[str, Any]:
        """Build the Allplan globals exposed to sandbox code"""

        scope: dict[str, Any] = {
            "coord_input": self.coord_input,
            "AllplanGeo": AllplanGeo,
            "AllplanIFW": AllplanIFW,
            "AllplanSettings": AllplanSettings,
            "AllplanBaseElements": AllplanBaseElements,
            "AllplanBasisElements": AllplanBasisElements,
            "AllplanBaseEle": AllplanBaseEle,
        }
        scope.update(self.optional_modules)
        return scope

    def scope_names(self) -> list[ScopeName]:
        """The names a script may use, for the host to report"""

        return sorted(self.api_scope())

    def execute(self, request: SandboxRequest) -> SandboxResult:
        return self.runtime.execute(request, self.api_scope())
