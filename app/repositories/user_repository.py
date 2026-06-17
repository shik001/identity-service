from abc import ABC, abstractmethod

from app.models.user import User


class UserRepository(ABC):

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    async def create(self, user: User) -> User: ...

    @abstractmethod
    async def get_by_reset_token(self, token: str) -> User | None: ...

    @abstractmethod
    async def get_by_verification_token(
        self, token: str
    ) -> User | None: ...

    @abstractmethod
    async def get_by_google_sub(
        self, google_sub: str
    ) -> User | None: ...

    @abstractmethod
    async def update(
        self, email: str, data: dict[str, object]
    ) -> User | None: ...

    @abstractmethod
    async def delete(self, email: str) -> bool: ...
