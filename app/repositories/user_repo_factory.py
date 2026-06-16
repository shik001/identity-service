from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.models.product import ProductConfig
from app.repositories.mongo_token_repo import MongoTokenRepository
from app.repositories.mongo_user_repo import MongoUserRepository


class UserRepositoryFactory:

    def __init__(self) -> None:
        self._clients: dict[str, AsyncIOMotorClient[dict[str, object]]] = {}

    def _get_db(
        self, product: ProductConfig
    ) -> AsyncIOMotorDatabase[dict[str, object]]:
        uri = product.mongo_uri
        if uri not in self._clients:
            self._clients[uri] = AsyncIOMotorClient(uri)
        return self._clients[uri][product.db_name]

    def get_user_repository(
        self, product: ProductConfig
    ) -> MongoUserRepository:
        return MongoUserRepository(self._get_db(product))

    def get_token_repository(
        self, product: ProductConfig
    ) -> MongoTokenRepository:
        return MongoTokenRepository(self._get_db(product))

    async def close_all(self) -> None:
        for client in self._clients.values():
            client.close()
        self._clients.clear()
