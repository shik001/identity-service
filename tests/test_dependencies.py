import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import get_product_repository
from app.config import Settings
from app.main import create_app
from app.repositories.memory_product_repo import MemoryProductRepository


@pytest.fixture
def product_repo():
    return MemoryProductRepository()


@pytest.fixture
def app(product_repo) -> FastAPI:
    settings = Settings(config_db_uri="", config_db_name="test")
    _app = create_app(settings=settings)
    _app.dependency_overrides[get_product_repository] = lambda: product_repo
    return _app


@pytest.fixture
def client(app) -> TestClient:
    with TestClient(app) as c:
        yield c


class TestDependencies:

    def test_get_product_from_path_404(self, client):
        resp = client.get("/admin/products/non-existent")
        assert resp.status_code == 404

    def test_get_product_from_path_ok(self, client):
        client.post(
            "/admin/products",
            json={
                "product_id": "test-product",
                "name": "Test",
                "mongo_uri": "mongodb://localhost",
                "db_name": "test",
            },
        )
        resp = client.get("/admin/products/test-product")
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "Test"
