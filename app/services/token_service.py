from datetime import UTC, datetime, timedelta
from uuid import uuid4

from jose import JWTError, jwt

from app.config import Settings
from app.models.token import (
    AccessTokenPayload,
    RefreshTokenPayload,
    TokenPair,
)


class TokenService:

    def __init__(self, settings: Settings) -> None:
        self._secret = settings.jwt_secret
        self._algorithm = settings.jwt_algorithm
        self._access_expire = timedelta(
            minutes=settings.access_token_expire_minutes
        )
        self._refresh_expire = timedelta(
            days=settings.refresh_token_expire_days
        )

    def create_access_token(self, email: str, product_id: str) -> str:
        now = datetime.now(UTC)
        payload = AccessTokenPayload(
            sub=email,
            product_id=product_id,
            exp=now + self._access_expire,
            iat=now,
        )
        return str(
            jwt.encode(
                payload.model_dump(),
                self._secret,
                algorithm=self._algorithm,
            )
        )

    def create_refresh_token(self, email: str, product_id: str) -> str:
        now = datetime.now(UTC)
        payload = RefreshTokenPayload(
            sub=email,
            product_id=product_id,
            exp=now + self._refresh_expire,
            iat=now,
            jti=uuid4().hex,
        )
        return str(
            jwt.encode(
                payload.model_dump(),
                self._secret,
                algorithm=self._algorithm,
            )
        )

    def decode_token(
        self, token: str
    ) -> AccessTokenPayload | RefreshTokenPayload:
        try:
            data: dict[str, object] = jwt.decode(
                token, self._secret, algorithms=[self._algorithm]
            )
        except JWTError:
            raise ValueError("Invalid or expired token")

        token_type = data.get("type")
        if token_type == "access":
            return AccessTokenPayload.model_validate(data)
        if token_type == "refresh":
            return RefreshTokenPayload.model_validate(data)
        raise ValueError(f"Unknown token type: {token_type}")

    def create_token_pair(
        self, email: str, product_id: str
    ) -> TokenPair:
        return TokenPair(
            access_token=self.create_access_token(email, product_id),
            refresh_token=self.create_refresh_token(email, product_id),
        )
