from app.models.product import now_utc
from app.models.user import User
from app.repositories.user_repository import UserRepository


class MemoryUserRepository(UserRepository):

    def __init__(self) -> None:
        self._store: dict[str, User] = {}

    async def get_by_email(self, email: str) -> User | None:
        return self._store.get(email)

    async def get_by_reset_token(self, token: str) -> User | None:
        for user in self._store.values():
            if user.reset_token == token:
                return user
        return None

    async def get_by_verification_token(
        self, token: str
    ) -> User | None:
        for user in self._store.values():
            if user.verification_token == token:
                return user
        return None

    async def get_by_google_sub(
        self, google_sub: str
    ) -> User | None:
        for user in self._store.values():
            if user.google_sub == google_sub:
                return user
        return None

    async def create(self, user: User) -> User:
        self._store[user.email] = user.model_copy(deep=True)
        return self._store[user.email]

    async def update(
        self, email: str, data: dict[str, object]
    ) -> User | None:
        existing = self._store.get(email)
        if existing is None:
            return None
        for key, value in data.items():
            if hasattr(existing, key):
                setattr(existing, key, value)
        existing.updated_at = now_utc()
        return existing.model_copy(deep=True)

    async def delete(self, email: str) -> bool:
        if email in self._store:
            del self._store[email]
            return True
        return False
