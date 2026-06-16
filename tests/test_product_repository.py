import pytest

from app.models.product import ProductConfig
from app.repositories.memory_product_repo import MemoryProductRepository


@pytest.fixture
def repo():
    return MemoryProductRepository()


@pytest.fixture
def sample_product():
    return ProductConfig(
        product_id="test-product",
        name="Test Product",
        mongo_uri="mongodb://localhost:27017",
        db_name="test_db",
    )


class TestMemoryProductRepository:

    async def test_create_and_get(self, repo, sample_product):
        created = await repo.create(sample_product)
        assert created.product_id == sample_product.product_id

        fetched = await repo.get(sample_product.product_id)
        assert fetched is not None
        assert fetched.name == sample_product.name
        assert fetched.created_at is not None
        assert fetched.updated_at is not None

    async def test_get_missing(self, repo):
        result = await repo.get("non-existent")
        assert result is None

    async def test_list_empty(self, repo):
        products = await repo.list()
        assert products == []

    async def test_list_with_items(self, repo):
        p1 = ProductConfig(
            product_id="p1",
            name="P1",
            mongo_uri="mongodb://localhost",
            db_name="p1",
        )
        p2 = ProductConfig(
            product_id="p2",
            name="P2",
            mongo_uri="mongodb://localhost",
            db_name="p2",
        )
        await repo.create(p1)
        await repo.create(p2)
        products = await repo.list()
        assert len(products) == 2

    async def test_update(self, repo, sample_product):
        await repo.create(sample_product)
        updated = await repo.update(
            sample_product.product_id, {"name": "Updated Name"}
        )
        assert updated is not None
        assert updated.name == "Updated Name"

    async def test_update_missing(self, repo):
        result = await repo.update("non-existent", {"name": "X"})
        assert result is None

    async def test_delete(self, repo, sample_product):
        await repo.create(sample_product)
        deleted = await repo.delete(sample_product.product_id)
        assert deleted is True
        assert await repo.get(sample_product.product_id) is None

    async def test_delete_missing(self, repo):
        result = await repo.delete("non-existent")
        assert result is False
