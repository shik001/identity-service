from abc import ABC, abstractmethod

from app.models.product import ProductConfig


class ProductRepository(ABC):

    @abstractmethod
    async def create(self, product: ProductConfig) -> ProductConfig: ...

    @abstractmethod
    async def get(self, product_id: str) -> ProductConfig | None: ...

    @abstractmethod
    async def list(self) -> list[ProductConfig]: ...

    @abstractmethod
    async def update(
        self, product_id: str, data: dict[str, object]
    ) -> ProductConfig | None: ...

    @abstractmethod
    async def delete(self, product_id: str) -> bool: ...
