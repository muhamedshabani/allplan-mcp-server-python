from __future__ import annotations

import importlib
from typing import Annotated, Any

import NemAll_Python_IFW_Input as AllplanIFW

from .limits import SandboxLimits
from .runtime import SandboxRuntime
from .validator import SandboxValidator

SandboxRequest = Annotated[dict[str, Any], "Incoming execute_python request"]
SandboxResult = Annotated[dict[str, Any], "JSON-safe execution result"]

# The Allplan modules exposed to sandbox code, as {module: (alias, ...)}.
#
# Sandbox code cannot import, so a module that is not named here is simply
# unreachable. ArchElements and Reinforcement were both missing: without the
# first there is no real Wand - only a generic ModelElement3D cuboid, which has
# no Wandschicht and so can never carry a Schraffur - and without the second the
# bundled rebar skill documents an API the sandbox cannot call.
#
# NemAll_Python_Utility is deliberately absent. It carries ShowMessageBox, and a
# modal dialog opened from sandbox code would block the UI thread the bridge
# marshals every request onto, deadlocking the host until someone clicks it.
API_MODULES: dict[str, tuple[str, ...]] = {
    "NemAll_Python_Geometry": ("AllplanGeo",),
    "NemAll_Python_IFW_Input": ("AllplanIFW",),
    "NemAll_Python_AllplanSettings": ("AllplanSettings",),
    "NemAll_Python_BaseElements": ("AllplanBaseElements", "AllplanBaseEle"),
    "NemAll_Python_BasisElements": ("AllplanBasisElements", "AllplanBasisEle"),
    "NemAll_Python_ArchElements": ("AllplanArchElements", "AllplanArchEle"),
    "NemAll_Python_Reinforcement": ("AllplanReinf",),
    "NemAll_Python_IFW_ElementAdapter": ("AllplanEleAdapter",),
}


def load_api_modules() -> tuple[dict[str, Any], list[str]]:
    """Import the exposed Allplan modules, skipping any this version lacks

    Returns the alias-to-module scope and the names that could not be imported.
    A missing module must not take the bridge down: older Allplan versions do
    not ship every one of these, and losing rebar support is better than losing
    the host.
    """

    scope: dict[str, Any] = {}
    missing: list[str] = []

    for module_name, aliases in API_MODULES.items():
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            missing.append(module_name)
            continue
        for alias in aliases:
            scope[alias] = module

    return scope, missing


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
        self.modules, self.missing_modules = load_api_modules()

    def api_scope(self) -> dict[str, Any]:
        """Build the Allplan globals exposed to sandbox code"""

        scope: dict[str, Any] = {"coord_input": self.coord_input}
        scope.update(self.modules)
        return scope

    def execute(self, request: SandboxRequest) -> SandboxResult:
        return self.runtime.execute(request, self.api_scope())
