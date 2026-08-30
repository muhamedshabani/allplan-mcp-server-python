from __future__ import annotations

import json
from pathlib import Path
from urllib.error import HTTPError

import pytest

from allplan_mcp import allplan_client as client_module
from allplan_mcp.allplan_client import AllplanAuthError, AllplanHostClient, AllplanHostError
from allplan_mcp.bridge_auth import TOKEN_HEADER


class FakeResponse:
    def __init__(self, body: str) -> None:
        self.body = body

    def read(self) -> bytes:
        return self.body.encode("utf-8")

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None


@pytest.fixture
def captured(monkeypatch: pytest.MonkeyPatch) -> list:
    calls: list = []

    def fake_urlopen(request, timeout=None):
        calls.append(request)
        return FakeResponse(json.dumps({"ok": True}))

    monkeypatch.setattr(client_module, "urlopen", fake_urlopen)
    return calls


def test_sends_the_token_header(captured: list) -> None:
    client = AllplanHostClient("http://127.0.0.1:5679", token="abc123")
    client.post("/get-allplan-version")

    request = captured[0]
    assert request.get_header(TOKEN_HEADER.capitalize()) == "abc123"
    assert request.get_header("Content-type") == "application/json"


def test_refuses_to_call_without_a_token(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("ALLPLAN_HOST_TOKEN", raising=False)
    monkeypatch.setenv("ALLPLAN_HOST_TOKEN_FILE", str(tmp_path / "absent.json"))

    client = AllplanHostClient("http://127.0.0.1:5679")

    with pytest.raises(AllplanAuthError, match="StartPythonHost"):
        client.post("/get-allplan-version")


@pytest.mark.parametrize("status", [401, 403])
def test_auth_failures_suggest_restarting_the_pythonpart(
    monkeypatch: pytest.MonkeyPatch, status: int
) -> None:
    def fake_urlopen(request, timeout=None):
        raise HTTPError(
            url="http://127.0.0.1:5679", code=status, msg="denied", hdrs=None, fp=None
        )

    monkeypatch.setattr(client_module, "urlopen", fake_urlopen)
    client = AllplanHostClient("http://127.0.0.1:5679", token="abc")

    with pytest.raises(AllplanAuthError, match="fresh token"):
        client.post("/execute-python")


def test_other_http_errors_stay_generic(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(request, timeout=None):
        raise HTTPError(
            url="http://127.0.0.1:5679", code=500, msg="boom", hdrs=None, fp=None
        )

    monkeypatch.setattr(client_module, "urlopen", fake_urlopen)
    client = AllplanHostClient("http://127.0.0.1:5679", token="abc")

    with pytest.raises(AllplanHostError) as error:
        client.post("/execute-python")

    assert not isinstance(error.value, AllplanAuthError)
