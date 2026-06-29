from __future__ import annotations

import json
from typing import Any, Protocol

import httpx

from .config import Settings
from .errors import WorkshopError


class TokenProvider(Protocol):
    def get_token(self) -> str:
        ...


class ApiClient:
    def __init__(
        self,
        settings: Settings,
        token_provider: TokenProvider,
        client: httpx.Client | None = None,
    ) -> None:
        self._settings = settings
        self._token_provider = token_provider
        self._client = client or httpx.Client(timeout=settings.request_timeout)

    def ledger(self, method: str, path: str, **kwargs: Any) -> Any:
        return self.request(method, self._settings.ledger_api, path, **kwargs)

    def validator(self, method: str, path: str, **kwargs: Any) -> Any:
        return self.request(method, self._settings.validator_admin_api, path, **kwargs)

    def request(self, method: str, base_url: str, path: str, **kwargs: Any) -> Any:
        headers = dict(kwargs.pop("headers", {}) or {})
        headers["Authorization"] = f"Bearer {self._token_provider.get_token()}"
        if "json" in kwargs:
            headers.setdefault("Content-Type", "application/json")

        url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
        response = self._client.request(method, url, headers=headers, **kwargs)
        if response.status_code >= 400:
            raise WorkshopError(self._format_error(response))
        if not response.content:
            return None
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            return response.json()
        return response.text

    @staticmethod
    def _format_error(response: httpx.Response) -> str:
        body = response.text
        try:
            parsed = response.json()
            body = json.dumps(parsed)
        except ValueError:
            pass
        return f"HTTP {response.status_code} from {response.request.method} {response.request.url}: {body}"
