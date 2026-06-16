import uuid

from app.models.product import ProductConfig, now_utc
from app.repositories.product_repository import ProductRepository


class MemoryProductRepository(ProductRepository):

    def __init__(self) -> None:
        self._store: dict[str, ProductConfig] = {}

    async def create(self, product: ProductConfig) -> ProductConfig:
        now = now_utc()
        product.id = uuid.uuid4().hex[:24]
        product.created_at = now
        product.updated_at = now
        self._store[product.id] = product.model_copy(deep=True)
        return self._store[product.id]

    async def get(self, product_id: str) -> ProductConfig | None:
        return self._store.get(product_id)

    async def list(self) -> list[ProductConfig]:
        return list(self._store.values())

    async def update(
        self, product_id: str, data: dict[str, object]
    ) -> ProductConfig | None:
        existing = self._store.get(product_id)
        if existing is None:
            return None
        for key, value in data.items():
            if value is not None and hasattr(existing, key):
                setattr(existing, key, value)
        existing.updated_at = now_utc()
        return existing.model_copy(deep=True)

    async def delete(self, product_id: str) -> bool:
        if product_id in self._store:
            del self._store[product_id]
            return True
        return False
