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
    "name": "KOL Intelligence",
    "mongo_uri": "mongodb://localhost:27017",
    "db_name": "kol_intelligence",
}


class TestAdminAPI:

    def test_create_product(self, client):
        resp = client.post("/admin/products", json=PAYLOAD)
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["id"] != ""
        assert data["name"] == "KOL Intelligence"

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
        create_resp = client.post("/admin/products", json=PAYLOAD)
        product_id = create_resp.json()["data"]["id"]
        resp = client.get(f"/admin/products/{product_id}")
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "KOL Intelligence"

    def test_get_product_not_found(self, client):
        resp = client.get("/admin/products/000000000000000000000000")
        assert resp.status_code == 404

    def test_update_product(self, client):
        create_resp = client.post("/admin/products", json=PAYLOAD)
        product_id = create_resp.json()["data"]["id"]
        resp = client.put(
            f"/admin/products/{product_id}",
            json={"name": "Updated"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "Updated"

    def test_update_product_not_found(self, client):
        resp = client.put(
            "/admin/products/000000000000000000000000",
            json={"name": "X"},
        )
        assert resp.status_code == 404

    def test_delete_product(self, client):
        create_resp = client.post("/admin/products", json=PAYLOAD)
        product_id = create_resp.json()["data"]["id"]
        resp = client.delete(f"/admin/products/{product_id}")
        assert resp.status_code == 204

    def test_delete_product_not_found(self, client):
        resp = client.delete("/admin/products/000000000000000000000000")
        assert resp.status_code == 404
