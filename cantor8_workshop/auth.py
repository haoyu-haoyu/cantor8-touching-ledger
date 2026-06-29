from __future__ import annotations

import time
from collections.abc import Callable

import httpx

from .config import Settings
from .errors import WorkshopError


class TokenManager:
    def __init__(
        self,
        settings: Settings,
        client: httpx.Client | None = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._settings = settings
        self._client = client or httpx.Client(timeout=settings.request_timeout)
        self._clock = clock
        self._access_token: str | None = None
        self._expires_at = 0.0

    def get_token(self) -> str:
        if self._access_token and self._clock() < self._expires_at - 60:
            return self._access_token

        response = self._client.post(
            self._settings.token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": self._settings.client_id,
                "client_secret": self._settings.client_secret,
            },
        )
        if response.status_code >= 400:
            raise WorkshopError(
                f"Token request failed with HTTP {response.status_code}: {response.text}"
            )

        body = response.json()
        try:
            token = body["access_token"]
        except KeyError as exc:
            raise WorkshopError(f"Token response did not include access_token: {body}") from exc

        expires_in = int(body.get("expires_in", 600))
        self._access_token = token
        self._expires_at = self._clock() + expires_in
        return token

