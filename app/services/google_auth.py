import json
import time
import urllib.request
from typing import cast
from urllib.error import URLError

from jose import jwk
from jose.jwt import decode, get_unverified_headers


class GoogleAuthService:
    """Verifies Google ID tokens using Google's JWKS endpoint.

    JWKS keys are cached in-memory with a 1-hour TTL to avoid
    fetching Google's public keys on every request.
    """

    JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
    _CACHE_TTL = 3600  # 1 hour

    def __init__(
        self, google_client_id: str, allowed_domain: str
    ) -> None:
        self._google_client_id = google_client_id
        self._allowed_domain = allowed_domain
        self._jwks_cache: dict[str, object] | None = None
        self._cache_loaded_at: float | None = None

    def _fetch_jwks(self) -> dict[str, object]:
        with urllib.request.urlopen(self.JWKS_URL) as resp:
            return cast(
                "dict[str, object]", json.loads(resp.read().decode())
            )

    def _get_jwks(self) -> dict[str, object]:
        now = time.time()
        if (
            self._jwks_cache is not None
            and self._cache_loaded_at is not None
            and (now - self._cache_loaded_at) < self._CACHE_TTL
        ):
            return self._jwks_cache
        try:
            self._jwks_cache = self._fetch_jwks()
            self._cache_loaded_at = now
        except URLError:
            if self._jwks_cache is not None:
                return self._jwks_cache
            raise
        return self._jwks_cache

    def verify_id_token(self, id_token: str) -> dict[str, object]:
        headers = get_unverified_headers(id_token)
        kid = headers.get("kid")
        if not kid:
            raise ValueError("Missing kid in token header")

        jwks = self._get_jwks()
        keys = cast("list[dict[str, object]]", jwks.get("keys", []))
        key_data = None
        for k in keys:
            if k.get("kid") == kid:
                key_data = k
                break
        if key_data is None:
            raise ValueError("No matching key found in JWKS")

        key = jwk.construct(key_data)
        payload = cast(
            "dict[str, object]",
            decode(
                id_token,
                key,
                algorithms=["RS256"],
                audience=self._google_client_id,
                issuer=[
                    "https://accounts.google.com",
                    "accounts.google.com",
                ],
            ),
        )

        if not payload.get("email_verified"):
            raise ValueError("Google email not verified")

        if self._allowed_domain:
            email = cast("str | None", payload.get("email"))
            if not email or not email.endswith(
                f"@{self._allowed_domain}"
            ):
                raise ValueError(
                    f"Email domain not allowed: {email}"
                )

        return payload
