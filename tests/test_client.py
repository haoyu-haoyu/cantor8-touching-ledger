import httpx
import pytest

from cantor8_workshop.client import ApiClient
from cantor8_workshop.config import Settings
from cantor8_workshop.errors import WorkshopError


class StaticToken:
    def get_token(self) -> str:
        return "token-1"


def test_api_client_adds_bearer_auth_and_returns_json():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer token-1"
        assert request.url.path == "/api/ledger/v2/version"
        return httpx.Response(200, json={"version": "3.5.5"})

    client = ApiClient(
        Settings(client_id="client", client_secret="secret"),
        StaticToken(),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    assert client.ledger("GET", "/v2/version") == {"version": "3.5.5"}


def test_api_client_formats_http_errors_with_response_body():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"code": "BAD_REQUEST", "cause": "bad payload"})

    client = ApiClient(
        Settings(client_id="client", client_secret="secret"),
        StaticToken(),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(WorkshopError, match="HTTP 400.*BAD_REQUEST.*bad payload"):
        client.ledger("POST", "/v2/parties", json={"partyIdHint": ""})

