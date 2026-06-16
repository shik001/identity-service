from abc import ABC, abstractmethod
from datetime import datetime


class TokenRepository(ABC):

    @abstractmethod
    async def blacklist(self, jti: str, expires_at: datetime) -> None: ...

    @abstractmethod
    async def is_blacklisted(self, jti: str) -> bool: ...
