from datetime import datetime

from app.repositories.token_repository import TokenRepository


class MemoryTokenRepository(TokenRepository):

    def __init__(self) -> None:
        self._blacklisted: set[str] = set()

    async def blacklist(self, jti: str, expires_at: datetime) -> None:
        self._blacklisted.add(jti)

    async def is_blacklisted(self, jti: str) -> bool:
        return jti in self._blacklisted
