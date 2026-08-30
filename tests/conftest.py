from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
BRIDGE_ROOT = REPO_ROOT / "python_host" / "PythonPartsScripts"

# The bridge lives in a folder that Allplan puts on sys.path at runtime.
if str(BRIDGE_ROOT) not in sys.path:
    sys.path.insert(0, str(BRIDGE_ROOT))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))


# The Allplan API only exists inside Allplan on Windows. fake_allplan installs
# behavioural stand-ins so the bridge imports here and its wiring - undo
# grouping, UUID reporting, viewport capture - is genuinely exercised.
import fake_allplan  # noqa: E402

fake_allplan.install()


@pytest.fixture
def runtime():
    from PythonHost.sandbox.runtime import SandboxRuntime

    return SandboxRuntime()


@pytest.fixture
def token_file(tmp_path: Path) -> Path:
    return tmp_path / "bridge-token.json"


@pytest.fixture
def allplan():
    """Reset the fake Allplan API and hand back its recorder"""

    fake_allplan.recorder.reset()
    return fake_allplan


@pytest.fixture
def handler(allplan):
    """Build a RequestHandler wired to the fake Allplan API"""

    from PythonHost.PythonHostHandler import RequestHandler

    return RequestHandler(allplan.FakeCoordinateInput())
