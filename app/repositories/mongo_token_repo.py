from datetime import UTC, datetime

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.repositories.token_repository import TokenRepository


class MongoTokenRepository(TokenRepository):

    def __init__(self, db: AsyncIOMotorDatabase[dict[str, object]]) -> None:
        self._collection = db["blacklisted_tokens"]

    async def blacklist(self, jti: str, expires_at: datetime) -> None:
        await self._collection.update_one(
            {"jti": jti},
            {"$set": {"jti": jti, "expires_at": expires_at}},
            upsert=True,
        )

    async def is_blacklisted(self, jti: str) -> bool:
        doc = await self._collection.find_one(
            {"jti": jti, "expires_at": {"$gt": datetime.now(UTC)}}
        )
        return doc is not None
