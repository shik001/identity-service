from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import TypeAdapter

from app.models.product import now_utc
from app.models.user import User
from app.repositories.user_repository import UserRepository

_user_adapter = TypeAdapter(User)


class MongoUserRepository(UserRepository):

    def __init__(self, db: AsyncIOMotorDatabase[dict[str, object]]) -> None:
        self._collection = db["users"]

    async def get_by_email(self, email: str) -> User | None:
        doc = await self._collection.find_one({"email": email})
        if doc is None:
            return None
        return _user_adapter.validate_python(doc)

    async def get_by_reset_token(self, token: str) -> User | None:
        doc = await self._collection.find_one({"reset_token": token})
        if doc is None:
            return None
        return _user_adapter.validate_python(doc)

    async def get_by_verification_token(
        self, token: str
    ) -> User | None:
        doc = await self._collection.find_one(
            {"verification_token": token}
        )
        if doc is None:
            return None
        return _user_adapter.validate_python(doc)

    async def create(self, user: User) -> User:
        doc = user.model_dump()
        await self._collection.insert_one(doc)
        return _user_adapter.validate_python(doc)

    async def update(
        self, email: str, data: dict[str, object]
    ) -> User | None:
        data["updated_at"] = now_utc()
        result = await self._collection.find_one_and_update(
            {"email": email},
            {"$set": data},
            return_document=True,
        )
        if result is None:
            return None
        return _user_adapter.validate_python(result)

    async def delete(self, email: str) -> bool:
        result = await self._collection.delete_one({"email": email})
        return result.deleted_count > 0
