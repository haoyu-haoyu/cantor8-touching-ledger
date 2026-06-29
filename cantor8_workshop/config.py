from __future__ import annotations

from dataclasses import dataclass
from os import environ
from typing import Mapping

from .errors import WorkshopError


@dataclass(frozen=True)
class Settings:
    client_id: str
    client_secret: str
    idp_base_url: str = "https://auth.dev.digik.cantor8.tech"
    validator_admin_api: str = "https://api.validator.dev.digik.cantor8.tech/api/validator"
    ledger_api: str = "https://api.validator.dev.digik.cantor8.tech/api/ledger"
    request_timeout: float = 30.0

    @property
    def token_url(self) -> str:
        return f"{self.idp_base_url.rstrip('/')}/realms/master/protocol/openid-connect/token"

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "Settings":
        env = environ if env is None else env
        client_id = env.get("CANTON_CLIENT_ID", "").strip()
        client_secret = env.get("CANTON_CLIENT_SECRET", "").strip()
        if not client_id or not client_secret:
            raise WorkshopError(
                "CANTON_CLIENT_ID and CANTON_CLIENT_SECRET must be set. "
                "For the Cantor8 workshop credentials, use the values supplied by the organizers."
            )

        return cls(
            client_id=client_id,
            client_secret=client_secret,
            idp_base_url=env.get("CANTON_IDP_BASE_URL", cls.idp_base_url).rstrip("/"),
            validator_admin_api=env.get(
                "CANTON_VALIDATOR_ADMIN_API", cls.validator_admin_api
            ).rstrip("/"),
            ledger_api=env.get("CANTON_LEDGER_API", cls.ledger_api).rstrip("/"),
            request_timeout=float(env.get("CANTON_REQUEST_TIMEOUT", "30")),
        )

