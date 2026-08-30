"""End to end check over a real socket.

StartPythonHost.py cannot be imported here - it pulls in clr and System, which
only exist inside Allplan on Windows. This module stands up an equivalent
handler from the same pieces, so the seam between the client, the security
policy, and the sandbox runtime is exercised for real: header names, content
type, token comparison, status codes, and structured error passthrough.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from PythonHost.sandbox.limits import SandboxLimits
from PythonHost.sandbox.runtime import SandboxRuntime
from PythonHost.security import BridgeAuthError, BridgeSecurityPolicy

from allplan_mcp.allplan_client import AllplanAuthError, AllplanHostClient

TOKEN = "integration-token"


class BridgeHandler(BaseHTTPRequestHandler):
    policy = BridgeSecurityPolicy(token=TOKEN)
    # Short budget so the timeout case does not stall the suite.
    runtime = SandboxRuntime(limits=SandboxLimits(timeout_seconds=0.5))

    def send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        try:
            self.policy.authorize(self.headers)
        except BridgeAuthError as error:
            self.send_json(error.status, {"ok": False, "error": str(error)})
            return

        length = int(self.headers.get("Content-Length") or 0)
        request = json.loads(self.rfile.read(length)) if length else {}
        self.send_json(200, self.runtime.execute(request, {"AllplanGeo": object()}))

    def log_message(self, format: str, *args: object) -> None:
        return


@pytest.fixture(scope="module")
def bridge_url() -> Iterator[str]:
    server = HTTPServer(("127.0.0.1", 0), BridgeHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()


def test_authenticated_round_trip(bridge_url: str) -> None:
    client = AllplanHostClient(bridge_url, token=TOKEN)
    response = client.post("/execute-python", {"code": "result = 2 + 2"})

    assert response["ok"] is True
    assert response["result"] == 4


def test_result_expression_round_trip(bridge_url: str) -> None:
    client = AllplanHostClient(bridge_url, token=TOKEN)
    response = client.post(
        "/execute-python",
        {"code": "value = 21", "result_expression": "value * 2"},
    )

    assert response["result"] == 42


def test_a_wrong_token_is_refused(bridge_url: str) -> None:
    client = AllplanHostClient(bridge_url, token="wrong")

    with pytest.raises(AllplanAuthError):
        client.post("/execute-python", {"code": "result = 1"})


def test_sandbox_failures_survive_the_wire(bridge_url: str) -> None:
    client = AllplanHostClient(bridge_url, token=TOKEN)
    response = client.post("/execute-python", {"code": "a = 1\nresult = a / 0"})

    assert response["ok"] is False
    assert response["error"]["kind"] == "runtime_error"
    assert response["error"]["lineno"] == 2


def test_timeout_survives_the_wire(bridge_url: str) -> None:
    client = AllplanHostClient(bridge_url, token=TOKEN)
    response = client.post("/execute-python", {"code": "while True:\n    pass"})

    assert response["ok"] is False
    assert response["error"]["kind"] == "timeout"


def test_a_browser_style_post_is_refused(bridge_url: str) -> None:
    import urllib.error
    import urllib.request

    # What a malicious page can send without tripping a CORS preflight.
    request = urllib.request.Request(
        f"{bridge_url}/execute-python",
        data=b'{"code": "result = 1"}',
        headers={"Content-Type": "text/plain", "Origin": "https://evil.example"},
        method="POST",
    )

    with pytest.raises(urllib.error.HTTPError) as error:
        urllib.request.urlopen(request, timeout=5)

    assert error.value.code == 403
