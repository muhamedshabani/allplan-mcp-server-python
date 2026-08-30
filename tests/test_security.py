from __future__ import annotations

from pathlib import Path

import pytest
from PythonHost.security import (
    TOKEN_HEADER,
    BridgeAuthError,
    BridgeSecurityPolicy,
    generate_token,
    hostname_of,
    read_token,
    write_token,
)

TOKEN = "test-token-value"


@pytest.fixture
def policy() -> BridgeSecurityPolicy:
    return BridgeSecurityPolicy(token=TOKEN)


def headers(**overrides: str) -> dict[str, str]:
    base = {
        "Host": "127.0.0.1:5679",
        "Content-Type": "application/json",
        TOKEN_HEADER: TOKEN,
    }
    base.update(overrides)
    return {key: value for key, value in base.items() if value is not None}


def test_accepts_a_well_formed_local_request(policy: BridgeSecurityPolicy) -> None:
    policy.authorize(headers())


def test_accepts_localhost_and_ipv6_loopback(policy: BridgeSecurityPolicy) -> None:
    policy.authorize(headers(Host="localhost:5679"))
    policy.authorize(headers(Host="[::1]:5679"))


class TestDnsRebinding:
    def test_rejects_a_non_loopback_host_header(
        self, policy: BridgeSecurityPolicy
    ) -> None:
        # A rebound DNS name resolves to 127.0.0.1 but still sends its own
        # hostname here, which is what makes this check work.
        with pytest.raises(BridgeAuthError) as error:
            policy.authorize(headers(Host="attacker.example.com:5679"))

        assert error.value.status == 403

    def test_rejects_a_missing_host_header(self, policy: BridgeSecurityPolicy) -> None:
        supplied = headers()
        del supplied["Host"]

        with pytest.raises(BridgeAuthError) as error:
            policy.authorize(supplied)

        assert error.value.status == 400


class TestBrowserRequests:
    def test_rejects_anything_carrying_an_origin(
        self, policy: BridgeSecurityPolicy
    ) -> None:
        with pytest.raises(BridgeAuthError) as error:
            policy.authorize(headers(Origin="https://evil.example"))

        assert error.value.status == 403

    @pytest.mark.parametrize(
        "content_type",
        ["text/plain", "application/x-www-form-urlencoded", "multipart/form-data"],
    )
    def test_rejects_simple_request_content_types(
        self, policy: BridgeSecurityPolicy, content_type: str
    ) -> None:
        # These three are exactly the types a page can POST without a CORS
        # preflight, so refusing them forces the browser to ask permission.
        with pytest.raises(BridgeAuthError) as error:
            policy.authorize(headers(**{"Content-Type": content_type}))

        assert error.value.status == 415

    def test_accepts_json_with_a_charset(self, policy: BridgeSecurityPolicy) -> None:
        policy.authorize(headers(**{"Content-Type": "application/json; charset=utf-8"}))


class TestToken:
    def test_rejects_a_wrong_token(self, policy: BridgeSecurityPolicy) -> None:
        with pytest.raises(BridgeAuthError) as error:
            policy.authorize(headers(**{TOKEN_HEADER: "not-the-token"}))

        assert error.value.status == 401

    def test_rejects_a_missing_token(self, policy: BridgeSecurityPolicy) -> None:
        supplied = headers()
        del supplied[TOKEN_HEADER]

        with pytest.raises(BridgeAuthError):
            policy.authorize(supplied)

    def test_generated_tokens_are_unique_and_long(self) -> None:
        tokens = {generate_token() for _ in range(50)}

        assert len(tokens) == 50
        assert all(len(token) >= 32 for token in tokens)


class TestTokenFile:
    def test_round_trips(self, token_file: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ALLPLAN_HOST_TOKEN", raising=False)
        token = generate_token()
        write_token(token, token_file)

        assert read_token(token_file) == token

    def test_missing_file_reads_as_none(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("ALLPLAN_HOST_TOKEN", raising=False)

        assert read_token(tmp_path / "absent.json") is None

    def test_corrupt_file_reads_as_none(
        self, token_file: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("ALLPLAN_HOST_TOKEN", raising=False)
        token_file.write_text("not json", encoding="utf-8")

        assert read_token(token_file) is None

    def test_env_var_wins(
        self, token_file: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        write_token("from-file", token_file)
        monkeypatch.setenv("ALLPLAN_HOST_TOKEN", "from-env")

        assert read_token(token_file) == "from-env"


@pytest.mark.parametrize(
    "host,expected",
    [
        ("127.0.0.1:5679", "127.0.0.1"),
        ("127.0.0.1", "127.0.0.1"),
        ("LOCALHOST:5679", "localhost"),
        ("[::1]:5679", "[::1]"),
        ("evil.example:80", "evil.example"),
    ],
)
def test_hostname_parsing(host: str, expected: str) -> None:
    assert hostname_of(host) == expected
