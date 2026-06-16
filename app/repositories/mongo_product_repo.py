from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import TypeAdapter

from app.models.product import ProductConfig, now_utc
from app.repositories.product_repository import ProductRepository

_product_adapter = TypeAdapter(ProductConfig)


def _doc_to_product(doc: dict[str, object]) -> ProductConfig:
    doc["id"] = str(doc.pop("_id"))
    return _product_adapter.validate_python(doc)


class MongoProductRepository(ProductRepository):

    def __init__(self, db: AsyncIOMotorDatabase[dict[str, object]]) -> None:
        self._collection = db["products"]

    async def create(self, product: ProductConfig) -> ProductConfig:
        now = now_utc()
        doc = product.model_dump()
        doc.pop("id", None)
        doc["created_at"] = now
        doc["updated_at"] = now
        result = await self._collection.insert_one(doc)
        created_doc = await self._collection.find_one(
            {"_id": result.inserted_id}
        )
        if created_doc is None:
            raise RuntimeError("Failed to read back created product")
        return _doc_to_product(created_doc)

    async def get(self, product_id: str) -> ProductConfig | None:
        from bson import ObjectId

        doc = await self._collection.find_one({"_id": ObjectId(product_id)})
        if doc is None:
            return None
        return _doc_to_product(doc)

    async def list(self) -> list[ProductConfig]:
        docs = await self._collection.find().to_list(length=None)
        return [_doc_to_product(d) for d in docs]

    async def update(
        self, product_id: str, data: dict[str, object]
    ) -> ProductConfig | None:
        from bson import ObjectId

        data["updated_at"] = now_utc()
        result = await self._collection.find_one_and_update(
            {"_id": ObjectId(product_id)},
            {"$set": data},
            return_document=True,
        )
        if result is None:
            return None
        return _doc_to_product(result)

    async def delete(self, product_id: str) -> bool:
        from bson import ObjectId

        result = await self._collection.delete_one(
            {"_id": ObjectId(product_id)}
        )
        return result.deleted_count > 0
