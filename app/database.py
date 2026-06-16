from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import Settings


async def create_mongo_client(
    settings: Settings,
) -> tuple[
    AsyncIOMotorClient[dict[str, object]],
    AsyncIOMotorDatabase[dict[str, object]],
]:
    client: AsyncIOMotorClient[dict[str, object]] = AsyncIOMotorClient(
        settings.config_db_uri
    )
    db: AsyncIOMotorDatabase[dict[str, object]] = client[
        settings.config_db_name
    ]
    return client, db
