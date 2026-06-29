import time

import httpx
import pytest

from cantor8_workshop.auth import TokenManager
from cantor8_workshop.config import Settings
from cantor8_workshop.errors import WorkshopError


def test_token_request_uses_lowercase_client_secret_and_caches_token():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        assert request.url.path == "/realms/master/protocol/openid-connect/token"
        body = request.content.decode()
        assert "grant_type=client_credentials" in body
        assert "client_id=client" in body
        assert "client_secret=secret" in body
        assert "Client_secret" not in body
        return httpx.Response(200, json={"access_token": "jwt-1", "expires_in": 900})

    manager = TokenManager(
        Settings(client_id="client", client_secret="secret"),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    assert manager.get_token() == "jwt-1"
    assert manager.get_token() == "jwt-1"
    assert len(calls) == 1


def test_token_refreshes_when_expiry_window_has_passed():
    tokens = iter(
        [
            {"access_token": "jwt-1", "expires_in": 120},
            {"access_token": "jwt-2", "expires_in": 120},
        ]
    )
    now = [1_000.0]

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=next(tokens))

    manager = TokenManager(
        Settings(client_id="client", client_secret="secret"),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        clock=lambda: now[0],
    )

    assert manager.get_token() == "jwt-1"
    now[0] = time.time() + 10_000
    assert manager.get_token() == "jwt-2"


def test_missing_credentials_raise_clear_error():
    with pytest.raises(WorkshopError, match="CANTON_CLIENT_ID and CANTON_CLIENT_SECRET"):
        Settings.from_env({})

