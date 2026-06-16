from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import TypeAdapter

from app.models.product import ProductConfig, now_utc
from app.repositories.product_repository import ProductRepository

_product_adapter = TypeAdapter(ProductConfig)


class MongoProductRepository(ProductRepository):

    def __init__(self, db: AsyncIOMotorDatabase[dict[str, object]]) -> None:
        self._collection = db["products"]

    async def create(self, product: ProductConfig) -> ProductConfig:
        now = now_utc()
        doc = product.model_dump()
        doc["created_at"] = now
        doc["updated_at"] = now
        await self._collection.insert_one(doc)
        return _product_adapter.validate_python(doc)

    async def get(self, product_id: str) -> ProductConfig | None:
        doc = await self._collection.find_one({"product_id": product_id})
        if doc is None:
            return None
        return _product_adapter.validate_python(doc)

    async def list(self) -> list[ProductConfig]:
        docs = await self._collection.find().to_list(length=None)
        return [_product_adapter.validate_python(d) for d in docs]

    async def update(
        self, product_id: str, data: dict[str, object]
    ) -> ProductConfig | None:
        data["updated_at"] = now_utc()
        result = await self._collection.find_one_and_update(
            {"product_id": product_id},
            {"$set": data},
            return_document=True,
        )
        if result is None:
            return None
        return _product_adapter.validate_python(result)

    async def delete(self, product_id: str) -> bool:
        result = await self._collection.delete_one(
            {"product_id": product_id}
        )
        return result.deleted_count > 0
