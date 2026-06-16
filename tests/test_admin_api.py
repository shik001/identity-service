import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import get_product_repository
from app.config import Settings
from app.main import create_app
from app.repositories.memory_product_repo import MemoryProductRepository


@pytest.fixture
def repo():
    return MemoryProductRepository()


@pytest.fixture
def app(repo) -> FastAPI:
    settings = Settings(config_db_uri="", config_db_name="test")
    _app = create_app(settings=settings)
    _app.dependency_overrides[get_product_repository] = lambda: repo
    return _app


@pytest.fixture
def client(app) -> TestClient:
    with TestClient(app) as c:
        yield c


PAYLOAD = {
    "product_id": "kol-intelligence",
    "name": "KOL Intelligence",
    "mongo_uri": "mongodb://localhost:27017",
    "db_name": "kol_intelligence",
}


class TestAdminAPI:

    def test_create_product(self, client):
        resp = client.post("/admin/products", json=PAYLOAD)
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["product_id"] == "kol-intelligence"
        assert data["name"] == "KOL Intelligence"

    def test_create_duplicate(self, client):
        client.post("/admin/products", json=PAYLOAD)
        resp = client.post("/admin/products", json=PAYLOAD)
        assert resp.status_code == 409

    def test_list_products_empty(self, client):
        resp = client.get("/admin/products")
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_list_products_with_items(self, client):
        client.post("/admin/products", json=PAYLOAD)
        resp = client.get("/admin/products")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 1

    def test_get_product(self, client):
        client.post("/admin/products", json=PAYLOAD)
        resp = client.get("/admin/products/kol-intelligence")
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "KOL Intelligence"

    def test_get_product_not_found(self, client):
        resp = client.get("/admin/products/non-existent")
        assert resp.status_code == 404

    def test_update_product(self, client):
        client.post("/admin/products", json=PAYLOAD)
        resp = client.put(
            "/admin/products/kol-intelligence",
            json={"name": "Updated"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "Updated"

    def test_update_product_not_found(self, client):
        resp = client.put(
            "/admin/products/non-existent",
            json={"name": "X"},
        )
        assert resp.status_code == 404

    def test_delete_product(self, client):
        client.post("/admin/products", json=PAYLOAD)
        resp = client.delete("/admin/products/kol-intelligence")
        assert resp.status_code == 204

    def test_delete_product_not_found(self, client):
        resp = client.delete("/admin/products/non-existent")
        assert resp.status_code == 404
