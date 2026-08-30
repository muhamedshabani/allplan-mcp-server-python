from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
BRIDGE_ROOT = REPO_ROOT / "python_host" / "PythonPartsScripts"

# The bridge lives in a folder that Allplan puts on sys.path at runtime.
if str(BRIDGE_ROOT) not in sys.path:
    sys.path.insert(0, str(BRIDGE_ROOT))


# executor.py imports the Allplan API, which only exists inside Allplan on
# Windows. Stubbing the modules lets the whole bridge import here. Everything
# under test is deliberately independent of what these modules actually do.
ALLPLAN_MODULES = (
    "NemAll_Python_AllplanSettings",
    "NemAll_Python_BaseElements",
    "NemAll_Python_BasisElements",
    "NemAll_Python_Geometry",
    "NemAll_Python_IFW_Input",
)

for module_name in ALLPLAN_MODULES:
    sys.modules.setdefault(module_name, types.ModuleType(module_name))


@pytest.fixture
def runtime():
    from PythonHost.sandbox.runtime import SandboxRuntime

    return SandboxRuntime()


@pytest.fixture
def token_file(tmp_path: Path) -> Path:
    return tmp_path / "bridge-token.json"
